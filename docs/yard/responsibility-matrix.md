# Yard Responsibility Matrix

Status: Active
Date: 2026-08-07
Milestone: CY-2

This matrix keeps Chronicle Stack, CSG-RAG, and chronicle-external-query from acquiring implicit
cross-product responsibilities.

| Concern | Chronicle Stack | CSG-RAG | chronicle-external-query |
|---|---|---|---|
| Primary Chronicle records | Owns and preserves JSONL-backed records | Reads derived context only | Reads handoff bundles only |
| Handoff bundle production | Produces and validates bundles | May consume governed bundles | Consumes and validates bundles |
| Graph/vector/runtime execution | Exports inspectable derived surfaces | Owns governed GraphRAG runtime | Owns downstream query/evaluation workspace |
| Provider experimentation | Out of core scope | Allowed inside governed runtime boundary | Allowed as evaluation input, not Stack authority |
| Review-store state | Uses Chronicle review/RDE records | May maintain runtime review store | May produce verifier review artifacts |
| Verifier output | May import only through explicit review/RDE | Produces runtime evidence | Produces query/evaluation reports |
| Write-back to Chronicle | Core services only | No implicit write-back | No implicit write-back |
| Public truth claims | Records claims and review state | Runtime answers are advisory | Evaluations are review artifacts |

## Contract Boundary

Related products should depend on:

- documented export and handoff bundle formats;
- federation package or integration package manifests;
- graph export documents;
- API contracts once they are accepted;
- verifier bundles or reports as review inputs.

They should not depend on:

- private store implementation details;
- `.chronicle/indexes/` as stable input;
- runtime side effects;
- cloud or hosted provider availability;
- unreviewed AI output as a primary Chronicle fact.

## Acceptance Notes

CY-2 is complete only when related repository README files and contract docs can point back to
this matrix or an equivalent product-family contract. Until then, this document is the Stack-side
anchor for responsibility separation.
