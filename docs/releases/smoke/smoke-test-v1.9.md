# Chronicle Stack v1.9.0 Reviewer Boundary Smoke Profile

Related: `../readiness/release-readiness-v1.9.md`, `../status/release-status-v1.9.0.md`, `../notes/release-notes-v1.9.0.md`, `../remaining/v1.9-release-remaining-issues.md`, `../../adr/0028-local-reviewer-session-enforcement-boundary.md`

## Purpose

This smoke profile validates the current `v1.9.0` release track as a local reviewer/session enforcement-boundary slice.

It checks that:

- `chronicle ui-smoke` remains read-only and serverless
- `reviewer_enforcement_summary` remains exposed on UI boundary, readiness, detail, and action surfaces
- `reviewer_validation_gate_summary` remains exposed for validation, authorization, target-state, and durable-write failure families
- reviewer/session wording remains aligned across preview, apply, readiness, and recovery-facing surfaces
- fail-closed route semantics remain aligned with the current local single-operator boundary

## Verification

Run:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected version:

```text
chronicle 1.9.0
```

Expected JSON smoke fields:

```json
{
  "passed": true,
  "read_only": true,
  "server_started": false,
  "browser_required": false,
  "external_runtime": false
}
```

## Contract spot checks

Confirm that the current `ui-smoke` and UI contract surfaces still expose:

- `reviewer_enforcement_summary.status`
- `reviewer_enforcement_summary.enforced_request_fields`
- `reviewer_validation_gate_summary.validation_error_codes`
- `reviewer_validation_gate_summary.authorization_error_codes`
- `reviewer_validation_gate_summary.target_state_error_codes`
- `reviewer_validation_gate_summary.durable_write_error_codes`

## Manual spot checks

When opening `chronicle ui` manually for local inspection, confirm:

- review detail still distinguishes route-enforced reviewer/session conditions from descriptive metadata
- validation/gate families remain readable in detail drilldown
- blocked/apply/result surfaces remain fail-closed and locally scoped
- no hosted or default-on mutation behavior is implied

## Boundary

`v1.9.0` smoke for this slice does not certify hosted auth, multi-user safety, default-on mutation, background runtime execution, GraphRAG runtime, correctness proof, or security certification.

## Warning classification

- Release warning: smoke completion is not tag/release publication.
- Auth warning: enforcement-boundary visibility is not hosted identity proof.
- Mutation warning: gate visibility is not write authority.
- Semantics warning: smoke remains diagnostic, not certification or proof.

## RDE review

Preserved: read-only smoke discipline, fail-closed route-contract visibility, CLI-compatible local recovery framing.

Transformed: reviewer/session boundary hardening is now represented through a dedicated `v1.9.0` release-track smoke entry point.

Supplemented: explicit smoke emphasis on enforcement scope and shared validation/gate-family exposure.

Unresolved: any follow-on release workflow after repository-side `v1.9.0` preparation.
