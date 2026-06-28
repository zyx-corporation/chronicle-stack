"""Local-first federation package creation and verification."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from chronicle import __version__
from chronicle.errors import ChronicleError
from chronicle.models.federation_package import (
    FederationPackageFileEntry,
    FederationPackageManifest,
    FederationPackageRedactionReport,
    FederationPackageVerificationEntry,
    FederationPackageVerificationReport,
    FederationPackageVisibility,
)
from chronicle.models.integration_package import IntegrationTargetEnvironment
from chronicle.services.integration_package_service import IntegrationPackageService


class FederationPackageService:
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
        if manifest.signature.status != "signed":
            warnings.append("signature_placeholder_only")
        valid = all(entry.matches for entry in entries)
        return FederationPackageVerificationReport(
            package_path=str(package_dir),
            manifest_path=str(package_dir / "manifest.json"),
            signature_status=manifest.signature.status,
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

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        digest.update(path.read_bytes())
        return digest.hexdigest()
