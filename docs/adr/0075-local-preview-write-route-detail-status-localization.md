# ADR-0075: Local Preview Write-Route Detail Status Localization

- Status: Accepted
- Date: 2026-06-26

## Context

`v1.55.0` localized the remaining compact success/failure badges.
The adjacent write-route detail panel still showed several raw internal status values for authorization, assurance, review status, and identity proof even though the contract already held the correct structured seam for i18n-ready status summaries.

## Decision

- authorization and target-state contracts now expose key-first localized status summaries
- write-route detail rendering reuses structured summaries for write status, authorization, target-state, and identity-proof status lines
- existing structured field/check detail arrays continue to back the related detail lists

## Consequences

- write-route detail status lines align with the localized compact badge wording
- raw fallback values remain available if structured summaries are absent
- local-first, read-only, presentation-only boundaries remain unchanged
