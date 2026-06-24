# ADR-0046: Local Package Handoff Structured Contracts

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.26.0` completed the package-readiness-summary structured-contract lane.

Adjacent runtime package handoff preview surfaces still lacked a complete structured presentation contract:

- `package_handoff_preview` exposed `message_key` but no stable counts summary key
- `package_handoff_preview` lacked a stable derived/read-only boundary note key
- smoke/test coverage did not yet enforce a structured contract for the top-level handoff preview payload

## Decision

`v1.27.0` begins as the local package-handoff structured-contract lane after the published `v1.26.0` release.

This lane may add stable `counts_summary_key` and `boundary_note_key` fields for read-only package handoff previews and extend smoke/test coverage for that contract.

This lane must not change package handoff semantics or authority, or widen hosted-auth, multi-user, or mutation-authority claims.
