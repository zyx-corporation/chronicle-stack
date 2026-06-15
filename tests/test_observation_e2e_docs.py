"""Documentation boundary checks for Observation E2E gate semantics."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "observation-e2e-gate.md"


def test_observation_e2e_document_preserves_core_boundary():
    text = DOC.read_text(encoding="utf-8")

    assert "Core CI          = primary merge phase gate" in text
    assert "Observation E2E  = separate workflow observation surface" in text
    assert "A Core CI pass does not imply Observation E2E pass" in text
    assert "An Observation E2E pass does not imply semantic correctness" in text


def test_observation_e2e_document_preserves_non_certification_boundary():
    text = DOC.read_text(encoding="utf-8")

    for phrase in (
        "semantic correctness",
        "security certification",
        "privacy sufficiency",
        "physical deletion",
        "access-control enforcement",
        "correctness of GraphRAG or Sayane runtime behavior",
    ):
        assert phrase in text


def test_observation_e2e_document_tracks_v06_scenarios():
    text = DOC.read_text(encoding="utf-8")

    for heading in (
        "### Lifecycle-aware export example",
        "### Package persistence and inspection example",
    ):
        assert heading in text

    assert "lifecycle-aware export remains advisory derived-output filtering" in text
    assert "package persistence remains a derived transport artifact" in text
