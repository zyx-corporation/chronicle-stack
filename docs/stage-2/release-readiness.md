# Stage 2 Release Readiness

Status: Implementation ready
Date: 2026-07-13

## Completed gates

- M2.0 specifications, provenance ledger, notices, and accepted architecture decisions
- M2.1 provider-neutral backend port, orchestrator, disabled/fake/local/HTTP backends, and compatibility facade
- M2.2 runtime event/recording separation and record-false coverage
- M2.3 static capability manifests, diagnostics, and read-only listing
- M2.4 scoped readers, proposal writer, and deny-by-default network policy
- M2.5 preview-first operation plan, stale/duplicate protection, proposal/review/apply lineage
- M2.6 declarative local proposal surface and guarded command-layer mutation
- M2.7 external interaction envelope, identity evidence, attachment references, mock adapter, and explicit non-executing promotion
- M2.8 doctor checks, negative tests, operations, migration, security, rights, performance, and exit RDE evidence

## Release boundary

Stage 2 is an implementation program, not an automatic semantic-version change. This branch does not alter `2.0.0`. Version selection and publication remain maintainer release actions after PR review and CI.

## Required final evidence

- `ruff check src/ tests/`
- full `pytest`
- `chronicle ui-smoke --json` against a temporary initialized Chronicle
- `chronicle index rebuild` followed by `chronicle doctor --json`
- clean Git diff and CI on the review branch
