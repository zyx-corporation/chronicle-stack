# ADR-0101: Resident Daemon and Chronicle-Native API Layer Boundary

Status: Accepted  
Date: 2026-08-07  
Scope: Chronicle Stack future daemon / API implementation planning  
Related: ADR-0016, ADR-0021, ADR-0097, ADR-0099, ADR-0100, ADR-0102, ADR-0103,
`docs/roadmaps/chronicle-daemon-api-roadmap.md`

## Context

Chronicle Stack has intentionally protected a local-first, file/CLI-oriented core. Earlier UI
and runtime decisions repeatedly warned against hidden daemons, hosted services, automatic model
runtime expansion, or convenience-driven write paths.

At the same time, Chronicle Stack's longer-term role as a Chronicle preservation mechanism
requires more than manual CLI recording. AI agents, Obsidian, Git tooling, browser extensions,
and business applications need a consistent way to record questions, judgments, evidence,
artifacts, RDE diffs, approvals, holds, and withdrawals as work happens.

The architectural question is whether Chronicle Stack may eventually expose a resident service
and API. The answer is yes, but only if the API is defined as a Chronicle-native local access
layer rather than a cloud-AI memory surface or generic logging sink. ADR-0102 separately defines
how this local layer may later connect to agent runtimes and Chronicle Cloud; ADR-0103 fixes the
role boundary that Chronicle Stack is a Chronicle preservation mechanism, not cloud AI memory.

## Decision

Chronicle Stack will plan a future resident daemon and API layer with three explicit layers:

```text
Chronicle Stack Core
  local-first Chronicle record, models, services, RDE, boundary rules, exports

Chronicle Daemon / Resident Service
  explicitly installed and managed local process that mediates API access

Chronicle API
  bounded entrypoint for tools and AI agents to record and inspect structured context
```

The Core remains authoritative. The daemon and API are access surfaces over Core services; they
must not become a second source of truth.

The API must be structured around Chronicle-native records and workflows, not generic logs. The
initial planning surface is:

```text
POST /events
GET  /context
POST /diffs
GET  /timeline
POST /assertions
GET  /boundaries
```

These endpoints are conceptual planning names until an implementation ADR and interface contract
fix exact schemas, auth behavior, idempotency, status codes, and persistence semantics.

## Boundary Rules

The future resident service must satisfy these rules before implementation is treated as stable:

- `.chronicle/chronicle.jsonl` remains the primary record.
- API writes must pass through existing service-layer validation or explicit new service
  boundaries.
- API writes must be audit-worthy and reconstructable.
- The daemon must be explicit, local-first, and operator-controlled; no hidden autostart.
- Remote exposure is out of scope until a later network/federation ADR defines it.
- Auth, authorization, session, origin, and capability boundaries must be specified before
  write endpoints are enabled.
- API responses are context access surfaces, not proof of truth, permission grants, or model
  correctness.
- AI clients may read and write through the API, but primary context control remains with the
  operator or organization that owns the Chronicle.
- The API must preserve Chronicle records and reconstruction metadata; it must not be presented
  as a cloud AI memory for storing the source of truth.

## Public Positioning

Public-facing pages should not imply that Chronicle API is already generally available until the
implementation, contracts, and validation exist.

Acceptable future-facing language:

```text
将来的には、ローカル常駐サービスとしてAI番頭や業務ツールから記録・照会・差分確認を
受け付けるAPI層を備える構想である。
```

Avoid:

```text
Chronicle Stack already provides a production API for external tools.
```

## Consequences

### Positive

- Chronicle Stack can become an in-situ Chronicle preservation substrate rather than only a
  manual archive.
- API planning remains aligned with Chronicle preservation and JSONL authority.
- Existing no-daemon warnings are preserved as anti-hidden-runtime constraints rather than as a
  permanent ban on explicit resident services.

### Negative / Cost

- The daemon introduces lifecycle, security, local networking, authentication, and operational
  support concerns.
- API contracts require dedicated tests, versioning, idempotency, and failure-mode design.
- The project must prevent external integrations from treating Chronicle as an unlimited memory
  dump.

## Non-goals

This decision does not:

- implement a daemon;
- add FastAPI, ASGI, or another web framework dependency;
- expose a public hosted API;
- replace CLI commands;
- change `.chronicle/chronicle.jsonl` authority;
- define final endpoint schemas or status codes;
- grant external tools permission to store arbitrary unstructured logs;
- turn Chronicle Stack into a cloud AI memory provider.

## RDE Review

### Preserved

- Local-first Core and JSONL authority.
- Existing service-layer model.
- Explicit boundaries around UI mutation, runtime execution, GraphRAG, and HTTP bridge auth.
- CI and T-RDE as non-certifying validation surfaces.

### Transformed

- "No daemon" changes from a permanent product identity to a guardrail against hidden or
  premature resident services.
- API moves from vague future possibility to a planned architecture track with a bounded scope.

### Added

- Core / Daemon / API layering.
- Conceptual minimal endpoint set.
- Public positioning guidance.
- Requirement that API writes remain structured, audit-worthy, and Chronicle-native.

### Unresolved

- Exact framework and transport.
- Local-only authentication mechanism.
- API schema versioning and OpenAPI publication policy.
- Idempotency-key design.
- Whether daemon management belongs in Chronicle Core or a companion package.
- How Obsidian, Git, browser extension, AI番頭, Kotone, and business-app connectors should be
  prioritized.

### Deviation Risks

- Exposing a generic log-ingestion API that weakens Chronicle semantics.
- Treating API availability as permission to sync or publish externally.
- Allowing daemon state to diverge from JSONL.
- Introducing remote access before local auth, audit, and capability boundaries are proven.
