"""Tests for local installer script safety behavior."""

import os
import subprocess
from pathlib import Path


def _make_local_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "source-repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "ci@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "CI"], cwd=repo, check=True)
    (repo / "README.md").write_text("installer smoke repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(["git", "tag", "v-test"], cwd=repo, check=True)
    return repo


def test_install_local_dry_run_fetches_requested_tag(tmp_path):
    script = Path("scripts/install-local.sh")
    repo = _make_local_repo(tmp_path)
    install_dir = tmp_path / "app"
    bin_dir = tmp_path / "bin"

    result = subprocess.run(
        ["bash", str(script)],
        check=True,
        cwd=Path.cwd(),
        env={
            **os.environ,
            "DRY_RUN": "1",
            "CHRONICLE_STACK_REPO_URL": str(repo),
            "CHRONICLE_STACK_REF": "v-test",
            "INSTALL_DIR": str(install_dir),
            "BIN_DIR": str(bin_dir),
        },
        capture_output=True,
        text=True,
    )

    assert "Repository: " in result.stdout
    assert "Ref: v-test" in result.stdout
    assert "Fetching tag ref if available: v-test" in result.stdout
    assert "Refreshing local tag from origin: v-test" in result.stdout
    assert "Checking out ref: v-test" in result.stdout
    assert "--force-reinstall" in result.stdout
    assert "CHRONICLE_STACK_ALLOW_MOVED_TAG=0" in result.stdout


def test_install_local_dry_run_can_disable_moved_tag_refresh(tmp_path):
    script = Path("scripts/install-local.sh")
    repo = _make_local_repo(tmp_path)
    install_dir = tmp_path / "app"
    bin_dir = tmp_path / "bin"

    result = subprocess.run(
        ["bash", str(script)],
        check=True,
        cwd=Path.cwd(),
        env={
            **os.environ,
            "DRY_RUN": "1",
            "CHRONICLE_STACK_REPO_URL": str(repo),
            "CHRONICLE_STACK_REF": "v-test",
            "CHRONICLE_STACK_ALLOW_MOVED_TAG": "0",
            "INSTALL_DIR": str(install_dir),
            "BIN_DIR": str(bin_dir),
        },
        capture_output=True,
        text=True,
    )

    assert "Moved-tag refresh disabled" in result.stdout
    assert "fetch --tags --prune origin" in result.stdout
