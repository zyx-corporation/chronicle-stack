# ADR-0047: Local Package Readiness Detail Structured Contracts

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.27.0` completed the package-handoff structured-contract lane.

The adjacent review-target package readiness detail still lacked a complete structured contract:

- package readiness detail exposed `message_key` but no stable counts summary key
- package readiness detail lacked a stable derived/read-only boundary note key
- smoke/test coverage did not yet enforce a structured contract for the top-level readiness detail payload

## Decision

`v1.28.0` begins as the local package-readiness-detail structured-contract lane after the published `v1.27.0` release.
