# ADR-0035: Local Mutation Enablement Check Structured i18n

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.15.0` completed and published the local blocker structured-i18n-contract lane.

That lane gave auth-boundary and mutation-blocker payloads stable `message_key` and `summary_key` contracts while preserving fallback strings.

The next adjacent presentation-only seam is the mutation enablement checklist itself:

- `enablement_checks` still expose raw labels and raw details
- `operational_readiness.unsatisfied_checks` still derive presentation strings from raw labels and details
- the embedded HTML renderer still has to consume those values as opaque text

This keeps a smaller i18n drift risk alive inside the read-only mutation-readiness surface.

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0034-local-blocker-structured-i18n-contracts.md`
- `docs/release-status-v1.15.0.md`
- `docs/v1.15-release-remaining-issues.md`

## Decision

`v1.16.0` begins as the local mutation-enablement-check structured-i18n lane after the published `v1.15.0` release.

This lane may:

1. add stable `label_key` and `detail_key` fields to mutation enablement checks
2. add stable `summary_key` plus params to unsatisfied-check summaries
3. preserve fallback labels, details, and summaries for degraded render paths
4. let the embedded HTML renderer prefer structured check keys while remaining read-only
5. extend smoke/test coverage for these explicit mutation-readiness presentation contracts

This lane must not:

- change mutation gating or write semantics
- translate machine-readable check codes
- widen GUI mutation scope
- make presentation-layer checklist wording authoritative over CLI/JSON contracts

## Consequences

Repository-side work in `v1.16.0` should keep mutation enablement payloads descriptive and local-first while making checklist presentation more explicit and key-driven.

This keeps the slice narrow and adjacent:

- blocker contracts stay intact
- mutation-readiness checklist localization becomes more deterministic
- fallback strings remain available for CLI-compatible inspection

## Rationale

After blocker summaries gained structured i18n contracts, mutation enablement checks became the next repeated presentation-only wording seam inside the same read-only overview/detail surfaces.

