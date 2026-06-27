# ADR-0078: Local Invocation, Auth, and Mutation Boolean Detail Localization

- Status: Accepted
- Date: 2026-06-27

## Context

`v1.58.0` localized response-metadata and runtime-config detail lines.
Adjacent invocation-plan, auth-boundary, UI-boundary, and mutation-readiness panels still rendered several booleans directly, which left the current local UI detail-line i18n phase only partially complete.

## Decision

- invocation-plan contracts now expose key-first boolean summaries for readiness and network intent
- auth-boundary and UI-boundary contracts now expose key-first boolean summaries for session-gating and mutation flags
- mutation-readiness contracts now expose key-first boolean summaries for enablement readiness

## Consequences

- the current boolean detail-line localization pass is complete for the adjacent invocation/auth/mutation inspection surfaces
- raw fallback values remain available if a summary key is absent
- local-first, read-only, presentation-only boundaries remain unchanged
