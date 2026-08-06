# 2026-08-07 - Chronicle Daemon and API Roadmap

## Chronicle Entry

- Date: 2026-08-07
- Task: Plan API implementation and create a roadmap from the Core / Daemon / API policy.
- Baseline: The repository already had no-hidden-daemon UI guidance, HTTP bridge auth guidance,
  local GraphRAG workspace ADRs, federation planning, and MDES procedure governance.
- Changed: Added ADR-0101 and the Chronicle Daemon/API roadmap, and linked the roadmap from the
  roadmap and documentation indexes.
- Preserved: Chronicle Core remains JSONL-authoritative and local-first; daemon/API is a future
  explicit access layer, not a second source of truth or hosted API claim.
- Why: Human-only manual recording is insufficient for an AI-era organizational memory system;
  tool-facing structured recording and context retrieval need a planned local API path.
- Next: Draft API schemas, threat model, auth/session boundary, idempotency contract, Kazane /
  agent capability contract, Chronicle Cloud authority model, and contract tests before
  implementation.
- Re-evaluate when: Implementation chooses a web framework, remote access is requested, or
  connector priority changes.

## RDE Notes

- Preserved: Core / local-first / context sovereignty / RDE / boundary rules.
- Transformed: "No daemon" is interpreted as "no hidden or premature daemon"; explicit resident
  service becomes a planned future layer. Chronicle Cloud is framed as a future service layer,
  not as a replacement source of truth.
- Added: Six conceptual endpoints, implementation phases, Agent Runtime / Kazane sequence,
  Chronicle Cloud planning, Federation boundary review, and public copy guidance.
- Unresolved: Framework, auth, schema versioning, connector order, daemon package location,
  Kazane capability scopes, Chronicle Cloud authority model, and sync conflict handling.
- Deviation risks: Generic logging drift, hosted-service drift, daemon state drift, cloud
  source-of-truth drift, agent-runtime authority drift, and public copy overstating availability.
