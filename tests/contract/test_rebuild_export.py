"""Contract tests for rebuild and export stability."""


import pytest

from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService
from chronicle.services.boundary_service import BoundaryService
from chronicle.models.boundary import BoundaryRuleType, BoundaryConditionField, BoundaryOperator


@pytest.fixture
def chronicle_svc(tmp_path):
    ChronicleService(tmp_path).init("Rebuild Export Test")
    return ChronicleService(tmp_path)


def test_rebuild_from_jsonl_only(chronicle_svc):
    """Index rebuild must work from JSONL alone, without existing indexes."""
    ctx_svc = ContextService(chronicle_svc.paths.root)
    ctx_svc.add_context(title="Rebuild Context")

    # Delete derived indexes
    for f in chronicle_svc.paths.indexes_dir.glob("*.json"):
        f.unlink()

    chronicle_svc.rebuild_indexes()
    contexts = chronicle_svc.index.load_contexts()
    assert len(contexts) >= 1


def test_rebuild_includes_boundary_rules(chronicle_svc):
    """Rebuild must restore boundary rules."""
    bsvc = BoundaryService(chronicle_svc.paths.root)
    bsvc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Rebuild test",
    )

    for f in chronicle_svc.paths.indexes_dir.glob("*.json"):
        f.unlink()

    chronicle_svc.rebuild_indexes()
    rules = chronicle_svc.index.load_boundary_rules()
    assert len(rules) >= 1


def test_rebuild_derived_index_is_not_primary_contract(chronicle_svc):
    """Derived indexes can be deleted and rebuilt; JSONL is the primary contract."""
    ctx_svc = ContextService(chronicle_svc.paths.root)
    ctx_svc.add_context(title="Primary Test")

    # Verify JSONL exists
    assert chronicle_svc.paths.events_file.exists()
    event_count_before = len(chronicle_svc.jsonl.read_all())

    # Delete all indexes
    for f in chronicle_svc.paths.indexes_dir.glob("*.json"):
        f.unlink()

    # Rebuild
    chronicle_svc.rebuild_indexes()

    # JSONL unchanged
    event_count_after = len(chronicle_svc.jsonl.read_all())
    assert event_count_after == event_count_before


def test_yaml_export_key_structure(chronicle_svc):
    """YAML export must maintain core key structure."""
    from chronicle.exporters.yaml_exporter import YamlExporter
    content = YamlExporter(chronicle_svc.paths.root).export()
    for key in ["metadata", "events", "artifacts", "versions", "contexts",
                "decisions", "boundary_rules"]:
        assert key in content, f"Missing key '{key}' in YAML export"


def test_markdown_export_includes_boundary_rules(chronicle_svc):
    """Markdown export must include boundary rules section."""
    bsvc = BoundaryService(chronicle_svc.paths.root)
    bsvc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.VISIBILITY,
        operator=BoundaryOperator.EQUALS,
        value="sensitive",
        reason="Export test",
    )
    from chronicle.exporters.markdown_exporter import MarkdownExporter
    content = MarkdownExporter(chronicle_svc.paths.root).export()
    assert "Boundary Rules" in content


def test_visibility_hint_not_redacted_in_export(chronicle_svc):
    """Export must not redact visibility_hint."""
    ctx_svc = ContextService(chronicle_svc.paths.root)
    ctx_svc.add_context(title="Sensitive Export", visibility_hint="sensitive")
    from chronicle.exporters.yaml_exporter import YamlExporter
    content = YamlExporter(chronicle_svc.paths.root).export()
    assert "sensitive" in content
