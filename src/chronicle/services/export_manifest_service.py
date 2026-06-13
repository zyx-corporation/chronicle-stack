"""Build export manifest metadata for derived export outputs."""

from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path
from typing import Any

from chronicle.models.export_manifest import ExportManifest
from chronicle.services.chronicle_service import ChronicleService


class ExportManifestService:
    """Create non-authoritative provenance metadata for exports."""

    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def build_manifest(
        self,
        export_format: str,
        *,
        export_options: dict[str, Any] | None = None,
    ) -> ExportManifest:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        return ExportManifest(
            export_format=export_format,
            generated_at=datetime.now(timezone.utc).astimezone(),
            chronicle_id=metadata.chronicle_id,
            chronicle_title=metadata.title,
            tool_version=self._tool_version(),
            event_count=len(events),
            export_options=export_options or {},
            notes=[
                "This manifest is provenance metadata, not cryptographic proof.",
                "Export outputs are derived views; chronicle.jsonl remains primary.",
            ],
        )

    @staticmethod
    def _tool_version() -> str:
        try:
            return package_version("chronicle-stack")
        except PackageNotFoundError:
            return "0.0.0+unknown"
