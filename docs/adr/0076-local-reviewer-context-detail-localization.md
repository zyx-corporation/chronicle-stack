# ADR-0076: Local Reviewer-Context Detail Localization

- Status: Accepted
- Date: 2026-06-26

## Context

`v1.56.0` localized write-route detail status lines.
The adjacent reviewer-context detail panel still mixed raw internal field, reviewer-kind, and session-boundary values with localized notes, which left one of the remaining read-only inspection surfaces only partially i18n-ready.

## Decision

- reviewer-context contracts now expose structured field and reviewer-kind detail entries
- reviewer-context detail rendering now reuses key-first summaries for session-boundary and ui-intent-required status lines
- reviewer-context field and reviewer-kind lists now prefer structured localized detail entries

## Consequences

- reviewer-context detail wording aligns with the contract-first i18n pattern used across neighboring UI surfaces
- raw fallback values remain available if structured detail is absent
- local-first, read-only, presentation-only boundaries remain unchanged
