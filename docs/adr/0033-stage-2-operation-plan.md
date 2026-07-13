# ADR-0033: Stage 2 Operation Plan

- Status: Accepted
- Date: 2026-07-13

## Context

AI or tool interpretation must not directly mutate Chronicle records. Operators need to inspect intent, targets, assumptions, and version expectations before a proposal enters review.

## Decision

`OperationPlan` is a preview-first intermediate representation. Plan creation does not mutate the target. Recording a plan stores an `assistant_output` event; conversion creates a proposal; review and apply remain separate operations. Target version IDs are checked during conversion and apply, and duplicate conversion or apply fails closed.

Artifact update is the first stable plan operation. Multi-step transactional plans remain out of scope until this single-operation contract is stable.

## Consequences

- preview, record, proposal, review, and apply have distinct identities
- stale targets are detectable before mutation
- plan lineage remains reconstructable from JSONL
- callers must retain proposed content until conversion or proposal creation
