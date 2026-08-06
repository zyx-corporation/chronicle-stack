# Chronicle Stack Workspace Chronicle

This file records workspace-wide documentation and operating policy history. Append entries;
do not rewrite prior history to make the project appear cleaner.

## 2026-08-07 - Documentation Stewardship Surfaces

- Task: Align the repository with the project initialization and maintenance instruction
  template.
- Baseline: The repository had strong implementation docs, ADRs, release docs, and an
  `AGENTS.md`, but lacked root `roadmap.md`, root `chronicle.md`, `docs/README.md`, and
  `docs/chronicles/` as explicit documentation stewardship surfaces.
- Changed: Added the missing entrypoint and chronicle surfaces, and supplemented `AGENTS.md`
  with documentation roles, reading order, AI operation elements, and prohibitions.
- Preserved: Existing source layout, `docs/adr/` as the ADR location, `.chronicle/chronicle.jsonl`
  as the primary record, and the existing README as a map rather than a rationale document.
- Why: The repository needs a clear path for future maintainers to know where instructions,
  roadmap pointers, important decisions, stable docs, task history, and workspace policy history
  belong.
- Next: Keep stable guidance in canonical docs and append task-specific maintenance entries under
  `docs/chronicles/`.
- Re-evaluate when: ADR location changes, a new documentation system is adopted, or generated
  maintenance notes begin to crowd stable documentation.

## 2026-08-07 - MDES Standard Coding Procedure Manifest Stored and Adopted

- Task: Store the ZYX MDES-driven standard coding procedure manifest and adopt it through ADR.
- Baseline: Chronicle Stack already had CI/T-RDE, local act, and documentation stewardship ADRs,
  but the broader MDES procedure lived only in the operator's Obsidian vault.
- Changed: Stored the manifest under `docs/development/`, added a development-procedure index,
  and accepted ADR-0100 to define Chronicle Stack's adoption boundary and exceptions.
- Preserved: Existing `AGENTS.md` precedence, ADR governance, local act CI boundary, and README
  map role.
- Why: The standard development protocol should be inspectable from the repository and connected
  to existing Chronicle Stack governance.
- Next: Use ADR-0100 when substantial work needs MDES framing, T-RDE evidence, or exception
  handling.
- Re-evaluate when: GitHub labels, branch policy, or release tooling are updated to enforce MDES
  procedure automatically.
