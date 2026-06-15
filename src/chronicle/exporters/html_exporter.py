"""Static HTML dashboard exporter (v0.4).

Produces a single-file, read-only HTML report from Chronicle records.
No web server, no external dependencies.
"""

import html
from datetime import datetime, timezone
from pathlib import Path

from chronicle.exporters.redaction import (
    REDACTED,
    RedactionOptions,
    event_has_sensitive_payload,
    model_is_sensitive,
)
from chronicle.lifecycle.derived_output_policy import LifecycleTargetState, lifecycle_state_by_target
from chronicle.models.event import ChronicleEvent
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.export_manifest_service import ExportManifestService
from chronicle.services.graph_export_service import GraphExportService
from chronicle.services.lifecycle_service import LifecycleService


CSS = """
body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; color: #333; background: #fff; }
h1 { border-bottom: 2px solid #2563eb; padding-bottom: 8px; }
h2 { border-bottom: 1px solid #e5e7eb; padding-bottom: 4px; margin-top: 24px; }
.nav { display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; padding: 12px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; }
.nav a { color: #2563eb; text-decoration: none; font-size: 0.9em; }
.nav a:hover { text-decoration: underline; }
.filter { margin: 16px 0; padding: 12px; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; }
.filter input { width: 100%; max-width: 420px; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; }
.cards { display: flex; flex-wrap: wrap; gap: 12px; }
.card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; min-width: 120px; text-align: center; }
.card .count { font-size: 2em; font-weight: bold; color: #2563eb; }
.card .label { font-size: 0.85em; color: #6b7280; }
table { width: 100%; border-collapse: collapse; margin-top: 8px; }
th, td { padding: 8px; text-align: left; border-bottom: 1px solid #e5e7eb; }
th { background: #f9fafb; font-weight: 600; }
.id { font-family: monospace; font-size: 0.85em; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: 600; }
.badge-sensitive { background: #fef2f2; color: #dc2626; }
.badge-private { background: #fefce8; color: #ca8a04; }
.badge-public { background: #f0fdf4; color: #16a34a; }
.badge-unknown { background: #f3f4f6; color: #6b7280; }
.badge-lifecycle-sealed { background: #eff6ff; color: #1d4ed8; }
.warning { background: #fefce8; border-left: 4px solid #eab308; padding: 8px 12px; margin: 8px 0; border-radius: 0 4px 4px 0; }
.footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 0.8em; color: #9ca3af; }
"""

FILTER_SCRIPT = """
<script>
function filterChronicleRows() {
  const query = document.getElementById('chronicle-filter').value.toLowerCase();
  document.querySelectorAll('[data-filter-row="true"]').forEach(function(row) {
    const text = row.getAttribute('data-filter-text').toLowerCase();
    row.style.display = text.indexOf(query) >= 0 ? '' : 'none';
  });
}
</script>
"""


def _esc(text: str) -> str:
    return html.escape(str(text))


def _badge(visibility: str) -> str:
    return f'<span class="badge badge-{visibility}">{_esc(visibility)}</span>'


def _sealed_badge(state: LifecycleTargetState | None) -> str:
    if state is not None and state.is_sealed:
        return ' <span class="badge badge-lifecycle-sealed">lifecycle_sealed_record</span>'
    return ""


def _id_cell(value: str) -> str:
    return f'<span class="id">{_esc(value)}</span>'


def _display_sensitive(value: str, options: RedactionOptions) -> str:
    return REDACTED if options.redact_sensitive else value


def _filter_attrs(*values: object) -> str:
    text = " ".join(str(value) for value in values)
    return f'data-filter-row="true" data-filter-text="{_esc(text)}"'


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


class HtmlDashboardExporter:
    def __init__(self, root: Path | None = None) -> None:
        self.chronicle = ChronicleService(root)
        self.manifest = ExportManifestService(root)
        self.lifecycle = LifecycleService(root)

    def export(self, redaction: RedactionOptions | None = None) -> str:
        options = redaction or RedactionOptions()
        metadata = self.chronicle.require_initialized()
        events = self.chronicle.jsonl.read_all()
        artifacts, _ = self.chronicle.index.load_artifacts()
        contexts = self.chronicle.index.load_contexts()
        decisions = self.chronicle.index.load_decisions()
        boundary_rules = self.chronicle.index.load_boundary_rules()
        lifecycle_states = lifecycle_state_by_target(self.lifecycle.list_events())
        manifest = self.manifest.build_manifest("html", export_options=options.as_manifest_options())

        visible_events = [
            event
            for event in events
            if not any(
                lifecycle_states.get(target_id) is not None and lifecycle_states[target_id].is_tombstoned
                for target_id in _event_target_ids(event)
            )
        ]

        recorded_plans = []
        for event in visible_events:
            if event.event_type.value == "injection_plan_recorded" and "injection_plan" in event.payload:
                recorded_plans.append(event.payload["injection_plan"])

        try:
            graph_export = GraphExportService(self.chronicle.paths.root).export_graph()
            graph_node_count = len(graph_export.nodes)
            graph_edge_count = len(graph_export.edges)
            graph_available = True
        except Exception:
            graph_node_count = 0
            graph_edge_count = 0
            graph_available = False

        visible_contexts = [
            c
            for c in contexts.values()
            if not (options.exclude_sensitive and model_is_sensitive(c))
            and not lifecycle_states.get(c.context_id, LifecycleTargetState(c.context_id)).is_tombstoned
        ]
        visible_artifacts = [
            a
            for a in artifacts.values()
            if not (options.exclude_sensitive and model_is_sensitive(a))
            and not lifecycle_states.get(a.artifact_id, LifecycleTargetState(a.artifact_id)).is_tombstoned
        ]
        excluded_lifecycle_tombstone_count = (
            len(artifacts)
            + len(contexts)
            - len([a for a in artifacts.values() if not lifecycle_states.get(a.artifact_id, LifecycleTargetState(a.artifact_id)).is_tombstoned])
            - len([c for c in contexts.values() if not lifecycle_states.get(c.context_id, LifecycleTargetState(c.context_id)).is_tombstoned])
        )
        excluded_lifecycle_event_count = len(events) - len(visible_events)
        sealed_lifecycle_count = sum(
            1
            for record_id in [
                *(artifact.artifact_id for artifact in visible_artifacts),
                *(context.context_id for context in visible_contexts),
            ]
            if lifecycle_states.get(record_id) is not None and lifecycle_states[record_id].is_sealed
        )

        now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        cid = metadata.chronicle_id

        lines = [
            "<!DOCTYPE html>",
            '<html lang="ja">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>Chronicle Dashboard — {_esc(metadata.title)}</title>",
            f"<style>{CSS}</style>",
            FILTER_SCRIPT,
            "</head>",
            "<body>",
            "<h1>Chronicle Stack Dashboard</h1>",
            f"<p>Chronicle: <strong>{_esc(metadata.title)}</strong> — ID: {_id_cell(cid)}</p>",
            f"<p>Generated: {_esc(now)}</p>",
            '<nav class="nav" aria-label="Dashboard sections">',
            '<a href="#manifest">Manifest</a>',
            '<a href="#summary">Summary</a>',
            '<a href="#events">Events</a>',
            '<a href="#contexts">Contexts</a>',
            '<a href="#artifacts">Artifacts</a>',
            '<a href="#decisions">Decisions</a>',
            '<a href="#rde-records">RDE</a>',
            '<a href="#boundary-rules">Boundary Rules</a>',
            '<a href="#injection-plans">Injection Plans</a>',
            '<a href="#notes">Notes</a>',
            '</nav>',
            '<div class="filter">',
            '<label for="chronicle-filter"><strong>Filter rows</strong></label><br>',
            '<input id="chronicle-filter" type="search" oninput="filterChronicleRows()" placeholder="Filter events, contexts, artifacts, decisions...">',
            '</div>',
            "",
            '<h2 id="manifest">Export Manifest</h2>',
            "<table><tr><th>Field</th><th>Value</th></tr>",
            f"<tr><td>Format</td><td>{_esc(manifest.export_format)}</td></tr>",
            f"<tr><td>Generated at</td><td>{_esc(manifest.generated_at.isoformat())}</td></tr>",
            f"<tr><td>Tool version</td><td>{_esc(manifest.tool_version)}</td></tr>",
            f"<tr><td>Event count</td><td>{manifest.event_count}</td></tr>",
            f"<tr><td>Redact sensitive</td><td>{str(options.redact_sensitive).lower()}</td></tr>",
            f"<tr><td>Exclude sensitive</td><td>{str(options.exclude_sensitive).lower()}</td></tr>",
            "</table>",
            "",
            '<h2 id="lifecycle-warnings">Lifecycle Export Warnings</h2>',
            '<div class="warning">',
        ]
        if excluded_lifecycle_tombstone_count:
            lines.append(f"<p>lifecycle_tombstoned_records_excluded: {_esc(excluded_lifecycle_tombstone_count)} record(s) omitted from this derived export.</p>")
        if excluded_lifecycle_event_count:
            lines.append(f"<p>lifecycle_tombstoned_events_excluded: {_esc(excluded_lifecycle_event_count)} event row(s) referencing omitted records hidden.</p>")
        if sealed_lifecycle_count:
            lines.append(f"<p>lifecycle_sealed_record: {_esc(sealed_lifecycle_count)} sealed record(s) marked in this derived export.</p>")
        if not excluded_lifecycle_tombstone_count and not excluded_lifecycle_event_count and not sealed_lifecycle_count:
            lines.append("<p>none</p>")
        lines.extend([
            "</div>",
            "",
            '<h2 id="summary">Summary</h2>',
            '<div class="cards">',
            self._card("Events", len(visible_events)),
            self._card("Contexts", len(visible_contexts)),
            self._card("Artifacts", len(visible_artifacts)),
            self._card("Decisions", len(decisions)),
            self._card("RDE Records", sum(1 for e in visible_events if e.event_type.value == "rde_diff_recorded")),
            self._card("Boundary Rules", len(boundary_rules)),
            self._card("Injection Plans", len(recorded_plans)),
        ])
        if graph_available:
            lines.append(self._card("Graph Nodes", graph_node_count))
            lines.append(self._card("Graph Edges", graph_edge_count))

        lines.extend([
            "</div>",
            "",
            '<h2 id="events">Recent Events</h2>',
            "<table><tr><th>Event ID</th><th>Type</th><th>Timestamp</th><th>Summary</th></tr>",
        ])
        for event in reversed(visible_events[-30:]):
            sensitive_event = event_has_sensitive_payload(event.model_dump(mode="json"))
            if options.exclude_sensitive and sensitive_event:
                continue
            event_state = next(
                (
                    lifecycle_states[target_id]
                    for target_id in _event_target_ids(event)
                    if lifecycle_states.get(target_id) is not None and lifecycle_states[target_id].is_sealed
                ),
                None,
            )
            summary = REDACTED if options.redact_sensitive and sensitive_event else event.summary
            ts = event.timestamp.strftime("%Y-%m-%d %H:%M")
            lines.append(
                f"<tr {_filter_attrs(event.event_id, event.event_type.value, ts, summary)}><td>{_id_cell(event.event_id)}</td>"
                f"<td>{_esc(event.event_type.value)}{_sealed_badge(event_state)}</td>"
                f"<td>{_esc(ts)}</td>"
                f"<td>{_esc(summary)}</td></tr>"
            )
        lines.append("</table>")

        lines.extend([
            "", '<h2 id="contexts">Contexts</h2>',
            "<table><tr><th>ID</th><th>Title</th><th>Scope</th><th>Visibility</th><th>Summary</th></tr>",
        ])
        for ctx in sorted(visible_contexts, key=lambda c: c.created_at):
            sensitive = model_is_sensitive(ctx)
            state = lifecycle_states.get(ctx.context_id)
            title = _display_sensitive(ctx.title, options) if sensitive else ctx.title
            summary = _display_sensitive(ctx.summary, options) if sensitive else ctx.summary
            lines.append(
                f"<tr {_filter_attrs(ctx.context_id, title, ctx.scope.value, ctx.visibility_hint.value, summary)}><td>{_id_cell(ctx.context_id)}</td>"
                f"<td>{_esc(title)}{_sealed_badge(state)}</td>"
                f"<td>{_esc(ctx.scope.value)}</td>"
                f"<td>{_badge(ctx.visibility_hint.value)}</td>"
                f"<td>{_esc(summary)}</td></tr>"
            )
        lines.append("</table>")

        lines.extend([
            "", '<h2 id="artifacts">Artifacts</h2>',
            "<table><tr><th>ID</th><th>Title</th><th>Type</th><th>Status</th><th>Visibility</th></tr>",
        ])
        for art in sorted(visible_artifacts, key=lambda a: a.created_at):
            sensitive = model_is_sensitive(art)
            state = lifecycle_states.get(art.artifact_id)
            title = _display_sensitive(art.title, options) if sensitive else art.title
            lines.append(
                f"<tr {_filter_attrs(art.artifact_id, title, art.artifact_type.value, art.status.value, art.visibility_hint.value)}><td>{_id_cell(art.artifact_id)}</td>"
                f"<td>{_esc(title)}{_sealed_badge(state)}</td>"
                f"<td>{_esc(art.artifact_type.value)}</td>"
                f"<td>{_esc(art.status.value)}</td>"
                f"<td>{_badge(art.visibility_hint.value)}</td></tr>"
            )
        lines.append("</table>")

        lines.append('<h2 id="decisions">Decisions</h2>')
        if decisions:
            lines.append("<table><tr><th>ID</th><th>Type</th><th>Reason</th></tr>")
            for dec in sorted(decisions.values(), key=lambda d: d.decided_at):
                lines.append(f"<tr {_filter_attrs(dec.decision_id, dec.decision_type.value, dec.reason)}><td>{_id_cell(dec.decision_id)}</td><td>{_esc(dec.decision_type.value)}</td><td>{_esc(dec.reason)}</td></tr>")
            lines.append("</table>")
        else:
            lines.append("<p>No decisions recorded.</p>")

        rdes = self.chronicle.index.load_rde_records()
        lines.append('<h2 id="rde-records">RDE Diff Records</h2>')
        if rdes:
            lines.append("<table><tr><th>ID</th><th>Artifact</th><th>From</th><th>To</th><th>Summary</th></tr>")
            for rde in sorted(rdes.values(), key=lambda r: r.created_at):
                lines.append(f"<tr {_filter_attrs(rde.rde_record_id, rde.artifact_id, rde.from_version_id, rde.to_version_id, rde.summary)}><td>{_id_cell(rde.rde_record_id)}</td><td>{_esc(rde.artifact_id)}</td><td>{_id_cell(rde.from_version_id)}</td><td>{_id_cell(rde.to_version_id)}</td><td>{_esc(rde.summary)}</td></tr>")
            lines.append("</table>")
        else:
            lines.append("<p>No RDE records found.</p>")

        lines.append('<h2 id="boundary-rules">Boundary Rules</h2>')
        if boundary_rules:
            lines.append("<table><tr><th>ID</th><th>Type</th><th>Field</th><th>Operator</th><th>Value</th><th>Reason</th></tr>")
            for rule in sorted(boundary_rules.values(), key=lambda r: r.created_at):
                val = rule.value if isinstance(rule.value, str) else ", ".join(rule.value)
                lines.append(f"<tr {_filter_attrs(rule.rule_id, rule.rule_type.value, rule.field.value, rule.operator.value, val, rule.reason)}><td>{_id_cell(rule.rule_id)}</td><td>{_esc(rule.rule_type.value)}</td><td>{_esc(rule.field.value)}</td><td>{_esc(rule.operator.value)}</td><td>{_esc(val)}</td><td>{_esc(rule.reason)}</td></tr>")
            lines.append("</table>")
        else:
            lines.append("<p>No boundary rules found.</p>")

        lines.append('<h2 id="injection-plans">Recorded Injection Plans</h2>')
        if recorded_plans:
            lines.append("<table><tr><th>ID</th><th>Task</th><th>Selected</th><th>Warned</th><th>Excluded</th></tr>")
            for plan in recorded_plans:
                task = REDACTED if options.redact_sensitive else plan["task"]
                lines.append(f"<tr {_filter_attrs(plan['plan_id'], task)}><td>{_id_cell(plan['plan_id'])}</td><td>{_esc(task)}</td><td>{len(plan.get('selected', []))}</td><td>{len(plan.get('warned', []))}</td><td>{len(plan.get('excluded', []))}</td></tr>")
            lines.append("</table>")
        else:
            lines.append("<p>No recorded injection plans found.</p>")

        lines.extend([
            "", '<h2 id="notes">Notes</h2>',
            '<div class="warning">',
            "<p>このDashboardは<strong>読み取り専用の派生ビュー</strong>です。</p>",
            "<p>このDashboardは単一HTMLファイルであり、ローカルのアンカー移動と行フィルタだけを提供します。</p>",
            "<p>一次記録は <code>.chronicle/chronicle.jsonl</code> です。</p>",
            "<p>Visibility Hint はアクセス制御やredactionではありません。</p>",
            "<p>Redaction-aware export は明示オプションによる派生export制御であり、access controlではありません。</p>",
            "<p>Lifecycle-aware export は派生ビュー上の助言的な表示制御であり、deletion / access control enforcement ではありません。</p>",
            "<p>Boundary Rules は助言的な分類であり、強制的な保護機構ではありません。</p>",
            "<p>Injection Plan はLLMへの自動注入ではありません。</p>",
            "<p>graph-json export はGraphRAG接続準備であり、GraphRAGエンジンではありません。</p>",
            "<p>Export Manifest は出力の来歴メタデータであり、暗号学的証明ではありません。</p>",
            "</div>",
            '<div class="footer">',
            f"<p>Chronicle Stack — {_esc(metadata.schema_version)} — Generated: {_esc(now)}</p>",
            f"<p>Chronicle ID: {_id_cell(cid)}</p>",
            "</div>",
            "</body>",
            "</html>",
        ])

        return "\n".join(lines)

    @staticmethod
    def _card(label: str, count: int) -> str:
        return f'<div class="card"><div class="count">{count}</div><div class="label">{_esc(label)}</div></div>'
