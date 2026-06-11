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
