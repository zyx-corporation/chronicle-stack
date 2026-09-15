# Chronicle Daemon and API Implementation Roadmap

Status: Planned  
Date: 2026-08-07  
Scope: Future resident service, API layer, agent runtime integration, and cloud expansion path  
Related: ADR-0101, ADR-0102, ADR-0103, ADR-0016, ADR-0021, ADR-0097, ADR-0100,
`docs/roadmaps/overall-roadmap.md`

## 1. Purpose

This roadmap plans a future Chronicle Daemon and API layer without weakening Chronicle Stack's
local-first Chronicle preservation model.

The goal is to make Chronicle Stack capable of receiving and serving structured context from
tools such as AI番頭, Kotone, Obsidian, Git integrations, browser extensions, Kazane, agent
runtimes, and business applications while keeping Chronicle record authority with the Chronicle
owner.

Chronicle Stack is the preservation mechanism for the Chronicle. It is not a cloud AI memory
that stores the source of truth.

## 2. Product Shape

Chronicle Stack should develop in this order:

```text
Local Chronicle
  Local/exportable Chronicle record authority.
  local-first / exportable / auditable

Resident Chronicle API
  Local resident service.
  AI番頭, Obsidian, Git, business tools, and browser extensions record and query through it.

Agent Runtime / Kazane
  Execution layer for work, proposals, editing, investigation, and dialogue.
  Reads context, boundaries, and judgment history through Chronicle API.

Chronicle Cloud
  Service layer for team sharing, device sync, organizational audit, permissions, and backup.
  Preserves Chronicle authority clarity, portability, and exportability.

Chronicle Federation
  Trust- and disclosure-scoped connection across companies, partners, and public material.
```

The API is not "memory for a cloud AI." It is a Chronicle-native API that AI and humans may use
while the organization retains primary control of the Chronicle record.

Chronicle Cloud is not "a cloud that takes the source of truth away" or "a cloud AI memory." It
is a service layer for sync, sharing, audit, permissions, and backup while local-first Chronicle
authority remains explicit.

## 3. Non-goals

- No hosted API in the first implementation.
- No hidden daemon, autostart, or background sync.
- No second primary database.
- No arbitrary log dump endpoint.
- No remote multi-user authorization claim.
- No external publication or federation transport.
- No claim that API output is truth, permission, or correctness proof.
- No Chronicle Cloud implementation in the daemon/API MVP.
- No claim that cloud sync, team sharing, or Kazane integration is already available.
- No positioning of Chronicle Stack as cloud AI memory for storing the source of truth.

## 4. Minimum API Surface

The first API contract should be small and Chronicle-native.

| Endpoint | Purpose | Initial semantics |
|---|---|---|
| `POST /events` | Record dialogue, judgment, artifact, diff, approval, hold, or withdrawal events | Structured event write through Core validation |
| `GET /context` | Retrieve context for a subject, matter, stakeholder, artifact, or decision | Boundary-aware read model; not unrestricted memory export |
| `POST /diffs` | Register RDE diffs for submitted, published, generated, or revised versions | Maps to RDE service and version lineage |
| `GET /timeline` | Retrieve time-ordered record and decision history | Derived view over JSONL and indexes |
| `POST /assertions` | Record claims, evidence, caveats, unknowns, and verification status | Chronicle object / reaction / source-provenance compatible |
| `GET /boundaries` | Retrieve expression, context-use, or decision rules for a company or matter | Advisory boundary rules, not access-control proof |

Each endpoint needs exact request/response schemas, idempotency behavior, auth requirements,
error contract, audit insertion, and tests before implementation.

## 5. Implementation Phases

### Current Implementation Status

| Phase | Status | Evidence |
|---|---|---|
| Phase 0 | In progress | ADR-0101 accepted; API threat model and connector priority drafts exist under `docs/api/` |
| Phase 1 | In progress | `src/chronicle/api/contracts.py` defines the six minimum transport-free request contracts |
| Phase 2 | In progress | `src/chronicle/services/api_adapter_service.py` provides dry-run write previews and read adapters without HTTP |
| Phase 3 | In progress | `chronicle daemon start` exposes loopback-only read endpoints with session-token auth |
| Phase 4 | In progress | `POST /events`, `POST /diffs`, and `POST /assertions` committed write paths are available with idempotency metadata and audit insertion |
| Phase 5 | In progress | Local connector prototype simulator covers Obsidian, Git, browser, agent, and business fact shapes without external integration |
| Phase 6 | In progress | `chronicle daemon smoke`, operator runbook, readiness, compatibility policy, and security review drafts exist |
| Phase 7 | In progress | Draft executable agent runtime contract and CLI inspection surface exist; no real Kazane integration yet |
| Phase 8 | In progress | Draft executable cloud authority model and CLI inspection surface exist; no cloud implementation |
| Phase 9 | In progress | Draft executable Cloud/Federation boundary matrix and CLI inspection surface exist |

### Phase 0: Manifest and Boundary Lock

Purpose: Turn the API idea into a bounded implementation problem.

Deliverables:

- ADR-0101 accepted.
- This roadmap accepted.
- API threat model draft.
- Connector priority list for AI番頭, Kotone, Obsidian, Git, browser extension, and business
  applications.
- Decision on whether implementation starts in Core or a companion package.

Acceptance criteria:

- The API is explicitly framed as local-first and Chronicle-native.
- Chronicle Stack is described as a Chronicle preservation mechanism, not cloud AI memory.
- Public copy does not claim API availability before implementation.
- Non-goals and source-of-truth boundaries are clear.

### Phase 1: Contract Skeleton

Purpose: Define API contracts without starting a daemon.

Deliverables:

- `docs/api/README.md`.
- OpenAPI or JSON-schema draft for the six minimum endpoints.
- Error taxonomy.
- Idempotency-key contract for write endpoints.
- Audit metadata contract for API-originated writes.
- Contract tests that validate schemas without opening network sockets.

Acceptance criteria:

- Contracts describe structured Chronicle records, not generic logs.
- Schemas map to existing models or explicitly proposed new models.
- Contract tests run in Core CI.

### Phase 2: Service Adapter Layer

Purpose: Add a framework-neutral service boundary for API operations.

Deliverables:

- Application/service adapter functions for event, context, diff, timeline, assertion, and
  boundary operations.
- Permission/capability preflight model.
- Dry-run mode for every write operation.
- Tests for idempotency, validation, audit metadata, and failure behavior.

Acceptance criteria:

- No HTTP server is required to exercise API semantics.
- All writes still pass through JSONL-backed Core services.
- Rejected writes fail before partial persistence.

### Phase 3: Loopback Daemon MVP

Purpose: Provide an explicitly launched local resident service.

Deliverables:

- `chronicle daemon start` or equivalent explicit command.
- Loopback-only bind by default.
- No autostart.
- Health endpoint.
- Read-only endpoints first: `GET /context`, `GET /timeline`, `GET /boundaries`.
- Auth/session boundary matching or extending the local UI workspace model.
- Smoke tests for bind scope, auth failure, and read-only behavior.

Acceptance criteria:

- Daemon startup metadata states root, bind scope, auth mode, and primary-record path.
- Remote binds fail closed unless a later ADR allows them.
- Daemon can be stopped without corrupting JSONL or derived indexes.

### Phase 4: Write Endpoint MVP

Purpose: Enable bounded structured recording.

Deliverables:

- `POST /events`.
- `POST /diffs`.
- `POST /assertions`.
- Idempotency keys required or strongly recommended for writes.
- Audit insertion for API writes.
- Dry-run and preview response mode.
- Failure contract for validation, authorization, conflict, duplicate, and partial persistence.

Acceptance criteria:

- API writes are reconstructable in JSONL.
- API-originated records preserve source tool, actor, confidence, review status, and boundary
  metadata.
- Generic unstructured log ingestion is rejected or routed through an explicit low-confidence
  event type.

### Phase 5: Connector Prototypes

Purpose: Lower integration uncertainty without making prototypes production surfaces.

Candidate prototypes:

- Obsidian capture plugin or local script.
- Git hook / PR evidence recorder.
- Browser extension capture.
- AI番頭 / Kotone local client.
- Business app webhook-to-local bridge simulator.

Acceptance criteria:

- Prototype branches are not merged as production code.
- Each prototype records what should and should not be carried into production.
- Connector writes are reviewed through T-RDE.

### Phase 6: Sustain and Release Readiness

Purpose: Convert daemon/API work into an operable release surface.

Deliverables:

- Operator runbook.
- Security review.
- Backup / restore behavior.
- API compatibility policy.
- Release notes.
- Full T-RDE release review.
- Follow-up issues for remote access, federation transport, or hosted scenarios.

Acceptance criteria:

- Local-only API is operationally documented.
- Known risks are classified.
- The release does not imply hosted API availability.

### Phase 7: Agent Runtime / Kazane Integration Planning

Purpose: Connect Chronicle API to execution layers without letting the execution layer own the
record.

Deliverables:

- Kazane / agent-runtime integration contract draft.
- Capability scopes for reading context, reading boundaries, writing events, writing assertions,
  writing diffs, and requesting review.
- Metadata rules distinguishing human judgment, AI proposal, agent action, business-system fact,
  and derived interpretation.
- Replay / audit story for agent-originated writes.
- Prototype client plan for Kazane or AI番頭.

Acceptance criteria:

- Agent runtime uses Chronicle as context source and record destination, not as an unbounded
  memory dump.
- Agent-originated records are reviewable and distinguishable from human statements.
- Tool capabilities are explicit and revocable.

### Phase 8: Chronicle Cloud Planning

Operational Cloud implementation is blocked until the
[Cloud implementation entry gate](../api/cloud-authority-model.md#cloud-implementation-entry-gate-blocking)
is cleared with linked review evidence. Planning progress does not clear this gate.

Purpose: Define cloud sync and team-sharing without turning Chronicle Cloud into cloud AI memory
or moving Chronicle authority into the cloud by default.

Deliverables:

- Chronicle Cloud concept document.
- Authority model for local records, cloud replicas, cloud indexes, and shared views.
- Sync and conflict-resolution problem statement.
- Organization/team permission model draft.
- Backup/export/recovery guarantees.
- Cloud audit trail requirements.
- Public copy boundary for cloud service positioning.

Acceptance criteria:

- Cloud is framed as sync/share/audit/permission/backup service layer.
- Local exportability and reconstructability remain required.
- Backup/sync is not treated as publication or federation.
- Cloud sharing and cross-organization federation remain distinct.

### Phase 9: Federation / Cloud Relationship Review

Purpose: Decide what belongs to Chronicle Cloud and what belongs to Chronicle Federation.

Deliverables:

- Comparison of team sync, organization sharing, partner disclosure, public material, and
  federation package/message surfaces.
- Trust-level and disclosure-scope matrix.
- ADR for any Cloud-to-Federation bridge.

Acceptance criteria:

- Federation remains the trust/disclosure relationship layer.
- Cloud does not silently bypass federation consent, redaction, or trust boundaries.

## 6. Security and Boundary Questions

These must be answered before enabling write endpoints:

- What authenticates a local API caller?
- How are capabilities assigned to tools such as Obsidian, Git, AI番頭, and browser extensions?
- Can one tool read records created by another tool?
- What metadata distinguishes human statement, AI output, business-app event, and derived
  assertion?
- Which endpoints can return sensitive context?
- How are prompt injection and untrusted external text marked?
- What recovery path exists for malformed, duplicate, or overbroad writes?
- What audit event is inserted for every write?
- What capabilities should Kazane or an agent runtime receive by default?
- How are cloud replicas, indexes, and team views labeled so they do not become ambiguous
  sources of truth?
- How are local export, backup, and recovery guaranteed if Chronicle Cloud exists?
- Where is the boundary between team sharing and external federation?

## 7. Public Copy Guidance

Until implementation and validation exist, use future-facing wording:

```text
将来的には、ローカル常駐サービスとしてAI番頭や業務ツールから記録・照会・差分確認を
受け付けるAPI層を備える構想である。
```

For later cloud positioning:

```text
将来的には、Kazaneなどのエージェント実行基盤と連携し、ローカル正本を保ちながら
クラウド同期、チーム共有、監査、権限管理を担うサービス層へ拡張する構想がある。
```

Do not describe Chronicle Stack as already providing a production API for external tools.
Do not describe Chronicle Stack as already providing Chronicle Cloud, team sync, or Kazane
integration.
Do not describe Chronicle Stack as a cloud AI memory that stores the source of truth.

## 8. T-RDE Planning Notes

### Preserved

- Core remains local-first and JSONL-authoritative.
- Chronicle Stack remains the preservation mechanism for Chronicle records, not cloud AI memory.
- Existing CLI and UI surfaces remain valid.
- Runtime and GraphRAG outputs remain review-required derived surfaces.

### Transformed

- Daemon/API becomes a planned implementation track rather than a vague future concept.
- "No daemon" becomes "no hidden or premature daemon."

### Added

- Six-endpoint minimum API surface.
- Phase plan from contract skeleton to daemon MVP and connector prototypes.
- Expansion sequence through Agent Runtime / Kazane, Chronicle Cloud, and Federation.
- Public copy guidance.

### Unresolved

- Framework choice.
- Auth/session implementation.
- Endpoint schema details.
- Connector priority.
- Whether remote access belongs in Chronicle Stack or only federation layers.
- Chronicle Cloud authority model, conflict resolution, and permission model.
- Kazane / agent-runtime capability contract.

### Deviation Risks

- API scope drifts into unstructured logging.
- Remote access is added before local safety boundaries.
- The daemon accumulates state that cannot be rebuilt from JSONL.
- Cloud service becomes the de facto primary record.
- Agent runtime writes blur human judgment and AI proposal.
- Public copy overstates implementation status.
