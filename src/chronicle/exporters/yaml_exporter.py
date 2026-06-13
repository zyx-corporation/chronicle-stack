"""YAML export."""

from pathlib import Path

import yaml

from chronicle.exporters.redaction import RedactionOptions, transform_event_dump, transform_model_dump
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.export_manifest_service import ExportManifestService


class YamlExporter:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.manifest = ExportManifestService(root)

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
        manifest = self.manifest.build_manifest(
            "yaml",
            export_options=options.as_manifest_options(),
        )

        event_dumps = [transform_event_dump(e, options) for e in events]
        artifact_dumps = {k: transform_model_dump(v, options) for k, v in artifacts.items()}
        context_dumps = {k: transform_model_dump(v, options) for k, v in contexts.items()}
        artifact_dumps = {k: v for k, v in artifact_dumps.items() if v is not None}
        context_dumps = {k: v for k, v in context_dumps.items() if v is not None}
        sensitive_artifact_ids = set(artifacts) - set(artifact_dumps)

        data = {
            "export_manifest": manifest.model_dump(mode="json"),
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
