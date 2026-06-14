"""Contract tests for model serialization compatibility."""

import json

import pytest

from chronicle.models.boundary import BoundaryConditionField, BoundaryOperator, BoundaryRuleType
from chronicle.models.context import ContextScope
from chronicle.models.visibility import VisibilityHint
from chronicle.services.boundary_service import BoundaryService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.context_service import ContextService


@pytest.fixture
def chronicle_svc(tmp_path):
    ChronicleService(tmp_path).init("Compat Test")
    return ChronicleService(tmp_path)


def test_context_legacy_scope_hint_compat(chronicle_svc):
    """v0.1 Context with only scope_hint must load with scope auto-populated."""
    legacy_payload = {
        "context_id": "ctx_legacy",
        "title": "Legacy Context",
        "summary": "v0.1 style",
        "source_type": "conversation",
        "source_ref": "",
        "scope_hint": "project",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }
    event = {
        "event_id": "evt_legacy", "chronicle_id": "chr_test",
        "timestamp": "2026-06-13T12:00:00+09:00",
        "event_type": "context_added", "actor": "user",
        "summary": "Legacy context",
        "payload": {"context": legacy_payload},
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    chronicle_svc.rebuild_indexes()
    contexts = chronicle_svc.index.load_contexts()
    ctx = contexts["ctx_legacy"]
    assert ctx.scope == ContextScope.PROJECT


def test_context_legacy_missing_visibility_defaults_unknown(chronicle_svc):
    """Context without visibility_hint must default to UNKNOWN."""
    legacy_payload = {
        "context_id": "ctx_novis",
        "title": "No Visibility",
        "summary": "",
        "source_type": "conversation",
        "source_ref": "",
        "scope": "task",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }
    event = {
        "event_id": "evt_novis", "chronicle_id": "chr_test",
        "timestamp": "2026-06-13T12:00:00+09:00",
        "event_type": "context_added", "actor": "user",
        "summary": "No vis",
        "payload": {"context": legacy_payload},
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    chronicle_svc.rebuild_indexes()
    contexts = chronicle_svc.index.load_contexts()
    ctx = contexts["ctx_novis"]
    assert ctx.visibility_hint == VisibilityHint.UNKNOWN


def test_context_legacy_missing_classification_defaults_none(chronicle_svc):
    """Context without v0.5 classification metadata must still load."""
    legacy_payload = {
        "context_id": "ctx_noclass",
        "title": "No Classification",
        "summary": "",
        "source_type": "conversation",
        "source_ref": "",
        "scope": "task",
        "visibility_hint": "unknown",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }
    event = {
        "event_id": "evt_noclass", "chronicle_id": "chr_test",
        "timestamp": "2026-06-13T12:00:00+09:00",
        "event_type": "context_added", "actor": "user",
        "summary": "No classification",
        "payload": {"context": legacy_payload},
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    chronicle_svc.rebuild_indexes()
    contexts = chronicle_svc.index.load_contexts()
    ctx = contexts["ctx_noclass"]
    assert ctx.classification is None


def test_context_with_classification_metadata_round_trips(chronicle_svc):
    payload = {
        "context_id": "ctx_classified",
        "title": "Classified",
        "summary": "",
        "source_type": "conversation",
        "source_ref": "",
        "scope": "task",
        "visibility_hint": "sensitive",
        "classification": {
            "layer": 3,
            "sensitivity": "sensitive",
            "owner": "owner@example.test",
            "allowed_operations": ["view", "reinterpret"],
            "llm_policy": {
                "local_allowed": True,
                "external_allowed": False,
                "masking_required": True,
            },
        },
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }
    event = {
        "event_id": "evt_classified", "chronicle_id": "chr_test",
        "timestamp": "2026-06-13T12:00:00+09:00",
        "event_type": "context_added", "actor": "user",
        "summary": "Classified context",
        "payload": {"context": payload},
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    chronicle_svc.rebuild_indexes()
    contexts = chronicle_svc.index.load_contexts()
    ctx = contexts["ctx_classified"]
    assert ctx.classification is not None
    assert ctx.classification.layer == 3
    assert ctx.classification.sensitivity == "sensitive"
    assert ctx.classification.llm_policy.external_allowed is False


def test_context_missing_source_defaults_none(chronicle_svc):
    """Context without source must load with source=None."""
    legacy_payload = {
        "context_id": "ctx_nosrc",
        "title": "No Source",
        "summary": "",
        "source_type": "conversation",
        "source_ref": "",
        "scope": "project",
        "visibility_hint": "unknown",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }
    event = {
        "event_id": "evt_nosrc", "chronicle_id": "chr_test",
        "timestamp": "2026-06-13T12:00:00+09:00",
        "event_type": "context_added", "actor": "user",
        "summary": "No source",
        "payload": {"context": legacy_payload},
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    chronicle_svc.rebuild_indexes()
    contexts = chronicle_svc.index.load_contexts()
    ctx = contexts["ctx_nosrc"]
    assert ctx.source is None


def test_source_provenance_missing_source_safe_in_boundary_eval(tmp_path):
    """BoundaryRule evaluation on source-less Context must not raise."""
    ChronicleService(tmp_path).init("Source Safety")
    ctx_svc = ContextService(tmp_path)
    bsvc = BoundaryService(tmp_path)

    ctx = ctx_svc.add_context(title="No Source Context")
    bsvc.add_rule(
        rule_type=BoundaryRuleType.WARN,
        field=BoundaryConditionField.SOURCE_TOOL,
        operator=BoundaryOperator.EQUALS,
        value="chatgpt",
        reason="Should not match",
    )
    # Must not raise
    results = bsvc.evaluate_context(ctx)
    matches = [r for r in results if r.matched]
    assert len(matches) == 0


def test_source_type_source_ref_compat_maintained(chronicle_svc):
    """Legacy source_type/source_ref fields must still be present."""
    legacy_payload = {
        "context_id": "ctx_srctype",
        "title": "Source Type Ref",
        "summary": "",
        "source_type": "document",
        "source_ref": "ref123",
        "scope": "project",
        "visibility_hint": "unknown",
        "confidence": "medium",
        "created_at": "2026-06-13T12:00:00+09:00",
        "tags": [],
    }
    event = {
        "event_id": "evt_srctype", "chronicle_id": "chr_test",
        "timestamp": "2026-06-13T12:00:00+09:00",
        "event_type": "context_added", "actor": "user",
        "summary": "Source type ref",
        "payload": {"context": legacy_payload},
    }
    with chronicle_svc.paths.events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

    chronicle_svc.rebuild_indexes()
    contexts = chronicle_svc.index.load_contexts()
    ctx = contexts["ctx_srctype"]
    # These compat fields must still be accessible
    assert ctx.source_type == "document"
    assert ctx.source_ref == "ref123"
