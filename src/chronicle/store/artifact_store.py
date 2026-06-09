"""Artifact file storage."""

from pathlib import Path

from chronicle.models.artifact import Artifact, ArtifactVersion


class ArtifactStore:
    def __init__(self, artifacts_dir: Path) -> None:
        self.artifacts_dir = artifacts_dir

    def create_artifact_files(
        self,
        artifact: Artifact,
        version: ArtifactVersion,
        source_file: Path | None = None,
        content: str | None = None,
    ) -> None:
        artifact_dir = self.artifacts_dir / artifact.artifact_id
        versions_dir = artifact_dir / "versions"
        versions_dir.mkdir(parents=True, exist_ok=True)

        body = self._read_content(source_file, content)
        current_path = artifact_dir / "current.md"
        version_path = versions_dir / f"{version.version_id}.md"

        current_path.write_text(body, encoding="utf-8")
        version_path.write_text(body, encoding="utf-8")

    def update_artifact_files(
        self,
        artifact_id: str,
        version: ArtifactVersion,
        source_file: Path | None = None,
        content: str | None = None,
    ) -> None:
        artifact_dir = self.artifacts_dir / artifact_id
        versions_dir = artifact_dir / "versions"
        versions_dir.mkdir(parents=True, exist_ok=True)

        body = self._read_content(source_file, content)
        current_path = artifact_dir / "current.md"
        version_path = versions_dir / f"{version.version_id}.md"

        current_path.write_text(body, encoding="utf-8")
        version_path.write_text(body, encoding="utf-8")

    def read_current(self, artifact_id: str) -> str:
        path = self.artifacts_dir / artifact_id / "current.md"
        return path.read_text(encoding="utf-8")

    def read_version(self, artifact_id: str, version_id: str) -> str:
        path = self.artifacts_dir / artifact_id / "versions" / f"{version_id}.md"
        return path.read_text(encoding="utf-8")

    def version_exists(self, artifact_id: str, version_id: str) -> bool:
        path = self.artifacts_dir / artifact_id / "versions" / f"{version_id}.md"
        return path.exists()

    def artifact_exists(self, artifact_id: str) -> bool:
        return (self.artifacts_dir / artifact_id).exists()

    @staticmethod
    def _read_content(source_file: Path | None, content: str | None) -> str:
        if source_file is not None:
            return source_file.read_text(encoding="utf-8")
        if content is not None:
            return content
        return ""
