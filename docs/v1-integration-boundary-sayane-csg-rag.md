# Chronicle Stack v1.0.0 Integration Boundary: Sayane and CSG-RAG

Issues: #165, #170

## Purpose

This document defines the integration boundary between Chronicle Stack, Sayane, and CSG-RAG for the v1.0.0 release.

Chronicle Stack may serve as a foundation for downstream or adjacent systems, but v1.0.0 does not absorb their runtime responsibilities.

## Chronicle Stack role

Chronicle Stack is the local-first record, review, package, export, and reconstruction foundation for AI-assisted work context.

It owns:

- local chronicle records
- context records and advisory metadata
- artifact and decision records
- RDE diff records
- source provenance
- boundary rules
- local export surfaces
- controlled integration packages
- package review reports
- audit and lifecycle traceability metadata

It does not own downstream model execution, hosted memory, graph retrieval, semantic ranking, live collaboration, authorization enforcement, or agent orchestration.

## Sayane boundary

Sayane may consume Chronicle Stack outputs such as:

- controlled context packages
- package review reports
- selected context records
- audit/lifecycle metadata
- exported markdown/YAML/JSON/graph-ready surfaces

Sayane integration should happen through explicit adapters. Chronicle Stack core should not import Sayane runtime assumptions, UI requirements, service lifecycle, model orchestration, or reasoning-loop policies.

## CSG-RAG boundary

CSG-RAG may consume Chronicle Stack outputs such as:

- graph-ready exports
- provenance-aware context packages
- source and boundary metadata
- selected context records
- package review diagnostics

CSG-RAG integration should happen through explicit adapters or import pipelines. Chronicle Stack core should not embed a GraphRAG query engine, vector database, graph database, ranking engine, model API, or retrieval service.

## Adapter-oriented future work

Future integration work may define:

- exported package schemas for Sayane review
- graph-ready import contracts for CSG-RAG
- adapter CLI examples
- integrity checks for handoff artifacts
- review gates before downstream ingestion

Such work should remain explicit and separately scoped.

## Non-goals

v1.0.0 does not implement:

- Sayane runtime integration
- CSG-RAG runtime integration
- hosted API service
- daemon or background service
- GraphRAG query engine
- vector DB
- graph DB
- external model API calls
- authorization enforcement
- legal/compliance enforcement

## Semantic boundary

Chronicle Stack is not merely retrieval infrastructure. Its core purpose is preserving and reconstructing the provenance, context, decisions, differences, and boundaries of AI-assisted work.

Downstream retrieval may use Chronicle outputs, but retrieval is not the whole meaning of Chronicle Stack.

## Warning classification

- Integration warning: related projects must not collapse into Chronicle Stack core.
- Architecture warning: GraphRAG references must not imply graph/vector DB runtime inclusion.
- Semantics warning: context sovereignty foundation must not be reduced to retrieval infrastructure.
- Runtime warning: adapter language must not imply a hidden server, daemon, or model API.

## RDE review

### Preserved

- Chronicle Stack remains an independent context sovereignty foundation.
- Sayane and CSG-RAG remain adjacent/downstream consumers, not hidden dependencies.
- Local-first boundaries remain intact.

### Transformed

- Ecosystem alignment becomes explicit adapter policy.

### Supplemented

- Sayane consumption boundary.
- CSG-RAG consumption boundary.
- Adapter-oriented future work list.

### Deviation risks

- Narrowing Chronicle Stack into a single downstream use case.
- Treating graph-ready export as an actual GraphRAG runtime.
- Allowing integration convenience to become architecture drift.
