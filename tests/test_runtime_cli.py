"""Tests for explicit local runtime CLI commands."""

import json
import os
import re
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.services.artifact_service import ArtifactService


runner = CliRunner()


class _RuntimeHandler(BaseHTTPRequestHandler):
    response_payload = {
        "output_text": "Configured provider summary.",
        "response_id": "resp_default",
        "finish_reason": "stop",
        "usage": {"input_tokens": 12, "output_tokens": 5},
    }
    status_code = 200
    expected_source_count = 0
    expected_prompt = ""
    expected_params: dict[str, str] = {}

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        assert payload["operation"]
        assert "input_text" in payload
        if self.expected_source_count:
            assert len(payload.get("source_refs", [])) == self.expected_source_count
        if self.expected_prompt:
            assert payload.get("prompt") == self.expected_prompt
        if self.expected_params:
            assert payload.get("params") == self.expected_params
        self.send_response(self.status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(self.response_payload).encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def _start_runtime_server() -> tuple[HTTPServer, threading.Thread]:
    server = HTTPServer(("127.0.0.1", 0), _RuntimeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_runtime_status_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Status"])

    result = runner.invoke(app, ["runtime", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["configured_provider_kind"] == "local"
    assert payload["external_call_made"] is False
    assert payload["generated_output_requires_review"] is True


def test_runtime_config_show_implicit_default(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Config"])

    result = runner.invoke(app, ["runtime", "config", "show", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["source"] == "implicit-default"
    assert payload["config"]["provider_kind"] == "local"
    assert payload["config"]["allow_network"] is False
    assert any("Configuration alone does not invoke" in item for item in payload["warnings"])


def test_runtime_config_set_http_persists_contract_and_updates_status(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime HTTP Config"])

    result = runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "manual-http-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["config"]["provider_kind"] == "http"
    assert payload["config"]["base_url"] == "https://runtime.example.invalid/v1"
    assert payload["config"]["api_key_env"] == "OPENAI_API_KEY"
    assert payload["config"]["allow_network"] is True
    assert any("stored contract only" in item for item in payload["warnings"])

    status_result = runner.invoke(app, ["runtime", "status", "--json"])
    assert status_result.exit_code == 0
    status_payload = json.loads(status_result.stdout)
    assert status_payload["provider_kind"] == "local"
    assert status_payload["configured_provider_kind"] == "http"
    assert status_payload["configured_model_name"] == "manual-http-model"


def test_runtime_config_disable_persists_disabled_contract(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Disable Config"])

    result = runner.invoke(app, ["runtime", "config", "disable", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["config"]["provider_kind"] == "disabled"
    assert any("disabled" in item.lower() for item in payload["warnings"])


def test_runtime_invoke_plan_blocks_http_without_network_permission(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invocation Blocked"])
    runner.invoke(
        app,
        [
            "runtime", "config", "set-http",
            "--base-url", "https://runtime.example.invalid/v1",
            "--model", "manual-http-model",
            "--api-key-env", "OPENAI_API_KEY",
        ],
    )

    result = runner.invoke(
        app,
        [
            "runtime", "invoke-plan",
            "--text", "Invocation planning source text.",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "http"
    assert payload["would_use_network"] is True
    assert payload["network_allowed_by_contract"] is False
    assert payload["invocation_ready"] is False
    assert "network_not_allowed_by_contract" in payload["blocking_reasons"]


def test_runtime_invoke_plan_can_record_ready_local_contract(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invocation Ready"])
    runner.invoke(
        app,
        ["runtime", "config", "set-local", "--model", "local-ready-model", "--provider-name", "local-ready"],
    )

    result = runner.invoke(
        app,
        [
            "runtime", "invoke-plan",
            "--text", "Invocation planning source text. It stays explicit.",
            "--record",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["invocation_ready"] is True
    assert payload["external_call_made"] is False
    assert payload["recorded"] is True
    assert re.match(r"evt_[a-f0-9]+", payload["event_id"])

    search_result = runner.invoke(app, ["search", "Runtime invocation plan generated", "--json"])
    search_payload = json.loads(search_result.stdout)
    assert any(item["kind"] == "event" for item in search_payload)


def test_runtime_summarize_json_without_record(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))

    result = runner.invoke(
        app,
        [
            "runtime",
            "summarize",
            "--text",
            "First sentence. Second sentence. Third sentence. Fourth sentence.",
            "--max-sentences",
            "2",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["external_call_made"] is False
    assert payload["recorded"] is False
    assert payload["generated_text"] == "First sentence. Second sentence."


def test_runtime_summarize_record_persists_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Chronicle"])

    result = runner.invoke(
        app,
        [
            "runtime",
            "summarize",
            "--text",
            "A local explicit runtime summary should be reviewable. It must stay local.",
            "--record",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["recorded"] is True
    assert re.match(r"evt_[a-f0-9]+", payload["event_id"])

    show_result = runner.invoke(app, ["show", "--json"])
    show_payload = json.loads(show_result.stdout)
    assert show_payload["event_count"] == 2

    search_result = runner.invoke(app, ["search", "Runtime summary generated", "--json"])
    search_payload = json.loads(search_result.stdout)
    assert any(item["kind"] == "event" for item in search_payload)


def test_runtime_summarize_can_persist_draft_summary_job(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Draft Chronicle"])

    result = runner.invoke(
        app,
        [
            "runtime",
            "summarize",
            "--text",
            "A runtime-produced draft should stay reviewable and explicit. It remains local.",
            "--draft-title",
            "Runtime Draft Summary",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["draft_summary_job_id"].startswith("sum_")
    assert payload["draft_artifact_id"].startswith("art_")
    assert payload["draft_version_id"].startswith("ver_")
    assert payload["external_call_made"] is False

    show_result = runner.invoke(app, ["summary", "show", "--id", payload["draft_summary_job_id"], "--json"])
    assert show_result.exit_code == 0
    job = json.loads(show_result.stdout)
    assert job["title"] == "Runtime Draft Summary"
    assert job["provenance"]["generated_by"] == "runtime_manual"
    assert job["provenance"]["invocation_mode"] == "explicit-manual"
    assert job["provenance"]["runtime"]["provider_kind"] == "local"


def test_runtime_summarize_http_requires_explicit_execution_flag(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime HTTP Chronicle"])
    runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "http-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
        ],
    )

    result = runner.invoke(
        app,
        [
            "runtime",
            "summarize",
            "--text",
            "HTTP execution should stay explicit.",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "RUNTIME_PROVIDER_EXECUTION_NOT_ENABLED"


def test_runtime_summarize_http_uses_configured_provider_when_explicitly_enabled(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime HTTP Chronicle"])
    server, thread = _start_runtime_server()
    os.environ["OPENAI_API_KEY"] = "test-key"
    try:
        runner.invoke(
            app,
            [
                "runtime",
                "config",
                "set-http",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "http-model",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--allow-network",
                "--json",
            ],
        )

        result = runner.invoke(
            app,
            [
                "runtime",
                "summarize",
                "--text",
                "HTTP execution should remain explicit and reviewable.",
                "--execute-configured-provider",
                "--draft-title",
                "HTTP Runtime Draft",
                "--record",
                "--json",
            ],
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "http"
    assert payload["provider_name"] == "http-manual"
    assert payload["external_call_made"] is True
    assert payload["invocation_mode"] == "explicit-http-manual"
    assert payload["generated_text"] == "Configured provider summary."
    assert payload["draft_summary_job_id"].startswith("sum_")
    assert payload["recorded"] is True

    show_result = runner.invoke(app, ["summary", "show", "--id", payload["draft_summary_job_id"], "--json"])
    job = json.loads(show_result.stdout)
    assert job["provenance"]["generated_by"] == "runtime_http_manual"
    assert job["provenance"]["external_call_made"] is True
    assert job["provenance"]["runtime"]["provider_kind"] == "http"
    assert job["provenance"]["runtime"]["model_name"] == "http-model"
    assert job["provenance"]["response_metadata"]["response_id"] == "resp_default"
    assert job["provenance"]["response_metadata"]["usage_input_tokens"] == 12
    assert "usage" in job["provenance"]["response_keys"]


def test_runtime_invoke_requires_explicit_execution_flag(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke HTTP Chronicle"])
    runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "http-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
        ],
    )

    result = runner.invoke(
        app,
        [
            "runtime",
            "invoke",
            "--text",
            "Invoke execution should stay explicit.",
            "--operation",
            "rewrite",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "RUNTIME_PROVIDER_EXECUTION_NOT_ENABLED"


def test_runtime_invoke_executes_configured_provider_and_records_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke Chronicle"])
    server, thread = _start_runtime_server()
    os.environ["OPENAI_API_KEY"] = "test-key"
    _RuntimeHandler.response_payload = {
        "output_text": "Configured provider rewrite.",
        "response_id": "resp_rewrite",
        "finish_reason": "stop",
        "usage": {"input_tokens": 21, "output_tokens": 7},
    }
    try:
        runner.invoke(
            app,
            [
                "runtime",
                "config",
                "set-http",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "http-model",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--allow-network",
            ],
        )

        result = runner.invoke(
            app,
            [
                "runtime",
                "invoke",
                "--text",
                "Rewrite this explicitly.",
                "--operation",
                "rewrite",
                "--execute-configured-provider",
                "--record",
                "--json",
            ],
        )
    finally:
        _RuntimeHandler.response_payload = {
            "output_text": "Configured provider summary.",
            "response_id": "resp_default",
            "finish_reason": "stop",
            "usage": {"input_tokens": 12, "output_tokens": 5},
        }
        server.shutdown()
        thread.join(timeout=2)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "http"
    assert payload["operation"] == "rewrite"
    assert payload["output_text"] == "Configured provider rewrite."
    assert payload["external_call_made"] is True
    assert payload["response_metadata"]["response_id"] == "resp_rewrite"
    assert payload["response_metadata"]["finish_reason"] == "stop"
    assert payload["response_metadata"]["usage_input_tokens"] == 21
    assert "usage" in payload["response_keys"]
    assert payload["recorded"] is True
    assert re.match(r"evt_[a-f0-9]+", payload["event_id"])

    search_result = runner.invoke(app, ["search", "Runtime rewrite generated", "--json"])
    search_payload = json.loads(search_result.stdout)
    assert any(item["kind"] == "event" for item in search_payload)


def test_runtime_invoke_plan_blocks_external_context_when_contract_disallows_it(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke Plan External Context"])
    runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "http-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
        ],
    )

    result = runner.invoke(
        app,
        [
            "runtime",
            "invoke-plan",
            "--text",
            "Rewrite this explicitly.",
            "--operation",
            "rewrite",
            "--source",
            "event:evt_source",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["invocation_ready"] is False
    assert "external_context_not_allowed_by_contract" in payload["blocking_reasons"]


def test_runtime_invoke_fails_closed_when_external_context_is_disallowed(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke External Context Blocked"])
    runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "http-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
        ],
    )

    result = runner.invoke(
        app,
        [
            "runtime",
            "invoke",
            "--text",
            "Rewrite this explicitly.",
            "--operation",
            "rewrite",
            "--source",
            "event:evt_source",
            "--execute-configured-provider",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "RUNTIME_PROVIDER_EXTERNAL_CONTEXT_NOT_ALLOWED"


def test_runtime_invoke_can_pass_source_refs_and_prompt_when_contract_allows_it(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke Context Chronicle"])
    server, thread = _start_runtime_server()
    os.environ["OPENAI_API_KEY"] = "test-key"
    _RuntimeHandler.expected_source_count = 2
    _RuntimeHandler.expected_prompt = "Rewrite with linked context."
    _RuntimeHandler.response_payload = {
        "output_text": "Configured provider contextual rewrite.",
        "response_id": "resp_context",
        "finish_reason": "stop",
        "usage": {"input_tokens": 30, "output_tokens": 8},
    }
    try:
        runner.invoke(
            app,
            [
                "runtime",
                "config",
                "set-http",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "http-model",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--allow-network",
                "--allow-external-context",
            ],
        )

        result = runner.invoke(
            app,
            [
                "runtime",
                "invoke",
                "--text",
                "Rewrite this with context.",
                "--operation",
                "rewrite",
                "--source",
                "event:evt_one",
                "--source",
                "ctx_ctx_two",
                "--prompt",
                "Rewrite with linked context.",
                "--execute-configured-provider",
                "--json",
            ],
        )
    finally:
        _RuntimeHandler.expected_source_count = 0
        _RuntimeHandler.expected_prompt = ""
        _RuntimeHandler.response_payload = {
            "output_text": "Configured provider summary.",
            "response_id": "resp_default",
            "finish_reason": "stop",
            "usage": {"input_tokens": 12, "output_tokens": 5},
        }
        server.shutdown()
        thread.join(timeout=2)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert len(payload["source_refs"]) == 2
    assert payload["source_refs"][0]["record_type"] == "event"
    assert payload["source_refs"][0]["record_id"] == "evt_one"
    assert payload["source_refs"][1]["record_id"] == "ctx_ctx_two"
    assert payload["prompt"] == "Rewrite with linked context."
    assert payload["response_metadata"]["response_id"] == "resp_context"


def test_runtime_invoke_plan_carries_param_preview(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke Param Plan"])
    runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "http-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
        ],
    )

    result = runner.invoke(
        app,
        [
            "runtime",
            "invoke-plan",
            "--text",
            "Rewrite this explicitly.",
            "--operation",
            "rewrite",
            "--param",
            "tone=concise",
            "--param",
            "audience=operator",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["request_preview"]["param_count"] == "2"
    assert payload["request_preview"]["param_keys"] == "audience,tone"
    assert payload["execution_request"]["params"] == {"tone": "concise", "audience": "operator"}


def test_runtime_execute_plan_runs_recorded_http_invocation(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Execute Plan Chronicle"])
    server, thread = _start_runtime_server()
    os.environ["OPENAI_API_KEY"] = "test-key"
    _RuntimeHandler.expected_params = {"tone": "concise"}
    try:
        runner.invoke(
            app,
            [
                "runtime",
                "config",
                "set-http",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "http-model",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--allow-network",
                "--allow-external-context",
            ],
        )

        plan_result = runner.invoke(
            app,
            [
                "runtime",
                "invoke-plan",
                "--text",
                "Rewrite this explicitly.",
                "--operation",
                "rewrite",
                "--source",
                "event:evt_runtime_source",
                "--prompt",
                "Rewrite for operator handoff.",
                "--param",
                "tone=concise",
                "--record",
                "--json",
            ],
        )
        assert plan_result.exit_code == 0, plan_result.stderr
        plan_payload = json.loads(plan_result.stdout)

        result = runner.invoke(
            app,
            [
                "runtime",
                "execute-plan",
                "--event",
                plan_payload["event_id"],
                "--record",
                "--artifact-title",
                "Recorded Plan Rewrite",
                "--execute-configured-provider",
                "--json",
            ],
        )
    finally:
        _RuntimeHandler.expected_params = {}
        server.shutdown()
        thread.join(timeout=2)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["operation"] == "rewrite"
    assert payload["recorded"] is True
    assert payload["artifact_id"].startswith("art_")
    assert payload["params"] == {"tone": "concise"}
    assert payload["source_refs"][0]["record_id"] == "evt_runtime_source"
    assert payload["prompt"] == "Rewrite for operator handoff."


def test_runtime_invoke_can_pass_operation_params(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke Param Chronicle"])
    server, thread = _start_runtime_server()
    os.environ["OPENAI_API_KEY"] = "test-key"
    _RuntimeHandler.expected_params = {"tone": "concise", "audience": "operator"}
    try:
        runner.invoke(
            app,
            [
                "runtime",
                "config",
                "set-http",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "http-model",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--allow-network",
            ],
        )

        result = runner.invoke(
            app,
            [
                "runtime",
                "invoke",
                "--text",
                "Rewrite this explicitly.",
                "--operation",
                "rewrite",
                "--param",
                "tone=concise",
                "--param",
                "audience=operator",
                "--execute-configured-provider",
                "--json",
            ],
        )
    finally:
        _RuntimeHandler.expected_params = {}
        server.shutdown()
        thread.join(timeout=2)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["params"] == {"tone": "concise", "audience": "operator"}


def test_runtime_invoke_can_persist_output_as_draft_artifact(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke Artifact Chronicle"])
    server, thread = _start_runtime_server()
    os.environ["OPENAI_API_KEY"] = "test-key"
    _RuntimeHandler.response_payload = {
        "output_text": "Configured provider note output.",
        "response_id": "resp_note",
        "finish_reason": "stop",
        "usage": {"input_tokens": 18, "output_tokens": 6},
    }
    try:
        runner.invoke(
            app,
            [
                "runtime",
                "config",
                "set-http",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "http-model",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--allow-network",
            ],
        )

        result = runner.invoke(
            app,
            [
                "runtime",
                "invoke",
                "--text",
                "Turn this into a reviewable note.",
                "--operation",
                "rewrite",
                "--execute-configured-provider",
                "--artifact-title",
                "Runtime Rewrite Note",
                "--artifact-type",
                "report",
                "--json",
            ],
        )
    finally:
        _RuntimeHandler.response_payload = {
            "output_text": "Configured provider summary.",
            "response_id": "resp_default",
            "finish_reason": "stop",
            "usage": {"input_tokens": 12, "output_tokens": 5},
        }
        server.shutdown()
        thread.join(timeout=2)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["artifact_id"].startswith("art_")
    assert payload["version_id"].startswith("ver_")
    assert payload["response_metadata"]["response_id"] == "resp_note"

    artifact_service = ArtifactService(tmp_path)
    artifact = artifact_service.get(payload["artifact_id"])
    assert artifact.title == "Runtime Rewrite Note"
    current = artifact_service.chronicle.artifact_store.read_current(payload["artifact_id"])
    assert current == "Configured provider note output."


def test_runtime_invoke_can_persist_output_as_summary_job(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Invoke Summary Chronicle"])
    server, thread = _start_runtime_server()
    os.environ["OPENAI_API_KEY"] = "test-key"
    _RuntimeHandler.response_payload = {
        "output_text": "Configured provider summary draft output.",
        "response_id": "resp_summary_job",
        "finish_reason": "stop",
        "usage": {"input_tokens": 24, "output_tokens": 9},
    }
    try:
        runner.invoke(
            app,
            [
                "runtime",
                "config",
                "set-http",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--model",
                "http-model",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--allow-network",
                "--allow-external-context",
            ],
        )

        result = runner.invoke(
            app,
            [
                "runtime",
                "invoke",
                "--text",
                "Summarize this for review.",
                "--operation",
                "summarize",
                "--source",
                "event:evt_runtime_source",
                "--prompt",
                "Summarize for operator review.",
                "--draft-summary-title",
                "Runtime Invoke Summary Draft",
                "--execute-configured-provider",
                "--json",
            ],
        )
    finally:
        _RuntimeHandler.response_payload = {
            "output_text": "Configured provider summary.",
            "response_id": "resp_default",
            "finish_reason": "stop",
            "usage": {"input_tokens": 12, "output_tokens": 5},
        }
        server.shutdown()
        thread.join(timeout=2)
        os.environ.pop("OPENAI_API_KEY", None)

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["draft_summary_job_id"].startswith("sum_")
    show_result = runner.invoke(app, ["summary", "show", "--id", payload["draft_summary_job_id"], "--json"])
    assert show_result.exit_code == 0
    job = json.loads(show_result.stdout)
    assert job["title"] == "Runtime Invoke Summary Draft"
    assert job["summary_text"] == "Configured provider summary draft output."
    assert job["provenance"]["generated_by"] == "runtime_http_manual"
    assert job["provenance"]["external_call_made"] is True
    assert job["provenance"]["operator"] == "runtime-invoke:summarize"
    assert job["provenance"]["prompt"] == "Summarize for operator review."
    assert job["provenance"]["response_metadata"]["response_id"] == "resp_summary_job"
    assert job["provenance"]["response_metadata"]["usage_output_tokens"] == 9
    assert "usage" in job["provenance"]["response_keys"]
    assert job["source_refs"][0]["record_id"] == "evt_runtime_source"


def test_runtime_retrieve_plan_json(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Retrieve"])
    record_result = runner.invoke(
        app,
        ["record", "--type", "user_input", "--actor", "user", "--summary", "GraphRAG planning context"],
    )
    event_id_match = re.search(r"evt_[a-f0-9]+", record_result.stdout)
    assert event_id_match is not None
    event_id = event_id_match.group(0)
    runner.invoke(
        app,
        [
            "ai-index",
            "vector",
            "add",
            "--record",
            event_id,
            "--text",
            "GraphRAG planning context for local retrieval plan",
        ],
    )

    result = runner.invoke(
        app,
        ["runtime", "retrieve-plan", "--query", "GraphRAG planning", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["external_call_made"] is False
    assert payload["query"] == "GraphRAG planning"
    assert payload["graph_adapter"]["contract_version"] == "1.0"
    assert payload["graph_adapter"]["incremental_mode"] == "event-driven_rebuildable"
    assert payload["composition"]["total_hit_count"] >= 2
    assert payload["composition"]["unique_identifier_count"] >= 1
    assert payload["composition"]["source_summaries"][0]["source"] == "vector_index"
    assert payload["vector_hits"]
    assert payload["chronicle_hits"]


def test_runtime_retrieve_plan_record_persists_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Runtime Retrieve Record"])
    runner.invoke(
        app,
        ["record", "--type", "user_input", "--actor", "user", "--summary", "Retrieval context event"],
    )

    result = runner.invoke(
        app,
        ["runtime", "retrieve-plan", "--query", "Retrieval context", "--record", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["recorded"] is True
    assert re.match(r"evt_[a-f0-9]+", payload["event_id"])

    show_result = runner.invoke(app, ["show", "--json"])
    show_payload = json.loads(show_result.stdout)
    assert show_payload["event_count"] == 3

    search_result = runner.invoke(app, ["search", "Runtime retrieval plan generated", "--json"])
    search_payload = json.loads(search_result.stdout)
    assert any(item["kind"] == "event" for item in search_payload)
