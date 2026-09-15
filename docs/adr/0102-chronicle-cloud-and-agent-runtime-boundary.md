# ADR-0102: Chronicle Cloud and Agent Runtime Boundary

Status: Accepted  
Date: 2026-08-07  
Scope: Future Chronicle Cloud, Kazane, and agent-runtime integration planning  
Related: ADR-0101, ADR-0103, ADR-0010, ADR-0016, ADR-0097,
`docs/roadmaps/chronicle-daemon-api-roadmap.md`

## Context

ADR-0101 defines a future local resident daemon and Chronicle-native API layer. That layer is a
necessary step, but it is not the final integration shape. If Chronicle Stack is to support
Kazane, AI番頭, Kotone, and broader agent execution environments, the system will eventually
need team sharing, device sync, organizational audit, permissions, backup, and cross-organization
connection.

The risk is that cloud expansion could turn Chronicle Stack into a generic SaaS record tool or a
cloud AI memory provider. That would weaken the core value: questions, judgments, evidence,
diffs, and boundaries should remain reconstructable as Chronicle records wherever work is
executed.

## Decision

Chronicle Stack will plan long-term expansion in this order:

```text
Local Chronicle
  local-first Chronicle record preservation and context sovereignty

Resident Chronicle API
  local explicitly controlled API surface for tools and agents

Agent Runtime / Kazane
  execution layer for work, proposals, editing, investigation, and dialogue

Chronicle Cloud
  service layer for team sharing, device sync, audit, permissions, backup, and operations

Chronicle Federation
  trust- and disclosure-scoped connection across organizations, partners, and public material
```

The role split is:

```text
Chronicle Stack = preservation mechanism for Chronicle records and reconstruction metadata
Kazane / agent runtime = execution layer that works with that context
Chronicle Cloud = service layer for synchronization, sharing, audit, permissions, and backup
Chronicle Federation = relationship layer across organizations and disclosure scopes
```

Chronicle Cloud may exist, but it must not become a cloud AI memory that takes ownership of the
Chronicle or stores the source of truth on behalf of agents. Cloud service behavior must preserve
authority clarity, portability, exportability, auditability, and local-first recovery paths.

## Boundary Rules

- Local Chronicle remains the conceptual authority anchor for Chronicle records.
- Cloud sync must preserve exportability and reconstructability.
- Cloud copies, indexes, caches, and collaboration views must be labeled by authority level.
- Agent runtimes may consume context and submit records through APIs, but they do not own the
  primary context.
- Cloud permissions are service-layer permissions; they do not erase local provenance or
  Chronicle boundary metadata.
- Cross-organization sharing belongs to Federation unless a later ADR explicitly defines a
  Cloud-specific sharing contract.
- Backup and sync must not silently become publication.
- Public copy must not imply that current Chronicle Stack already provides Chronicle Cloud.
- Public copy must not describe Chronicle Stack as a cloud AI memory that stores the source of
  truth.

## Public Positioning

Acceptable future-facing language:

```text
将来的には、Kazaneなどのエージェント実行基盤と連携し、ローカル正本を保ちながら
クラウド同期、チーム共有、監査、権限管理を担うサービス層へ拡張する構想がある。
```

Avoid:

```text
Chronicle Stack is already a cloud collaboration service.
Chronicle Stackは、正本を保管するクラウド型AIメモリである。
```

## Consequences

### Positive

- Cloud expansion is allowed without surrendering context sovereignty.
- Kazane and agent runtimes get a clear role as execution layers, not source-of-truth owners.
- Federation remains distinct from ordinary team sync and backup.
- Public positioning can describe the future honestly without overstating current capability.

### Negative / Cost

- Cloud sync and team sharing require difficult authority, permission, tenancy, and conflict
  resolution design.
- The product story must repeatedly distinguish local truth, cloud service copies, and
  federation disclosures.
- Agent runtime integrations need capability contracts and audit trails before broad use.

## Non-goals

This decision does not:

- implement Chronicle Cloud;
- implement Kazane integration;
- add remote sync;
- add hosted multi-tenant authorization;
- replace the local resident API roadmap;
- define conflict resolution, billing, tenancy, or cloud storage architecture;
- treat Cloud as the owner of the Chronicle;
- merge Federation and Cloud into one surface.

## RDE Review

### Preserved

- Local Chronicle authority framing.
- Resident API as the next local integration layer.
- Federation as the relationship and disclosure layer.
- No current public claim that Cloud is available.

### Transformed

- Cloud service is no longer only a distant speculation; it becomes an explicitly bounded future
  service layer.
- Agent runtime / Kazane is placed as an execution layer that refers to Chronicle rather than
  replacing it.

### Added

- Ordered expansion path from local Chronicle authority to cloud service layers and federation.
- Chronicle Cloud role definition.
- Public copy guidance for future cloud positioning.

### Unresolved

- Cloud authority model and conflict resolution.
- Team/organization permission model.
- Tenant isolation and encryption model.
- Sync protocol and offline-first behavior.
- Kazane integration contract and capability scopes.

### Deviation Risks

- Cloud service becomes the de facto primary Chronicle record.
- Agent runtime writes blur human judgment, AI proposal, and business-system fact.
- Backup/sync is mistaken for publication or federation.
- Public pages overstate Cloud or agent integration readiness.
