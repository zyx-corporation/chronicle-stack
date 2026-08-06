# Chronicle Stack Documentation

This directory contains the stable documentation surface for Chronicle Stack.

## Start Here

- [Architecture](architecture.md): system structure and major boundaries.
- [Interface Contracts](interface-contracts.md): CLI and data contract expectations.
- [CLI Reference](cli-reference.md): current command reference for the `chronicle` CLI.
- [Data Model](data-model.md): model-level overview.
- [Testing Strategy](testing-strategy.md): test and validation expectations.
- [Development Procedure Documents](development/README.md): stored development-procedure
  manifests and adoption boundaries.
- [ADR Index](adr/README.md): accepted architecture and governance decisions.
- [Chronicles](chronicles/README.md): task-specific decision history and maintenance entries.
- [Roadmaps](roadmaps/README.md): roadmap documents and planning boundaries.
- [Chronicle Daemon and API Roadmap](roadmaps/chronicle-daemon-api-roadmap.md): planned
  local resident service, tool-facing API, agent-runtime integration, and Chronicle Cloud track
  under the rule that Chronicle Stack is Chronicle preservation, not cloud AI memory.
- [Chronicle Yard Product Family Milestones](roadmaps/chronicle-yard-product-family-milestones.md):
  milestone plan for Chronicle Yard as the umbrella over Chronicle Stack and related products.
- [Future Concepts](future/README.md): speculative product concepts, including the Chronicle
  Yard naming note.
- [Release Docs](releases/README.md): release notes, readiness, status, and operations.

## Role

`docs/` is for stable specifications, definitions, criteria, procedures, contracts, ADRs, and
promoted knowledge. It is not the place for transient work notes.

## Source-of-Truth Boundary

`.chronicle/chronicle.jsonl` is the primary record for Chronicle data. Documentation explains
contracts, behavior, and decisions; it does not replace the primary record.
