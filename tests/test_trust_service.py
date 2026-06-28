"""Tests for trust model Phase 6 service."""

from chronicle.models.trust import TrustLevel
from chronicle.services.audit_service import AuditService
from chronicle.services.chronicle_service import ChronicleService
from chronicle.services.trust_service import TrustService


def test_trust_service_adds_node_profile_and_asserts_relation(tmp_path):
    ChronicleService(tmp_path).init("Trust Test")
    service = TrustService(tmp_path)

    profile = service.add_node_profile(
        node_id="node:partner:beta",
        subject_id="subject:beta",
        display_name="Partner Beta",
    )
    relation = service.assert_relation(
        target_node="node:partner:beta",
        target_subject_id="subject:beta",
        domain="technical_review",
        purpose="project review",
        level=TrustLevel.TRUSTED,
        capabilities=["review", "reference"],
    )

    summary = service.summarize_for_target(target_node="node:partner:beta", purpose="project review")

    assert profile.node_id == "node:partner:beta"
    assert relation.relation_id.startswith("tr_")
    assert summary.active_relation_count == 1
    assert summary.dominant_level == "trusted"
    assert summary.capability_counts["review"] == 1


def test_trust_service_withdraws_relation_and_audits_proxy_metadata(tmp_path):
    ChronicleService(tmp_path).init("Trust Withdraw Test")
    service = TrustService(tmp_path)
    relation = service.assert_relation(
        target_node="node:partner:gamma",
        target_subject_id="subject:gamma",
        domain="ops",
        purpose="incident response",
        level=TrustLevel.LIMITED,
        capabilities=["request_context"],
        delegated_actor_metadata={"actor": "ops-lead"},
        ai_proxy_generation_metadata={"model": "local-summarizer"},
    )

    withdrawn = service.withdraw_relation(
        relation_id=relation.relation_id,
        reason="trust window expired",
    )
    audits = AuditService(tmp_path).list_events()

    assert withdrawn.status.value == "withdrawn"
    assert withdrawn.withdrawal_reason == "trust window expired"
    assert audits[-1].metadata["delegated_actor_present"] == "true"
    assert audits[-1].metadata["ai_proxy_present"] == "true"
