# ADR-0103: Chronicle Preservation Mechanism, Not Cloud AI Memory

Status: Accepted  
Date: 2026-08-07  
Scope: Chronicle Stack role boundary for API, agent runtime, and cloud planning  
Related: ADR-0101, ADR-0102, `docs/roadmaps/chronicle-daemon-api-roadmap.md`

## Context

ADR-0101 and ADR-0102 define a future resident API, agent-runtime integration, and Chronicle
Cloud planning path. Those plans need one stronger role boundary.

Chronicle Stack may expose APIs and may later have cloud-adjacent service layers, but it must
not be framed as a cloud AI memory that stores the source of truth for a person, company, or
agent. That framing would make Chronicle Stack sound like an AI-provider memory service and
would blur the owner of the Chronicle.

The intended role is narrower and stronger: Chronicle Stack is the preservation mechanism for
Chronicle records. It stores and reconstructs the Chronicle: questions, judgments, evidence,
artifacts, RDE diffs, approvals, holds, withdrawals, boundaries, and their provenance.

## Decision

Chronicle Stack is defined as:

```text
Chronicle Stack = preservation mechanism for Chronicle records and reconstruction metadata
```

It is not:

```text
cloud AI memory for storing the source of truth
```

This means:

- Chronicle Stack preserves Chronicle records; it does not become the owner of company memory.
- The source Chronicle record remains inspectable, exportable, auditable, and reconstructable.
- API and daemon layers are access paths into Chronicle preservation workflows.
- Chronicle Cloud, if later designed, is a service layer for sync, sharing, audit,
  permissions, backup, and operations; it is not a cloud AI memory authority.
- Agent runtimes may read from and write to Chronicle through explicit contracts, but they do
  not own the Chronicle.

## Wording Rule

Prefer:

```text
Chronicle Stackは、クロニクルの保管機構である。
```

Also acceptable:

```text
Chronicle Stackは、問い、判断、根拠、成果物、差分、境界の来歴を、
再構成可能なクロニクルとして保管する基盤である。
```

Avoid:

```text
Chronicle Stackは、正本を保管するクラウド型AIメモリである。
```

Avoid public copy that implies:

- the cloud service owns the source Chronicle;
- AI agents use Chronicle Stack as an unbounded memory store;
- Chronicle Cloud is the canonical place where all context must live;
- local/exportable Chronicle records are optional.

## Consequences

### Positive

- API, daemon, agent, and cloud planning now has a concise role boundary.
- Chronicle Cloud can be discussed without implying cloud-first memory ownership.
- Public positioning can describe future service layers while preserving local/exportable
  Chronicle authority.

### Negative / Cost

- Some "organizational memory" language must be used carefully or translated into Chronicle
  preservation language.
- Cloud product planning must distinguish storage, sync, backup, collaboration views, and
  authority labels.
- Agent runtime integration must avoid memory-store metaphors in API contracts.

## Non-goals

This decision does not:

- prohibit local or cloud storage;
- prohibit APIs;
- prohibit team sync, backup, or collaboration;
- prohibit Kazane or other agent-runtime integration;
- define Chronicle Cloud storage architecture;
- define remote authorization or tenancy.

It only fixes the identity boundary: Chronicle Stack is a Chronicle preservation mechanism, not
a cloud AI memory authority.

## RDE Review

### Preserved

- Local-first and exportable Chronicle records.
- JSONL-backed authority in the current implementation.
- Future API, daemon, Kazane, and cloud planning as possible directions.

### Transformed

- "Organizational memory" language becomes shorthand for reconstructable Chronicle records, not
  a claim that Chronicle Stack owns all organizational context.
- Chronicle Cloud is described as a service layer, not as the source memory.

### Added

- Explicit Japanese wording rule.
- Cloud AI memory prohibition.
- Authority distinction between Chronicle preservation and agent/cloud access paths.

### Unresolved

- Exact authority labels for future cloud replicas, indexes, caches, and collaboration views.
- Whether cloud storage is optional, mirrored, escrowed, or package-based.
- How agent memory, execution state, and Chronicle records are separated in contracts.

### Deviation Risks

- Marketing copy drifts back toward cloud AI memory language.
- Cloud implementation treats local/exportable Chronicle records as secondary.
- Agent runtime APIs become an unbounded memory dump.
