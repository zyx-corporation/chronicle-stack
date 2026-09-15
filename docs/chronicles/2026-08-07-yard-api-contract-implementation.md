# 2026-08-07 Yard and API Contract Implementation

Status: Active maintenance entry

## Context

The roadmap next cut called for completing CY-0, starting CY-1 and CY-2, and deferring daemon
implementation until an API contract skeleton exists.

## Changes

- Added a Yard product map and product-family responsibility matrix.
- Added Stack handoff contract review notes for downstream CSG-RAG and chronicle-external-query
  alignment.
- Added a Chronicle API contract skeleton and Phase 0 drafts for threat model and connector
  priority.
- Added transport-free Pydantic API contract models under `src/chronicle/api/`.
- Added contract tests that validate the six minimum API endpoints without opening sockets.
- Added a framework-neutral API adapter service for dry-run write previews and read adapters.
- Added an explicit loopback-local read-only daemon MVP with health, context, timeline, and
  boundaries endpoints.
- Added the first committed API write path for `POST /events` with idempotency detection and
  audit insertion.
- Added `POST /assertions` persistence as reviewable Chronicle Objects with idempotency and
  audit insertion.
- Added `POST /diffs` persistence through the RDE service with idempotency and audit insertion.
- Added a local connector prototype simulator for Obsidian, Git, browser, agent, and business
  fact shapes without contacting external applications.
- Added `chronicle daemon smoke` plus daemon/API operator runbook, readiness, compatibility, and
  security review drafts.
- Added a draft executable agent runtime contract and CLI inspection surface for
  Kazane-compatible integration planning.
- Added a draft executable Chronicle Cloud authority model and CLI inspection surface without
  cloud implementation.
- Added a draft executable Cloud/Federation boundary matrix and CLI inspection surface.

## RDE Checkpoint

### Preserved

- Chronicle Stack remains the local-first preservation mechanism.
- JSONL remains the primary record.
- API and Yard language remain planned or contract-level surfaces.

### Transformed

- Yard moved from naming note plus roadmap lane into a documentation entrypoint.
- API Phase 1 moved from roadmap text into executable contract models.
- API Phase 2 started as a non-HTTP service adapter that blocks committed writes.
- API Phase 3 started with a read-only loopback daemon; write endpoints remain disabled.
- API Phase 4 started with all three write endpoints: events, diffs, and assertions.
- API Phase 5 started with a local simulator that keeps `production_surface=false`.
- API Phase 6 started with smoke validation and operator-facing readiness docs.
- API Phase 7 started with contract models for capability scopes and agent-origin metadata.
- API Phase 8 started with local/cloud authority labels and cloud-AI-memory prohibition encoded
  as contract fields.
- API Phase 9 started with Cloud/Federation separation encoded as a boundary matrix.

### Supplemented

- Idempotency and origin metadata are required at write-contract level.
- Connector priority is now explicit and bounded.

### Unresolved

- Service hardening for validation, conflict details, and operator-facing failure docs.
- Real external connector implementations and connector-specific T-RDE promotion reviews.
- Deeper daemon hardening, release evidence capture, and follow-up issue creation for remote or
  hosted scenarios.
- Real Kazane or agent-runtime client implementation.
- Real Chronicle Cloud sync/share/audit/permission/backup implementation and conflict model.
- ADR and implementation for any future Cloud-to-Federation bridge.
- Operator runbook and daemon release readiness.
- Cross-repository links to CSG-RAG and chronicle-external-query contract docs.

### Deviation Risks

- Treating draft API contracts as an available daemon.
- Allowing connector prototypes to become production write paths without T-RDE review.
