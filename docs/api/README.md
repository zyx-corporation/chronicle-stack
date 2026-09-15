# Chronicle API Contract Skeleton

Status: Draft contract
Date: 2026-08-07
Roadmap: `../roadmaps/chronicle-daemon-api-roadmap.md`
ADR: `../adr/0101-resident-daemon-api-layer-boundary.md`

This directory defines the first Chronicle-native API contract skeleton and local daemon MVP.
It does not implement a hosted API, remote authorization, or cloud sync.

The executable contract models live in `src/chronicle/api/contracts.py`. The first
framework-neutral service adapter lives in `src/chronicle/services/api_adapter_service.py`.
They are validated by `tests/test_api_contracts.py` without opening network sockets.

Operational docs:

- `connector-prototypes.md`
- `agent-runtime-contract.md`
- `cloud-authority-model.md`
- `cloud-federation-boundary.md`
- `compatibility-policy.md`
- `../releases/operations/daemon-api-operator-runbook.md`
- `../releases/readiness/daemon-api-readiness.md`
- `../security/daemon-api-security-review.md`

## Minimum Surface

| Endpoint | Request model | Initial semantics |
|---|---|---|
| `POST /events` | `EventWriteRequest` | Structured Chronicle event write through Core validation |
| `GET /context` | `ContextQueryRequest` | Boundary-aware read model, not unrestricted memory export |
| `POST /diffs` | `DiffWriteRequest` | RDE diff registration mapped to artifact/version lineage |
| `GET /timeline` | `TimelineQueryRequest` | Time-ordered derived view over JSONL-backed records |
| `POST /assertions` | `AssertionWriteRequest` | Claims, evidence, caveats, unknowns, and verification status |
| `GET /boundaries` | `BoundariesQueryRequest` | Advisory boundary rules, not access-control proof |

## Contract Rules

- `schema_version` is `chronicle-api/v0.1-draft`.
- Write requests require an idempotency key.
- Write requests require API-origin metadata: source tool, actor id, and actor kind.
- Write requests default to `dry_run=true` and `review_status=needs_review`.
- `POST /events` supports committed writes through Core services when `dry_run=false`.
- `POST /assertions` supports committed writes as reviewable Chronicle Objects when
  `dry_run=false`.
- `POST /diffs` supports committed writes through the RDE service when `dry_run=false`.
- Read requests stay boundary-aware and default to not returning full payloads.
- `GET /health` is liveness-only and returns `{"status":"ok"}` without daemon metadata or
  credentials.
- The loopback HTTP transport requires an exact local `Host` authority and rejects every request
  carrying an `Origin` header before route logic.
- API responses are access surfaces, not proof of truth, permission, identity, or model
  correctness.
- Generic unstructured log ingestion is not the normal path. API writes must map to Chronicle
  events, RDE diffs, or reviewable assertions.

## Error Taxonomy

The draft contract/service error codes are:

- `validation_error`
- `unauthorized`
- `forbidden`
- `conflict`
- `duplicate`
- `boundary_warning`
- `partial_persistence_blocked`

The loopback HTTP transport can reject a request before contract routing with:

- `invalid_host` (HTTP transport boundary)
- `origin_not_allowed` (HTTP transport boundary)

## Idempotency

Write endpoints require an `idempotency_key` at contract level. `POST /events` stores
idempotency metadata inside the Chronicle Event payload and returns the existing event on
duplicate replay. Later write endpoints must define equivalent duplicate and conflict behavior
before committed persistence is enabled.

## Phase Status

| Roadmap phase | Status | Evidence |
|---|---|---|
| Phase 0: Manifest and Boundary Lock | In progress | ADR-0101 accepted, roadmap accepted, threat model and connector priority drafts added |
| Phase 1: Contract Skeleton | In progress | Contract models and schema tests added |
| Phase 2: Service Adapter Layer | In progress | Dry-run write previews, read adapters, and `POST /events` commit adapter added |
| Phase 3: Loopback Daemon MVP | In progress | `chronicle daemon start` adds explicit loopback endpoints with session-token auth |
| Phase 4: Write Endpoint MVP | In progress | `POST /events`, `POST /diffs`, and `POST /assertions` commit with idempotency and audit |
| Phase 5: Connector Prototypes | In progress | Local connector prototype simulator added without external app integration |
| Phase 6: Sustain and Release Readiness | In progress | Daemon smoke command, operator runbook, readiness, compatibility, and security review drafts added |
| Phase 7: Agent Runtime / Kazane Integration Planning | In progress | Draft executable agent runtime contract and CLI inspection added |
| Phase 8: Chronicle Cloud Planning | In progress | Draft executable cloud authority model and CLI inspection added |
| Phase 9: Federation / Cloud Relationship Review | In progress | Draft executable Cloud/Federation boundary matrix and CLI inspection added |

## Non-goals

- No hosted API.
- No hidden daemon or autostart.
- No second primary database.
- No arbitrary memory dump endpoint.
- No remote multi-user authorization claim.
- No remote write surface; this remains loopback-local and session-token gated.
- No production connector implementation; Phase 5 uses a local simulator only.
