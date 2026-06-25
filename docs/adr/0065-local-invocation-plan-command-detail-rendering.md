# ADR-0065: Local Invocation-Plan Command-Detail Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.45.0` moved review recovery and follow-up commands onto structured command details.
The adjacent invocation-plan notice still rendered downstream commands as raw strings even though those commands are stable, local-only follow-up guidance.

## Decision

- invocation-plan payloads now expose `downstream_command_details`
- invocation-plan detail rendering prefers localized command-detail summaries before falling back to raw command strings

## Consequences

- invocation-plan command guidance becomes i18n-ready without changing any local execution boundary
- copyable CLI commands remain intact while visible summaries gain stable structured keys
