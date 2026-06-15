"""Markdown export."""

from pathlib import Path

from chronicle.lifecycle.derived_output_policy import (
    LifecycleTargetState,
    count_sealed_targets,
    event_lifecycle_target_ids,
    event_references_tombstoned_target,
    is_lifecycle_tombstoned,
    lifecycle_state_by_target,
)
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.lifecycle_service import LifecycleService


def _lifecycle_marker(state: LifecycleTargetState | None) -> str:
    if state is not None and state.is_sealed:
        return " [lifecycle: sealed]"
    return ""


class MarkdownExporter:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.lifecycle = LifecycleService(root)

    def export(self, output: Path | None = None) -> str:
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, versions = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        lifecycle_states = lifecycle_state_by_target(self.lifecycle.list_events())

        visible_artifacts = [
            artifact
            for artifact in artifacts.values()
            if not is_lifecycle_tombstoned(artifact.artifact_id, lifecycle_states)
        ]
        visible_contexts = [
            context
            for context in contexts.values()
            if not is_lifecycle_tombstoned(context.context_id, lifecycle_states)
        ]
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
            [
                *(artifact.artifact_id for artifact in visible_artifacts),
                *(context.context_id for context in visible_contexts),
            ],
            lifecycle_states,
        )

        lines = [
            f"# Chronicle: {metadata.title}",
            "",
            f"- ID: `{metadata.chronicle_id}`",
            f"- Created: {metadata.created_at.isoformat()}",
            f"- Schema: {metadata.schema_version}",
            "",
            "## Export Warnings",
            "",
        ]
        if excluded_lifecycle_tombstone_count:
            lines.append(
                f"- lifecycle_tombstoned_records_excluded: {excluded_lifecycle_tombstone_count} record(s) omitted from this derived export."
            )
        if excluded_lifecycle_event_count:
            lines.append(
                f"- lifecycle_tombstoned_events_excluded: {excluded_lifecycle_event_count} event row(s) referencing omitted records hidden."
            )
        if sealed_lifecycle_count:
            lines.append(
                f"- lifecycle_sealed_record: {sealed_lifecycle_count} sealed record(s) marked in this derived export."
            )
        if not excluded_lifecycle_tombstone_count and not excluded_lifecycle_event_count and not sealed_lifecycle_count:
            lines.append("- none")

        lines.extend([
            "",
            "## Events",
            "",
        ])

        for event in visible_events:
            event_state = next(
                (
                    lifecycle_states[target_id]
                    for target_id in event_lifecycle_target_ids(event)
                    if lifecycle_states.get(target_id) is not None and lifecycle_states[target_id].is_sealed
                ),
                None,
            )
            lines.append(
                f"- `{event.event_id}` **{event.event_type.value}{_lifecycle_marker(event_state)}** "
                f"({event.timestamp.strftime('%Y-%m-%d %H:%M')}) — {event.summary}"
            )

        lines.extend(["", "## Artifacts", ""])
        for artifact in visible_artifacts:
            artifact_state = lifecycle_states.get(artifact.artifact_id)
            lines.append(f"### {artifact.title}{_lifecycle_marker(artifact_state)}")
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

        if visible_contexts:
            lines.extend(["## Contexts", ""])
            for ctx in visible_contexts:
                context_state = lifecycle_states.get(ctx.context_id)
                lines.append(
                    f"- **{ctx.title}{_lifecycle_marker(context_state)}** (`{ctx.context_id}`): {ctx.summary}"
                )
            lines.append("")

        if decisions:
            lines.extend(["## Decisions", ""])
            for dec in decisions.values():
                lines.append(
                    f"- **{dec.decision_type.value}** (`{dec.decision_id}`): {dec.reason}"
                )
            lines.append("")

        if boundary_rules:
            lines.extend(["## Boundary Rules", ""])
            for rule in boundary_rules.values():
                val = rule.value if isinstance(rule.value, str) else ", ".join(rule.value)
                lines.append(
                    f"- `{rule.rule_id}` **{rule.rule_type.value}** "
                    f"{rule.field.value} {rule.operator.value} `{val}`"
                )
                if rule.reason:
                    lines.append(f"  - {rule.reason}")
            lines.append("")

        content = "\n".join(lines)
        if output:
            output.write_text(content, encoding="utf-8")
        return content
