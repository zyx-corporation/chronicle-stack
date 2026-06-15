# Chronicle Stack v1.0.0 Release Criteria and Compatibility Policy

Issue: #166  
Parent roadmap: #165

## Purpose

This document defines the release criteria and compatibility policy for Chronicle Stack v1.0.0.

v1.0.0 should mark the transition from release-candidate hardening to a stable, compatibility-aware context sovereignty foundation. It does not change Chronicle Stack into a server, daemon, model runtime, GraphRAG engine, vector database, or graph database.

## v1.0.0 position

Chronicle Stack v1.0.0 is intended to be a stable local-first foundation for recording, reviewing, packaging, exporting, and reconstructing AI-assisted work context.

The stable claim is about documented local workflows, CLI behavior, release validation, and boundary clarity. It is not a claim that Chronicle Stack provides complete security enforcement, legal finality, correctness proof, or downstream application integration.

## Stable release criteria

A v1.0.0 release may be prepared only when all of the following are true.

1. Version and release notes are finalized.
   - `pyproject.toml` reports `1.0.0`.
   - `CHANGELOG.md` contains a v1.0.0 section.
   - v1.0.0 release notes include scope, non-goals, verification, and warning classification.

2. Core validation passes.
   - Unit and integration tests pass.
   - Lint checks pass where configured.
   - CLI entry points respond to `--help`.
   - `chronicle --version` reports `1.0.0` after version finalization.

3. Installer smoke passes from the release tag.
   - A clean local install can be performed from the tag.
   - Installed commands are discoverable.
   - `chronicle --version` and `chronicle --help` work from the installed command directory.
   - The smoke report preserves the no-daemon and no-external-runtime notes.

4. Documentation is internally consistent.
   - README release status reflects the current release state.
   - v0.7, v0.8, v0.9, and v1.0 docs are discoverable where relevant.
   - Legal/governance drafts remain marked as draft completed / counsel review pending.

5. Boundary statements are explicit.
   - Advisory metadata is not described as enforcement.
   - Package review pass status is not described as a correctness proof.
   - Graph-ready export is not described as an embedded GraphRAG runtime.
   - No server, daemon, model API, vector DB, or graph DB is introduced unless separately scoped after v1.0.0.

## Stable CLI surface

The following entry points are candidates for the v1.0.0 stable CLI surface:

- `chronicle`
- `chronicle-context`
- `chronicle-export`
- `chronicle-package`
- `chronicle-graph`
- `chronicle-audit`
- `chronicle-lifecycle`

Stability means that documented command names, documented options, documented JSON output shapes, and documented error semantics should not change casually after v1.0.0.

Stability does not mean every internal Python module, private helper, storage implementation detail, or diagnostic wording is frozen.

## Compatibility policy

After v1.0.0, changes should follow these rules.

### Patch releases

Patch releases should be limited to bug fixes, documentation fixes, smoke-test improvements, and non-breaking diagnostic refinements.

Patch releases should not remove documented commands, rename documented fields, or change documented behavior in incompatible ways.

### Minor releases

Minor releases may add commands, options, fields, warnings, or advisory workflows.

Minor releases may deprecate behavior, but deprecations should be documented before removal.

### Breaking changes

Breaking changes should require an explicit compatibility note and should normally wait for a major release.

A breaking change includes removing a documented command, renaming a documented option, changing required JSON fields, changing the meaning of a documented status, or changing release/install assumptions.

## Advisory workflow boundaries

The following workflow boundaries must remain visible in v1.0.0 documentation and release notes.

- Classification metadata is advisory metadata, not access control.
- Audit events are traceability metadata, not enforcement.
- Lifecycle markers are advisory metadata and do not mutate primary records by themselves.
- Package review is a diagnostic workflow.
- A package review `pass` status is not a correctness proof.
- A `warning` status is not automatic approval.
- A `blocked` status requires review before handoff.
- Graph-ready export produces local derived surfaces; it does not introduce a GraphRAG engine, vector DB, or graph DB.

## Integration boundary

Sayane, CSG-RAG, and other downstream systems may consume Chronicle Stack records, packages, exports, or reports through explicit adapter boundaries.

Chronicle Stack core should not silently absorb downstream runtime responsibilities. Integration work must preserve local-first context recording as the core purpose.

## Release PR expectations

A v1.0.0 release PR should include:

- Summary
- Boundary
- Verification
- Warning classification
- RDE review

The Verification section should distinguish between executed checks and planned release-operator checks. Tag creation and GitHub Release publication may require local `git` / `gh` commands if connector operations are unavailable.

## Warning classification

- Compatibility warning: v1.0.0 should stabilize documented surfaces without freezing accidental internals.
- Semantics warning: advisory metadata and diagnostic reviews must not be overstated as enforcement or proof.
- Runtime warning: stable release language must not imply server, daemon, model API, GraphRAG, vector DB, or graph DB inclusion.
- Legal warning: commercial license and contributor policy drafts remain counsel-review pending.
- Integration warning: Sayane / CSG-RAG alignment must remain adapter-oriented and must not collapse project boundaries.

## RDE review

### Preserved

- Chronicle Stack remains a local-first context sovereignty foundation.
- v0.7 operational workflows, v0.8 package review, and v0.9 release hardening remain the base.
- Release validation remains evidence-based rather than assertion-based.

### Transformed

- Release readiness becomes a compatibility and governance boundary rather than only a technical checklist.

### Supplemented

- Explicit release criteria.
- Stable CLI surface expectations.
- Breaking-change policy.
- Integration and advisory-workflow boundary language.

### Unresolved

- Exact v1.0.0 release date.
- Whether docs should be consolidated before final release.
- Whether any CLI help text needs minor wording changes before v1.0.0.

### Deviation risks

- Treating v1.0.0 as a full security/enforcement system.
- Treating package review as correctness proof.
- Freezing accidental implementation details.
- Narrowing Chronicle Stack into a single downstream integration use case.
