# Chronicle Stack Local AI Runtime Architecture

Status: v1.7 architecture boundary  
Scope: GraphRAG, vector search, graph search, summarization, and review workflow

## Purpose

Chronicle Stack is moving from a local-first record/review foundation toward a controlled local AI runtime vertical slice.

The purpose of this document is to define the boundary before implementation proceeds.

The target capabilities are:

- GraphRAG execution
- vector search
- graph search
- LLM-assisted summarization
- GUI-assisted edit / approve / reject workflow

The first rule is:

```text
AI runtime execution is explicit, configured, provenance-recorded, and disabled by default.
```

## Design principles

### Local-first by default

Chronicle records remain local files unless the operator explicitly exports or invokes a configured external runtime.

### Runtime disabled by default

No LLM, embedding, vector DB, graph DB, or GraphRAG provider is called by default.

A fresh Chronicle checkout must not make network calls merely by installing, importing, viewing, exporting, or running smoke checks.

### Adapter boundary before provider choice

Provider-specific implementation must sit behind explicit adapters.

Initial provider classes:

```text
disabled
local
http
```

Future provider examples:

```text
Ollama
OpenAI-compatible HTTP endpoint
Chroma
Qdrant
SQLite-backed vector baseline
NetworkX
Neo4j
local file-backed graph baseline
```

Provider names are not commitments. They are adapter slots.

### Generated output is not accepted output

AI-derived summaries, graph expansions, and retrieval answers are draft artifacts until reviewed.

They must carry:

- source record references
- runtime configuration reference
- provider kind
- prompt or query provenance, if applicable
- generation timestamp
- review status

### GUI mutation follows command-layer review

The local UI may expose review queues before it can mutate records.

Mutation-capable GUI surfaces must not precede command-layer review controls.

## Vertical slice plan

### Phase A: Runtime configuration and status

Add a local runtime config model and status command.

Minimum concepts:

```text
RuntimeProviderKind: disabled | local | http
RuntimeCapability: llm | embedding | vector | graph | summarization
RuntimeStatus: configured | disabled | unavailable | error
```

Initial behavior:

- default runtime is `disabled`
- status command reports disabled provider
- no network calls
- no model calls
- no database runtime calls

### Phase B: Summarization job skeleton

Add a recordable summarization job model.

Minimum job states:

```text
draft
pending_review
approved
rejected
request_changes
```

Initial behavior:

- create job metadata
- attach source record references
- optionally attach manually supplied summary text
- no automatic LLM call until runtime provider is explicitly configured and invoked

### Phase C: Review workflow

Add explicit review decisions.

Minimum commands:

```text
chronicle review list
chronicle review show --id <id>
chronicle review approve --id <id>
chronicle review reject --id <id> --reason <text>
chronicle review request-changes --id <id> --reason <text>
```

Initial behavior:

- review decisions are recorded locally
- audit events are written for review decisions
- generated artifacts remain distinguishable from accepted records

### Phase D: Vector and graph adapter contracts

Add adapter contracts before selecting a production DB.

Minimum vector operations:

```text
index_record(record_id, text, metadata)
search(query, limit)
delete_record(record_id)
status()
```

Minimum graph operations:

```text
add_node(node_id, labels, properties)
add_edge(source_id, target_id, relation, properties)
neighbors(node_id, depth)
status()
```

Initial implementation may be local file-backed and diagnostic.

### Phase E: UI review queue visibility

Add read-only UI endpoints first:

```text
/api/review
/api/review/<id>
/api/runtime/status
```

Initial UI remains read-only.

Mutation through UI requires a later explicit design for authentication, authorization, CSRF, audit events, and rollback behavior.

## GraphRAG boundary

GraphRAG is not one feature. It combines:

- source record selection
- chunking
- embedding
- vector retrieval
- graph expansion
- prompt construction
- model response
- provenance capture
- review decision

Each step must be separately inspectable.

A GraphRAG answer should not be accepted unless its sources and runtime provenance are available.

## LLM API boundary

External LLM APIs are allowed only when explicitly configured and invoked.

Configuration must include:

- provider kind
- endpoint or provider name
- capability
- redaction/export policy reference, if applicable
- explicit operator action

External calls must not be hidden inside export, UI smoke, package review, or doctor commands.

## GUI edit / approve / reject boundary

GUI-assisted review is a later mutation surface.

Before GUI mutation, Chronicle Stack needs:

- command-layer review workflow
- audit event model for review decisions
- explicit rollback or correction story
- clear local-only binding defaults
- authentication / authorization decision if the UI binds beyond loopback

Until then, UI review queue endpoints should be read-only.

## Security and privacy risks

AI runtime features create new risks:

- sensitive context embedded into vector indexes
- source text sent to external LLM APIs
- summaries accepted without review
- graph relations creating inferred personal data
- GUI mutation without adequate authorization
- stale indexes diverging from primary records

The design must keep primary Chronicle records authoritative.

Indexes and summaries are derived surfaces.

## Warning classification

- Runtime warning: all AI runtime providers are disabled by default.
- Network warning: no external calls without explicit configuration and invocation.
- Review warning: generated output is draft until reviewed.
- Index warning: vector and graph indexes are derived surfaces, not primary records.
- GUI warning: mutation-capable UI requires a later explicit security design.
- Semantics warning: retrieval and summarization are assistive, not correctness proof.
- Privacy warning: indexes and prompts may expose sensitive context.

## RDE review

### Preserved

- Local-first context sovereignty.
- Primary record authority.
- Explicit runtime boundaries.
- Read-only UI baseline.
- Diagnostic smoke discipline.

### Transformed

- Previously out-of-scope AI runtime features become explicitly bounded implementation targets.

### Supplemented

- Runtime provider boundary.
- Summarization job model direction.
- Review workflow direction.
- Vector and graph adapter contracts.
- GUI review queue staging.

### Unresolved

- Specific provider selection.
- Encrypted store/key management.
- Authentication and authorization for mutation-capable GUI.
- Index invalidation strategy.
- Redaction policy for external LLM calls.
- GraphRAG answer citation format.

### Deviation risks

- Accidental external calls.
- Treating generated summaries as accepted facts.
- Treating indexes as authoritative records.
- GUI mutation without review or audit.
- Provider-specific leakage bypassing Chronicle export boundaries.
