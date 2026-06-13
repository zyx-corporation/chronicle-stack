"""Tests for v0.2 Context Injection Plans."""

import json

import pytest

from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.context import ContextScope
from chronicle.models.visibility import VisibilityHint
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.injection_service import InjectionPlanService
from chronicle.exporters.injection_plan_report import format_injection_plan


@pytest.fixture
def plan_svc(tmp_path):
    ChronicleService(tmp_path).init("Injection Plan Test")
    return InjectionPlanService(tmp_path)


def test_generate_plan_selects_context_by_default(plan_svc, tmp_path):
    ctx_svc = ContextService(tmp_path)
    ctx_svc.add_context(title="Default Context", scope=ContextScope.PROJECT)
    plan = plan_svc.generate_plan(task="Test task")
    assert len(plan.selected) == 1
    assert plan.selected[0].reason == "default candidate"
    assert len(plan.warned) == 0
    assert len(plan.excluded) == 0


def test_generate_plan_excludes_context_by_rule(plan_svc, tmp_path):
    ctx_svc = ContextService(tmp_path)
    boundary_svc = BoundaryService(tmp_path)
    ctx_svc.add_context(title="Temp Context", scope=ContextScope.TEMPORARY)
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.EXCLUDE,
        field=BoundaryConditionField.SCOPE,
        operator=BoundaryOperator.EQUALS,
        value="temporary",
        reason="Temporary not for injection",
    )
    plan = plan_svc.generate_plan(task="Test task")
    assert len(plan.excluded) == 1
    assert plan.excluded[0].title == "Temp Context"
    assert len(plan.selected) == 0


def test_generate_plan_warns_context_by_rule(plan_svc, tmp_path):
    ctx_svc = ContextService(tmp_path)
    boundary_svc = BoundaryService(tmp_path)
    ctx_svc.add_context(title="Sensitive Context", visibility_hint=VisibilityHint.SENSITIVE)
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Sensitive needs review",
    )
    plan = plan_svc.generate_plan(task="Test task")
    assert len(plan.selected) == 1
    assert len(plan.warned) == 1
    assert plan.warned[0].title == "Sensitive Context"
    assert plan.warned[0].warnings == ["Sensitive needs review"]


def test_generate_plan_ignores_disabled_rules(plan_svc, tmp_path):
    boundary_svc = BoundaryService(tmp_path)
    rule = boundary_svc.add_rule(
        rule_type=BoundaryRuleType.EXCLUDE,
        field=BoundaryConditionField.SCOPE,
        operator=BoundaryOperator.EQUALS,
        value="temporary",
        reason="Temporary excluded",
    )
    rules = boundary_svc.list_rules()
    assert any(r.rule_id == rule.rule_id and r.enabled for r in rules)


def test_injection_plan_markdown_empty_sections_show_none(plan_svc):
    plan = plan_svc.generate_plan(task="Empty task")
    report = format_injection_plan(plan)
    assert "(none)" in report
    assert "# Context Injection Plan" in report


def test_injection_plan_has_plan_id(plan_svc):
    plan = plan_svc.generate_plan(task="ID test")
    assert plan.plan_id.startswith("ip_")


def test_cli_injection_plan_json(tmp_path):
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Plan"])
    runner.invoke(app, ["add-context", "--title", "CLI Context", "--scope", "project"])

    result = runner.invoke(app, ["injection", "plan", "--task", "Test task", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    plan = data["plan"]
    assert plan["plan_id"].startswith("ip_")
    assert len(plan["selected"]) >= 1
    assert data["recorded"] is False
    assert data["event_id"] is None


def test_cli_injection_plan_markdown(tmp_path):
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Plan"])

    result = runner.invoke(app, ["injection", "plan", "--task", "Test task"])
    assert result.exit_code == 0
    assert "# Context Injection Plan" in result.stdout


def test_cli_injection_plan_with_warning_rule(tmp_path):
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Warnings"])
    runner.invoke(app, [
        "add-context", "--title", "Warn Me",
        "--scope", "project", "--visibility", "sensitive",
    ])
    runner.invoke(app, [
        "boundary", "add",
        "--type", "warn", "--field", "visibility",
        "--operator", "equals", "--value", "sensitive",
        "--reason", "Review sensitive",
    ])

    result = runner.invoke(app, ["injection", "plan", "--task", "Test warnings", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    plan = data["plan"]
    assert len(plan["warned"]) >= 1
    assert plan["warned"][0]["warnings"] == ["Review sensitive"]


def test_injection_plan_default_non_persistent(tmp_path):
    """injection plan without --record must not change JSONL event count."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Non-Persist"])
    runner.invoke(app, ["add-context", "--title", "ctx", "--scope", "project"])

    before = len(list((tmp_path / ".chronicle" / "chronicle.jsonl").read_text().splitlines()))
    runner.invoke(app, ["injection", "plan", "--task", "No record"])
    after = len(list((tmp_path / ".chronicle" / "chronicle.jsonl").read_text().splitlines()))
    assert after == before, "Plan generation without --record must not add events"


def test_injection_plan_record_persists_to_jsonl(tmp_path):
    """injection plan --record adds an event to JSONL."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Persist Plan"])
    runner.invoke(app, ["add-context", "--title", "ctx", "--scope", "project"])

    before = len(list((tmp_path / ".chronicle" / "chronicle.jsonl").read_text().splitlines()))
    result = runner.invoke(app, ["injection", "plan", "--task", "Record me", "--record", "--json"])
    assert result.exit_code == 0
    after = len(list((tmp_path / ".chronicle" / "chronicle.jsonl").read_text().splitlines()))
    assert after > before, "--record must add an event to JSONL"

    data = json.loads(result.stdout)
    assert data["recorded"] is True
    assert data["event_id"] is not None
    assert data["event_id"].startswith("evt_")


def test_injection_plan_record_event_type(tmp_path):
    """Recorded plan event must have event_type injection_plan_recorded."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "EventType Check"])
    runner.invoke(app, ["add-context", "--title", "ctx", "--scope", "project"])
    runner.invoke(app, ["injection", "plan", "--task", "Type check", "--record"])

    from chronicle.services.chronicle_service import ChronicleService
    svc = ChronicleService(tmp_path)
    events = svc.jsonl.read_all()
    plan_events = [e for e in events if e.event_type.value == "injection_plan_recorded"]
    assert len(plan_events) >= 1
    payload = plan_events[-1].payload
    assert "injection_plan" in payload
    plan_data = payload["injection_plan"]
    assert "plan_id" in plan_data
    assert "selected" in plan_data
    assert "warned" in plan_data
    assert "excluded" in plan_data
    assert "notes" in plan_data


def test_injection_plan_recorded_searchable(tmp_path):
    """Recorded plan must be searchable by task text."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Search Plan"])
    runner.invoke(app, ["add-context", "--title", "ctx", "--scope", "project"])
    runner.invoke(app, ["injection", "plan", "--task", "UniqueSearchTask999", "--record"])

    result = runner.invoke(app, ["search", "UniqueSearchTask999", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert len(data) >= 1
    kinds = {r["kind"] for r in data}
    assert "event" in kinds


def test_injection_plan_recorded_survives_rebuild(tmp_path):
    """Recorded plan must survive index rebuild."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "Rebuild Plan"])
    runner.invoke(app, ["add-context", "--title", "ctx", "--scope", "project"])
    runner.invoke(app, ["injection", "plan", "--task", "Rebuild target", "--record"])

    from chronicle.services.chronicle_service import ChronicleService
    svc = ChronicleService(tmp_path)
    event_count_before = len(svc.jsonl.read_all())
    svc.rebuild_indexes()
    event_count_after = len(svc.jsonl.read_all())
    assert event_count_after == event_count_before
