# Chronicle Stack v1.7.0 Local Observability Smoke Profile

Related: `smoke-test-v1.7-phase-d-e.md`, `smoke-test-v1.7-phase-h.md`, `../../v1.7-phase-f-g-h-closeout-summary.md`

## Purpose

This smoke profile validates v1.7.0 as a local AI/runtime/review/package observability release.

It checks that:

- placeholder AI index surfaces remain locally inspectable
- runtime and retrieval-plan surfaces remain explicit and reviewable
- Phase H auth-readiness / mutation-readiness surfaces remain read-only by default
- `chronicle ui-smoke` continues to cover the local UI data plane without starting a server

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

## Coverage references

Also confirm these release-track documents remain aligned:

```text
../../v1.7-phase-d-e-progress.md
smoke-test-v1.7-phase-d-e.md
../../v1.7-phase-f-g-h-closeout-summary.md
../../v1.7-phase-h-readiness-status.md
smoke-test-v1.7-phase-h.md
../notes/release-notes-v1.7.0.md
../readiness/release-readiness-v1.7.md
../status/release-status-v1.7.0.md
```

## Manual spot checks

When opening `chronicle ui` manually for local inspection, confirm:

- AI index overview/vector/graph surfaces remain read-only
- runtime records / review queue / summary jobs expose shared triage vocabulary
- overview auth / identity / mutation panels stay descriptive only
- blocked-route preview responses and CLI fallback copy remain aligned across list/detail surfaces
- no hidden runtime or background service behavior is implied

## Boundary

v1.7.0 is a local observability and gated-local-write preparation release.

It does not add hosted runtime, daemon/service installation, default-on GUI mutation, authenticated GUI mutation, GraphRAG runtime, vector DB, graph DB, correctness proof, or security certification.

## Warning classification

- Release warning: smoke completion is not tag/release publication.
- Mutation warning: read-only visibility and gated preview do not grant approval authority.
- Auth warning: placeholder auth/authz metadata remains descriptive.
- Runtime warning: explicit provider/runtime contracts do not imply hidden execution.
- Semantics warning: smoke remains diagnostic, not certification or proof.

## RDE review

Preserved: local-first smoke discipline, read-only UI boundary, explicit runtime execution boundary.

Transformed: separate phase smoke notes become one release smoke entry point.

Supplemented: release-specific doc alignment checks for v1.7.0.

Unresolved: external `v1.7.0` tag publication and release evidence capture.
