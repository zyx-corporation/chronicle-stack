import json
import os

from typer.testing import CliRunner

from chronicle.cli import app


def _run(tmp_path, *args):
    os.chdir(str(tmp_path))
    runner = CliRunner()
    return runner.invoke(app, list(args))


def test_federation_package_create_inspect_and_verify_cli(tmp_path):
    assert _run(tmp_path, "init", "--title", "Federation Package CLI").exit_code == 0
    context_result = _run(
        tmp_path,
        "add-context",
        "--title",
        "Federation CLI Context",
        "--summary",
        "Shareable context",
        "--json",
    )
    context_id = json.loads(context_result.stdout)["context_id"]
    package_dir = tmp_path / "fed-bundle"

    create_result = _run(
        tmp_path,
        "federation",
        "package",
        "create",
        "--purpose",
        "cli review",
        "--target-node",
        "node:partner:beta",
        "--context",
        context_id,
        "--output-dir",
        str(package_dir),
        "--json",
    )
    assert create_result.exit_code == 0, create_result.stderr
    manifest = json.loads(create_result.stdout)
    assert manifest["target_node"] == "node:partner:beta"

    inspect_result = _run(
        tmp_path,
        "federation",
        "package",
        "inspect",
        "--package-dir",
        str(package_dir),
        "--json",
    )
    assert inspect_result.exit_code == 0, inspect_result.stderr
    inspect_payload = json.loads(inspect_result.stdout)
    assert inspect_payload["manifest"]["purpose"] == "cli review"
    assert inspect_payload["redaction_report"]["record_count"] == 1

    verify_result = _run(
        tmp_path,
        "federation",
        "package",
        "verify",
        "--package-dir",
        str(package_dir),
        "--json",
    )
    assert verify_result.exit_code == 0, verify_result.stderr
    verify_payload = json.loads(verify_result.stdout)
    assert verify_payload["valid"] is True
    assert verify_payload["warnings"] == ["signature_unsigned"]


def test_federation_package_create_and_verify_signed_cli(tmp_path):
    assert _run(tmp_path, "init", "--title", "Federation Package Signed CLI").exit_code == 0
    context_result = _run(
        tmp_path,
        "add-context",
        "--title",
        "Federation Signed CLI Context",
        "--summary",
        "Signed shareable context",
        "--json",
    )
    context_id = json.loads(context_result.stdout)["context_id"]
    package_dir = tmp_path / "fed-bundle-signed"

    create_result = _run(
        tmp_path,
        "federation",
        "package",
        "create",
        "--purpose",
        "cli signed review",
        "--target-node",
        "node:partner:beta",
        "--context",
        context_id,
        "--output-dir",
        str(package_dir),
        "--signature-mode",
        "local_dev",
        "--json",
    )
    assert create_result.exit_code == 0, create_result.stderr
    manifest = json.loads(create_result.stdout)
    assert manifest["signature"]["status"] == "signed"
    assert manifest["signature"]["value"]

    verify_result = _run(
        tmp_path,
        "federation",
        "package",
        "verify",
        "--package-dir",
        str(package_dir),
        "--json",
    )
    assert verify_result.exit_code == 0, verify_result.stderr
    verify_payload = json.loads(verify_result.stdout)
    assert verify_payload["valid"] is True
    assert verify_payload["signature_status"] == "signed"
    assert verify_payload["warnings"] == []
