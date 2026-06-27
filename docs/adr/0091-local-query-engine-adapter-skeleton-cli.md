# ADR 0091: Local Query-Engine Adapter Skeleton Is CLI-Regenerated

- Status: Accepted
- Date: 2026-06-27

## Context

After `v1.71.0`, Chronicle Stack had a stable downstream adapter skeleton model, builder, and example fixture. However, downstream implementers still needed a repository-side way to regenerate the same descriptive skeleton from the current retrieval dry-run handoff without copying example files by hand.

## Decision

Chronicle Stack will expose a local CLI command that regenerates the descriptive query-engine adapter skeleton from the current retrieval dry-run handoff. The command remains read-only and dry-run only: it may emit JSON to stdout or a file, but it does not execute imports, hosted query engines, or external runtimes.

## Consequences

- Downstream implementers can regenerate a fresh skeleton directly from the current handoff contract.
- The skeleton remains a descriptive transport artifact rather than an executable adapter.
- Chronicle Stack still avoids embedding downstream import execution or GraphRAG runtime responsibilities.
