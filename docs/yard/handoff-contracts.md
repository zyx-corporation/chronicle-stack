# Stack Handoff Contract Review

Status: Active
Date: 2026-08-07
Milestone: CY-1

Chronicle Stack is the authority for primary Chronicle records and for producing derived
handoff surfaces. Downstream products may inspect, validate, query, or evaluate those surfaces,
but must not treat private Stack implementation state as their contract.

## Current Handoff Surfaces

| Surface | Consumer use | Authority level | Notes |
|---|---|---|---|
| `.chronicle/chronicle.jsonl` | Primary local record inspection | Primary Stable | Owned by Stack; not a downstream mutation target |
| YAML / Markdown / HTML export | Human review and sharing | Semi-public / human-facing | Export options and lifecycle warnings matter |
| Graph export | Derived graph inspection | Derived | Rebuildable; not a GraphRAG engine |
| Integration package | Controlled package handoff | Semi-public | Requires manifest and review semantics |
| Query-engine handoff bundle | Downstream query/evaluation | Semi-public | See `../downstream-query-engine-handoff-bundle.md` |
| Federation package | Manual partner disclosure | Planned/available bounded surface | Inspect/verify before import or sharing |

## Required Metadata

Every handoff path used by Yard-family products should preserve or explicitly report loss of:

- source authority level;
- source event, artifact, context, decision, and RDE identifiers where applicable;
- provenance and source metadata;
- classification, visibility, lifecycle, and boundary hints;
- review status and confidence;
- export or package creation options;
- warnings for AI interpretation, redaction, consent, or incomplete verification.

## Failure Gates

- A consumer needs direct access to Stack private services or index internals.
- Provenance or lifecycle metadata disappears without an explicit warning.
- Query/runtime behavior is added to Stack core to satisfy a downstream shortcut.
- Verifier output is presented as truth proof rather than review evidence.

## Next Implementation Hooks

- Add or reuse fixtures that represent sanitized handoff bundles.
- Keep package verification and API contract tests in Core CI.
- Add downstream repository links when CSG-RAG and chronicle-external-query contract documents
  are available.
