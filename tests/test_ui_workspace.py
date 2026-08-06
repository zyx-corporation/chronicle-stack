"""User-facing Chronicle workspace tests."""

from http import HTTPStatus

from chronicle.services.chronicle_service import ChronicleService
from chronicle.ui_server import (
    ChronicleUIDataService,
    UIAuthMode,
    UIAuthorizationMode,
)


def _workspace(tmp_path):  # noqa: ANN001, ANN202
    ChronicleService(tmp_path).init("Workspace")
    return ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
        workspace_enabled=True,
    )


def test_quick_capture_writes_note_and_artifact(tmp_path):
    service = _workspace(tmp_path)

    note_status, note = service.capture_response({"kind": "note", "content": "A useful note"})
    artifact_status, artifact = service.capture_response(
        {"kind": "artifact", "title": "Draft", "content": "# Draft\n\nBody"}
    )

    assert note_status == HTTPStatus.CREATED
    assert note["event_id"].startswith("evt_")
    assert artifact_status == HTTPStatus.CREATED
    assert artifact["artifact_id"].startswith("art_")
    assert len(service.chronicle.jsonl.read_all()) == 3


def test_workspace_shell_prioritizes_user_tasks(tmp_path):
    html = _workspace(tmp_path).html_shell()

    assert "記録する" in html
    assert "Chronicleに聞く" in html
    assert 'id="capture-form"' in html
    assert 'id="assistant-form"' in html
    assert 'data-endpoint="/api/graphrag-status"' in html


def test_review_mutation_mode_does_not_enable_workspace(tmp_path):
    ChronicleService(tmp_path).init("Review only")
    service = ChronicleUIDataService(
        tmp_path,
        mutation_capability_flag=True,
        enable_ui_mutation=True,
        auth_mode=UIAuthMode.LOOPBACK_LOCAL,
        authorization_mode=UIAuthorizationMode.REVIEWER_DECLARED,
    )

    html = service.html_shell()
    boundary = service.runtime_boundary()

    assert 'aria-label="Chronicle workspace" hidden' in html
    assert "レビュー書き込み有効" in html
    assert boundary["read_only"] is True
    assert boundary["external_model_api"] is False
    assert boundary["graphrag_runtime"] is False


def test_workspace_runtime_boundary_reports_optional_runtime(tmp_path):
    service = _workspace(tmp_path)

    boundary = service.runtime_boundary()

    assert boundary["read_only"] is False
    assert boundary["external_model_api"] is True
    assert boundary["graphrag_runtime"] is True
    assert boundary["vector_db"] is True
    assert boundary["graph_db"] is True
