"""Persistence for controlled integration packages."""

import json
from pathlib import Path

from chronicle.models.integration_package import IntegrationPackage, IntegrationPackageManifest, IntegrationPackageRecord
from chronicle.store.paths import ChroniclePaths


class IntegrationPackageStore:
    """Store controlled integration packages under `.chronicle/packages`.

    This store persists package transport artifacts only. It does not call models,
    vector databases, graph databases, or external runtimes.
    """

    def __init__(self, paths: ChroniclePaths) -> None:
        self.paths = paths

    def save(self, package: IntegrationPackage) -> Path:
        package_id = package.manifest.package_id
        package_dir = self.paths.package_dir(package_id)
        package_dir.mkdir(parents=True, exist_ok=True)

        self.paths.package_manifest_path(package_id).write_text(
            json.dumps(package.manifest.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.paths.package_records_path(package_id).write_text(
            json.dumps([record.model_dump(mode="json") for record in package.records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return package_dir

    def list_package_ids(self) -> list[str]:
        """Return persisted package IDs that have a manifest file."""
        if not self.paths.packages_dir.exists():
            return []
        return sorted(
            package_dir.name
            for package_dir in self.paths.packages_dir.iterdir()
            if package_dir.is_dir() and (package_dir / "manifest.json").exists()
        )

    def load_manifest(self, package_id: str) -> IntegrationPackageManifest:
        manifest_raw = json.loads(self.paths.package_manifest_path(package_id).read_text(encoding="utf-8"))
        return IntegrationPackageManifest.model_validate(manifest_raw)

    def load_records(self, package_id: str) -> list[IntegrationPackageRecord]:
        records_raw = json.loads(self.paths.package_records_path(package_id).read_text(encoding="utf-8"))
        return [IntegrationPackageRecord.model_validate(record) for record in records_raw]

    def load(self, package_id: str) -> IntegrationPackage:
        return IntegrationPackage(
            manifest=self.load_manifest(package_id),
            records=self.load_records(package_id),
        )
