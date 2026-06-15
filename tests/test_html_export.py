"""Tests for static HTML dashboard / review console export."""

import os

import pytest
from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.exporters.html_exporter import HtmlDashboardExporter
from chronicle.models.artifact import ArtifactType
from chronicle.models.audit import AuditOperation, AuditSeverity, AuditTargetEnvironment
from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.lifecycle import LifecycleAction, LifecycleReasonClass
from chronicle.models.visibility import VisibilityHint
from chronicle.services.artifact_service import ArtifactService
from chronicle.services.audit_service import AuditService
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.injection_service import InjectionPlanService
from chronicle.services.lifecycle_service import LifecycleService


@pytest.fixture
def populated_chronicle(tmp_path):
    """Chronicle with various records for dashboard testing."""
    svc = ChronicleService(tmp_path)
    svc.init("Dashboard Test")

    ctx_svc = ContextService(tmp_path)
    public_ctx = ctx_svc.add_context(title="Public Context", visibility_hint=VisibilityHint.PUBLIC)
    sensitive_ctx = ctx_svc.add_context(
        title="Sensitive Note",
        summary="Secret <script>alert(1)</script>",
        visibility_hint=VisibilityHint.SENSITIVE,
    )

    art_svc = ArtifactService(tmp_path)
    f = tmp_path / "doc.md"
    f.write_text("Content", encoding="utf-8")
    art_svc.create(
        title="Private Artifact",
        artifact_type=ArtifactType.DOCUMENT,
        source_file=f,
        visibility_hint=VisibilityHint.PRIVATE,
    )

    bsvc = BoundaryService(tmp_path)
    bsvc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Sensitive & private",
    )

    ip_svc = InjectionPlanService(tmp_path)
    plan = ip_svc.generate_plan(task="Dashboard task")
    ip_svc.record_plan(plan)

    AuditService(tmp_path).record(
        operation=AuditOperation.EXPORT,
        actor="test",
        purpose="review console audit",
        target_environment=AuditTargetEnvironment.LOCAL,
        result=AuditSeverity.WARNING,
        summary="Audit review marker",
        referenced_records=[public_ctx.context_id],
    )

    LifecycleService(tmp_path).record(
        action=LifecycleAction.SEAL,
        target_id=sensitive_ctx.context_id,
        target_kind="context",
        actor="test",
        reason_class=LifecycleReasonClass.PRIVACY,
        reason="Review console lifecycle marker",
    )

    return HtmlDashboardExporter(tmp_path)


@pytest.fixture
def populated_root(populated_chronicle):
    return populated_chronicle.chronicle.paths.root


def test_html_export_succeeds(populated_chronicle):
    """HTML export must return a non-empty string."""
    html = populated_chronicle.export()
    assert len(html) > 0


def test_html_export_contains_basic_structure(populated_chronicle):
    """HTML export must contain basic HTML elements."""
    html = populated_chronicle.export()
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "<body" in html
    assert "Chronicle Stack Review Console" in html


def test_html_export_contains_navigation_and_filter(populated_chronicle):
    """HTML export must contain local navigation and row filtering."""
    html = populated_chronicle.export()
    assert 'class="nav"' in html
    assert 'href="#contexts"' in html
    assert 'href="#artifacts"' in html
    assert 'href="#package-review"' in html
    assert 'href="#audit-events"' in html
    assert 'href="#lifecycle-markers"' in html
    assert 'id="chronicle-filter"' in html
    assert "filterChronicleRows" in html
    assert 'data-filter-row="true"' in html


def test_html_export_contains_section_anchors(populated_chronicle):
    """Important dashboard sections should have stable local anchors."""
    html = populated_chronicle.export()
    for anchor in (
        'id="review-console"',
        'id="manifest"',
        'id="summary"',
        'id="package-review"',
        'id="audit-events"',
        'id="lifecycle-markers"',
        'id="events"',
        'id="contexts"',
        'id="artifacts"',
        'id="decisions"',
        'id="rde-records"',
        'id="boundary-rules"',
        'id="injection-plans"',
        'id="notes"',
    ):
        assert anchor in html


def test_html_export_contains_summary_cards(populated_chronicle):
    """HTML export must contain summary count cards."""
    html = populated_chronicle.export()
    assert "Events" in html
    assert "Contexts" in html
    assert "Artifacts" in html
    assert "Boundary Rules" in html
    assert "Injection Plans" in html
    assert "Audit Events" in html
    assert "Lifecycle Markers" in html
    assert "Package Findings" in html


def test_html_export_contains_review_console_boundary(populated_chronicle):
    """Review console must describe its read-only runtime boundary."""
    html = populated_chronicle.export()
    assert "Read-first review console" in html
    assert "does not write Chronicle records" in html
    assert "start a daemon" in html
    assert "Primary record" in html
    assert "Audit log" in html
    assert "Lifecycle log" in html
    assert "Packages" in html


def test_html_export_contains_package_review_snapshot(populated_chronicle):
    """Review console should include package review status and findings."""
    html = populated_chronicle.export()
    assert "Package Review Snapshot" in html
    assert "html review console snapshot" in html
    assert "Output classification" in html
    assert "unclassified_context" in html
    assert "classify the Context before package or export review" in html


def test_html_export_contains_audit_events(populated_chronicle):
    """Review console should display audit events."""
    html = populated_chronicle.export()
    assert "Audit Events" in html
    assert "review console audit" in html
    assert "Audit review marker" in html
    assert "badge-warning" in html


def test_html_export_contains_lifecycle_markers(populated_chronicle):
    """Review console should display lifecycle markers."""
    html = populated_chronicle.export()
    assert "Lifecycle Markers" in html
    assert "Review console lifecycle marker" in html
    assert "privacy" in html
    assert "seal" in html


def test_html_export_contains_contexts(populated_chronicle):
    """HTML export must display context entries."""
    html = populated_chronicle.export()
    assert "Public Context" in html
    assert "Sensitive Note" in html


def test_html_export_contains_artifacts(populated_chronicle):
    """HTML export must display artifact entries."""
    html = populated_chronicle.export()
    assert "Private Artifact" in html


def test_html_export_contains_boundary_rules(populated_chronicle):
    """HTML export must display boundary rules."""
    html = populated_chronicle.export()
    assert "Sensitive &amp; private" in html


def test_html_export_contains_recorded_injection_plans(populated_chronicle):
    """HTML export must display recorded injection plans."""
    html = populated_chronicle.export()
    assert "Recorded Injection Plans" in html
    assert "Dashboard task" in html


def test_html_export_visibility_badges(populated_chronicle):
    """HTML export must show visibility badges for sensitive/private."""
    html = populated_chronicle.export()
    assert "badge-sensitive" in html
    assert "badge-private" in html
    assert "badge-public" in html


def test_html_export_does_not_redact_sensitive(populated_chronicle):
    """sensitive/private visibility must NOT be redacted by default."""
    html = populated_chronicle.export()
    assert "sensitive" in html
    assert "private" in html


def test_html_export_html_escapes_user_content(populated_chronicle):
    """User-provided HTML-like strings must be escaped even though dashboard has inline JS."""
    html = populated_chronicle.export()
    assert "Secret &lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "Secret <script>alert(1)</script>" not in html


def test_html_export_does_not_mutate_jsonl(populated_chronicle):
    """HTML export must not change chronicle.jsonl."""
    before = len(populated_chronicle.chronicle.jsonl.read_all())
    populated_chronicle.export()
    after = len(populated_chronicle.chronicle.jsonl.read_all())
    assert after == before


def test_html_export_contains_notes(populated_chronicle):
    """HTML export must contain the disclaimer notes."""
    html = populated_chronicle.export()
    assert "読み取り専用の派生ビュー" in html
    assert "一次記録" in html
    assert "access control" in html.lower() or "アクセス制御" in html
    assert "単一HTMLファイル" in html
    assert "Audit events" in html
    assert "Package review" in html


def test_cli_export_html(tmp_path):
    """CLI export --format html must succeed."""
    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI HTML"])

    result = runner.invoke(app, ["export", "--format", "html"])
    assert result.exit_code == 0
    assert "<!DOCTYPE html>" in result.stdout
    assert "Chronicle Stack Review Console" in result.stdout
    assert "CLI HTML" in result.stdout
    assert 'id="chronicle-filter"' in result.stdout
    assert 'id="review-console"' in result.stdout


def test_html_export_graph_overview(populated_chronicle):
    """HTML export should include graph overview when graph export works."""
    html = populated_chronicle.export()
    assert "Graph Nodes" in html
    assert "Graph Edges" in html
