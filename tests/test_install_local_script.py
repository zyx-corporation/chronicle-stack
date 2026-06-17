"""Static checks for local installer hardening notes."""

from pathlib import Path


def test_install_local_script_mentions_moved_tag_controls():
    script = Path("scripts/install-local.sh").read_text(encoding="utf-8")

    assert "CHRONICLE_STACK_ALLOW_MOVED_TAG" in script
    assert "Refreshing local tag from origin" in script
    assert "Moved-tag refresh disabled" in script
    assert "--force-reinstall" in script


def test_local_deployment_docs_mention_moved_tag_handling():
    docs = Path("docs/local-deployment-curl.md").read_text(encoding="utf-8")

    assert "Moved or Recreated Tags" in docs
    assert "CHRONICLE_STACK_ALLOW_MOVED_TAG" in docs
    assert "clean install directory" in docs
