"""Local-first federation package creation and verification."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from chronicle import __version__
from chronicle.errors import ChronicleError
from chronicle.security.integrity import canonical_json_bytes
from chronicle.models.federation_package import (
    FederationPackageFileEntry,
    FederationPackageManifest,
    FederationPackageRedactionReport,
    FederationPackageSignature,
    FederationPackageSignatureMode,
    FederationPackageSignatureStatus,
    FederationPackageVerificationEntry,
    FederationPackageVerificationReport,
    FederationPackageVisibility,
)
from chronicle.models.integration_package import IntegrationTargetEnvironment
from chronicle.services.integration_package_service import IntegrationPackageService


class FederationPackageService:
    _LOCAL_DEV_SIGNING_KEYS = {
        "local-dev-key": "chronicle-local-dev-signing-key",
        "local-dev-rotated": "chronicle-local-dev-signing-key-rotated",
    }

    def __init__(self, root: Path | None = None) -> None:
        self.integration_packages = IntegrationPackageService(root)
        self.paths = self.integration_packages.chronicle.paths

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

        report = FederationPackageRedactionReport(
            record_count=len(package.records),
            reference_only_record_ids=[
                record.record_id
                for record in package.records
                if record.content_boundary.value == "reference_only"
            ],
            warning_codes=sorted(
                {
                    *package.manifest.warnings,
                    *(warning for record in package.records for warning in record.warnings),
                }
            ),
            notes=[
                "Redaction report is advisory and derived from current package boundaries.",
                "Reference-only records stay excluded from body export.",
                "No received-side import or auto-apply behavior is implied by this package.",
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

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        digest.update(path.read_bytes())
        return digest.hexdigest()
