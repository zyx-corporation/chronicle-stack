"""Read-only smoke checks for the Chronicle local UI data surface.

This module does not start a web server, open a browser, bind sockets, call
external model APIs, or certify correctness. It only checks that the local UI
read models can be derived from an initialized Chronicle root.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from chronicle.ui_server import ChronicleUIDataService


@dataclass(frozen=True)
class UISmokeCheck:
    """One smoke check result."""

    name: str
    passed: bool
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "message": self.message}


@dataclass(frozen=True)
class UISmokeReport:
    """Summary of read-only UI smoke checks."""

    root: str
    passed: bool
    checks: list[UISmokeCheck] = field(default_factory=list)
    read_only: bool = True
    server_started: bool = False
    browser_required: bool = False
    external_runtime: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "passed": self.passed,
            "read_only": self.read_only,
            "server_started": self.server_started,
            "browser_required": self.browser_required,
            "external_runtime": self.external_runtime,
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


_COLLECTION_CHECKS: tuple[tuple[str, str], ...] = (
    ("/api/overview", "counts"),
    ("/api/events", "events"),
    ("/api/contexts", "contexts"),
    ("/api/artifacts", "artifacts"),
    ("/api/decisions", "decisions"),
    ("/api/rde", "rde_records"),
    ("/api/boundary", "boundary_rules"),
    ("/api/audit", "audit_events"),
    ("/api/lifecycle", "lifecycle_markers"),
    ("/api/package-review", "package_review"),
    ("/api/graph-summary", "graph_summary"),
)

_DETAIL_ID_FIELDS: dict[str, str] = {
    "/api/events": "event_id",
    "/api/contexts": "context_id",
    "/api/artifacts": "artifact_id",
    "/api/decisions": "decision_id",
    "/api/rde": "rde_record_id",
    "/api/boundary": "rule_id",
    "/api/audit": "audit_id",
    "/api/lifecycle": "lifecycle_id",
}


def _first_array(payload: dict[str, Any]) -> list[dict[str, Any]] | None:
    for value in payload.values():
        if isinstance(value, list):
            return value
    return None


def run_ui_smoke(root: Path | None = None) -> UISmokeReport:
    """Run read-only UI smoke checks against a Chronicle root."""
    root_path = root or Path.cwd()
    service = ChronicleUIDataService(root_path)
    checks: list[UISmokeCheck] = []
    collection_payloads: dict[str, dict[str, Any]] = {}

    try:
        for endpoint, expected_key in _COLLECTION_CHECKS:
            payload = service.api_payload(endpoint)
            if payload is None:
                checks.append(UISmokeCheck(endpoint, False, "missing payload"))
                continue
            collection_payloads[endpoint] = payload
            checks.append(
                UISmokeCheck(
                    endpoint,
                    expected_key in payload,
                    "ok" if expected_key in payload else f"missing key: {expected_key}",
                )
            )

        for endpoint, id_field in _DETAIL_ID_FIELDS.items():
            payload = collection_payloads.get(endpoint)
            if payload is None:
                continue
            rows = _first_array(payload)
            if not rows:
                checks.append(UISmokeCheck(f"{endpoint}/<id>", True, "skipped: no records"))
                continue
            record_id = rows[0].get(id_field)
            if not isinstance(record_id, str) or not record_id:
                checks.append(UISmokeCheck(f"{endpoint}/<id>", False, f"missing id field: {id_field}"))
                continue
            detail = service.detail_payload(f"{endpoint}/{record_id}")
            checks.append(
                UISmokeCheck(
                    f"{endpoint}/{record_id}",
                    detail is not None and "record" in detail,
                    "ok" if detail is not None and "record" in detail else "missing detail record",
                )
            )

        missing = service.detail_payload("/api/contexts/__chronicle_missing_context__")
        checks.append(
            UISmokeCheck(
                "/api/contexts/__chronicle_missing_context__",
                missing is None,
                "ok" if missing is None else "missing detail unexpectedly returned payload",
            )
        )
    except Exception as exc:  # pragma: no cover - converted to visible smoke failure
        checks.append(UISmokeCheck("ui-smoke", False, str(exc)))

    return UISmokeReport(
        root=str(root_path.resolve()),
        passed=all(check.passed for check in checks),
        checks=checks,
    )
