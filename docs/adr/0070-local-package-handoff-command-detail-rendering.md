# ADR-0070: Local Package-Handoff Command-Detail Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.50.0` aligned compact preview-contract badges with structured command summaries.
The adjacent package-handoff preview still lacked explicit structured command hints even though the handoff has stable local follow-up CLI guidance.

## Decision

- package-handoff preview payloads now expose `suggested_command_details`
- package-handoff rendering prefers localized command-detail summaries before falling back to raw command strings

## Consequences

- package-handoff guidance becomes i18n-ready without changing local read-only preview semantics
- suggested CLI commands remain copyable while visible summaries gain stable structured keys
