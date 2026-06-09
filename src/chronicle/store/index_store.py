"""Derived index storage."""

import json
from pathlib import Path

from chronicle.models.artifact import Artifact, ArtifactVersion
from chronicle.models.context import Context
from chronicle.models.decision import Decision


class IndexStore:
    def __init__(
        self,
        indexes_dir: Path,
        artifact_index_file: Path,
        context_index_file: Path,
        decision_index_file: Path,
    ) -> None:
        self.indexes_dir = indexes_dir
        self.artifact_index_file = artifact_index_file
        self.context_index_file = context_index_file
        self.decision_index_file = decision_index_file

    def save_artifacts(
        self,
        artifacts: dict[str, Artifact],
        versions: dict[str, list[ArtifactVersion]],
    ) -> None:
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "artifacts": {k: v.model_dump(mode="json") for k, v in artifacts.items()},
            "versions": {
                aid: [v.model_dump(mode="json") for v in vlist]
                for aid, vlist in versions.items()
            },
        }
        self.artifact_index_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_artifacts(
        self,
    ) -> tuple[dict[str, Artifact], dict[str, list[ArtifactVersion]]]:
        if not self.artifact_index_file.exists():
            return {}, {}

        raw = json.loads(self.artifact_index_file.read_text(encoding="utf-8"))
        artifacts = {
            k: Artifact.model_validate(v) for k, v in raw.get("artifacts", {}).items()
        }
        versions = {
            aid: [ArtifactVersion.model_validate(v) for v in vlist]
            for aid, vlist in raw.get("versions", {}).items()
        }
        return artifacts, versions

    def save_contexts(self, contexts: dict[str, Context]) -> None:
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        data = {k: v.model_dump(mode="json") for k, v in contexts.items()}
        self.context_index_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_contexts(self) -> dict[str, Context]:
        if not self.context_index_file.exists():
            return {}
        raw = json.loads(self.context_index_file.read_text(encoding="utf-8"))
        return {k: Context.model_validate(v) for k, v in raw.items()}

    def save_decisions(self, decisions: dict[str, Decision]) -> None:
        self.indexes_dir.mkdir(parents=True, exist_ok=True)
        data = {k: v.model_dump(mode="json") for k, v in decisions.items()}
        self.decision_index_file.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load_decisions(self) -> dict[str, Decision]:
        if not self.decision_index_file.exists():
            return {}
        raw = json.loads(self.decision_index_file.read_text(encoding="utf-8"))
        return {k: Decision.model_validate(v) for k, v in raw.items()}
