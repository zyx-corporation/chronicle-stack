# Chronicle Stack v1.62.0 Release Notes

Chronicle Stack `v1.62.0` is a local interactive-UI mutation-session continuity and duplicate-guard release over the published `v1.61.0` baseline.

## Added

- browser-triggered review write routes now require explicit local mutation session continuity metadata
- duplicate local mutation request identifiers are rejected before durable review work begins
- route-contract and reviewer-context metadata now expose mutation session and request-id expectations

## Kept stable

- `.chronicle/chronicle.jsonl` primary-record authority
- loopback-local explicit UI boundary
- fail-closed review decision and audit persistence semantics
