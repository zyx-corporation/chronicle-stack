# Stage 2 Security Review

Status: Passed for Stage 2 scope
Date: 2026-07-13

## Reviewed boundaries

- runtime execution is explicit and provider adapters cannot write Chronicle storage
- recording is owned by `RuntimeRecordingService`
- capability lookup is static and unknown IDs fail closed
- scoped runtime readers expose only selected records
- network authorization is deny-by-default and destination/operation bound
- capability mutation produces proposals, not direct artifact/context updates
- operation plans reject stale targets and duplicate conversion/apply
- local UI mutation is loopback-only, explicitly enabled, authenticated, authorized, and request/session bound
- external envelope metadata rejects common secret-bearing keys
- attachment payloads store bounded references rather than embedded bytes
- external identity evidence is not promoted to Chronicle actor identity
- message receipt and command execution are separate; promotion records `not_executed`

## Negative-test evidence

Tests cover disabled execution, external-context denial, backend errors, record-false behavior, scoped access denial, network denial, duplicate and stale plans, UI session/token/duplicate/stale checks, secret metadata rejection, and embedded attachment rejection.

## Residual risks

- `PolicyBoundNetworkClient` authorizes policy; actual provider transport isolation remains process-level application code rather than an OS sandbox.
- real webhook signature verification is intentionally outside Stage 2 because no production transport adapter is included.
- HTTP credentials remain operator-managed environment variables.

These risks match the local-first, explicit-operation Stage 2 scope and must be reassessed before hosted runtime or real transport work.
