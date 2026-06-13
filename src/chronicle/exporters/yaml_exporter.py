"""YAML export."""

from pathlib import Path

import yaml

from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.export_manifest_service import ExportManifestService


class YamlExporter:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.manifest = ExportManifestService(root)

    def export(self, output: Path | None = None) -> str:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, versions = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        manifest = self.manifest.build_manifest("yaml")

        data = {
            "export_manifest": manifest.model_dump(mode="json"),
            "metadata": metadata.model_dump(mode="json"),
            "events": [e.model_dump(mode="json") for e in events],
            "artifacts": {k: v.model_dump(mode="json") for k, v in artifacts.items()},
            "versions": {
                aid: [v.model_dump(mode="json") for v in vlist]
                for aid, vlist in versions.items()
            },
            "contexts": {k: v.model_dump(mode="json") for k, v in contexts.items()},
            "decisions": {k: v.model_dump(mode="json") for k, v in decisions.items()},
            "boundary_rules": {k: v.model_dump(mode="json") for k, v in boundary_rules.items()},
        }

        content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        if output:
            output.write_text(content, encoding="utf-8")
        return content
