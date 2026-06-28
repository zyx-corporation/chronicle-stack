"""Local-first federation package creation and verification."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from chronicle import __version__
from chronicle.errors import ChronicleError
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.federation_package import (
    FederationPackageFileEntry,
    FederationPackageManifest,
    FederationPackageConsent,
    FederationPackagePreviewFinding,
    FederationPackagePreviewReport,
    FederationPackageRedactionReport,
    FederationPackageSignature,
    FederationPackageSignatureMode,
    FederationPackageSignatureStatus,
    FederationPackageVisibilityMappingEntry,
    FederationPackageVerificationEntry,
    FederationPackageVerificationReport,
    FederationPackageVisibility,
)
from chronicle.models.integration_package import IntegrationTargetEnvironment
from chronicle.security.integrity import canonical_json_bytes
from chronicle.services.audit_service import AuditService
from chronicle.services.integration_package_service import IntegrationPackageService


class FederationPackageService:
    _LOCAL_DEV_SIGNING_KEYS = {
        "local-dev-key": "chronicle-local-dev-signing-key",
        "local-dev-rotated": "chronicle-local-dev-signing-key-rotated",
    }

    def __init__(self, root: Path | None = None) -> None:
        self.integration_packages = IntegrationPackageService(root)
        self.paths = self.integration_packages.chronicle.paths
        self.audit = AuditService(root)

    def create_package(
        self,
        *,
        purpose: str,
        target_node: str,
        output_dir: Path,
        created_by_node: str = "node:local:default",
        visibility: FederationPackageVisibility = FederationPackageVisibility.FEDERATED,
        context_ids: list[str] | None = None,
        trust_target_node: str | None = None,
        signature_mode: FederationPackageSignatureMode = FederationPackageSignatureMode.UNSIGNED,
        signature_key_id: str = "local-dev-key",
        signature_expires_at: datetime | None = None,
        signature_revoked: bool = False,
        signature_revocation_reason: str | None = None,
        consent_granted_by: str = "",
        consent_recorded_at: datetime | None = None,
        consent_scope: str = "",
        third_party_sharing_allowed: bool = False,
        third_party_sharing_reason: str | None = None,
    ) -> FederationPackageManifest:
        package = self.integration_packages.build_context_package(
            purpose=purpose,
            target_environment=IntegrationTargetEnvironment.EXTERNAL,
            context_ids=context_ids,
            trust_target_node=trust_target_node or target_node,
        )
        metadata = self.integration_packages.chronicle.require_initialized()
        output_dir.mkdir(parents=True, exist_ok=True)

        records_jsonl = "\n".join(
            json.dumps(record.model_dump(mode="json"), ensure_ascii=False) for record in package.records
        )
        (output_dir / "records.jsonl").write_text(records_jsonl + ("\n" if records_jsonl else ""), encoding="utf-8")

        visibility_mappings = [
            self._visibility_mapping_for_record(record)
            for record in package.records
        ]
        report = FederationPackageRedactionReport(
            record_count=len(package.records),
            reference_only_record_ids=[
                record.record_id
                for record in package.records
                if record.content_boundary.value == "reference_only"
            ],
            visibility_mappings=visibility_mappings,
            warning_codes=sorted(
                {
                    *package.manifest.warnings,
                    *(warning for record in package.records for warning in record.warnings),
                    *(
                        {"package_visibility_broader_than_recommended"}
                        if any(
                            self._visibility_rank(visibility) > self._visibility_rank(mapping.recommended_visibility)
                            for mapping in visibility_mappings
                        )
                        else set()
                    ),
                }
            ),
            notes=[
                "Redaction report is advisory and derived from current package boundaries.",
                "Reference-only records stay excluded from body export.",
                "No received-side import or auto-apply behavior is implied by this package.",
                "Visibility mappings are recommendations derived from Chronicle visibility and classification metadata.",
            ],
        )
        (output_dir / "redaction-report.json").write_text(
            json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        readme_text = "\n".join(
            [
                "# Chronicle Federation Package",
                "",
                f"- Purpose: {purpose}",
                f"- Target node: {target_node}",
                f"- Visibility: {visibility.value}",
                f"- Referenced records: {len(package.manifest.referenced_records)}",
                "",
                "Boundary:",
                "- local-first descriptive handoff only",
                "- no unattended sync, no auto-application, no hosted runtime",
                "- Chronicle primary records remain authoritative over this bundle",
            ]
        )
        (output_dir / "README.md").write_text(readme_text, encoding="utf-8")

        manifest = FederationPackageManifest(
            package_id=package.manifest.package_id,
            chronicle_id=metadata.chronicle_id,
            created_at=datetime.now(timezone.utc).astimezone(),
            created_by_node=created_by_node,
            target_node=target_node,
            purpose=purpose,
            visibility=visibility,
            source_root=str(self.paths.root),
            tool_version=__version__,
            referenced_records=package.manifest.referenced_records,
            warnings=sorted(set(package.manifest.warnings)),
            consent=FederationPackageConsent(
                status="recorded" if consent_granted_by else "not_recorded",
                granted_by=consent_granted_by,
                recorded_at=consent_recorded_at,
                purpose=purpose,
                scope=consent_scope,
                third_party_sharing_allowed=third_party_sharing_allowed,
                third_party_sharing_reason=third_party_sharing_reason,
            ),
            notes=[
                "Package stays local-first and reviewable before any transport decision.",
                "Signature is a placeholder until a later signed-manifest phase.",
            ],
            metadata={
                **package.manifest.metadata,
                "integration_package_kind": package.manifest.package_kind.value,
                "output_classification": package.manifest.output_classification,
            },
        )

        manifest.files = [
            self._file_entry(output_dir / "records.jsonl", output_dir),
            self._file_entry(output_dir / "redaction-report.json", output_dir),
            self._file_entry(output_dir / "README.md", output_dir),
        ]
        manifest.signature = self._build_signature(
            manifest=manifest,
            signature_mode=signature_mode,
            signature_key_id=signature_key_id,
            signature_expires_at=signature_expires_at,
            signature_revoked=signature_revoked,
            signature_revocation_reason=signature_revocation_reason,
        )
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._record_package_audit(
            manifest=manifest,
            output_dir=output_dir,
            visibility_mappings=visibility_mappings,
        )
        return manifest

    def inspect_package(self, package_dir: Path) -> dict[str, object]:
        manifest = self._load_manifest(package_dir)
        report_path = package_dir / "redaction-report.json"
        report = FederationPackageRedactionReport.model_validate(
            json.loads(report_path.read_text(encoding="utf-8"))
        )
        return {
            "manifest": manifest.model_dump(mode="json"),
            "redaction_report": report.model_dump(mode="json"),
        }

    def verify_package(self, package_dir: Path) -> FederationPackageVerificationReport:
        manifest = self._load_manifest(package_dir)
        entries: list[FederationPackageVerificationEntry] = []
        warnings: list[str] = []
        for file_entry in manifest.files:
            file_path = package_dir / file_entry.path
            exists = file_path.exists()
            actual = self._sha256(file_path) if exists else None
            matches = exists and actual == file_entry.sha256
            entries.append(
                FederationPackageVerificationEntry(
                    path=file_entry.path,
                    expected_sha256=file_entry.sha256,
                    actual_sha256=actual,
                    exists=exists,
                    matches=matches,
                )
            )
        signature_status, signature_warnings = self._verify_signature(manifest)
        warnings.extend(signature_warnings)
        valid = all(entry.matches for entry in entries) and signature_status in {
            FederationPackageSignatureStatus.UNSIGNED,
            FederationPackageSignatureStatus.SIGNED,
        }
        return FederationPackageVerificationReport(
            package_path=str(package_dir),
            manifest_path=str(package_dir / "manifest.json"),
            signature_status=signature_status,
            valid=valid,
            files_checked=entries,
            warnings=warnings,
        )

    def preview_package(self, package_dir: Path) -> FederationPackagePreviewReport:
        inspect_payload = self.inspect_package(package_dir)
        verification = self.verify_package(package_dir)
        manifest = FederationPackageManifest.model_validate(inspect_payload["manifest"])
        redaction_report = FederationPackageRedactionReport.model_validate(inspect_payload["redaction_report"])
        findings = self._preview_findings(manifest, redaction_report, verification)
        status = self._preview_status(findings)
        warning_codes = [finding.code for finding in findings if finding.severity != "pass"]
        return FederationPackagePreviewReport(
            package_path=str(package_dir),
            status=status,
            import_candidate=verification.valid and status != "blocked",
            boundary_note=(
                "Federation package preview remains derived, read-only, and non-authoritative over Chronicle primary records."
            ),
            manifest=manifest.model_dump(mode="json"),
            redaction_report=redaction_report.model_dump(mode="json"),
            verification=verification.model_dump(mode="json"),
            findings=findings,
            warnings=warning_codes,
        )

    def import_preview_package(self, package_dir: Path) -> FederationPackagePreviewReport:
        preview = self.preview_package(package_dir)
        import_findings = list(preview.findings)
        if not preview.import_candidate:
            import_findings.append(
                FederationPackagePreviewFinding(
                    severity="blocked",
                    code="import_candidate_not_ready",
                    summary="Import preview remains blocked until structural verification and package review findings are resolved.",
                    recommendation="Re-run `chronicle federation package verify` and inspect preview findings before any manual import decision.",
                )
            )
        return FederationPackagePreviewReport(
            package_path=preview.package_path,
            status=self._preview_status(import_findings),
            import_candidate=preview.import_candidate,
            boundary_note=(
                "Import preview remains advisory and manual-only; Chronicle primary records stay authoritative until a separate import step is explicitly reviewed."
            ),
            manifest=preview.manifest,
            redaction_report=preview.redaction_report,
            verification=preview.verification,
            findings=import_findings,
            warnings=[finding.code for finding in import_findings if finding.severity != "pass"],
        )

    def boundary_check(
        self,
        *,
        purpose: str,
        target_node: str,
        visibility: FederationPackageVisibility = FederationPackageVisibility.FEDERATED,
        context_ids: list[str] | None = None,
        trust_target_node: str | None = None,
    ) -> dict[str, object]:
        package = self.integration_packages.build_context_package(
            purpose=purpose,
            target_environment=IntegrationTargetEnvironment.EXTERNAL,
            context_ids=context_ids,
            trust_target_node=trust_target_node or target_node,
        )
        visibility_mappings = [
            self._visibility_mapping_for_record(record)
            for record in package.records
        ]
        recommended_visibility = self._recommended_package_visibility(visibility_mappings)
        warning_codes = sorted(
            {
                *package.manifest.warnings,
                *(warning for record in package.records for warning in record.warnings),
                *(
                    {"package_visibility_broader_than_recommended"}
                    if self._visibility_rank(visibility) > self._visibility_rank(recommended_visibility)
                    else set()
                ),
                *(
                    {"consent_required_for_external_handoff"}
                    if package.records
                    else set()
                ),
            }
        )
        return {
            "status": "warning" if warning_codes else "pass",
            "purpose": purpose,
            "target_node": target_node,
            "requested_visibility": visibility.value,
            "recommended_visibility": recommended_visibility.value,
            "record_count": len(package.records),
            "referenced_records": package.manifest.referenced_records,
            "visibility_mappings": [item.model_dump(mode="json") for item in visibility_mappings],
            "warning_codes": warning_codes,
            "trust_preview": package.manifest.metadata.get("trust_preview", ""),
            "consent_required": bool(package.records),
            "boundary_note": (
                "Federation boundary check is a local preflight surface and does not create a package, transport data, or mutate Chronicle primary records."
            ),
        }

    def record_consent(
        self,
        *,
        target_node: str,
        purpose: str,
        scope: str,
        granted_by: str,
        third_party_sharing_allowed: bool,
        third_party_sharing_reason: str | None = None,
        context_ids: list[str] | None = None,
        recorded_at: datetime | None = None,
    ) -> dict[str, object]:
        self.integration_packages.chronicle.require_initialized()
        consent_recorded_at = recorded_at or datetime.now(timezone.utc).astimezone()
        audit = self.audit.record(
            operation=AuditOperation.CONSENT_RECORD,
            actor=granted_by or "unknown",
            purpose=purpose,
            target_environment=AuditTargetEnvironment.PACKAGE,
            referenced_records=context_ids or [],
            result=AuditSeverity.INFO,
            summary=f"Recorded federation consent for target node {target_node}.",
            metadata={
                "target_node": target_node,
                "consent_scope": scope,
                "third_party_sharing_allowed": str(third_party_sharing_allowed).lower(),
                "third_party_sharing_reason": third_party_sharing_reason or "",
                "recorded_at": consent_recorded_at.isoformat(),
            },
        )
        return {
            "status": "recorded",
            "audit_id": audit.audit_id,
            "target_node": target_node,
            "purpose": purpose,
            "scope": scope,
            "granted_by": granted_by,
            "recorded_at": consent_recorded_at.isoformat(),
            "third_party_sharing_allowed": third_party_sharing_allowed,
            "third_party_sharing_reason": third_party_sharing_reason,
            "referenced_records": context_ids or [],
            "boundary_note": (
                "Consent record is append-only audit metadata and does not create or import a federation package by itself."
            ),
        }

    def _load_manifest(self, package_dir: Path) -> FederationPackageManifest:
        manifest_path = package_dir / "manifest.json"
        if not package_dir.exists():
            raise ChronicleError(
                code="FEDERATION_PACKAGE_DIR_NOT_FOUND",
                message=f"Federation package directory not found: {package_dir}",
                hint="Create one with `chronicle federation package create ...` first.",
            )
        if not manifest_path.exists():
            raise ChronicleError(
                code="FEDERATION_PACKAGE_MANIFEST_NOT_FOUND",
                message=f"Federation package manifest not found: {manifest_path}",
                hint="Re-create the package so `manifest.json` is present.",
            )
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ChronicleError(
                code="FEDERATION_PACKAGE_MANIFEST_INVALID",
                message=f"Federation package manifest is not valid JSON: {manifest_path}",
                hint=str(exc),
            ) from exc
        return FederationPackageManifest.model_validate(payload)

    def _file_entry(self, path: Path, root: Path):
        return FederationPackageFileEntry(
            path=path.relative_to(root).as_posix(),
            sha256=self._sha256(path),
        )

    def _visibility_mapping_for_record(
        self, record
    ) -> FederationPackageVisibilityMappingEntry:
        source_visibility = record.metadata.get("visibility_hint", "unknown")
        classification_layer = record.classification_layer
        if classification_layer is not None and classification_layer >= 4:
            return FederationPackageVisibilityMappingEntry(
                record_id=record.record_id,
                source_visibility=source_visibility,
                classification_layer=classification_layer,
                recommended_visibility=FederationPackageVisibility.PRIVATE,
                rationale="restricted_secret_records_stay_private",
            )
        if classification_layer is not None and classification_layer >= 3:
            return FederationPackageVisibilityMappingEntry(
                record_id=record.record_id,
                source_visibility=source_visibility,
                classification_layer=classification_layer,
                recommended_visibility=FederationPackageVisibility.TRUSTED,
                rationale="sensitive_context_requires_trusted_sharing",
            )
        if classification_layer == 2:
            return FederationPackageVisibilityMappingEntry(
                record_id=record.record_id,
                source_visibility=source_visibility,
                classification_layer=classification_layer,
                recommended_visibility=FederationPackageVisibility.ORGANIZATION,
                rationale="internal_context_maps_to_organization_scope",
            )
        if classification_layer == 1:
            return FederationPackageVisibilityMappingEntry(
                record_id=record.record_id,
                source_visibility=source_visibility,
                classification_layer=classification_layer,
                recommended_visibility=FederationPackageVisibility.FEDERATED,
                rationale="shareable_context_maps_to_federated_scope",
            )
        if source_visibility == "private":
            return FederationPackageVisibilityMappingEntry(
                record_id=record.record_id,
                source_visibility=source_visibility,
                classification_layer=classification_layer,
                recommended_visibility=FederationPackageVisibility.PRIVATE,
                rationale="private_visibility_hint_stays_private",
            )
        if source_visibility == "sensitive":
            return FederationPackageVisibilityMappingEntry(
                record_id=record.record_id,
                source_visibility=source_visibility,
                classification_layer=classification_layer,
                recommended_visibility=FederationPackageVisibility.TRUSTED,
                rationale="sensitive_visibility_hint_limits_sharing",
            )
        if source_visibility == "public":
            return FederationPackageVisibilityMappingEntry(
                record_id=record.record_id,
                source_visibility=source_visibility,
                classification_layer=classification_layer,
                recommended_visibility=FederationPackageVisibility.PUBLIC,
                rationale="public_visibility_hint_can_remain_public",
            )
        return FederationPackageVisibilityMappingEntry(
            record_id=record.record_id,
            source_visibility=source_visibility,
            classification_layer=classification_layer,
            recommended_visibility=FederationPackageVisibility.FEDERATED,
            rationale="default_unknown_visibility_maps_to_reviewable_federated_scope",
        )

    def _preview_findings(
        self,
        manifest: FederationPackageManifest,
        redaction_report: FederationPackageRedactionReport,
        verification: FederationPackageVerificationReport,
    ) -> list[FederationPackagePreviewFinding]:
        findings: list[FederationPackagePreviewFinding] = []
        if verification.signature_status == FederationPackageSignatureStatus.UNSIGNED:
            findings.append(
                FederationPackagePreviewFinding(
                    severity="warning",
                    code="signature_unsigned",
                    summary="Manifest signature is unsigned, so provenance remains reviewable but not signed.",
                    recommendation="Use `--signature-mode local_dev` when you need a local signed-manifest review surface.",
                )
            )
        if verification.signature_status in {
            FederationPackageSignatureStatus.MISMATCH,
            FederationPackageSignatureStatus.EXPIRED,
            FederationPackageSignatureStatus.REVOKED,
        }:
            findings.append(
                FederationPackagePreviewFinding(
                    severity="blocked",
                    code=f"signature_{verification.signature_status.value}",
                    summary=f"Manifest signature status is `{verification.signature_status.value}`.",
                    recommendation="Resolve signature verification issues before any downstream preview or manual import decision.",
                )
            )
        if not verification.valid:
            findings.append(
                FederationPackagePreviewFinding(
                    severity="blocked",
                    code="payload_verification_failed",
                    summary="At least one payload file failed structural verification.",
                    recommendation="Recreate the federation package and rerun verification before sharing or import review.",
                )
            )
        if manifest.consent.status != "recorded":
            findings.append(
                FederationPackagePreviewFinding(
                    severity="warning",
                    code="consent_not_recorded",
                    summary="Consent metadata is not recorded for this federation package.",
                    recommendation="Add consent metadata when the sharing workflow requires explicit review provenance.",
                )
            )
        if not manifest.consent.third_party_sharing_allowed:
            findings.append(
                FederationPackagePreviewFinding(
                    severity="warning",
                    code="third_party_sharing_restricted",
                    summary="Third-party sharing remains restricted for this package.",
                    recommendation="Keep redistribution manual and limited to the declared target unless the restriction is updated.",
                )
            )
        if "package_visibility_broader_than_recommended" in redaction_report.warning_codes:
            findings.append(
                FederationPackagePreviewFinding(
                    severity="warning",
                    code="package_visibility_broader_than_recommended",
                    summary="Requested package visibility is broader than at least one record's recommended federation visibility.",
                    recommendation="Lower the package visibility or review the visibility mappings before external handoff.",
                )
            )
        return findings

    def _recommended_package_visibility(
        self, mappings: list[FederationPackageVisibilityMappingEntry]
    ) -> FederationPackageVisibility:
        if not mappings:
            return FederationPackageVisibility.FEDERATED
        return min(mappings, key=lambda item: self._visibility_rank(item.recommended_visibility)).recommended_visibility

    @staticmethod
    def _preview_status(findings: list[FederationPackagePreviewFinding]) -> str:
        if any(finding.severity == "blocked" for finding in findings):
            return "blocked"
        if any(finding.severity == "warning" for finding in findings):
            return "warning"
        return "pass"

    @staticmethod
    def _visibility_rank(visibility: FederationPackageVisibility) -> int:
        return {
            FederationPackageVisibility.PRIVATE: 0,
            FederationPackageVisibility.TRUSTED: 1,
            FederationPackageVisibility.PROJECT: 2,
            FederationPackageVisibility.ORGANIZATION: 3,
            FederationPackageVisibility.COMMUNITY: 4,
            FederationPackageVisibility.FEDERATED: 5,
            FederationPackageVisibility.PUBLIC: 6,
        }[visibility]

    def _build_signature(
        self,
        *,
        manifest: FederationPackageManifest,
        signature_mode: FederationPackageSignatureMode,
        signature_key_id: str,
        signature_expires_at: datetime | None,
        signature_revoked: bool,
        signature_revocation_reason: str | None,
    ) -> FederationPackageSignature:
        if signature_mode == FederationPackageSignatureMode.UNSIGNED:
            return FederationPackageSignature(
                algorithm="placeholder",
                key_id=signature_key_id,
                value="",
                status=FederationPackageSignatureStatus.UNSIGNED,
                expires_at=signature_expires_at,
            )
        if signature_mode != FederationPackageSignatureMode.LOCAL_DEV:
            raise ChronicleError(
                code="FEDERATION_PACKAGE_SIGNATURE_MODE_UNSUPPORTED",
                message=f"Unsupported federation package signature mode: {signature_mode}",
                hint="Use `unsigned` or `local_dev`.",
            )
        signing_key = self._LOCAL_DEV_SIGNING_KEYS.get(signature_key_id)
        if signing_key is None:
            raise ChronicleError(
                code="FEDERATION_PACKAGE_SIGNATURE_KEY_UNKNOWN",
                message=f"Unknown federation package signature key: {signature_key_id}",
                hint="Use one of the documented local dev signing keys.",
            )
        signed_at = datetime.now(timezone.utc).astimezone()
        status = FederationPackageSignatureStatus.REVOKED if signature_revoked else FederationPackageSignatureStatus.SIGNED
        signature = FederationPackageSignature(
            algorithm="local-dev-sha256",
            key_id=signature_key_id,
            value="",
            status=status,
            signed_at=signed_at,
            expires_at=signature_expires_at,
            revoked_at=signed_at if signature_revoked else None,
            revocation_reason=signature_revocation_reason if signature_revoked else None,
        )
        signature.value = self._sign_manifest_payload(manifest, signature, signing_key)
        return signature

    def _verify_signature(
        self, manifest: FederationPackageManifest
    ) -> tuple[FederationPackageSignatureStatus, list[str]]:
        signature = manifest.signature
        if signature.status == FederationPackageSignatureStatus.UNSIGNED:
            return signature.status, ["signature_unsigned"]
        if signature.status == FederationPackageSignatureStatus.REVOKED:
            return signature.status, ["signature_revoked"]
        if signature.expires_at and signature.expires_at < datetime.now(timezone.utc).astimezone():
            return FederationPackageSignatureStatus.EXPIRED, ["signature_expired"]
        signing_key = self._LOCAL_DEV_SIGNING_KEYS.get(signature.key_id)
        if signing_key is None:
            return FederationPackageSignatureStatus.MISMATCH, ["signature_key_unknown"]
        if signature.algorithm != "local-dev-sha256":
            return FederationPackageSignatureStatus.MISMATCH, ["signature_algorithm_unsupported"]
        expected = self._sign_manifest_payload(manifest, signature, signing_key)
        if expected != signature.value:
            return FederationPackageSignatureStatus.MISMATCH, ["signature_mismatch"]
        return FederationPackageSignatureStatus.SIGNED, []

    def _sign_manifest_payload(
        self,
        manifest: FederationPackageManifest,
        signature: FederationPackageSignature,
        signing_key: str,
    ) -> str:
        payload = {
            "schema_version": manifest.schema_version,
            "package_id": manifest.package_id,
            "chronicle_id": manifest.chronicle_id,
            "created_at": manifest.created_at.isoformat(),
            "created_by_node": manifest.created_by_node,
            "target_node": manifest.target_node,
            "purpose": manifest.purpose,
            "visibility": manifest.visibility.value,
            "source_root": manifest.source_root,
            "tool_version": manifest.tool_version,
            "referenced_records": manifest.referenced_records,
            "warnings": manifest.warnings,
            "files": [item.model_dump(mode="json") for item in manifest.files],
            "retention_policy": manifest.retention_policy.model_dump(mode="json"),
            "notes": manifest.notes,
            "metadata": manifest.metadata,
            "signature_meta": {
                "algorithm": signature.algorithm,
                "key_id": signature.key_id,
                "status": signature.status.value,
                "signed_at": signature.signed_at.isoformat() if signature.signed_at else None,
                "expires_at": signature.expires_at.isoformat() if signature.expires_at else None,
                "revoked_at": signature.revoked_at.isoformat() if signature.revoked_at else None,
                "revocation_reason": signature.revocation_reason,
            },
        }
        digest = hashlib.sha256()
        digest.update(signing_key.encode("utf-8"))
        digest.update(canonical_json_bytes(payload))
        return digest.hexdigest()

    def _record_package_audit(
        self,
        *,
        manifest: FederationPackageManifest,
        output_dir: Path,
        visibility_mappings: list[FederationPackageVisibilityMappingEntry],
    ) -> None:
        self.audit.record(
            operation=AuditOperation.EXPORT,
            actor="federation-package-service",
            purpose=manifest.purpose,
            target_environment=AuditTargetEnvironment.PACKAGE,
            output_classification=manifest.metadata.get("output_classification", "unknown"),
            referenced_records=manifest.referenced_records,
            result=AuditSeverity.INFO,
            summary=f"Created federation package {manifest.package_id}.",
            metadata={
                "package_id": manifest.package_id,
                "package_path": str(output_dir),
                "target_node": manifest.target_node,
                "visibility": manifest.visibility.value,
                "consent_status": manifest.consent.status,
                "consent_scope": manifest.consent.scope,
                "third_party_sharing_allowed": str(manifest.consent.third_party_sharing_allowed).lower(),
                "visibility_mapping_count": str(len(visibility_mappings)),
            },
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        digest.update(path.read_bytes())
        return digest.hexdigest()
