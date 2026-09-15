# Chronicle Daemon API Security Review

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 6

## Scope

This review covers the explicit local daemon and API contract surface:

- loopback-only bind validation;
- session-token gated read/write endpoints;
- framework-neutral API adapter;
- connector prototype simulator;
- audit insertion for committed API writes.

## Preserved Boundaries

- `.chronicle/chronicle.jsonl` remains the primary record.
- The daemon is explicit foreground execution, not hidden autostart.
- `GET /health` is the only unauthenticated endpoint.
- `GET /health` returns only `{"status":"ok"}` and never returns startup metadata or credentials.
- Every request requires exactly one `Host` header for `127.0.0.1:<bound-port>` or
  `localhost:<bound-port>`.
- Every request carrying an `Origin` header is rejected before route logic.
- Read/write API endpoints require `X-Chronicle-Daemon-Token`.
- Committed writes pass through Core services.
- Connector prototypes do not contact external applications.

## Residual Risks

| Risk | Current mitigation | Follow-up |
|---|---|---|
| Local token disclosure on shared machines | Generated token is stored only in an exclusive 0600 file; no argv/startup/health disclosure | Same-UID access and abrupt-termination stale files remain outside the guarantee |
| No full RBAC/ABAC | Scope is local session token, not multi-user auth | Defer remote/multi-user claims |
| No transport-neutral API authorization | Origin and capability metadata are descriptive, not grants | Add one service-level authorization policy before MCP or connector release |
| Read selectors are not yet an authorization boundary | Session token currently grants the daemon's full local read capability | Validate selector enforcement and content-scope policy before release |
| Request validation still broad for event payloads | Structured contracts require origin/idempotency and audit | Add endpoint-specific payload policy if needed |
| Connector simulator mistaken for production | `production_surface=false` and docs warnings | Keep prototypes out of public integration claims |
| Prompt injection in captured text | Stored as data; no automatic execution | Add connector-specific sanitizer checks before production connectors |
| Browser-based local UI has a separate request boundary | Daemon rejects all Origin-bearing requests; UI cannot use that rule unchanged | ADR-0106 now gates UI reads and writes with bootstrap/cookie/mutation credentials |

## Security Non-Claims

- No hosted API.
- No remote authorization.
- No cloud IAM.
- No tenant isolation.
- No proof of truth or identity.
- No prompt-injection prevention guarantee.
