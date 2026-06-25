# ADR-0067: Local Retrieval-Handoff Command-Detail Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.47.0` aligned review CLI-equivalent summaries with structured command details.
The adjacent retrieval-handoff notice still rendered downstream commands as raw strings even though they were stable local package-review follow-up guidance.

## Decision

- retrieval-handoff payloads now expose `downstream_command_details`
- retrieval-handoff rendering prefers localized command-detail summaries before falling back to raw command strings

## Consequences

- retrieval-handoff guidance becomes i18n-ready without changing the local dry-run boundary
- copyable downstream CLI commands remain intact while visible summaries gain stable structured keys
