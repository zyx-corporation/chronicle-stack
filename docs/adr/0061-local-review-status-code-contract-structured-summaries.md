# ADR-0061: Local Review Status-Code Contract Structured Summaries

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.41.0` aligned overview failure-family rendering with the write-route detail surface.
The adjacent `status_code_contract` rows still depended on renderer-side concatenation of status code, family, and localized `when` text.

## Decision

- each review write-route status-code row carries a stable `summary_key`
- the write-route detail renderer uses `summary_key` first and falls back to local summary text

## Consequences

- status-code contract wording is stable and i18n-ready without changing the underlying route behavior
- local fail-closed review semantics and authority boundaries remain unchanged
