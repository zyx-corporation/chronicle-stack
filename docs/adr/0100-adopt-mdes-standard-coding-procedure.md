# ADR-0100: Adopt the MDES Standard Coding Procedure Manifest

Status: Accepted  
Date: 2026-08-07  
Scope: Chronicle Stack development procedure governance  
Related: ADR-0002, ADR-0098, ADR-0099,
`docs/development/mdes-standard-coding-procedure-manifest.md`

## Context

Chronicle Stack already treats CI as a T-RDE execution surface, local `act` as the primary Core
CI execution surface, and documentation stewardship as an explicit repository governance
surface. The operator provided the ZYX MDES-driven standard coding procedure manifest as the
broader development protocol to preserve in the repository and adopt as an ADR.

The manifest defines MDES as a Manifest, Design, Evolve, Sustain spiral and connects that
spiral to Roadmap, Milestone, Phase, Epic, Issue, Branch, Pull Request, Test, CI, T-RDE,
Release, and knowledge-base mirroring.

## Decision

Chronicle Stack will store the MDES standard coding procedure manifest under
`docs/development/mdes-standard-coding-procedure-manifest.md` and adopt it as the normal
development procedure for substantial work.

The adoption boundary is:

- Use MDES phases to frame non-trivial work: Manifest, Design, Evolve, Sustain.
- Start substantial changes from a problem statement, acceptance criteria, test plan, and
  T-RDE view.
- Prefer issue-scoped branches and pull requests for ordinary implementation work.
- Use Prototype First when uncertainty is high, and do not merge prototype branches directly as
  production work.
- Use Test First / TDD where implementation behavior can be specified in tests.
- Treat local `act` and repository tests as reproducibility gates per ADR-0002 and ADR-0098.
- Record important design or governance decisions as ADRs.
- Record meaningful semantic differences through lightweight or full T-RDE depending on risk.
- Keep release work connected to release notes, known constraints, validation evidence, and
  follow-up issues.

The manifest is a standard procedure, not a replacement for repository-specific instructions.
When there is a conflict, the precedence order is:

1. explicit human instruction for the current task;
2. safety, license, and source-of-truth constraints;
3. `AGENTS.md`;
4. accepted ADRs;
5. stable documentation under `docs/`;
6. the MDES manifest as the general procedure.

## Exceptions

Small documentation maintenance, emergency repairs, or Codex desktop housekeeping may proceed
without the full Roadmap / Milestone / Phase / Epic / Issue hierarchy when the work remains
bounded and the exception is clear from the task context or recorded afterward.

Even in exceptions:

- destructive or irreversible operations still require explicit human confirmation;
- source-of-truth changes must be recorded;
- tests or validation appropriate to the change must be run or the gap must be stated;
- prototype or exploratory output must not be presented as stable production behavior.

## Consequences

### Positive

- Chronicle Stack development has a standard procedure that connects problem definition,
  design, implementation, validation, T-RDE, release, and sustain review.
- Existing CI and documentation governance ADRs become part of a broader development lifecycle.
- The stored manifest can be inspected without depending on the operator's Obsidian vault.

### Negative / Cost

- Substantial work requires more explicit planning and evidence recording.
- The full hierarchy can be too heavy for small maintenance unless exceptions are used carefully.
- The manifest contains organization-wide guidance, so repository-specific ADRs must clarify
  local adoption boundaries.

## Non-goals

This decision does not:

- require every small edit to have a GitHub Issue, Milestone, Phase, Epic, and PR;
- override `AGENTS.md`;
- replace ADR-0002, ADR-0098, or ADR-0099;
- change branch protection or GitHub repository settings by itself;
- make CI pass a correctness, security, or semantic-validity certification;
- require mirroring every repository record back into Obsidian.

## RDE Review

### Preserved

- Existing Chronicle Stack source-of-truth boundaries.
- CI as a T-RDE execution surface.
- local `act` as the primary Core CI execution surface.
- ADRs as the place for important decisions.
- README as a map rather than a rationale document.

### Transformed

- The repository now has an explicit stored copy of the ZYX MDES development manifest.
- Development procedure governance is connected to MDES phases rather than only local
  repository conventions.
- T-RDE is reinforced as a normal semantic-difference review surface for substantial work.

### Added

- `docs/development/mdes-standard-coding-procedure-manifest.md`.
- `docs/development/README.md`.
- This ADR's adoption boundary and exception policy.

### Unresolved

- Whether GitHub labels should be synchronized with the manifest's standard label taxonomy.
- Whether future CI should enforce MDES documentation surfaces for substantial PRs.
- Whether release tooling should generate MDES Sustain Review entries automatically.

### Deviation Risks

- Treating the full MDES hierarchy as mandatory for tiny edits and slowing maintenance.
- Treating exceptions as the default path.
- Applying organization-wide manifest rules without checking Chronicle Stack-specific ADRs.
- Recording T-RDE language without actually checking semantic differences.
