"""Chronicle directory paths and layout."""

from pathlib import Path

CHRONICLE_DIR = ".chronicle"
EVENTS_FILE = "chronicle.jsonl"
AUDIT_FILE = "audit.jsonl"
LIFECYCLE_FILE = "lifecycle.jsonl"
METADATA_FILE = "metadata.yaml"
ARTIFACTS_DIR = "artifacts"
INDEXES_DIR = "indexes"
PACKAGES_DIR = "packages"
FEDERATION_DIR = "federation"
AI_INDEXES_DIR = "ai_indexes"
REPORTS_DIR = "reports/rde"
SUMMARY_JOBS_DIR = "summary_jobs"
REVIEWS_DIR = "reviews"
RUNTIME_CONFIG_FILE = "runtime.yaml"


class ChroniclePaths:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path.cwd()
        self.chronicle_dir = self.root / CHRONICLE_DIR
        self.events_file = self.chronicle_dir / EVENTS_FILE
        self.audit_file = self.chronicle_dir / AUDIT_FILE
        self.lifecycle_file = self.chronicle_dir / LIFECYCLE_FILE
        self.metadata_file = self.chronicle_dir / METADATA_FILE
        self.artifacts_dir = self.chronicle_dir / ARTIFACTS_DIR
        self.indexes_dir = self.chronicle_dir / INDEXES_DIR
        self.packages_dir = self.chronicle_dir / PACKAGES_DIR
        self.federation_dir = self.chronicle_dir / FEDERATION_DIR
        self.federation_inbox_dir = self.federation_dir / "inbox"
        self.federation_outbox_dir = self.federation_dir / "outbox"
        self.trust_dir = self.chronicle_dir / "trust"
        self.trust_nodes_dir = self.trust_dir / "nodes"
        self.trust_relations_dir = self.trust_dir / "relations"
        self.ai_indexes_dir = self.chronicle_dir / AI_INDEXES_DIR
        self.reports_dir = self.chronicle_dir / REPORTS_DIR
        self.summary_jobs_dir = self.chronicle_dir / SUMMARY_JOBS_DIR
        self.reviews_dir = self.chronicle_dir / REVIEWS_DIR
        self.runtime_config_file = self.chronicle_dir / RUNTIME_CONFIG_FILE
        self.artifact_index_file = self.indexes_dir / "artifact_index.json"
        self.context_index_file = self.indexes_dir / "context_index.json"
        self.decision_index_file = self.indexes_dir / "decision_index.json"
        self.rde_index_file = self.indexes_dir / "rde_index.json"
        self.boundary_rule_index_file = self.indexes_dir / "boundary_rule_index.json"
        self.vector_index_file = self.ai_indexes_dir / "vector_index.json"
        self.graph_index_file = self.ai_indexes_dir / "graph_index.json"

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

    def package_dir(self, package_id: str) -> Path:
        return self.packages_dir / package_id

    def package_manifest_path(self, package_id: str) -> Path:
        return self.package_dir(package_id) / "manifest.json"

    def package_records_path(self, package_id: str) -> Path:
        return self.package_dir(package_id) / "records.json"

    def rde_report_path(self, rde_record_id: str) -> Path:
        return self.reports_dir / f"{rde_record_id}.md"

    def summary_job_path(self, summary_job_id: str) -> Path:
        return self.summary_jobs_dir / f"{summary_job_id}.json"

    def review_decision_path(self, review_id: str) -> Path:
        return self.reviews_dir / f"{review_id}.json"
