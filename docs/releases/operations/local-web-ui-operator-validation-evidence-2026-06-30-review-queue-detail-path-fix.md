# Local Web UI Operator Validation Evidence 2026-06-30 Review Queue Detail-Path Fix

Related: `local-web-ui-operator-validation-v1.0.md`, `local-web-ui-operator-validation-report-template.md`, `local-web-ui-operator-validation-evidence-2026-06-30-manual-walkthrough.md`, `local-web-ui-operator-validation-evidence-2026-06-30-detail-entry-followup.md`

This record captures the browser walkthrough follow-up after the review-queue detail-path resolver was repaired.
It focuses on whether the first-column `JSON` and `Open Detail` affordances are rendered and actionable again in the current read-only local UI.

## Validation Metadata

- validation date: 2026-06-30
- operator: Codex assisted local browser walkthrough
- local commit SHA: `8163d72`
- Chronicle root: `/Users/tomyuk/Projects/Chronicle/chronicle-stack`
- validation scope: localhost browser walkthrough for review-queue first-column detail affordances
- validation mode: read-only baseline
- startup command: `./.venv/bin/python -m chronicle.cli ui --host localhost --port 8765`

## Preflight

- `./.venv/bin/ruff check src tests`: passed
- `./.venv/bin/pytest -q tests/test_ui_server.py`: passed (`43 passed`)
- `./.venv/bin/python -m chronicle.cli ui-smoke --json`: passed (`"passed": true`)
- `./.venv/bin/pytest -q`: passed (`464 passed`)

## Walkthrough Summary

### Confirmed

- overview loaded at `http://localhost:8765` and the triage CTA `レビューキューを開く` reached `/api/review-queue`
- the first review row now renders both `JSON` and `詳細を開く` inside the first-column `detail-cell`
- the repaired first-row buttons have stable visible geometry in the browser walkthrough:
  - `JSON`: width `58`, height `33`
  - `詳細を開く`: width `89`, height `33`
- first-row `詳細を開く` navigation now opens `/api/review-queue/evt_e48eec568324433ba5637375d99866a3` in the detail rail

### Closed Earlier Friction

1. the earlier empty first-column affordance in review queue rows is resolved; the browser now sees populated `data-detail` and `data-detail-nav` buttons
2. the local UI no longer depends on drilldown notices alone to reach the first pending review detail

## Checklist Results

### 1. Startup / Boundary

- result: passed
- notes: localhost foreground startup still reports loopback-only, read-only operation with mutation disabled

### 2. Overview Operator Picture

- result: passed
- notes: overview loaded and `レビューキューを開く` remained actionable as the operator handoff into the workspace list

### 3. Review Queue Workspace

- result: passed
- notes: the first review row now exposes both first-column detail controls directly, and first-row detail navigation succeeds into the detail rail

### 4. Navigation / Reconstruction

- result: passed
- notes: first-column list-to-detail reconstruction is restored for review queue without relying on secondary drilldown buttons

## Gaps / Friction

- broken navigation paths: none observed in this follow-up walkthrough
- misleading boundary copy: none observed in this follow-up walkthrough
- overview/list/detail mismatches: none observed for the repaired review-queue first-column detail path
- missing CLI fallback guidance: none observed in this follow-up walkthrough
- other operator friction: full-page screenshot evidence was not revisited in this pass

## Follow-on Recommendation

- no follow-on needed for the repaired review-queue detail path
- next recommended slice: continue feature-facing UI work until a fresh manual walkthrough finds new operator friction

## Evidence Links

- local browser walkthrough: `http://localhost:8765` -> `レビューキューを開く` -> first-row `JSON` / `詳細を開く`
- related PR / issue: `#337`
