"""YAML export."""

from pathlib import Path

import yaml

from chronicle.services.chronicle_service import ChronicleService


class YamlExporter:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def export(self, output: Path | None = None) -> str:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, versions = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()

        data = {
            "metadata": metadata.model_dump(mode="json"),
            "events": [e.model_dump(mode="json") for e in events],
            "artifacts": {k: v.model_dump(mode="json") for k, v in artifacts.items()},
            "versions": {
                aid: [v.model_dump(mode="json") for v in vlist]
                for aid, vlist in versions.items()
            },
            "contexts": {k: v.model_dump(mode="json") for k, v in contexts.items()},
            "decisions": {k: v.model_dump(mode="json") for k, v in decisions.items()},
        }

        content = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        if output:
            output.write_text(content, encoding="utf-8")
        return content
