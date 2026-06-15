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

    def load(self, package_id: str) -> IntegrationPackage:
        manifest_raw = json.loads(self.paths.package_manifest_path(package_id).read_text(encoding="utf-8"))
        records_raw = json.loads(self.paths.package_records_path(package_id).read_text(encoding="utf-8"))
        return IntegrationPackage(
            manifest=IntegrationPackageManifest.model_validate(manifest_raw),
            records=[IntegrationPackageRecord.model_validate(record) for record in records_raw],
        )
