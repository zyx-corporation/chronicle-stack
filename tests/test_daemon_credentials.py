"""Private daemon credential delivery and cleanup regressions."""

import json
import os
import stat

import pytest
from typer.testing import CliRunner

from chronicle.cli import app
from chronicle import daemon_server
from chronicle.errors import ChronicleError
from chronicle.services.chronicle_service import ChronicleService

TOKEN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"


@pytest.mark.parametrize("token", ["short", "a" * 64, "abcd" * 16, "非ASCII" * 20, ""])
def test_weak_tokens_rejected_before_bind(tmp_path, token):
    with pytest.raises(ChronicleError):
        daemon_server.make_daemon_server(root=tmp_path, port=0, session_token=token)


def test_metadata_never_contains_a_credential(tmp_path):
    metadata = daemon_server.build_daemon_startup_metadata(root=tmp_path)
    assert "session_token" not in metadata.to_dict()
    assert not hasattr(metadata, "session_token")


@pytest.mark.parametrize("mode", [0o600, 0o644, 0o400])
def test_existing_token_file_rejected_without_replacing(tmp_path, mode):
    from chronicle.daemon_credentials import daemon_token_file
    path = tmp_path / "daemon.token"
    path.write_text("pre-existing")
    path.chmod(mode)
    with pytest.raises(ChronicleError):
        with daemon_token_file(path):
            pytest.fail("existing credential was reused")
    assert path.read_text() == "pre-existing"
    assert stat.S_IMODE(path.stat().st_mode) == mode


def test_symlink_token_file_rejected(tmp_path):
    from chronicle.daemon_credentials import daemon_token_file
    target = tmp_path / "target"
    target.write_text("untouched")
    path = tmp_path / "daemon.token"
    path.symlink_to(target)
    with pytest.raises(ChronicleError):
        with daemon_token_file(path):
            pytest.fail("symlink followed")
    assert target.read_text() == "untouched"
    assert path.is_symlink()


def test_created_credential_is_private_and_removed_on_error(tmp_path):
    from chronicle.daemon_credentials import daemon_token_file
    path = tmp_path / "daemon.token"
    with pytest.raises(RuntimeError):
        with daemon_token_file(path) as token:
            assert stat.S_IMODE(path.stat().st_mode) == 0o600
            assert path.read_text().strip() == token
            assert len(token) >= 43
            raise RuntimeError("server failed")
    assert not path.exists()


def test_replacement_file_is_not_removed(tmp_path):
    from chronicle.daemon_credentials import daemon_token_file
    path = tmp_path / "daemon.token"
    with daemon_token_file(path):
        path.rename(tmp_path / "original")
        path.write_text("replacement")
    assert path.read_text() == "replacement"


def test_restrictive_umask_rejected_and_created_file_cleaned(tmp_path):
    from chronicle.daemon_credentials import daemon_token_file
    path = tmp_path / "daemon.token"
    previous = os.umask(0o777)
    try:
        with pytest.raises(ChronicleError):
            with daemon_token_file(path):
                pytest.fail("non-0600 credential created")
    finally:
        os.umask(previous)
    assert not path.exists()


@pytest.mark.parametrize("json_output", [False, True])
def test_cli_never_prints_token(tmp_path, monkeypatch, json_output):
    ChronicleService(tmp_path).init("Daemon credential")
    monkeypatch.setattr(daemon_server.secrets, "token_urlsafe", lambda _: TOKEN)
    observed = []

    class Server:
        def serve_forever(self):
            observed.append((tmp_path / ".chronicle/daemon.token").read_text().strip())
            raise KeyboardInterrupt

        def server_close(self):
            pass

    monkeypatch.setattr(daemon_server, "make_daemon_server", lambda **kwargs: Server())
    args = ["daemon", "start", "--root", str(tmp_path)]
    if json_output:
        args.append("--json")
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert TOKEN not in result.output
    if json_output:
        assert "session_token" not in json.loads(result.stdout)
        assert observed == []  # metadata-only must not issue a credential
    else:
        assert observed == [TOKEN]
    assert not (tmp_path / ".chronicle/daemon.token").exists()


def test_removed_argv_token_option_does_not_echo_value(tmp_path):
    ChronicleService(tmp_path).init("No argv credential")
    result = CliRunner().invoke(app, ["daemon", "start", "--root", str(tmp_path),
                                     "--session-token", TOKEN, "--json"])
    assert result.exit_code != 0
    assert TOKEN not in result.output


def test_bind_failure_cleans_token_file(tmp_path, monkeypatch):
    ChronicleService(tmp_path).init("Bind failure")

    def fail(**kwargs):
        assert (tmp_path / ".chronicle/daemon.token").exists()
        raise OSError("bind failed")

    monkeypatch.setattr(daemon_server, "make_daemon_server", fail)
    with pytest.raises(ChronicleError):
        daemon_server.serve_daemon(root=tmp_path)
    assert not (tmp_path / ".chronicle/daemon.token").exists()


def test_parent_symlink_rejected(tmp_path):
    from chronicle.daemon_credentials import daemon_token_file
    directory = tmp_path / "private"
    directory.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ChronicleError):
        with daemon_token_file(alias / "daemon.token"):
            pytest.fail("parent symlink followed")
    assert not (directory / "daemon.token").exists()


def test_real_daemon_sigterm_cleanup_and_private_auth(tmp_path):
    import http.client
    import subprocess
    import sys
    import time

    ChronicleService(tmp_path).init("SIGTERM lifecycle")
    token_path = tmp_path / ".chronicle/daemon.token"
    # Reserve a loopback port, then hand it to the subprocess.
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    command = [sys.executable, "-c", "from chronicle.cli import main; main()",
               "daemon", "start", "--root", str(tmp_path),
               "--port", str(port)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    token = ""
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if token_path.exists():
                token = token_path.read_text().strip()
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
                try:
                    connection.request("GET", "/context?subject_ref=test",
                                       headers={"X-Chronicle-Daemon-Token": token})
                    response = connection.getresponse()
                    assert response.status == 200
                    response.read()
                    break
                except ConnectionRefusedError:
                    pass
                finally:
                    connection.close()
            assert process.poll() is None, "daemon exited before serving"
            time.sleep(0.05)
        else:
            pytest.fail("daemon did not start")
        assert token and token not in " ".join(command)
        assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, stderr
        assert token not in stdout + stderr
        assert not token_path.exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
