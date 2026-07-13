"""Local installer regression coverage."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_install_local_dry_run_includes_backup_restore_helpers(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "install-local.sh"
    install_dir = tmp_path / "install"
    bin_dir = tmp_path / "bin"
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    env = os.environ.copy()
    env.update(
        {
            "DRY_RUN": "1",
            "INSTALL_DIR": str(install_dir),
            "BIN_DIR": str(bin_dir),
            "CHRONICLE_STACK_REPO_URL": str(repo_root),
            "CHRONICLE_STACK_REF": head_sha,
        }
    )

    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    stdout = result.stdout
    assert "chronicle-backup-local" in stdout
    assert "chronicle-restore-local" in stdout
    assert f"{install_dir}/scripts/backup-local.sh" in stdout
    assert f"{install_dir}/scripts/restore-local.sh" in stdout
