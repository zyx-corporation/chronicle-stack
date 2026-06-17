"""Tests for local installer script safety behavior."""

from pathlib import Path


def test_install_local_script_refreshes_requested_tag():
    script = Path("scripts/install-local.sh").read_text(encoding="utf-8")

    assert "CHRONICLE_STACK_ALLOW_MOVED_TAG" in script
    assert "ALLOW_MOVED_TAG" in script
    assert "remote_has_tag" in script
    assert "+refs/tags/$REF:refs/tags/$REF" in script
    assert "Refreshing local tag from origin" in script


def test_install_local_script_preserves_opt_out_and_reinstall_behavior():
    script = Path("scripts/install-local.sh").read_text(encoding="utf-8")

    assert "Moved-tag refresh disabled" in script
    assert "fetch --tags --prune origin" in script
    assert "--force-reinstall" in script
    assert "Checked out commit" in script


def test_local_deployment_docs_document_moved_tag_behavior():
    docs = Path("docs/local-deployment-curl.md").read_text(encoding="utf-8")

    assert "Moved or Recreated Tags" in docs
    assert "CHRONICLE_STACK_ALLOW_MOVED_TAG" in docs
    assert "clean install directory" in docs
    assert "release tags should normally be immutable" in docs.lower()
