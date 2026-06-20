# Chronicle Stack v1.7 Phase H Auth Readiness Smoke Profile

Related: `docs/adr/0019-local-ui-review-semantics-parity-boundary.md`, `docs/v1.7-phase-h-auth-ui-design.md`

## Purpose

This smoke profile validates the read-only Phase H auth-readiness surfaces that
prepare GUI-mutation design work without enabling GUI mutation.

It focuses on:

- overview auth / identity / mutation-readiness aggregates
- runtime record auth-readiness visibility
- review queue auth-readiness visibility
- summary job auth-readiness visibility
- detail-level auth-readiness notices
- `chronicle ui-smoke` continuity for those derived surfaces

## Boundary

The Phase H auth-readiness surface:

- does not enable GUI mutation
- does not add authenticated write routes
- does not add authorization enforcement
- does not create approval authority from UI wording
- does not add hosted auth providers
- does not add background approval automation
- keeps Chronicle JSONL as the authoritative record
- keeps CLI review as the primary mutation contract

## Pre-verification

Run:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

## Local fixture setup

```bash
rm -rf /tmp/chronicle-v17-phase-h-smoke
mkdir -p /tmp/chronicle-v17-phase-h-smoke
cd /tmp/chronicle-v17-phase-h-smoke

chronicle init --title "v1.7 Phase H Smoke"
chronicle record --type user_input --actor user --summary "phase h smoke event"
chronicle add-context --title "Phase H Context" --summary "phase h smoke context" --scope task
chronicle runtime summarize --text "Phase H runtime summary stays local." --record
chronicle runtime retrieve-plan --query "Phase H Context" --record
chronicle summary create --title "Phase H Summary Draft" --text "Phase H draft body." --prompt "Phase H prompt"
chronicle review request-changes --event <RUNTIME_SUMMARY_EVENT_ID> --reviewer alice --kind local_operator --session ui-smoke --note "phase h smoke review"
```

## Read-only UI smoke

```bash
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected JSON smoke fields remain:

```json
{
  "passed": true,
  "read_only": true,
  "server_started": false,
  "browser_required": false,
  "external_runtime": false
}
```

Expected auth-readiness smoke checks include:

- `/api/overview#runtime-auth-readiness`
- `/api/overview#summary-auth-readiness`
- `/api/review-queue/<id>#auth-readiness`
- `/api/runtime-records/<id>#auth-readiness`
- `/api/summary-jobs/<id>#auth-readiness`
- `html-shell`

## Manual spot checks

If opening `chronicle ui` manually for local inspection, confirm these read-only
surfaces remain descriptive only:

- overview `Auth Boundary`, `Identity Boundary`, `Runtime Records`, `Summary Jobs`
- runtime records list `auth` badges
- review queue list `auth` badges
- summary jobs list `auth` badges
- runtime / review / summary detail `Auth Readiness` notices

## Warning classification

- Mutation warning: auth-readiness visibility does not enable GUI writes.
- Auth warning: placeholder auth/authz metadata is not enforcement.
- Semantics warning: advisory/aligned badges are derived interpretation, not approval state.
- Runtime warning: local runtime/read-model visibility does not imply provider execution.

## RDE review

Preserved: primary-record authority, read-only UI boundary, CLI-first mutation semantics.

Transformed: scattered Phase H readiness signals become one smoke-verifiable read-only surface set.

Supplemented: auth-readiness smoke expectations across overview/list/detail surfaces.

Unresolved: authenticated GUI write routes, authorization enforcement, and mutation-path audit insertion.
