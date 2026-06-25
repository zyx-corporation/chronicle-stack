# ADR-0066: Local Review CLI-Equivalent Structured Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.46.0` aligned invocation-plan downstream commands with structured command details.
The adjacent review action surfaces still rendered the single `CLI equivalent` line as a raw command string even though it was a stable local follow-up contract.

## Decision

- review action payloads now expose `cli_equivalent_detail`
- review preview summaries and detail panes prefer localized CLI-equivalent summaries before falling back to the raw command string

## Consequences

- review CLI-equivalent wording becomes i18n-ready without changing local fail-closed review semantics
- copyable review CLI commands remain intact while payloads gain a stable structured contract
