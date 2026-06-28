# Release Notes v1.88.0

## Added

- `chronicle reaction` commands for relation-oriented reactions such as `insufficient_evidence`, `reference`, and `propose_collaboration`
- read-only `/api/reactions`, `/api/lineage-view`, `/api/delta-view`, `/api/context-boundary-view`, `/api/objection-view`, `/api/decay-view`, `/api/ai-involvement-view`, and `/api/timeline-view`
- `/api/context-sns-contract` for question-follow and Chronicle-subscription design previews without enabling network delivery

## Boundary

- reactions remain meaning-bearing local records rather than engagement metrics
- Context SNS surfaces stay preview-first, read-only, and local; no feed ranking, ad delivery, or auto-follow transport is added
