"""Summary job CLI tests."""

import json
import os
import re
from pathlib import Path

from typer.testing import CliRunner

from chronicle.cli import app
from chronicle.services.artifact_service import ArtifactService

runner = CliRunner()


def _extract_summary_job_id(text: str) -> str:
    match = re.search(r"\b(sum_[a-f0-9]+)\b", text)
    assert match is not None, text
    return match.group(1)


def test_summary_create_records_pending_review_job_without_runtime(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Test"])

    result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Draft summary",
            "--text", "This is a manually supplied draft summary.",
            "--source", "event:evt_source",
            "--prompt", "Summarize the source event.",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    data = json.loads(result.stdout)

    assert data["summary_job_id"].startswith("sum_")
    assert data["status"] == "pending_review"
    assert data["artifact_id"].startswith("art_")
    assert data["version_id"].startswith("ver_")
    assert data["event_id"].startswith("evt_")
    assert data["provenance"]["generated_by"] == "manual"
    assert data["provenance"]["invocation_mode"] == "explicit-manual"
    assert data["provenance"]["external_call_made"] is False
    assert data["provenance"]["runtime"]["provider_kind"] == "disabled"
    assert data["source_refs"][0]["record_type"] == "event"
    assert data["source_refs"][0]["record_id"] == "evt_source"

    job_path = tmp_path / ".chronicle" / "summary_jobs" / f"{data['summary_job_id']}.json"
    assert job_path.exists()


def test_summary_list_and_show(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Test"])

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Draft summary",
            "--text", "Draft body.",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    summary_job_id = _extract_summary_job_id(create_result.stdout)

    list_result = runner.invoke(app, ["summary", "list"])
    assert list_result.exit_code == 0
    assert summary_job_id in list_result.stdout
    assert "pending_review" in list_result.stdout

    show_result = runner.invoke(app, ["summary", "show", "--id", summary_job_id, "--json"])
    assert show_result.exit_code == 0
    data = json.loads(show_result.stdout)
    assert data["summary_job_id"] == summary_job_id
    assert data["status"] == "pending_review"
    assert data["provenance"]["external_call_made"] is False


def test_summary_run_creates_runtime_backed_draft(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Run Test"])

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Source Draft",
            "--text", "First sentence. Second sentence. Third sentence.",
            "--source", "event:evt_source",
            "--prompt", "Condense the source draft.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    source_job = json.loads(create_result.stdout)

    run_result = runner.invoke(
        app,
        [
            "summary", "run",
            "--id", source_job["summary_job_id"],
            "--max-sentences", "2",
            "--json",
        ],
    )
    assert run_result.exit_code == 0, run_result.stderr
    result = json.loads(run_result.stdout)
    assert result["draft_summary_job_id"].startswith("sum_")
    assert result["generated_text"] == "First sentence. Second sentence."

    show_result = runner.invoke(app, ["summary", "show", "--id", result["draft_summary_job_id"], "--json"])
    assert show_result.exit_code == 0
    draft_job = json.loads(show_result.stdout)
    assert draft_job["provenance"]["generated_by"] == "runtime_manual"
    assert draft_job["provenance"]["operator"] == "summary-run"
    assert draft_job["provenance"]["prompt"] == "Condense the source draft."
    assert draft_job["source_refs"][0]["record_id"] == "evt_source"


def test_summary_run_can_record_runtime_summary_event(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Run Record Test"])

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Source Draft",
            "--text", "First sentence. Second sentence. Third sentence.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    source_job = json.loads(create_result.stdout)

    run_result = runner.invoke(
        app,
        [
            "summary", "run",
            "--id", source_job["summary_job_id"],
            "--record",
            "--json",
        ],
    )
    assert run_result.exit_code == 0, run_result.stderr
    result = json.loads(run_result.stdout)
    assert result["recorded"] is True
    assert re.match(r"evt_[a-f0-9]+", result["event_id"])


def test_summary_run_can_use_configured_provider_explicitly(
    tmp_path: Path,
    monkeypatch,
) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Run HTTP Test"])
    runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "http-summary-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
        ],
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Source Draft",
            "--text", "First sentence. Second sentence. Third sentence.",
            "--source", "event:evt_source",
            "--prompt", "Condense the source draft.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    source_job = json.loads(create_result.stdout)

    from chronicle.services.runtime_service import RuntimeService

    def _stub_http_summary(*, config, text, operation, max_sentences):  # type: ignore[no-untyped-def]
        assert config.provider_kind.value == "http"
        assert text == "First sentence. Second sentence. Third sentence."
        assert operation == "summarize"
        assert max_sentences == 2
        return {
            "output_text": "HTTP provider condensed summary.",
            "response_id": "resp_summary_run",
            "finish_reason": "stop",
            "usage": {"input_tokens": 16, "output_tokens": 6},
        }

    monkeypatch.setattr(RuntimeService, "_invoke_http_operation", staticmethod(_stub_http_summary))

    run_result = runner.invoke(
        app,
        [
            "summary", "run",
            "--id", source_job["summary_job_id"],
            "--max-sentences", "2",
            "--execute-configured-provider",
            "--json",
        ],
    )
    assert run_result.exit_code == 0, run_result.stderr
    result = json.loads(run_result.stdout)
    assert result["provider_kind"] == "http"
    assert result["external_call_made"] is True
    assert result["generated_text"] == "HTTP provider condensed summary."

    show_result = runner.invoke(app, ["summary", "show", "--id", result["draft_summary_job_id"], "--json"])
    draft_job = json.loads(show_result.stdout)
    assert draft_job["provenance"]["generated_by"] == "runtime_http_manual"
    assert draft_job["provenance"]["external_call_made"] is True
    assert draft_job["provenance"]["runtime"]["provider_kind"] == "http"
    assert draft_job["provenance"]["response_metadata"]["response_id"] == "resp_summary_run"
    assert draft_job["provenance"]["response_metadata"]["usage_output_tokens"] == 6


def test_summary_run_can_execute_non_summarize_operation_with_persistence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Run Rewrite Test"])
    runner.invoke(
        app,
        [
            "runtime",
            "config",
            "set-http",
            "--base-url",
            "https://runtime.example.invalid/v1",
            "--model",
            "http-rewrite-model",
            "--api-key-env",
            "OPENAI_API_KEY",
            "--allow-network",
            "--allow-external-context",
        ],
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Rewrite Source Draft",
            "--text", "Rewrite this source summary explicitly.",
            "--source", "event:evt_source",
            "--prompt", "Rewrite for operator handoff.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    source_job = json.loads(create_result.stdout)

    from chronicle.services.runtime_service import RuntimeService

    def _stub_http_invoke(*, config, text, operation, max_sentences, source_refs=None, prompt="", extra_params=None):  # type: ignore[no-untyped-def]
        assert config.provider_kind.value == "http"
        assert text == "Rewrite this source summary explicitly."
        assert operation == "rewrite"
        assert len(source_refs or []) == 1
        assert prompt == "Rewrite for operator handoff."
        assert extra_params == {"tone": "concise"}
        return {
            "output_text": "HTTP provider rewrite output.",
            "response_id": "resp_summary_rewrite",
            "finish_reason": "stop",
            "usage": {"input_tokens": 14, "output_tokens": 4},
        }

    monkeypatch.setattr(RuntimeService, "_invoke_http_operation", staticmethod(_stub_http_invoke))

    run_result = runner.invoke(
        app,
        [
            "summary", "run",
            "--id", source_job["summary_job_id"],
            "--operation", "rewrite",
            "--param", "tone=concise",
            "--artifact-title", "Summary Rewrite Artifact",
            "--record",
            "--execute-configured-provider",
            "--json",
        ],
    )
    assert run_result.exit_code == 0, run_result.stderr
    result = json.loads(run_result.stdout)
    assert result["operation"] == "rewrite"
    assert result["external_call_made"] is True
    assert result["recorded"] is True
    assert result["draft_summary_job_id"].startswith("sum_")
    assert result["artifact_id"].startswith("art_")
    assert result["response_metadata"]["response_id"] == "resp_summary_rewrite"

    artifact = ArtifactService(tmp_path).get(result["artifact_id"])
    assert artifact.title == "Summary Rewrite Artifact"

    show_result = runner.invoke(app, ["summary", "show", "--id", result["draft_summary_job_id"], "--json"])
    draft_job = json.loads(show_result.stdout)
    assert draft_job["provenance"]["generated_by"] == "runtime_http_manual"
    assert draft_job["provenance"]["operator"] == "runtime-invoke:rewrite"
    assert draft_job["provenance"]["prompt"] == "Rewrite for operator handoff."


def test_summary_invoke_plan_carries_summary_context(tmp_path: Path) -> None:
    os.chdir(str(tmp_path))
    runner.invoke(app, ["init", "--title", "Summary Invoke Plan Test"])
    runner.invoke(
        app,
        [
            "runtime", "config", "set-local",
            "--model", "summary-plan-model",
            "--provider-name", "summary-plan-provider",
        ],
    )

    create_result = runner.invoke(
        app,
        [
            "summary", "create",
            "--title", "Source Draft",
            "--text", "First sentence. Second sentence. Third sentence.",
            "--source", "event:evt_source",
            "--prompt", "Condense the source draft.",
            "--json",
        ],
    )
    assert create_result.exit_code == 0, create_result.stderr
    source_job = json.loads(create_result.stdout)

    plan_result = runner.invoke(
        app,
        [
            "summary", "invoke-plan",
            "--id", source_job["summary_job_id"],
            "--record",
            "--json",
        ],
    )
    assert plan_result.exit_code == 0, plan_result.stderr
    payload = json.loads(plan_result.stdout)
    assert payload["provider_kind"] == "local"
    assert payload["invocation_ready"] is True
    assert payload["recorded"] is True
    assert payload["request_preview"]["summary_job_id"] == source_job["summary_job_id"]
    assert payload["request_preview"]["summary_title"] == "Source Draft"
    assert payload["request_preview"]["prompt"] == "Condense the source draft."
    assert payload["request_preview"]["source_ref_count"] == "1"

    search_result = runner.invoke(app, ["search", source_job["summary_job_id"], "--json"])
    assert search_result.exit_code == 0
