# Chronicle Yard Naming Note

Status: Future concept  
Date: 2026-08-07  
Scope: Product naming, public positioning, and architecture vocabulary  
Related: `docs/product-overview.md`, `docs/adr/0103-chronicle-preservation-not-cloud-ai-memory.md`,
`docs/roadmaps/chronicle-daemon-api-roadmap.md`

## 1. Purpose

This note preserves a naming discussion: Chronicle Yard may be the umbrella name for Chronicle
Stack and its related product family, while Chronicle Stack remains the technical architecture
name for the core preservation mechanism.

This is not a rename decision. It is a vocabulary option for future product pages, service
design, ecosystem diagrams, and product-family boundaries.

## 2. Core Intuition

`Chronicle Stack` sounds like a technical foundation. It fits the implementation view: local
store, resident API, RDE diff records, manifests, exports, federation packages, indexes, and
service boundaries.

`Chronicle Yard` may better express the product family. It suggests a place where questions,
judgments, evidence, artifacts, people, organizations, and AI agents come and go; records are
placed, sorted, maintained, inspected, and connected to the next work.

In this sense, Yard is not a cloud AI memory. It is the place-like product metaphor for
Chronicle preservation: a working yard, storage yard, maintenance yard, and dispatch yard for
reconstructable Chronicle records and the related products that work around them.

## 3. Proposed Name Layers

```text
Chronicle Yard
  Umbrella name for Chronicle Stack and related products.
  A place-like product family where a company's memory, judgments, evidence, relationships,
  artifacts, agents, and workflows are gathered, maintained, and made usable again.

Chronicle Stack
  Core technical architecture and preservation mechanism.
  The local-first store, resident API, RDE diff, manifest, federation, index, and export
  components that preserve reconstructable Chronicle records.

Chronicle Cloud
  Related future service layer under the Chronicle Yard umbrella.
  Cloud sync, team sharing, audit, permissions, backup, and operations.
  It must not become a cloud AI memory that owns the Chronicle.

Chronicle API
  Interface layer under the Chronicle Yard umbrella.
  Agent runtimes, Kazane, local tools, business apps, and user-facing surfaces connect through it.
  It records and retrieves Chronicle-native structures, not arbitrary memory dumps.

CSG-RAG
  Related local runtime product under the Chronicle Yard umbrella.
  Provides Context Sovereignty GraphRAG review-store, governed question answering, verifier
  bundle export, local API, and controlled runtime behavior outside Chronicle Stack core.

chronicle-external-query
  Related downstream query and evaluation workspace under the Chronicle Yard umbrella.
  Consumes Chronicle-derived handoff bundles, validates contracts, runs retrieval/runtime
  evaluation, and keeps graph/vector/query execution outside Chronicle Stack core.

Kazane / Agent Runtime Integrations
  Related execution products or integrations under the Chronicle Yard umbrella.
  They act with Chronicle context, but they do not own the Chronicle.
```

## 4. Public Positioning Option

If future public pages use the two-layer wording, prefer:

```text
Chronicle Yard は、AI時代の会社の文脈、判断、根拠、成果物をローカル優先で記録し、
人間やエージェントが再利用できるよう整える、Chronicle Stack と関連製品群の総称です。

Chronicle Stack は、その中核となるクロニクル保管機構・技術構成です。
```

This wording intentionally keeps the Chronicle preservation boundary. It does not claim that
Chronicle Yard or Chronicle Stack is a cloud AI memory where the source Chronicle is handed over
to an AI provider.

## 5. Why Yard Works

`Stack` emphasizes components. That is useful for developers and architecture work, but it can
make the project sound like a bundle of infrastructure parts.

`Yard` emphasizes place, practice, and ecosystem. It can carry the feeling that records arise
from work, are placed somewhere inspectable, get maintained, and can later be dispatched into
another project, review, agent action, publication, cloud sync, or federation package.

That image fits Chronicle's core idea better than a pure memory metaphor: Chronicle is not only
stored; it is arranged so that provenance, judgment, difference, and boundary can be
reconstructed. It also gives the related product family a name without forcing every component
to be called Stack.

## 6. Boundary Rules

- Do not treat this note as an accepted rename.
- Do not rename packages, CLI commands, repository names, release artifacts, or APIs from
  Chronicle Stack to Chronicle Yard without a later ADR.
- Use `Chronicle Stack` for current implementation, repository, CLI, core preservation
  mechanism, and technical architecture.
- Use `Chronicle Yard` only as a possible umbrella name for Chronicle Stack and related product
  surfaces.
- Treat `Chronicle Cloud`, `Chronicle API`, Kazane integrations, and future user-facing apps as
  possible members of the Chronicle Yard product family.
- Treat `csg-rag` and `chronicle-external-query` as concrete examples of related products in
  the Chronicle Yard family, while keeping their runtime/query responsibilities outside
  Chronicle Stack core.
- Keep `Chronicle Cloud` as a service layer, not the owner of the Chronicle.
- Keep `Chronicle API` as an interface boundary, not a generic AI memory endpoint.

## 7. Re-evaluation Points

Re-evaluate this naming split when:

- a public product page is drafted;
- Chronicle Cloud or a hosted service layer is specified;
- a user-facing app or service needs a non-technical product name;
- related products need a shared umbrella name;
- repository, CLI, package, or API names are proposed for change;
- Kazane or other agent runtime integration needs a shared product vocabulary.
