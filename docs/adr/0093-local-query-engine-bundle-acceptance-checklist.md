# ADR 0093: Local Query-Engine Bundle Includes Acceptance Checklist

- Status: Accepted
- Date: 2026-06-27

## Context

After `v1.73.0`, Chronicle Stack could emit a local downstream handoff bundle, but the release still lacked an explicit repository-side acceptance checklist for deciding whether that bundle was sufficient before opening a separate downstream implementation repo.

## Decision

Chronicle Stack will include a local acceptance checklist alongside the handoff bundle and document the acceptance boundary in-repo. The checklist is descriptive guidance only and does not certify semantic correctness or runtime readiness.

## Consequences

- bundle consumers get a consistent sufficiency rubric
- implementation-repo escalation stays explicit rather than automatic
- Chronicle Stack still avoids embedding downstream execution logic
