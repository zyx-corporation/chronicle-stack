# ADR-0064: Local Review Command-Detail Structured Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.44.0` aligned write-route action-route and CLI-equivalent summaries with stable templates.
The adjacent recovery and follow-up command lines still rendered raw command lists even though those commands were stable read-only follow-up descriptors.

## Decision

- recovery and follow-up command lists now carry structured command details
- review action detail renderers prefer localized command details and fall back to raw command strings only when needed

## Consequences

- command-detail wording becomes i18n-ready without changing any command semantics
- local fail-closed review behavior and CLI parity remain unchanged
