# ADR-0099: Repository Documentation Stewardship Surfaces

Status: Accepted  
Date: 2026-08-07  
Scope: Chronicle Stack repository documentation governance  
Related: `AGENTS.md`, `README.md`, `roadmap.md`, `chronicle.md`, `docs/README.md`,
`docs/chronicles/README.md`, ADR-0098

## Context

Chronicle Stack already had substantial documentation: `AGENTS.md`, `README.md`, `docs/`,
`docs/adr/`, release notes, release readiness, stage documents, and roadmaps. However, the
repository did not have explicit root surfaces for roadmap navigation, workspace-wide policy
history, or task-specific maintenance history.

The project initialization and maintenance instruction template requires existing projects to
make these roles explicit without overwriting existing assets or moving important decisions into
README.

## Decision

Chronicle Stack will use the following documentation stewardship surfaces:

- `AGENTS.md`: agent behavior, prohibitions, repository-specific operating rules, and reading
  order.
- `README.md`: first-reader map only.
- `roadmap.md`: root map that points to canonical roadmap documents.
- `docs/`: stable specifications, definitions, criteria, procedures, contracts, ADRs, and
  promoted knowledge.
- `docs/adr/`: important architecture, governance, security boundary, contract, and
  interoperability decisions.
- `docs/chronicles/`: task-specific maintenance history.
- `chronicle.md`: workspace-wide documentation and operating policy history.

Existing `docs/adr/` remains the ADR location. The repository will not create a parallel root
`ADR/` directory unless a future ADR explicitly changes the location.

## Consequences

### Positive

- Future maintainers can distinguish instructions, maps, plans, stable docs, decisions, task
  history, and workspace policy history.
- README stays concise and map-like.
- Documentation governance can be improved without moving existing ADRs or rewriting history.

### Negative / Cost

- There are more top-level documentation surfaces to maintain.
- Contributors must choose the correct surface when recording history or promoting knowledge.

## Non-goals

This decision does not:

- change `.chronicle/chronicle.jsonl` as the primary record;
- move ADR files out of `docs/adr/`;
- replace release notes, release readiness, or release status documents;
- turn task chronicles into formal specifications;
- require every small documentation edit to receive a new ADR.

## RDE Review

### Preserved

- Existing repository layout and ADR location under `docs/adr/`.
- README as a map for first readers.
- `.chronicle/chronicle.jsonl` as the primary record.

### Transformed

- Documentation maintenance now has explicit root and task-history surfaces.
- `AGENTS.md` now carries documentation governance in addition to engineering guidance.

### Added

- Root `roadmap.md`.
- Root `chronicle.md`.
- `docs/README.md`.
- `docs/chronicles/README.md`.
- A task-specific chronicle entry for the maintenance alignment.

### Unresolved

- Whether future release tooling should automatically append maintenance chronicle entries.
- Whether documentation surface checks should be added to CI.

### Deviation Risks

- Contributors may still place transient work notes in `docs/`.
- Important decisions may be recorded only in chronicles instead of ADRs.
- README may accumulate rationale over time unless reviewers keep it map-like.
