"""Chronicle directory paths and layout."""

from pathlib import Path

CHRONICLE_DIR = ".chronicle"
EVENTS_FILE = "chronicle.jsonl"
METADATA_FILE = "metadata.yaml"
ARTIFACTS_DIR = "artifacts"
INDEXES_DIR = "indexes"
REPORTS_DIR = "reports/rde"


class ChroniclePaths:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.chronicle_dir = self.root / CHRONICLE_DIR
        self.events_file = self.chronicle_dir / EVENTS_FILE
        self.metadata_file = self.chronicle_dir / METADATA_FILE
        self.artifacts_dir = self.chronicle_dir / ARTIFACTS_DIR
        self.indexes_dir = self.chronicle_dir / INDEXES_DIR
        self.reports_dir = self.chronicle_dir / REPORTS_DIR
        self.artifact_index_file = self.indexes_dir / "artifact_index.json"
        self.context_index_file = self.indexes_dir / "context_index.json"
        self.decision_index_file = self.indexes_dir / "decision_index.json"

    def is_initialized(self) -> bool:
        return self.events_file.exists() and self.metadata_file.exists()

    def artifact_dir(self, artifact_id: str) -> Path:
        return self.artifacts_dir / artifact_id

    def artifact_current(self, artifact_id: str) -> Path:
        return self.artifact_dir(artifact_id) / "current.md"

    def artifact_versions_dir(self, artifact_id: str) -> Path:
        return self.artifact_dir(artifact_id) / "versions"

    def artifact_version_path(self, artifact_id: str, version_id: str) -> Path:
        return self.artifact_versions_dir(artifact_id) / f"{version_id}.md"

    def rde_report_path(self, rde_record_id: str) -> Path:
        return self.reports_dir / f"{rde_record_id}.md"
