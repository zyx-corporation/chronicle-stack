# Chronicle API Threat Model Draft

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 0

This draft frames the first local API risks before any daemon implementation.

## Assets

- `.chronicle/chronicle.jsonl` primary record.
- Artifact files and version history.
- Context, boundary, lifecycle, classification, audit, and RDE metadata.
- Operator expectations around local-first control and explicit execution.

## Trust Boundaries

| Boundary | Risk |
|---|---|
| Tool to API contract | Tool submits generic logs or unverifiable claims as Chronicle records |
| API contract to Core service | Partial writes bypass validation or audit insertion |
| Read response to external tool | Boundary-aware context becomes unrestricted memory export |
| Local daemon bind | A local-only service accidentally becomes remotely reachable |
| Browser or DNS-rebound request to local daemon | Attacker-controlled page reaches loopback with an untrusted Host or Origin |
| Agent runtime integration | AI proposal, human judgment, and business-system fact blur together |

## Required Mitigations Before Write Commit

- Idempotency handling for write endpoints.
- Origin metadata for source tool, actor, and session.
- Dry-run and preview responses before persistence.
- Validation failure before partial persistence.
- Audit insertion for accepted writes.
- Boundary warnings for external context disclosure and AI interpretation.
- Explicit local bind and auth/session rules before daemon startup exists. The first daemon MVP
  uses loopback-only binding and `X-Chronicle-Daemon-Token` for read endpoints.
- Liveness-only health response with no startup metadata or credential disclosure.
- Exact loopback `Host` allowlist and rejection of every Origin-bearing request before route logic.

## Out of Scope For The First Contract

- Remote access.
- Hosted API.
- Tenant isolation.
- Cloud IAM.
- Complete RBAC/ABAC.
- Generic log ingestion.
- Prompt-injection prevention guarantees.
