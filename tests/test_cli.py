"""CLI integration tests using Typer CliRunner."""

import json
import os
import re
from pathlib import Path

from typer.testing import CliRunner

from chronicle.cli import app

runner = CliRunner()


def _extract_id(text: str, prefix: str) -> str | None:
    """Extract a prefixed ID (e.g. art_xxx) from CLI output text."""
    # IDs may be wrapped in parentheses: (art_xxx)
    match = re.search(rf"\b\(?({prefix}[a-f0-9]+)\)?", text)
    return match.group(1) if match else None


def test_init_with_title(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    try:
        result = runner.invoke(app, ["init", "--title", "CLI Test Chronicle"])
        assert result.exit_code == 0
        assert "CLI Test Chronicle" in result.stdout
        assert (tmp_path / ".chronicle" / "chronicle.jsonl").exists()
        assert (tmp_path / ".chronicle" / "metadata.yaml").exists()
    finally:
        pass  # os.chdir back is handled by per-test isolation


def test_record_user_input(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    result = runner.invoke(
        app,
        [
            "record",
            "--type", "user_input",
            "--actor", "user",
            "--summary", "Create specification",
        ],
    )
    assert result.exit_code == 0
    assert "evt_" in result.stdout


def test_artifact_create(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    source = tmp_path / "spec.md"
    source.write_text("# Spec\n\nContent.", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Test Spec",
            "--type", "specification",
            "--file", str(source),
        ],
    )
    assert result.exit_code == 0
    assert "art_" in result.stdout
    assert "ver_" in result.stdout


def test_artifact_update(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    source = tmp_path / "v1.md"
    source.write_text("Version 1", encoding="utf-8")

    create_result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Doc",
            "--type", "document",
            "--file", str(source),
        ],
    )
    art_id = _extract_id(create_result.stdout, "art_")
    assert art_id is not None, f"Could not find artifact_id in: {create_result.stdout}"

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Version 2", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "artifact", "update",
            "--artifact", art_id,
            "--file", str(source_v2),
            "--summary", "Second version",
        ],
    )
    assert result.exit_code == 0
    assert "ver_" in result.stdout


def test_artifact_history(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    source = tmp_path / "doc.md"
    source.write_text("Content", encoding="utf-8")

    create_result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Doc",
            "--type", "document",
            "--file", str(source),
        ],
    )
    art_id = _extract_id(create_result.stdout, "art_")
    assert art_id is not None

    result = runner.invoke(
        app,
        ["artifact", "history", "--artifact", art_id],
    )
    assert result.exit_code == 0
    assert "ver_" in result.stdout


def test_decision_record(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    source = tmp_path / "doc.md"
    source.write_text("Content", encoding="utf-8")

    create_result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Doc",
            "--type", "document",
            "--file", str(source),
        ],
    )
    art_id = _extract_id(create_result.stdout, "art_")
    assert art_id is not None

    result = runner.invoke(
        app,
        [
            "decision", "record",
            "--type", "accepted",
            "--reason", "Looks good for v0.1",
            "--artifact", art_id,
        ],
    )
    assert result.exit_code == 0
    assert "dec_" in result.stdout


def test_rde_record_with_fields(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    source_v1 = tmp_path / "v1.md"
    source_v1.write_text("Original", encoding="utf-8")

    create_result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Spec",
            "--type", "specification",
            "--file", str(source_v1),
        ],
    )
    output = create_result.stdout
    art_id = _extract_id(output, "art_")
    ver1_id = _extract_id(output, "ver_")
    assert art_id is not None
    assert ver1_id is not None

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Updated", encoding="utf-8")

    update_result = runner.invoke(
        app,
        [
            "artifact", "update",
            "--artifact", art_id,
            "--file", str(source_v2),
            "--summary", "Updated",
        ],
    )
    ver2_id = _extract_id(update_result.stdout, "ver_")
    assert ver2_id is not None

    result = runner.invoke(
        app,
        [
            "rde", "record",
            "--artifact", art_id,
            "--from", ver1_id,
            "--to", ver2_id,
            "--summary", "RDE test",
            "--preserved", "Original intent",
            "--preserved", "Core structure",
            "--deviation-risk", "Possible scope creep",
        ],
    )
    assert result.exit_code == 0
    assert "rde_" in result.stdout


def test_search(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    runner.invoke(
        app,
        [
                "record",
            "--type", "user_input",
            "--actor", "user",
            "--summary", "UniqueQueryTerm",
        ],
    )

    result = runner.invoke(app, ["search", "UniqueQueryTerm"])
    assert result.exit_code == 0
    assert "UniqueQueryTerm" in result.stdout


def test_export_yaml(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    result = runner.invoke(app, ["export", "--format", "yaml"])
    assert result.exit_code == 0
    assert "CLI Test" in result.stdout
    assert "events:" in result.stdout


def test_export_markdown(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    result = runner.invoke(app, ["export", "--format", "markdown"])
    assert result.exit_code == 0
    assert "# Chronicle: CLI Test" in result.stdout


def test_index_rebuild(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    result = runner.invoke(app, ["index", "rebuild"])
    assert result.exit_code == 0


def test_artifact_update_without_file_errors(tmp_path: Path) -> None:
    """artifact update without --file must fail with ARTIFACT_CONTENT_MISSING."""
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])
    source = tmp_path / "doc.md"
    source.write_text("Content", encoding="utf-8")

    create_result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Doc",
            "--type", "document",
            "--file", str(source),
        ],
    )
    art_id = _extract_id(create_result.stdout, "art_")
    assert art_id is not None

    result = runner.invoke(
        app,
        ["artifact", "update", "--artifact", art_id],
    )
    assert result.exit_code == 1
    assert "either --file or --content" in result.stderr


def test_rde_record_fields_in_report(tmp_path: Path) -> None:
    """All six RDE fields must appear in the generated Markdown report."""
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])

    source_v1 = tmp_path / "v1.md"
    source_v1.write_text("Original", encoding="utf-8")
    create_result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Spec",
            "--type", "specification",
            "--file", str(source_v1),
        ],
    )
    art_id = _extract_id(create_result.stdout, "art_")
    ver1_id = _extract_id(create_result.stdout, "ver_")
    assert art_id is not None
    assert ver1_id is not None

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Updated", encoding="utf-8")
    update_result = runner.invoke(
        app,
        [
            "artifact", "update",
            "--artifact", art_id,
            "--file", str(source_v2),
            "--summary", "Updated",
        ],
    )
    ver2_id = _extract_id(update_result.stdout, "ver_")
    assert ver2_id is not None

    rde_result = runner.invoke(
        app,
        [
            "rde", "record",
            "--artifact", art_id,
            "--from", ver1_id,
            "--to", ver2_id,
            "--summary", "Full RDE test",
            "--preserved", "Preserved item",
            "--transformed", "Transformed item",
            "--supplemented", "Supplemented item",
            "--unresolved", "Unresolved item",
            "--deviation-risk", "Deviation risk item",
            "--next-update-policy", "Next update policy item",
        ],
    )
    assert rde_result.exit_code == 0, f"rde record failed: {rde_result.stderr}"
    rde_id = _extract_id(rde_result.stdout, "rde_")
    assert rde_id is not None

    # Read the generated RDE report and verify all six sections
    report_path = tmp_path / ".chronicle" / "reports" / "rde" / f"{rde_id}.md"
    assert report_path.exists(), f"Report not found at {report_path}"
    report_text = report_path.read_text(encoding="utf-8")

    assert "## Preserved" in report_text
    assert "Preserved item" in report_text
    assert "## Transformed" in report_text
    assert "Transformed item" in report_text
    assert "## Supplemented" in report_text
    assert "Supplemented item" in report_text
    assert "## Unresolved" in report_text
    assert "Unresolved item" in report_text
    assert "## Deviation Risks" in report_text
    assert "Deviation risk item" in report_text
    assert "## Next Update Policy" in report_text
    assert "Next update policy item" in report_text


def test_rde_record_links_to_version(tmp_path: Path) -> None:
    """After RDE record + index rebuild, artifact history JSON shows rde_record_id."""
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])

    source_v1 = tmp_path / "v1.md"
    source_v1.write_text("Original", encoding="utf-8")
    create_result = runner.invoke(
        app,
        [
            "artifact", "create",
            "--title", "Spec",
            "--type", "specification",
            "--file", str(source_v1),
        ],
    )
    art_id = _extract_id(create_result.stdout, "art_")
    ver1_id = _extract_id(create_result.stdout, "ver_")
    assert art_id is not None
    assert ver1_id is not None

    source_v2 = tmp_path / "v2.md"
    source_v2.write_text("Updated", encoding="utf-8")
    update_result = runner.invoke(
        app,
        [
            "artifact", "update",
            "--artifact", art_id,
            "--file", str(source_v2),
            "--summary", "Updated",
        ],
    )
    ver2_id = _extract_id(update_result.stdout, "ver_")
    assert ver2_id is not None

    rde_result = runner.invoke(
        app,
        [
            "rde", "record",
            "--artifact", art_id,
            "--from", ver1_id,
            "--to", ver2_id,
            "--summary", "RDE link test",
            "--preserved", "Original intent",
        ],
    )
    assert rde_result.exit_code == 0
    rde_id = _extract_id(rde_result.stdout, "rde_")
    assert rde_id is not None

    # Rebuild indexes to trigger rde_record_id enrichment
    rebuild_result = runner.invoke(app, ["index", "rebuild"])
    assert rebuild_result.exit_code == 0

    # Read artifact history JSON and verify rde_record_id
    history_result = runner.invoke(
        app,
        ["artifact", "history", "--artifact", art_id, "--json"],
    )
    assert history_result.exit_code == 0
    data = json.loads(history_result.stdout)
    versions = data["versions"]
    v2_entry = [v for v in versions if v["version_id"] == ver2_id][0]
    assert v2_entry.get("rde_record_id") == rde_id, (
        f"Expected rde_record_id={rde_id} but got {v2_entry.get('rde_record_id')}"
    )


def test_ai_boundary_preview_and_rde_draft_cli(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI AI Boundary Test"])

    context_result = runner.invoke(
        app,
        [
            "add-context",
            "--title",
            "AI Boundary Context",
            "--summary",
            "Safe context for preview",
            "--scope",
            "task",
        ],
    )
    ctx_id = _extract_id(context_result.stdout, "ctx_")
    assert ctx_id is not None

    preview_result = runner.invoke(
        app,
        [
            "ai-boundary",
            "preview",
            "--task",
            "summarize for external model",
            "--context",
            ctx_id,
            "--model",
            "external:test-model",
            "--record",
            "--json",
        ],
    )
    assert preview_result.exit_code == 0, preview_result.stderr
    preview = json.loads(preview_result.stdout)
    assert preview["recorded"] is True
    assert preview["included_context_ids"] == [ctx_id]
    assert preview["sayane_contract"]["import_command"].startswith("chronicle rde draft")

    source_v1 = tmp_path / "ai-v1.md"
    source_v1.write_text("Original", encoding="utf-8")
    create_result = runner.invoke(
        app,
        [
            "artifact",
            "create",
            "--title",
            "AI Draft Artifact",
            "--type",
            "specification",
            "--file",
            str(source_v1),
        ],
    )
    art_id = _extract_id(create_result.stdout, "art_")
    ver1_id = _extract_id(create_result.stdout, "ver_")
    assert art_id is not None and ver1_id is not None

    source_v2 = tmp_path / "ai-v2.md"
    source_v2.write_text("Updated", encoding="utf-8")
    update_result = runner.invoke(
        app,
        [
            "artifact",
            "update",
            "--artifact",
            art_id,
            "--file",
            str(source_v2),
            "--summary",
            "Updated",
        ],
    )
    ver2_id = _extract_id(update_result.stdout, "ver_")
    assert ver2_id is not None

    draft_result = runner.invoke(
        app,
        [
            "rde",
            "draft",
            "--artifact",
            art_id,
            "--from",
            ver1_id,
            "--to",
            ver2_id,
            "--summary",
            "AI-assisted delta",
            "--mode",
            "ai-assisted",
            "--ai-summary",
            "Separated AI summary",
            "--interpretation",
            "Treat this as a hypothesis",
            "--record",
            "--json",
        ],
    )
    assert draft_result.exit_code == 0, draft_result.stderr
    memo = json.loads(draft_result.stdout)
    assert memo["recorded_rde_id"].startswith("rde_")
    assert memo["linked_delta_object_id"] == f"obj_delta_{memo['recorded_rde_id']}"
    assert memo["linked_hypothesis_object_id"].startswith("obj_")


def test_reaction_cli_records_meaningful_relation(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Reaction Test"])

    result = runner.invoke(
        app,
        [
            "reaction",
            "record",
            "--type",
            "reference",
            "--target-object",
            "obj_target",
            "--source-object",
            "obj_source",
            "--summary",
            "Reference this object",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["reaction_id"].startswith("react_")
    assert payload["reaction_type"] == "reference"


def test_chronicle_object_record_and_show(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])

    record_result = runner.invoke(
        app,
        [
            "object",
            "record",
            "--type",
            "question",
            "--summary",
            "Why is this boundary needed?",
            "--created-by",
            "tester",
        ],
    )
    assert record_result.exit_code == 0
    object_id = _extract_id(record_result.stdout, "obj_")
    assert object_id is not None

    show_result = runner.invoke(app, ["object", "show", "--id", object_id, "--json"])
    assert show_result.exit_code == 0
    payload = json.loads(show_result.stdout)
    assert payload["object_id"] == object_id
    assert payload["object_type"] == "question"

    list_result = runner.invoke(app, ["object", "list", "--type", "question", "--json"])
    assert list_result.exit_code == 0
    rows = json.loads(list_result.stdout)
    assert any(row["object_id"] == object_id for row in rows)


def test_federation_message_create_and_inspect(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])

    create_result = runner.invoke(
        app,
        [
            "federation",
            "message",
            "create",
            "--type",
            "request_context",
            "--source-node",
            "node:local:alpha",
            "--target-node",
            "node:local:beta",
            "--purpose",
            "project review",
            "--object-ref",
            "ctx_1",
            "--json",
        ],
    )
    assert create_result.exit_code == 0
    payload = json.loads(create_result.stdout)
    assert payload["message"]["message_type"] == "request_context"
    assert payload["message"]["preview_only"] is True

    inbox_create_result = runner.invoke(
        app,
        [
            "federation",
            "message",
            "create",
            "--type",
            "decay_notice",
            "--source-node",
            "node:local:alpha",
            "--target-node",
            "node:local:beta",
            "--purpose",
            "decay review",
            "--box",
            "inbox",
            "--json",
        ],
    )
    assert inbox_create_result.exit_code == 0
    inbox_payload = json.loads(inbox_create_result.stdout)
    message_id = inbox_payload["message"]["message_id"]
    assert inbox_payload["audit_recorded"] is True

    inspect_result = runner.invoke(app, ["federation", "inbox", "inspect", "--json"])
    assert inspect_result.exit_code == 0
    rows = json.loads(inspect_result.stdout)
    assert any(row["message_id"] == message_id and row["audit_recorded"] is True for row in rows)


def test_trust_node_assert_withdraw_and_list(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "CLI Test"])

    node_result = runner.invoke(
        app,
        [
            "trust",
            "node",
            "add",
            "--node-id",
            "node:partner:beta",
            "--subject-id",
            "subject:beta",
            "--json",
        ],
    )
    assert node_result.exit_code == 0
    assert json.loads(node_result.stdout)["node_id"] == "node:partner:beta"

    assert_result = runner.invoke(
        app,
        [
            "trust",
            "assert",
            "--target-node",
            "node:partner:beta",
            "--target-subject-id",
            "subject:beta",
            "--domain",
            "technical_review",
            "--purpose",
            "project review",
            "--level",
            "trusted",
            "--capability",
            "review",
            "--json",
        ],
    )
    assert assert_result.exit_code == 0
    relation_id = json.loads(assert_result.stdout)["relation_id"]

    withdraw_result = runner.invoke(
        app,
        ["trust", "withdraw", "--relation", relation_id, "--reason", "expired", "--json"],
    )
    assert withdraw_result.exit_code == 0
    assert json.loads(withdraw_result.stdout)["status"] == "withdrawn"

    list_result = runner.invoke(app, ["trust", "list", "--json"])
    assert list_result.exit_code == 0
    rows = json.loads(list_result.stdout)
    assert any(row["relation_id"] == relation_id for row in rows)
