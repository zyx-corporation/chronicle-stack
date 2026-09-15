# Chronicle Yard Product Map

Status: Active
Date: 2026-08-07
Roadmap: `../roadmaps/chronicle-yard-product-family-milestones.md`

Chronicle Yard is the product-family umbrella for Chronicle Stack and related products.
Chronicle Stack remains the current repository, CLI, package, and core preservation mechanism.

This page completes the first product-boundary cut for CY-0 and provides the stable entrypoint
for CY-1 and CY-2 work. It is not a rename decision and does not claim that Chronicle Yard is a
released hosted suite.

For a Japanese overview of the Yard concept and user-facing flow, see
[`overview.ja.md`](overview.ja.md).

## Product Roles

| Name | Role | Current status | Authority boundary |
|---|---|---|---|
| Chronicle Yard | Product-family umbrella | Vocabulary and planning lane | Does not replace Stack implementation names |
| Chronicle Stack | Local-first Chronicle preservation mechanism | Current repository and CLI | Owns JSONL-backed primary records and derived handoff bundles |
| Chronicle API | Chronicle-native interface boundary | Planned local contract surface | Access path over Core services, not generic memory ingestion |
| Chronicle Cloud | Future service layer | Planned concept | Sync/share/audit/permission/backup, not source authority |
| CSG-RAG | Governed Context Sovereignty GraphRAG runtime | Related product | Runtime/retrieval behavior stays outside Stack core |
| chronicle-external-query | Downstream query and evaluation workspace | Related product | Consumes handoff bundles; verifier output is review artifact |
| Kazane / agent runtimes | Execution layer integrations | Planned integration surface | May act with Chronicle context, but does not own the Chronicle |

## Boundary Rules

- Use Chronicle Stack for current implementation, repository, CLI, and core preservation.
- Use Chronicle Yard only as the product-family umbrella.
- Keep graph, vector, query, provider experiments, and runtime evaluation outside Stack core.
- Keep Chronicle Cloud as a service layer, not a cloud AI memory authority.
- Keep API contracts Chronicle-native: events, context, diffs, timeline, assertions, and
  boundaries.
- Require explicit contracts, handoff bundles, API schemas, or verifier artifacts for
  cross-product integration.

## Reading Order

1. `overview.ja.md`
2. `../roadmaps/chronicle-yard-product-family-milestones.md`
3. `responsibility-matrix.md`
4. `handoff-contracts.md`
5. `../api/README.md`

## Current Milestone State

| Milestone | State | Evidence |
|---|---|---|
| CY-0 | Complete for vocabulary boundary | This map and the existing Yard naming note |
| CY-1 | In progress | Handoff contract review started in `handoff-contracts.md` |
| CY-2 | In progress | Product responsibility matrix started in `responsibility-matrix.md` |
| CY-3 | In progress through API Phase 1 | API contract skeleton in `../api/README.md` and code contracts |

## Non-goals

- Repository, CLI, package, or API rename.
- Hosted product launch claim.
- Monorepo consolidation.
- Moving CSG-RAG or chronicle-external-query responsibilities into Stack core.
- Treating Chronicle Stack as cloud AI memory.
