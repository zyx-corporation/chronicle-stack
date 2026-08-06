# Chronicle Yard Product Family Milestones

Status: Planned  
Date: 2026-08-07  
Scope: Product-family milestones across Chronicle Stack and related Chronicle Yard products  
Related: `docs/future/chronicle-yard-naming-note.md`,
`docs/roadmaps/overall-roadmap.md`, `docs/roadmaps/chronicle-daemon-api-roadmap.md`

## 1. Purpose

This document turns the Chronicle Yard naming concept into milestone-level planning.

Chronicle Yard is treated as the umbrella name for Chronicle Stack and related products.
Chronicle Stack remains the core Chronicle preservation mechanism. Related products such as
`csg-rag` and `chronicle-external-query` belong to the Yard product family because they run
governed GraphRAG, downstream query, retrieval, runtime evaluation, verifier capture, or other
work around Chronicle-derived records without moving those responsibilities into Chronicle
Stack core.

For brevity, this document uses `EQ` to mean `chronicle-external-query`.

These milestones are not release promises. They are dependency and exit-condition checkpoints
for deciding what belongs in Chronicle Stack, what belongs in adjacent repositories, and what
belongs in future service layers such as Chronicle Cloud.

## 2. Current Roadmap Recheck

The current roadmap remains structurally valid:

- Chronicle Stack must continue to preserve local/exportable Chronicle records.
- API, daemon, agent runtime, cloud sync, and federation planning must not turn Chronicle Stack
  into cloud AI memory.
- GraphRAG, downstream query execution, runtime comparison, and provider experimentation should
  stay outside Chronicle Stack core.
- Chronicle Cloud can be planned as a service layer, but it must not own the Chronicle.

The gap is vocabulary and product-family coordination. `docs/roadmaps/overall-roadmap.md`
describes Chronicle Stack implementation tracks, while Chronicle Yard now needs a separate
cross-product milestone lane that covers:

- Chronicle Stack core preservation and API readiness;
- `csg-rag` as a governed Context Sovereignty GraphRAG local runtime;
- `chronicle-external-query` as a downstream handoff-bundle query/evaluation workspace;
- future Chronicle API, Chronicle Cloud, Kazane, and user-facing app surfaces.

## 3. Milestone Operating Rules

- Milestones are ordered by dependency, not calendar date.
- A milestone is complete only when its acceptance criteria are met and its failure gates are
  avoided.
- Cross-repository integration must use explicit contracts, handoff bundles, APIs, or verifier
  artifacts.
- Chronicle Stack core must not silently absorb runtime/query responsibilities from related
  products.
- Public copy must distinguish current implementation, planned interfaces, and speculative
  Yard-family concepts.

## 4. Recommended Milestone Titles

If these are mirrored to GitHub or another tracker, use these titles:

```text
CY-0 — Yard Vocabulary and Product Boundary
CY-1 — Stack Preservation Baseline and Handoff Contracts
CY-2 — Downstream Query and GraphRAG Product Mapping
CY-3 — Chronicle API Contract Readiness
CY-4 — Governed Local Runtime Interoperability
CY-5 — Yard Operator Journey and Documentation
CY-6 — Chronicle Cloud Authority Model
CY-7 — Federation and Product-Family Governance
```

## 5. Milestone Summary

| ID | Milestone | Primary outcome | Depends on |
|---|---|---|---|
| CY-0 | Yard Vocabulary and Product Boundary | Yard / Stack / Cloud / API / CSG-RAG / EQ roles are named | ADR-0103, Yard naming note |
| CY-1 | Stack Preservation Baseline and Handoff Contracts | Stack exports and handoff surfaces are authoritative enough for related products | Core / Security baseline |
| CY-2 | Downstream Query and GraphRAG Product Mapping | `csg-rag` and `chronicle-external-query` are mapped as Yard products with non-core responsibilities | CY-1 |
| CY-3 | Chronicle API Contract Readiness | API contracts exist before daemon implementation | CY-1, ADR-0101 |
| CY-4 | Governed Local Runtime Interoperability | Stack, CSG-RAG, and EQ can be evaluated through explicit local contracts | CY-2, CY-3 |
| CY-5 | Yard Operator Journey and Documentation | User-facing Yard journey is explainable without collapsing product boundaries | CY-0 through CY-4 |
| CY-6 | Chronicle Cloud Authority Model | Cloud is specified as sync/share/audit layer, not AI memory authority | CY-5, ADR-0102 |
| CY-7 | Federation and Product-Family Governance | Federation, Cloud, and product-family governance are separated | CY-6, federation roadmap |

## 5.1 Current Status

| ID | Status | Current note |
|---|---|---|
| CY-0 | In progress | Yard naming note exists; roadmap references added; no implementation rename performed |
| CY-1 | Next | Review Stack handoff/export contracts against EQ and CSG-RAG needs |
| CY-2 | Next | Draft Stack / CSG-RAG / EQ responsibility matrix |
| CY-3 | Pending | Wait for API contract skeleton before daemon implementation |
| CY-4 | Pending | Wait for CY-2/CY-3 contract clarity |
| CY-5 | Pending | Wait for operator journey across Stack, CSG-RAG, and EQ |
| CY-6 | Pending | Wait for Cloud authority labels and local recovery guarantees |
| CY-7 | Pending | Wait for Cloud/Federation boundary readiness |

## 6. CY-0 — Yard Vocabulary and Product Boundary

### Goal

Fix the vocabulary so Chronicle Yard can be used as the umbrella name without renaming Chronicle
Stack implementation artifacts.

### In scope

- Yard as product-family umbrella.
- Stack as core preservation mechanism.
- Cloud as future service layer.
- API as interface boundary.
- CSG-RAG and EQ as concrete related products.
- Public-copy guardrails.

### Out of scope

- Repository rename.
- CLI rename.
- Package rename.
- Hosted product launch claim.
- Cloud AI memory positioning.

### Required artifacts

- `docs/future/chronicle-yard-naming-note.md`
- Product overview reference.
- Roadmap index reference.
- Chronicle history entry.

### Acceptance criteria

- A reader can distinguish Yard, Stack, Cloud, API, CSG-RAG, and EQ.
- Yard is described as a product-family umbrella, not merely a new name for Stack.
- The documentation says that Stack is not cloud AI memory.
- No implementation names are changed.

### Failure gates

- Public copy implies that Chronicle Yard already exists as a released hosted suite.
- Chronicle Stack is renamed casually in code, CLI, package, or repository contexts.
- Cloud is described as owning the Chronicle.

## 7. CY-1 — Stack Preservation Baseline and Handoff Contracts

### Goal

Make Chronicle Stack's preservation and handoff surfaces reliable enough for Yard-family
products to consume without depending on private implementation assumptions.

### In scope

- JSONL authority and exportability.
- Handoff bundles.
- Graph export.
- Integration package contracts.
- RDE and provenance metadata.
- Boundary and lifecycle metadata required by downstream products.

### Out of scope

- Query execution inside Chronicle Stack core.
- Hosted retrieval infrastructure.
- Provider experimentation inside Stack.
- Implicit write-back from downstream products.

### Required artifacts

- Contract docs for handoff bundles and graph export.
- Validation fixtures.
- Boundary notes for downstream consumers.
- T-RDE evidence for exported structures.

### Acceptance criteria

- Related products can validate Chronicle-derived bundles before use.
- Handoff contracts identify authority level, provenance, boundary, and lifecycle metadata.
- Stack remains the producer of primary records and derived handoff bundles.
- Downstream products do not need to import Stack internals.

### Failure gates

- A related product requires direct access to private Stack state.
- A handoff bundle loses provenance or lifecycle meaning.
- Downstream runtime behavior is added to Stack core as a convenience shortcut.

## 8. CY-2 — Downstream Query and GraphRAG Product Mapping

### Goal

Map concrete Yard-family repositories and their responsibilities.

### In scope

- `csg-rag` as governed Context Sovereignty GraphRAG local runtime.
- `chronicle-external-query` as downstream query, retrieval, runtime evaluation, and verifier
  capture workspace.
- Responsibility matrix across Stack / CSG-RAG / EQ.
- Contract boundary review between repositories.

### Out of scope

- Merging repositories.
- Treating CSG-RAG or EQ as Stack plugins by default.
- Requiring hosted providers for baseline validation.

### Required artifacts

- Product-family responsibility matrix.
- Link map to the related repositories' README and contract docs.
- Boundary note for runtime/query responsibilities.

### Acceptance criteria

- CSG-RAG owns governed runtime and review-store behavior.
- EQ owns downstream query/retrieval/evaluation over Chronicle-derived bundles.
- Stack owns primary Chronicle preservation and handoff production.
- Cross-product flow is understandable without chat history.

### Failure gates

- Graph/vector/query runtime concerns drift back into Stack core.
- Runtime review-store state is confused with Chronicle source authority.
- EQ verifier output is treated as proof of truth rather than review artifact.

## 9. CY-3 — Chronicle API Contract Readiness

### Goal

Define Chronicle API contracts before introducing any daemon implementation.

### In scope

- Six minimum endpoints from the daemon/API roadmap.
- JSON schema or OpenAPI draft.
- Idempotency contract.
- Error taxonomy.
- API-originated audit metadata.
- Capability and actor metadata requirements.

### Out of scope

- Running daemon.
- Public hosted API.
- Remote multi-user auth.
- Generic log ingestion.

### Required artifacts

- `docs/api/README.md` or equivalent API contract index.
- Endpoint schema drafts.
- Contract tests that do not open network sockets.
- Threat model draft.

### Acceptance criteria

- API writes map to Chronicle-native records.
- API reads are boundary-aware and do not imply unrestricted memory export.
- Contract tests run in Chronicle Stack CI.
- Daemon implementation can be deferred without losing API semantics.

### Failure gates

- The API is described as cloud AI memory.
- Endpoint schemas accept arbitrary unstructured logs as the normal path.
- Auth, idempotency, or audit semantics are left implicit.

## 10. CY-4 — Governed Local Runtime Interoperability

### Goal

Prove a local, reviewable interoperability path across Stack, CSG-RAG, and EQ.

### In scope

- Chronicle Stack exports or handoff bundles.
- EQ validation and query/evaluation over those bundles.
- Optional same-host CSG-RAG local API checks.
- Verifier bundle or report capture.
- No implicit write-back into Stack.

### Out of scope

- Hosted provider dependency for baseline.
- Automatic synchronization.
- Remote production API.
- Treating runtime answers as primary Chronicle facts.

### Required artifacts

- Local operator walkthrough.
- Sample bundle or sanitized fixture path.
- EQ report output example.
- CSG-RAG local API boundary note.
- RDE review of the cross-product flow.

### Acceptance criteria

- A clean checkout can validate the local flow with explicit commands.
- Every product's authority boundary is visible in the walkthrough.
- Runtime answers and verifier outputs are review artifacts, not primary facts.
- Failures are explainable without corrupting Chronicle records.

### Failure gates

- A runtime answer writes back to Stack implicitly.
- Hosted provider behavior becomes required for baseline verification.
- Operator cannot tell which product owns which state.

## 11. CY-5 — Yard Operator Journey and Documentation

### Goal

Make the product-family story usable by operators, not only maintainers.

### In scope

- Yard-level product map.
- "Start here" reading order.
- Operator journey from Chronicle capture to handoff, query, review, and possible federation.
- Public positioning draft that preserves cloud AI memory boundary.
- Documentation links across related repositories.

### Out of scope

- Marketing launch page.
- Hosted service availability claim.
- Single monorepo assumption.

### Required artifacts

- Yard product map.
- Cross-repository reading order.
- Operator workflow overview.
- Glossary for Yard / Stack / Cloud / API / CSG-RAG / EQ / Kazane.

### Acceptance criteria

- A new reader can understand the Yard product family in one pass.
- The first workflow does not require cloud service, hosted model, or network federation.
- Every linked product states its boundary and non-goals.

### Failure gates

- Documentation makes Yard sound like one already-shipped platform.
- Stack, CSG-RAG, EQ, Cloud, and API are blurred into a single runtime.
- Public copy implies AI-provider memory ownership.

## 12. CY-6 — Chronicle Cloud Authority Model

### Goal

Specify Chronicle Cloud as a Yard-family service layer without making it the owner of the
Chronicle.

### In scope

- Local/cloud authority model.
- Cloud replica, index, cache, and collaboration-view labels.
- Sync and conflict problem statement.
- Team permissions draft.
- Backup/export/recovery guarantees.
- Cloud audit requirements.

### Out of scope

- Cloud implementation.
- Hosted multi-tenant auth implementation.
- Cloud-first primary record.
- Billing, tenancy, or production operations.

### Required artifacts

- Chronicle Cloud concept document.
- Authority-label matrix.
- Sync/conflict ADR draft or decision note.
- Public copy boundary.

### Acceptance criteria

- Cloud is framed as sync/share/audit/permission/backup service layer.
- Local exportability and reconstructability remain non-negotiable.
- Cloud sharing and federation remain distinct.
- Cloud copies cannot be mistaken for source authority.

### Failure gates

- Cloud is described as a cloud AI memory.
- Local Chronicle records become optional.
- Cloud permission state erases local provenance or boundary metadata.

## 13. CY-7 — Federation and Product-Family Governance

### Goal

Define how Yard-family products relate to federation, external partners, and public material.

### In scope

- Cloud/Federation boundary.
- Trust and disclosure scope matrix.
- Partner handoff or federation package flow.
- Product-family governance for new Yard members.
- ADR requirement for adding major Yard-family products.

### Out of scope

- Networked federation implementation before package/manifest/trust readiness.
- Automatic partner sync.
- Central product-family authority database.

### Required artifacts

- Cloud-to-Federation boundary ADR.
- Product-family membership checklist.
- Trust/disclosure matrix.
- Federation package and message alignment review.

### Acceptance criteria

- New Yard-family products have explicit responsibility and authority boundaries.
- Federation remains the trust/disclosure relationship layer.
- Partner or public sharing cannot bypass redaction, consent, or preview.
- Product-family governance does not weaken Stack core preservation.

### Failure gates

- A Yard-family product can publish or sync Chronicle records without consent.
- Cloud and Federation are treated as the same surface.
- Trust decisions become global scores instead of context-scoped assertions.

## 14. Near-Term Cut

The next practical cut should be:

1. Complete CY-0 by keeping the Yard naming note and roadmap references synchronized.
2. Start CY-1 by reviewing Stack handoff/export contracts against EQ and CSG-RAG needs.
3. Start CY-2 by drafting a responsibility matrix for Stack / CSG-RAG / EQ.
4. Defer CY-3 daemon/API implementation until the API contract skeleton is written.
5. Defer CY-6 Cloud until authority labels and local recovery guarantees are specified.

This keeps the current work honest: product-family language can advance now, while runtime,
query, cloud, and federation implementation remain gated by explicit contracts.

## 15. RDE Planning Notes

### Preserved

- Chronicle Stack remains the core Chronicle preservation mechanism.
- JSONL and derived handoff authority boundaries remain intact.
- CSG-RAG and EQ stay outside Stack core.
- Cloud AI memory positioning remains prohibited.

### Transformed

- Chronicle Yard moves from naming intuition to product-family milestone lane.
- Roadmap planning now includes cross-repository responsibilities, not only Stack-internal
  implementation stages.

### Added

- CY-0 through CY-7 milestones.
- Concrete product-family examples: `csg-rag` and `chronicle-external-query`.
- Near-term cut for Stack/EQ/CSG-RAG contract alignment.

### Unresolved

- Exact contract gaps between current Stack handoff bundles and EQ/CSG-RAG consumption.
- Whether Yard product-family governance belongs in ADRs, roadmap docs, or a separate product
  catalog.
- Chronicle Cloud authority labels and sync/conflict model.

### Deviation Risks

- Yard becomes a vague brand instead of a governed product-family boundary.
- Related products accumulate implicit contracts that are not documented in Stack.
- Runtime/query features drift into Stack core because that is convenient.
- Cloud service planning outruns local/exportable Chronicle authority.
