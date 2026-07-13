# Stage C Security and Boundary Baseline Closeout

Status: Completed
Date: 2026-07-13
Roadmap: `../roadmaps/overall-roadmap.md`

## Outcome

Stage C is complete for its advisory, local-first scope. Chronicle distinguishes record classification, intended operations, model-context policy, export/injection/reinterpretation audit, lifecycle guidance, integrity metadata, and AI interpretation warnings without presenting these surfaces as authentication or access-control enforcement.

## Acceptance matrix

| Requirement | Product evidence | Verification |
|---|---|---|
| Classification metadata | `ClassificationMetadata` on Context, Artifact, and Event | serialization and restricted-default tests |
| Distinct operations | `AllowedOperation` separates view, export, inject, reinterpret, and publish | disjoint operation-category tests |
| LLM policy | local/external/masking policy on classified records | doctor sensitive-use checks |
| Injection preview | InjectionPlan and AI boundary preview are non-executing by default | CLI/service tests |
| Prompt-injection boundary | stored text is scanned and rendered as data-boundary guidance | marker and doctor tests |
| Auditability | export, inject, and reinterpret use explicit audit operation categories | audit/export tests |
| Lifecycle | redact, seal, tombstone, retention, and decay guidance remain explicit | lifecycle model/export tests |
| Integrity metadata | optional record hash and previous-hash preparation | classification and doctor tests |
| Security-aware export | named profiles apply advisory redaction/exclusion and audit metadata | export-profile tests |
| AI interpretation warning | stable warning code, severity, message, and next action | AI boundary and runtime-preview tests |

## AI interpretation warning contract

The stable warning codes are:

- `not_primary_fact`: generated or interpreted content is not a primary Chronicle fact
- `review_required`: a human disposition is required before trust or apply
- `decay_candidate`: interpretation should be represented as hypothesis/decay-target material
- `external_context_disclosure`: selected Chronicle context may cross an external AI boundary
- `derived_content_persisted`: prompt or response text is configured for persistence

Warnings remain separate from provider output text. They are derived safety guidance, not proof of model correctness or policy enforcement.

## Preserved boundary

- `.chronicle/chronicle.jsonl` remains the primary record
- classification and allowed operations are advisory metadata, not RBAC/ABAC
- redaction-aware export is not leak-proof access control
- integrity hashes are not signatures or remote attestation
- AI preview performs no external send
- accepted meaning still enters Chronicle through proposal, review, decision, or RDE workflows

## Deferred beyond Stage C

- complete RBAC/ABAC and identity enforcement
- tenant isolation or cloud IAM
- perfect prompt-injection prevention
- cryptographic signing and remote attestation
- OS-level runtime sandboxing

These are explicit non-goals, not incomplete Stage C work.
