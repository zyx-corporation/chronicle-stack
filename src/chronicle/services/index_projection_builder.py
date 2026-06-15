"""Build derived index projections from Chronicle events."""

from chronicle.models.artifact import Artifact, ArtifactVersion
from chronicle.models.boundary import BoundaryRule
from chronicle.models.context import Context
from chronicle.models.decision import Decision
from chronicle.models.event import ChronicleEvent, EventType
from chronicle.models.index_projection import IndexProjection
from chronicle.models.rde import RdeDiffRecord


class IndexProjectionBuilder:
    """Project Chronicle events into typed derived indexes.

    This builder interprets event payloads but does not read from or write to
    storage. Persistence remains the responsibility of ChronicleService and
    IndexStore.
    """

    def build(self, events: list[ChronicleEvent]) -> IndexProjection:
        raw = _RawIndexProjection()
        for event in events:
            raw.apply(event)
        return raw.to_projection()


class _RawIndexProjection:
    """Mutable raw projection state before model validation."""

    def __init__(self) -> None:
        self.artifacts: dict = {}
        self.versions: dict = {}
        self.contexts: dict = {}
        self.decisions: dict = {}
        self.rde_records: dict = {}
        self.boundary_rules: dict = {}

    def apply(self, event: ChronicleEvent) -> None:
        payload = event.payload
        if event.event_type == EventType.CONTEXT_ADDED and "context" in payload:
            self._apply_context(payload["context"])
        elif event.event_type == EventType.ARTIFACT_CREATED and "artifact" in payload:
            self._apply_artifact_created(payload)
        elif event.event_type in (
            EventType.ARTIFACT_UPDATED,
            EventType.ARTIFACT_VERSIONED,
        ) and "version" in payload:
            self._apply_artifact_versioned(payload)
        elif event.event_type == EventType.DECISION_RECORDED and "decision" in payload:
            self._apply_decision(payload["decision"])
        elif event.event_type == EventType.RDE_DIFF_RECORDED and "rde" in payload:
            self._apply_rde(payload["rde"])
        elif event.event_type == EventType.BOUNDARY_RULE_ADDED and "boundary_rule" in payload:
            self._apply_boundary_rule(payload["boundary_rule"])

    def _apply_context(self, context_data: dict) -> None:
        self.contexts[context_data["context_id"]] = context_data

    def _apply_artifact_created(self, payload: dict) -> None:
        artifact_data = payload["artifact"]
        self.artifacts[artifact_data["artifact_id"]] = artifact_data
        if "version" in payload:
            version_data = payload["version"]
            artifact_id = version_data["artifact_id"]
            self.versions.setdefault(artifact_id, []).append(version_data)

    def _apply_artifact_versioned(self, payload: dict) -> None:
        version_data = payload["version"]
        artifact_id = version_data["artifact_id"]
        self.versions.setdefault(artifact_id, []).append(version_data)
        if "artifact" in payload:
            artifact_data = payload["artifact"]
            self.artifacts[artifact_data["artifact_id"]] = artifact_data

    def _apply_decision(self, decision_data: dict) -> None:
        self.decisions[decision_data["decision_id"]] = decision_data

    def _apply_rde(self, rde_data: dict) -> None:
        self.rde_records[rde_data["rde_record_id"]] = rde_data

    def _apply_boundary_rule(self, boundary_rule_data: dict) -> None:
        self.boundary_rules[boundary_rule_data["rule_id"]] = boundary_rule_data

    def to_projection(self) -> IndexProjection:
        parsed_versions = self._parsed_versions()
        self._attach_rde_record_ids(parsed_versions)
        return IndexProjection(
            artifacts={k: Artifact.model_validate(v) for k, v in self.artifacts.items()},
            versions=parsed_versions,
            contexts={k: Context.model_validate(v) for k, v in self.contexts.items()},
            decisions={k: Decision.model_validate(v) for k, v in self.decisions.items()},
            rde_records={k: RdeDiffRecord.model_validate(v) for k, v in self.rde_records.items()},
            boundary_rules={k: BoundaryRule.model_validate(v) for k, v in self.boundary_rules.items()},
        )

    def _parsed_versions(self) -> dict[str, list[ArtifactVersion]]:
        return {
            artifact_id: [ArtifactVersion.model_validate(version) for version in version_list]
            for artifact_id, version_list in self.versions.items()
        }

    def _attach_rde_record_ids(self, parsed_versions: dict[str, list[ArtifactVersion]]) -> None:
        for rde_data in self.rde_records.values():
            to_version_id = rde_data.get("to_version_id")
            rde_id = rde_data["rde_record_id"]
            if not to_version_id:
                continue
            for version_list in parsed_versions.values():
                for version in version_list:
                    if version.version_id == to_version_id:
                        version.rde_record_id = rde_id
                        break
