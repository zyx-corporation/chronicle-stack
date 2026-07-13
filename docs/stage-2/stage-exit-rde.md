# Stage 2 Exit RDE

Status: Passed
Date: 2026-07-13
Baseline: `docs/stage-2/basic-specification.md`

## Preserved

- `.chronicle/chronicle.jsonl` remains the primary record
- local-first operation and explicit external execution
- proposal, review, apply, audit, and reconstructability boundaries
- derived indexes and registries remain rebuildable/non-authoritative
- CLI parity for mutation paths

## Transformed

- `RuntimeService` is now a compatibility facade over provider-neutral orchestration and separate recording
- local UI can perform tightly gated review mutations through the shared command layer
- external messages have a transport-neutral envelope and explicit promotion record

## Supplemented

- static capability manifests and scoped execution ports
- preview-first operation plans with target-version checks
- proposal surface JSON contract and session/request continuity checks
- transport identity evidence and bounded attachment references
- provenance ledger, rights review, security review, migration report, and performance baseline

## Unresolved

- no Stage 2 blocker remains in repository scope
- production transport adapters, hosted relay, dynamic plugins, sandboxed packages, and federated execution remain explicitly deferred beyond Stage 2

## Deviation risks

- future adapters could bypass scoped ports or promotion if merged without the Stage 2 failure gates
- OS-level runtime sandboxing is not provided
- commercial-edition reuse still requires its own rights review

## Next update policy

Reopen this RDE when adding a production transport, dynamic capability loading, hosted runtime, new provider SDK, primary-record schema requirement, or mutation path not shared by CLI and UI.
