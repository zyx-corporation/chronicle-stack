# 2026-08-07 - MDES Manifest Storage and ADR Adoption

## Chronicle Entry

- Date: 2026-08-07
- Task: Store the ZYX MDES-driven standard coding procedure manifest and make it an ADR-backed
  repository governance document.
- Baseline: The manifest was provided from the operator's Obsidian vault. Chronicle Stack already
  had ADR-0002 for CI/T-RDE, ADR-0098 for local `act`, and ADR-0099 for documentation stewardship.
- Changed: Added a stored manifest copy under `docs/development/`, added a development-procedure
  index, added ADR-0100, linked it from the ADR and docs indexes, and referenced it from
  `AGENTS.md`.
- Preserved: Existing source-of-truth hierarchy, `AGENTS.md` precedence, `docs/adr/` as the ADR
  location, and the ability to use bounded exceptions for small maintenance work.
- Why: The manifest should be available inside the repository and its adoption boundary should be
  reconstructable without depending on an external vault.
- Next: Consider whether GitHub label taxonomy, PR templates, or release tooling should later
  reflect the MDES manifest.
- Re-evaluate when: The repository introduces enforced branch protection, PR templates,
  GitHub Projects workflows, or MDES-Orbit integration.

## RDE Notes

- Preserved: MDES four-phase framing, issue-scoped branch preference, Prototype First,
  Test First/TDD, local CI, T-RDE, and Sustain Review concepts.
- Transformed: Organization-wide procedure was adapted into a Chronicle Stack-specific adoption
  boundary rather than treated as an unconditional override.
- Added: Exception policy for small documentation maintenance, emergency repairs, and Codex
  desktop housekeeping.
- Unresolved: Whether standard labels and PR templates should be added.
- Deviation risks: Using MDES language performatively without evidence, or making small changes
  too heavy by requiring the full hierarchy.
