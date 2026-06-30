# Chronicle Stack Local Web UI Operator Validation v1.0

Related: `release-operator-guide.md`, `../../cli-reference.md`

Status: draft operator validation guide  
Scope: manual validation checklist for the current local web UI

## Purpose

This guide captures how to validate the current Chronicle Stack local web UI as an operator-facing surface.

It is intended for the current product boundary:

- foreground local web UI
- local-first
- read-only by default
- mutation preview always available only as inspection/contract evidence
- browser-triggered write path available only under explicit gated local conditions

The goal is not visual polish review. The goal is to confirm that the UI still supports:

- trustworthy read-only inspection
- fast reconstruction of state
- operator triage across runtime records, review queue, and summary jobs
- explicit mutation boundary understanding
- predictable fallback to CLI when write routes are blocked

## Boundary

This guide does not certify:

- product completeness
- multi-user behavior
- hosted deployment
- browser automation
- security audit completeness
- legal/governance sign-off
- external runtime correctness

This guide assumes local operator use against a local Chronicle root.

## Preconditions

Run from a working local checkout:

```bash
python -m pip install -e ".[dev]"
ruff check src/ tests/
pytest -q
chronicle ui-smoke --json
chronicle ui --json
```

Expected:

- `pytest -q` passes
- `chronicle ui-smoke --json` reports `passed: true`
- `chronicle ui --json` returns loopback-local startup metadata without starting a long-lived server

## Recommended Start Modes

Read-only baseline:

```bash
chronicle ui --host 127.0.0.1 --port 8765
```

Preview-capability boundary visibility:

```bash
chronicle ui --host 127.0.0.1 --port 8765 --mutation-capability-flag
```

Explicit gated local write-path validation:

```bash
chronicle ui \
  --host 127.0.0.1 \
  --port 8765 \
  --mutation-capability-flag \
  --enable-ui-mutation \
  --auth-mode loopback_local \
  --authorization-mode reviewer_declared
```

## Validation Checklist

### 1. Startup / Boundary

- confirm the UI binds only to loopback-local host values
- confirm overview loads without requiring any external runtime or browser extension
- confirm the UI clearly remains read-only unless explicit gated mutation flags are enabled
- confirm `UI Boundary`, `Auth Boundary`, and `Mutation Readiness` panels expose current boundary state without implying hidden background execution

### 2. Overview Operator Picture

- confirm overview shows current operating picture before raw artifact chronology
- confirm `Runtime Records`, `Summary Jobs`, and `Review Queue` panels expose meaningful aggregate counts
- confirm latest-response navigation links open the corresponding detail/read model target
- confirm warning/attention slices jump to matching filtered list views rather than mutating state

### 3. Runtime Records Workspace

- confirm list filters, sort changes, and reset behavior work without page confusion
- confirm `mutation`, `auth`, and `kind` sorting still change row ordering predictably
- confirm row preview summaries, auth badges, and related buttons provide enough context before opening detail
- confirm detail view exposes runtime preview, runtime workspace, response metadata, and related-link navigation

### 4. Review Queue Workspace

- confirm `Needs attention`, `CLI drift first`, reviewer sort, and warning-priority behavior remain understandable
- confirm warning badges and auth/identity slices are clickable and stay read-only
- confirm detail view exposes review capability, auth readiness, identity assurance, CLI parity, mutation enablement, action preview, and review timeline
- confirm blocked review routes still return explicit preview/fallback semantics rather than silent failure

### 5. Summary Jobs Workspace

- confirm summary-job list supports title/review/mutation sorting with no broken state carry-over
- confirm summary job rows still expose runtime/source/reviewer context without opening detail
- confirm detail view connects summary job state back to review capability, package readiness, and mutation preview contracts

### 6. Mutation Boundary Understanding

- in read-only mode, confirm action previews explain why routes are blocked and what CLI fallback/recovery path applies
- in explicit gated mode, confirm reviewer/session fields appear only when expected
- confirm mutation enablement detail sections explain:
  - readiness status
  - operational readiness
  - reviewer context
  - write route contract
  - next steps
- confirm failed action responses preserve recovery path, rollback status, and follow-up guidance

### 7. Navigation / Reconstruction

- confirm back-to-list, previous-detail, trail, and related-link navigation remain consistent
- confirm filtered list -> detail -> related list traversal does not lose operator context unexpectedly
- confirm record JSON / response JSON visibility still matches the surrounding read model

## Evidence to Record

For a validation pass, record:

- startup command used
- whether validation was read-only baseline or explicit gated local mutation mode
- any broken navigation path
- any misleading boundary copy
- any mismatch between overview/list/detail state
- any case where CLI fallback guidance is missing or unclear

Recommended evidence format:

- validation date
- local commit SHA
- validation mode
- passed checks
- open gaps
- follow-on recommendation

## Exit Guidance

If this guide passes cleanly:

- prefer shifting the next slice toward feature-facing UI work
- avoid adding new UI helpers unless a fresh repeated pattern appears in multiple concrete consumers

If this guide finds operator friction:

- convert the observed friction into a feature-facing UI issue or release follow-on
- avoid abstract refactors that do not directly resolve the observed operator problem
