# 2026-08-07 - Project Initialization and Maintenance Alignment

## Chronicle Entry

- Date: 2026-08-07
- Task: Align Chronicle Stack with the project initialization and maintenance instruction
  template.
- Baseline: `AGENTS.md`, `README.md`, `docs/adr/`, and extensive `docs/` content existed.
  Root `roadmap.md`, root `chronicle.md`, `docs/README.md`, and `docs/chronicles/` did not.
- Changed: Added minimal documentation entrypoints and task-history surfaces, and updated
  `AGENTS.md` to include documentation roles, AI operation elements, reading order, and
  prohibitions.
- Preserved: Existing repository layout, source code, tests, release documents, ADR directory
  location under `docs/adr/`, and README's role as a first-reader map.
- Why: The template requires existing projects to make source-of-truth relationships,
  important-decision storage, task-history storage, and workspace-wide policy history explicit.
- Next: Use `docs/chronicles/` for future task-specific maintenance history and `chronicle.md`
  only for workspace-wide policy history.
- Re-evaluate when: The project moves ADRs out of `docs/adr/`, changes the primary record model,
  or adopts a different documentation governance structure.

## Current Diagnosis

- `AGENTS.md`: present, useful for engineering rules, but needed documentation governance
  supplementation.
- `README.md`: present and already functioning primarily as a repository map.
- `roadmap.md`: missing at root; added as a pointer to canonical roadmap documents.
- `docs/adr/`: present and active; preserved as the decision record location.
- `docs/`: present and extensive; added `docs/README.md` as an entry map.
- `docs/chronicles/`: missing; added as the task-specific history location.
- `chronicle.md`: missing; added for workspace-wide policy history.

## Evidence Required

- Future documentation changes should state whether they update instructions, stable docs,
  ADRs, task-specific chronicles, or workspace policy history.
- Destructive source-of-truth changes still require explicit human confirmation.
