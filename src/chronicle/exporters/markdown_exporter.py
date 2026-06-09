"""Markdown export."""

from pathlib import Path

from chronicle.services.chronicle_service import ChronicleService


class MarkdownExporter:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)

    def export(self, output: Path | None = None) -> str:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, versions = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()

        lines = [
            f"# Chronicle: {metadata.title}",
            "",
            f"- ID: `{metadata.chronicle_id}`",
            f"- Created: {metadata.created_at.isoformat()}",
            f"- Schema: {metadata.schema_version}",
            "",
            "## Events",
            "",
        ]

        for event in events:
            lines.append(
                f"- `{event.event_id}` **{event.event_type.value}** "
                f"({event.timestamp.strftime('%Y-%m-%d %H:%M')}) — {event.summary}"
            )

        lines.extend(["", "## Artifacts", ""])
        for artifact in artifacts.values():
            lines.append(f"### {artifact.title}")
            lines.append("")
            lines.append(f"- ID: `{artifact.artifact_id}`")
            lines.append(f"- Type: {artifact.artifact_type.value}")
            lines.append(f"- Status: {artifact.status.value}")
            artifact_versions = versions.get(artifact.artifact_id, [])
            if artifact_versions:
                lines.append("")
                lines.append("Versions:")
                for ver in sorted(artifact_versions, key=lambda v: v.created_at):
                    lines.append(
                        f"- `{ver.version_id}` {ver.created_at.strftime('%Y-%m-%d %H:%M')} "
                        f"— {ver.change_summary}"
                    )
            lines.append("")

        if contexts:
            lines.extend(["## Contexts", ""])
            for ctx in contexts.values():
                lines.append(f"- **{ctx.title}** (`{ctx.context_id}`): {ctx.summary}")
            lines.append("")

        if decisions:
            lines.extend(["## Decisions", ""])
            for dec in decisions.values():
                lines.append(
                    f"- **{dec.decision_type.value}** (`{dec.decision_id}`): {dec.reason}"
                )
            lines.append("")

        content = "\n".join(lines)
        if output:
            output.write_text(content, encoding="utf-8")
        return content
