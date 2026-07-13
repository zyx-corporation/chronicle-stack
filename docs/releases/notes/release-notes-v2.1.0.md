# Release Notes v2.1.0

## Added

- provider-neutral runtime orchestration with disabled, fake, local, and HTTP backends
- separate runtime recording and explicit `record=false` behavior
- static capability registry, read-only CLI inspection, scoped readers, proposal-only writes, and deny-by-default network policy
- preview-first operation plans connected to proposal, review, and apply lineage
- guarded local Proposal Surface behavior with session, request, stale, and duplicate checks
- transport-neutral external interaction envelopes and mock adapter with explicit non-executing command promotion
- Stage 2 ADRs, operator runbook, security and rights reviews, migration report, performance baseline, release readiness, and Exit RDE
- installed local backup and restore helper commands

## Changed

- project and CLI version report `2.1.0`
- doctor reports capability-registry health and dangerous configured HTTP runtime settings
- Stage 2 specification, roadmap, and milestones are complete
- README repository links are portable rather than checkout-specific

## Verification

- Ruff passed for `src/` and `tests/`
- 508 tests passed on the implementation merge
- GitHub CI passed on Stage 2 PR #383
- index rebuild completed successfully
- doctor completed with zero errors on a fresh Chronicle
- UI smoke passed 60 checks without a server, browser, or external runtime

## Boundary

- runtime and network execution remain explicit and disabled by default
- generated output and external input remain review-required
- external messages never directly execute capabilities
- dynamic plugins, hosted runtime, production transport adapters, autonomous remote execution, and OS-level sandboxing are not included
