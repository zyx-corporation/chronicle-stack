"""Tests for local installer script safety behavior."""

import os
import subprocess
from pathlib import Path


def test_install_local_dry_run_fetches_requested_tag(tmp_path):
    script = Path("scripts/install-local.sh")
    install_dir = tmp_path / "app"
    bin_dir = tmp_path / "bin"

    result = subprocess.run(
        ["bash", str(script)],
        check=True,
        cwd=Path.cwd(),
        env={
            **os.environ,
            "DRY_RUN": "1",
            "CHRONICLE_STACK_REF": "v1.3.0",
            "INSTALL_DIR": str(install_dir),
            "BIN_DIR": str(bin_dir),
        },
        capture_output=True,
        text=True,
    )

    assert "Ref: v1.3.0" in result.stdout
    assert "Fetching tag ref if available: v1.3.0" in result.stdout
    assert "Checking out ref: v1.3.0" in result.stdout
    assert "--force-reinstall" in result.stdout
    assert "CHRONICLE_STACK_ALLOW_MOVED_TAG=0" in result.stdout


def test_install_local_dry_run_can_disable_moved_tag_refresh(tmp_path):
    script = Path("scripts/install-local.sh")
    install_dir = tmp_path / "app"
    bin_dir = tmp_path / "bin"

    result = subprocess.run(
        ["bash", str(script)],
        check=True,
        cwd=Path.cwd(),
        env={
            **os.environ,
            "DRY_RUN": "1",
            "CHRONICLE_STACK_REF": "v1.3.0",
            "CHRONICLE_STACK_ALLOW_MOVED_TAG": "0",
            "INSTALL_DIR": str(install_dir),
            "BIN_DIR": str(bin_dir),
        },
        capture_output=True,
        text=True,
    )

    assert "Moved-tag refresh disabled" in result.stdout
    assert "fetch --tags --prune origin" in result.stdout
