# ADR-0049: Local Mutation Summary Structured Contracts

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.29.0` completed the provider-response structured-contract lane.

The adjacent `mutation_enablement_summary` list payload still depended on ad hoc prose:

- list rows exposed `message` and `scope_note` without stable key fields
- the first remaining prerequisite summary was only a rendered fallback string
- runtime/review/summary row rendering still localized mutation-summary text mainly via raw prose

This created avoidable locale drift next to already-keyed mutation enablement checks and read-only mutation readiness detail payloads.

## Decision

`v1.30.0` begins as the local mutation-summary structured-contract lane after the published `v1.29.0` release.

Repository-side work in this lane will:

1. add stable `message_key` fields for mutation readiness summaries
2. add stable `scope_note_key` fields for mutation summary scope wording
3. add stable `remaining_summary_key` plus params for first unsatisfied prerequisite summaries
4. expose matching operational-readiness message keys for detail rendering
5. extend smoke/test coverage for runtime records, review queue, and summary jobs list-row mutation-summary contracts

## Consequences

- read-only mutation summary payloads stay local-first, descriptive, and non-authoritative
- UI rendering can prefer key-driven mutation summary wording over exact-string fallback translation
- existing status codes, counts, and mutation gating semantics remain unchanged
