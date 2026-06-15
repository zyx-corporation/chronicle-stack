"""YAML export."""

from pathlib import Path
from typing import Any

import yaml

from chronicle.exporters.redaction import RedactionOptions, transform_event_dump, transform_model_dump
from chronicle.lifecycle.derived_output_policy import LifecycleTargetState, lifecycle_state_by_target
from chronicle.models.event import ChronicleEvent
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.export_manifest_service import ExportManifestService
from chronicle.services.lifecycle_service import LifecycleService


def _event_target_ids(event: ChronicleEvent) -> set[str]:
    target_ids: set[str] = set()
    for key in ("context", "artifact", "decision", "boundary_rule"):
        value = event.payload.get(key)
        if isinstance(value, dict):
            for id_key in ("context_id", "artifact_id", "decision_id", "rule_id"):
                record_id = value.get(id_key)
                if isinstance(record_id, str):
                    target_ids.add(record_id)
    for id_key in ("context_id", "artifact_id", "decision_id", "rule_id", "target_id"):
        record_id = event.payload.get(id_key)
        if isinstance(record_id, str):
            target_ids.add(record_id)
    return target_ids


def _mark_lifecycle_sealed(data: dict[str, Any], state: LifecycleTargetState | None) -> dict[str, Any]:
    if state is None or not state.is_sealed:
        return data
    marked = dict(data)
    warnings = list(marked.get("warnings", []))
    if "lifecycle_sealed_record" not in warnings:
        warnings.append("lifecycle_sealed_record")
    marked["warnings"] = warnings
    return marked


class YamlExporter:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.manifest = ExportManifestService(root)
        self.lifecycle = LifecycleService(root)

    def export(
        self,
        output: Path | None = None,
        redaction: RedactionOptions | None = None,
    ) -> str:
        options = redaction or RedactionOptions()
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, versions = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        lifecycle_states = lifecycle_state_by_target(self.lifecycle.list_events())

        visible_artifacts = {
            artifact_id: artifact
            for artifact_id, artifact in artifacts.items()
            if not lifecycle_states.get(artifact_id, LifecycleTargetState(artifact_id)).is_tombstoned
        }
        visible_contexts = {
            context_id: context
            for context_id, context in contexts.items()
            if not lifecycle_states.get(context_id, LifecycleTargetState(context_id)).is_tombstoned
        }
        visible_events = [
            event
            for event in events
            if not any(
                lifecycle_states.get(target_id) is not None and lifecycle_states[target_id].is_tombstoned
                for target_id in _event_target_ids(event)
            )
        ]
        excluded_lifecycle_tombstone_count = (
            len(artifacts)
            + len(contexts)
            - len(visible_artifacts)
            - len(visible_contexts)
        )
        excluded_lifecycle_event_count = len(events) - len(visible_events)
        sealed_lifecycle_count = sum(
            1
            for record_id in [*visible_artifacts.keys(), *visible_contexts.keys()]
            if lifecycle_states.get(record_id) is not None and lifecycle_states[record_id].is_sealed
        )

        manifest = self.manifest.build_manifest(
            "yaml",
            export_options=options.as_manifest_options(),
        )
        manifest_dump = manifest.model_dump(mode="json")
        lifecycle_warnings: list[str] = []
        if excluded_lifecycle_tombstone_count:
            lifecycle_warnings.append("lifecycle_tombstoned_records_excluded")
        if excluded_lifecycle_event_count:
            lifecycle_warnings.append("lifecycle_tombstoned_events_excluded")
        if sealed_lifecycle_count:
            lifecycle_warnings.append("lifecycle_sealed_record")
        if lifecycle_warnings:
            manifest_dump["warnings"] = [*manifest_dump.get("warnings", []), *lifecycle_warnings]
            manifest_dump.setdefault("metadata", {})
            manifest_dump["metadata"].update({
                "excluded_lifecycle_tombstone_count": str(excluded_lifecycle_tombstone_count),
                "excluded_lifecycle_event_count": str(excluded_lifecycle_event_count),
                "sealed_lifecycle_count": str(sealed_lifecycle_count),
            })

        event_dumps = [transform_event_dump(e, options) for e in visible_events]
        artifact_dumps = {
            k: transform_model_dump(v, options)
            for k, v in visible_artifacts.items()
        }
        context_dumps = {
            k: transform_model_dump(v, options)
            for k, v in visible_contexts.items()
        }
        artifact_dumps = {
            k: _mark_lifecycle_sealed(v, lifecycle_states.get(k))
            for k, v in artifact_dumps.items()
            if v is not None
        }
        context_dumps = {
            k: _mark_lifecycle_sealed(v, lifecycle_states.get(k))
            for k, v in context_dumps.items()
            if v is not None
        }
        sensitive_artifact_ids = set(artifacts) - set(artifact_dumps)

        data = {
            "export_manifest": manifest_dump,
            "metadata": metadata.model_dump(mode="json"),
            "events": [e for e in event_dumps if e is not None],
            "artifacts": artifact_dumps,
            "versions": {
                aid: [v.model_dump(mode="json") for v in vlist]
                for aid, vlist in versions.items()
                if aid not in sensitive_artifact_ids
            },
            "contexts": context_dumps,
            "decisions": {k: v.model_dump(mode="json") for k, v in decisions.items()},
            "boundary_rules": {k: v.model_dump(mode="json") for k, v in boundary_rules.items()},
        }

        content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        if output:
            output.write_text(content, encoding="utf-8")
        return content
