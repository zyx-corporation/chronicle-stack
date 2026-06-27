# ADR-0079: Local Target-State Recovery and Review-Capability Status Localization

- Status: Accepted
- Date: 2026-06-27

## Context

`v1.59.0` localized adjacent boolean detail lines across invocation, auth, and mutation-readiness surfaces.
The next local UI gap was narrower but still user-visible: target-state recovery, review-capability, identity-assurance, and auth-readiness detail rows still surfaced raw status strings instead of explicit i18n summary contracts.

## Decision

- target-state recovery contracts now expose key-first localized status summaries
- review-capability contracts now expose key-first localized status and reviewability summaries
- identity-assurance and auth-readiness contracts now expose key-first localized status summaries for detail rendering

## Consequences

- the adjacent status-detail i18n lane is complete for review queue and auth-readiness drilldown surfaces
- raw fallback values remain available if a summary key is absent or a future status is unknown
- local-first, read-only, presentation-only UI boundaries remain unchanged
