# Chronicle Stack v1.8.0 Local GUI Review Route Contract Smoke Profile

Related: `docs/release-readiness-v1.8.md`, `docs/release-status-v1.8.0.md`, `docs/adr/0027-local-gui-review-route-contract.md`, `docs/v1.7-phase-h-gated-gui-mutation-preview.md`

## Purpose

This smoke profile validates the current `v1.8.0` release track as a local GUI review-route contract-hardening slice.

It checks that:

- `chronicle ui-smoke` remains read-only and serverless
- write-route contract metadata remains exposed on UI boundary and mutation-readiness surfaces
- action-route family and CLI-equivalent route semantics remain visible
- status-code contract semantics remain visible
- fail-closed route semantics remain aligned with the current local boundary

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

Expected current version before release cut:

```text
chronicle 1.7.0
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

- `write_route_contract.route_template`
- `write_route_contract.action_routes`
- `write_route_contract.status_code_contract`
- `write_route_contract.failure_families`
- `write_route_contract.authorization_contract`
- `write_route_contract.target_state_contract`

## Manual spot checks

When opening `chronicle ui` manually for local inspection, confirm:

- review detail still shows the explicit local review route family
- action-route and CLI-equivalent route semantics remain aligned
- status-code semantics remain readable in detail drilldown
- blocked/apply/result surfaces remain fail-closed and locally scoped
- no hosted or default-on mutation behavior is implied

## Boundary

`v1.8.0` smoke for this slice does not certify hosted auth, multi-user safety, default-on mutation, background runtime execution, GraphRAG runtime, correctness proof, or security certification.

## Warning classification

- Release warning: smoke completion is not tag/release publication.
- Mutation warning: contract visibility is not write authority.
- Auth warning: local reviewer/session metadata remains boundary-scoped.
- Semantics warning: smoke remains diagnostic, not certification or proof.

## RDE review

Preserved: read-only smoke discipline, fail-closed route contract visibility, CLI-compatible local recovery framing.

Transformed: prior Phase H contract checks become a `v1.8.0` release-track smoke entry point.

Supplemented: explicit smoke emphasis on action-route and status-code contract exposure.

Unresolved: final `v1.8.0` release evidence, release notes, version bump, and publication workflow.
