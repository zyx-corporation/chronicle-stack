# 2026-08-27 - Daemon Request Boundary Hotfix

Status: Validated hotfix; follow-up security issues required

## Chronicle Entry

- Date: 2026-08-27
- Task: Close credential disclosure and browser request paths at the loopback daemon boundary.
- Branch: `codex/hotfix-daemon-request-boundary`
- Baseline: The unauthenticated `GET /health` response reused daemon startup metadata and exposed
  the session token, Chronicle root, primary-record path, and endpoint inventory. The handler did
  not validate `Host` or reject browser `Origin` headers.
- Changed: `GET /health` now returns only `{"status":"ok"}`. GET and POST handling now requires
  exactly one `Host` equal to `127.0.0.1:<bound-port>` or `localhost:<bound-port>`, rejects every
  Origin-bearing request before routing, and compares the session token in constant time.
- Preserved: Explicit foreground execution, loopback binding, the operator-visible startup token,
  Core-mediated writes, and `.chronicle/chronicle.jsonl` as the authoritative append-only record.
- Why: Loopback reachability is not caller authentication. An attacker-controlled browser origin
  or another local process must not obtain the only credential protecting Chronicle reads and
  writes.
- Next: Re-audit this hotfix through a normal MDES Issue; add transport-neutral authorization and
  resource-scope enforcement before MCP or connector release; separately audit the browser UI's
  Host, Origin, and CSRF boundary.
- Re-evaluate when: A browser client, a new transport, a non-loopback bind, per-client principals,
  or remotely delegated capabilities are proposed.

## Problem Statement

The daemon treated loopback binding as a sufficient request boundary while publishing its bearer
credential from an unauthenticated endpoint. Because the same credential authorized all current
read and write routes, credential disclosure collapsed the entire daemon authentication boundary.

## Acceptance Criteria

- Health is an exact, non-sensitive liveness response.
- Foreign, missing, duplicate, and wrong-port Host authorities fail before routing.
- Any Origin-bearing GET or POST fails before authentication, body parsing, or service execution.
- A rejected write leaves the JSONL primary record unchanged.
- Valid non-browser clients retain the existing authenticated read/write behavior.

## Failure Note

- What happened: Startup metadata, including `session_token`, was returned by unauthenticated
  `GET /health`.
- Why it happened: One metadata object was reused for operator startup output and remote health
  output, and loopback binding was mistaken for proof that the caller was trusted. Negative tests
  checked neither response secrecy nor hostile request headers.
- What changes next time: Separate operator-only metadata from network liveness contracts, model
  request authenticity independently from service authorization, and add negative security tests
  before enabling a write-capable local HTTP surface.
- What to check again: Other loopback HTTP servers, especially the browser UI, for token exposure,
  unscoped reads, Host validation, same-origin enforcement, and CSRF resistance.

## Full T-RDE

### Target

- Emergency security repair for the Chronicle daemon/API Phase 3-6 work.
- Governing decisions: ADR-0100, ADR-0101, and ADR-0104.

### Original Manifest Intent

Chronicle must remain explicit, local-first, reconstructable, and safe to restore. Security changes
must preserve authority boundaries, fail before partial persistence, carry tests, and expose
unresolved deviations instead of converting a prototype assumption into a release claim.

### Original Design Intent

The daemon is a thin, explicitly started loopback transport over Chronicle services. It must not
become a hidden runtime or a second source of truth, and its session token is intended to gate the
available read and write endpoints.

### Preserved

- The daemon remains opt-in, foreground, and loopback-bound.
- Startup metadata remains available to the operator who explicitly launches the daemon.
- Accepted writes continue through Chronicle services and append to the JSONL primary record.
- HTTP-specific request checks remain outside Chronicle record semantics.

### Transformed

- Health changes from startup-metadata disclosure to a liveness-only contract.
- Loopback changes from an assumed trust proof to one input within a request-authenticity boundary.
- Token comparison changes from ordinary equality to constant-time comparison.

### Supplemented

- Exact request-authority validation against the server's actual bound port.
- Fail-closed rejection of browser Origin headers.
- Negative socket tests for hostile Host values, Origin-bearing reads and writes, and non-mutation.
- A durable distinction between transport authentication and reusable service authorization.

### Unresolved

- The API adapter and Core do not yet enforce endpoint capabilities, caller-resource scopes, or a
  binding between authenticated principal and caller-supplied origin metadata.
- Current context, timeline, and boundary selectors are not proven authorization filters.
- The browser UI has a different but related DNS-rebinding surface; it needs exact Host plus
  browser-compatible same-origin and CSRF rules rather than the daemon's blanket Origin rejection.
- Actor and assertion-origin fields remain semantically fragmented across current models.

### Deviation Risks

- Describing the daemon as authorized merely because it is token-authenticated.
- Treating caller-supplied capability or origin metadata as an enforceable grant or identity proof.
- Weakening Origin rejection to support a browser without a separate browser security design.
- Copying authorization rules into MCP rather than sharing one transport-neutral decision point.

### Test Mapping

- Exact health response: daemon socket integration test.
- Accepted canonical authorities: existing `127.0.0.1` request plus explicit `localhost` request.
- Host rejection: foreign, missing, duplicate, and wrong-port cases.
- Origin rejection: unauthenticated health, authenticated read, and authenticated write cases.
- Persistence safety: JSONL record count is unchanged after the rejected write.
- Regression behavior: existing daemon read, write, idempotency, assertion, and RDE paths remain in
  the daemon integration suite.

### CI Result

- Targeted daemon suite: `7 passed`.
- Repository lint: `ruff check src/ tests/` passed.
- Full local suite: `556 passed`.
- Primary local CI mirror: the Python 3.11 `act pull_request` job passed Ruff, all 556 tests,
  and the UI smoke workflow.

### Sustain Impact

The operator runbook, threat model, security review, compatibility policy, readiness checklist, and
ADR index now carry the request-boundary contract. A normal post-hotfix security Issue remains
required for shared authorization and UI review.

### Next Update Policy

Before MCP or production connector work, define a caller context and enforce endpoint and resource
capabilities once below all transports. Before any browser access to daemon functions, record a
separate browser-origin design. Preserve this validation evidence and refresh it whenever the
request boundary or daemon client contract changes.

### Judgment

`Accept with Follow-up Issue`. The credential disclosure and specified HTTP request paths are
closed and validated. This judgment does not promote the daemon to release-ready: shared
authorization, selector enforcement, and the separate UI request boundary remain open.
