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

## 2026-08-07 - Chronicle Daemon and API Roadmap

- Task: Plan a resident service and API layer for Chronicle Stack.
- Baseline: Chronicle Stack had strong local-first Core, local UI, runtime, GraphRAG workspace,
  HTTP bridge guidance, and federation planning, but no explicit daemon/API implementation
  roadmap.
- Changed: Added ADR-0101 and `docs/roadmaps/chronicle-daemon-api-roadmap.md` to define Core /
  Daemon / API layering, the minimum endpoint surface, implementation phases, and public copy
  guidance.
- Preserved: JSONL authority, local-first Core, no hidden daemon, no hosted API claim, and
  existing UI/runtime/federation boundaries.
- Why: Chronicle Stack needs a path for tools and agents to write reconstructable Chronicle
  records in situ without collapsing into a generic cloud memory or log API.
- Next: Draft API contracts and a threat model before implementing any daemon process.
- Re-evaluate when: A framework is chosen, auth/session design is proposed, or remote access is
  requested.

## 2026-08-07 - Chronicle Cloud and Agent Runtime Boundary

- Task: Reflect the long-term sequence from local Chronicle authority to resident API, agent
  runtime, cloud sync/team sharing, and federation.
- Baseline: ADR-0101 and the daemon/API roadmap planned local resident API but did not yet place
  Kazane, agent runtimes, or Chronicle Cloud in the architecture.
- Changed: Added ADR-0102 and expanded the daemon/API roadmap and overall roadmap with Agent
  Runtime / Kazane, Chronicle Cloud, and Federation sequencing.
- Preserved: Local Chronicle as authority anchor, context sovereignty, exportability,
  auditability, and the warning not to claim cloud service availability before implementation.
- Why: Cloud service and agent runtime integration are natural future directions, but they must
  not turn Chronicle Stack into a SaaS tool that takes ownership of the Chronicle.
- Next: Draft authority, sync, permission, conflict-resolution, and Kazane capability contracts
  before implementation.
- Re-evaluate when: Chronicle Cloud, team sharing, remote sync, or Kazane integration moves from
  concept to implementation.

## 2026-08-07 - Chronicle Preservation, Not Cloud AI Memory

- Task: Clarify that Chronicle Stack is the preservation mechanism for the Chronicle, not a
  cloud AI memory that stores the source of truth.
- Baseline: The daemon/API and cloud planning documents allowed future service layers, but some
  source-of-truth and organizational-memory phrasing could be read too broadly.
- Changed: Added ADR-0103 and revised ADR-0101, ADR-0102, and the daemon/API roadmap to frame
  API, cloud, and agent integration as access paths around Chronicle preservation.
- Preserved: Future API, Kazane/agent-runtime, cloud sync, team sharing, audit, permissions, and
  backup remain possible planning directions.
- Why: Chronicle Stack's identity is stronger when it is defined as a reconstructable Chronicle
  record preservation mechanism rather than as cloud-owned AI memory.
- Next: Use ADR-0103 wording before writing public copy or implementation contracts for daemon,
  API, agent-runtime, or cloud features.
- Re-evaluate when: Chronicle Cloud storage, replica authority labels, or agent memory contracts
  are designed.
