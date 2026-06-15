"""YAML export."""

from pathlib import Path

import yaml

from chronicle.exporters.redaction import RedactionOptions, transform_event_dump, transform_model_dump
from chronicle.lifecycle.derived_output_policy import (
    LIFECYCLE_SEALED_RECORD_WARNING,
    count_sealed_targets,
    event_references_tombstoned_target,
    is_lifecycle_tombstoned,
    lifecycle_state_by_target,
    mark_lifecycle_sealed_warning,
)
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.export_manifest_service import ExportManifestService
from chronicle.services.lifecycle_service import LifecycleService


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
            if not is_lifecycle_tombstoned(artifact_id, lifecycle_states)
        }
        visible_contexts = {
            context_id: context
            for context_id, context in contexts.items()
            if not is_lifecycle_tombstoned(context_id, lifecycle_states)
        }
        visible_events = [
            event
            for event in events
            if not event_references_tombstoned_target(event, lifecycle_states)
        ]
        excluded_lifecycle_tombstone_count = (
            len(artifacts)
            + len(contexts)
            - len(visible_artifacts)
            - len(visible_contexts)
        )
        excluded_lifecycle_event_count = len(events) - len(visible_events)
        sealed_lifecycle_count = count_sealed_targets(
            [*visible_artifacts.keys(), *visible_contexts.keys()],
            lifecycle_states,
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
            lifecycle_warnings.append(LIFECYCLE_SEALED_RECORD_WARNING)
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
            k: mark_lifecycle_sealed_warning(v, lifecycle_states.get(k))
            for k, v in artifact_dumps.items()
            if v is not None
        }
        context_dumps = {
            k: mark_lifecycle_sealed_warning(v, lifecycle_states.get(k))
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
