# Local Web UI Operator Validation Report Template

Related: `local-web-ui-operator-validation-v1.0.md`, `release-operator-guide.md`

Use this template when recording one manual validation pass of the current local web UI.

## Quick Start

1. `local-web-ui-operator-validation-v1.0.md` の checklist を走らせる
2. この template に結果を転記する
3. follow-on recommendation を 1 つ選んで次の action へつなぐ

## Validation Metadata

- validation date:
- operator:
- local commit SHA:
- Chronicle root:
- validation scope:
  - preflight and startup evidence only
  - manual browser walkthrough
  - manual browser walkthrough with explicit gated local mutation
- validation mode:
  - read-only baseline
  - preview-capability boundary visibility
  - explicit gated local mutation
- startup command:

## Preflight

- `ruff check src/ tests/`:
- `pytest -q`:
- `chronicle ui-smoke --json`:
- `chronicle ui --json`:

## Checklist Results

### 1. Startup / Boundary

- result:
- notes:

### 2. Overview Operator Picture

- result:
- notes:

### 3. Runtime Records Workspace

- result:
- notes:

### 4. Review Queue Workspace

- result:
- notes:

### 5. Summary Jobs Workspace

- result:
- notes:

### 6. Mutation Boundary Understanding

- result:
- notes:

### 7. Navigation / Reconstruction

- result:
- notes:

## Gaps / Friction

- broken navigation paths:
- misleading boundary copy:
- overview/list/detail mismatches:
- missing CLI fallback guidance:
- other operator friction:

## Follow-on Recommendation

- no follow-on needed
- docs clarification
- feature-facing UI issue
- validation rerun needed

## Evidence Links

- screenshots:
- terminal captures:
- related PR / issue:
