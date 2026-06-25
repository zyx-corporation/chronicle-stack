# ADR-0068: Local Package-Readiness Command-Detail Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.48.0` aligned retrieval-handoff downstream commands with structured command details.
The adjacent package-readiness notice still rendered suggested commands as raw strings even though they were stable local package-review follow-up guidance.

## Decision

- package-readiness payloads now expose `suggested_command_details`
- package-readiness rendering prefers localized command-detail summaries before falling back to raw command strings

## Consequences

- package-readiness guidance becomes i18n-ready without changing local read-only derivation semantics
- suggested CLI commands remain intact while visible summaries gain stable structured keys
