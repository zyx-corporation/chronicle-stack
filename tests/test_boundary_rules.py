"""Tests for v0.2 Context Boundary Rules."""

import json

import pytest

from chronicle.models.boundary import (
    BoundaryConditionField,
    BoundaryOperator,
    BoundaryRuleType,
)
from chronicle.models.visibility import VisibilityHint
from chronicle.models.source import SourceProvenance
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService


@pytest.fixture
def boundary_svc(tmp_path):
    ChronicleService(tmp_path).init("Boundary Test")
    return BoundaryService(tmp_path)


@pytest.fixture
def ctx_svc(tmp_path):
    ChronicleService(tmp_path).init("Boundary Test")
    return ContextService(tmp_path)


def test_add_boundary_rule(boundary_svc):
    """add_rule creates a rule with br_ prefix and correct fields."""
    rule = boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Sensitive contexts need review",
    )
    assert rule.rule_id.startswith("br_")
    assert rule.rule_type == BoundaryRuleType.WARN
    assert rule.field == BoundaryConditionField.VISIBILITY
    assert rule.value == "sensitive"


def test_boundary_rule_survives_index_rebuild(boundary_svc):
    """Boundary rules persist across index rebuild."""
    rule = boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Test rebuild",
    )
    boundary_svc.chronicle.rebuild_indexes()
    rules = boundary_svc.list_rules()
    assert any(r.rule_id == rule.rule_id for r in rules)


def test_boundary_rule_warn_on_sensitive_visibility(boundary_svc, ctx_svc):
    """WARN rule on visibility=sensitive matches a sensitive Context."""
    ctx = ctx_svc.add_context(
        title="Sensitive Context",
        visibility_hint=VisibilityHint.SENSITIVE,
    )
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Sensitive needs review",
    )
    results = boundary_svc.evaluate_context(ctx)
    warn_results = [r for r in results if r.rule_type == BoundaryRuleType.WARN]
    assert len(warn_results) >= 1
    assert warn_results[0].matched


def test_boundary_rule_exclude_scope_temporary(boundary_svc, ctx_svc):
    """EXCLUDE rule on scope=temporary matches temporary Context."""
    from chronicle.models.context import ContextScope
    ctx = ctx_svc.add_context(
        title="Temp Context",
        scope=ContextScope.TEMPORARY,
    )
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.EXCLUDE,
        field=BoundaryConditionField.SCOPE,
        operator=BoundaryOperator.EQUALS,
        value="temporary",
        reason="Temporary contexts not for injection",
    )
    results = boundary_svc.evaluate_context(ctx)
    exclude_results = [r for r in results if r.rule_type == BoundaryRuleType.EXCLUDE]
    assert len(exclude_results) >= 1
    assert exclude_results[0].matched


def test_boundary_rule_source_tool_match(boundary_svc, ctx_svc):
    """source_tool=chatgpt rule matches a chatgpt-sourced Context."""
    source = SourceProvenance(source_tool="chatgpt")
    ctx = ctx_svc.add_context(
        title="ChatGPT Context",
        source_type="conversation",
        source=source,
    )
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.SOURCE_TOOL,
        operator=BoundaryOperator.EQUALS,
        value="chatgpt",
        reason="ChatGPT source needs review",
    )
    results = boundary_svc.evaluate_context(ctx)
    matches = [r for r in results if r.matched]
    assert len(matches) >= 1


def test_boundary_rule_no_source_safe(boundary_svc, ctx_svc):
    """Evaluating source_tool rule on Context without source does not crash."""
    ctx = ctx_svc.add_context(title="No Source Context")
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.SOURCE_TOOL,
        operator=BoundaryOperator.EQUALS,
        value="chatgpt",
        reason="Should not match",
    )
    results = boundary_svc.evaluate_context(ctx)
    matches = [r for r in results if r.matched]
    assert len(matches) == 0


def test_cli_boundary_add_json(tmp_path):
    """CLI boundary add --json outputs rule with correct fields."""
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()
    runner.invoke(app, ["init", "--title", "CLI Boundary"])

    result = runner.invoke(app, [
        "boundary", "add",
        "--type", "warn",
        "--field", "visibility",
        "--operator", "equals",
        "--value", "sensitive",
        "--reason", "Sensitive needs review",
        "--json",
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["rule_id"].startswith("br_")
    assert data["rule_type"] == "warn"


def test_cli_boundary_list_json(boundary_svc, tmp_path):
    """CLI boundary list --json shows added rules."""
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Test list",
    )
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(tmp_path))
    runner = CliRunner()

    result = runner.invoke(app, ["boundary", "list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_cli_boundary_check_json(boundary_svc, ctx_svc):
    """CLI boundary check --json shows matched warnings."""
    ctx = ctx_svc.add_context(
        title="Sensitive Check",
        visibility_hint=VisibilityHint.SENSITIVE,
    )
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Check test",
    )
    import os
    from typer.testing import CliRunner
    from chronicle.cli import app

    os.chdir(str(ctx_svc.chronicle.paths.root))
    runner = CliRunner()

    result = runner.invoke(app, ["boundary", "check", "--context", ctx.context_id, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    matched = [r for r in data if r.get("matched")]
    assert len(matched) >= 1


def test_search_boundary_rule(boundary_svc):
    """Search finds boundary rules by reason text."""
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="UniqueSearchReason123",
    )
    from chronicle.services.search_service import SearchService
    search = SearchService(boundary_svc.chronicle.paths.root)
    results = search.search("UniqueSearchReason123")
    assert any(r.kind == "boundary_rule" for r in results)


def test_export_includes_boundary_rules(boundary_svc):
    """YAML export includes boundary rule data."""
    boundary_svc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="ExportTest123",
    )
    from chronicle.exporters.yaml_exporter import YamlExporter
    content = YamlExporter(boundary_svc.chronicle.paths.root).export()
    assert "ExportTest123" in content
