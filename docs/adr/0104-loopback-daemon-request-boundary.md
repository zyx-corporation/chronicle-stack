# ADR-0104: Loopback Daemon Request Boundary

Status: Accepted  
Date: 2026-08-27  
Scope: Chronicle Stack loopback daemon request validation and credential disclosure boundary  
Related: ADR-0016, ADR-0101, `docs/api/threat-model.md`,
`docs/security/daemon-api-security-review.md`

## Context

The first daemon MVP exposed `GET /health` without authentication and returned the complete
startup metadata object. That object included the daemon session token, Chronicle root, primary
record path, and endpoint inventory. A caller that could reach the loopback socket could therefore
obtain the credential intended to protect the read and write routes.

Loopback binding alone does not establish caller trust. Other local processes can reach loopback,
and a browser page can attempt DNS-rebinding or browser-originated requests against a loopback
service. A local HTTP daemon must validate the request authority before routing and must not place
credentials in an unauthenticated health response.

## Decision

The Chronicle daemon adopts the following request boundary:

1. `GET /health` returns exactly `{"status":"ok"}` and no startup metadata, paths, endpoint
   inventory, or credentials.
2. Every GET and POST request is rejected before route, authentication, or business logic unless
   it has exactly one `Host` header equal to `127.0.0.1:<bound-port>` or
   `localhost:<bound-port>`.
3. Every request carrying an `Origin` header is rejected. The daemon is a non-browser transport;
   browser access is not an accepted client mode.
4. Session-token comparison remains a transport authentication concern and uses constant-time
   comparison. It is not treated as Core authorization or identity proof.
5. Future HTTP and MCP transports must share transport-neutral authorization and capability
   policy below their transport adapters. Host, Origin, and transport credential validation remain
   transport-specific preconditions and must not be moved into Chronicle record semantics.

The current API adapter does not yet implement that transport-neutral authorization policy.
Origin and capability fields currently record provenance and requested scope; they do not grant
authority.

## Alternatives

### Rely on loopback binding and the session token

Rejected. The vulnerable health endpoint disclosed the token to any caller that reached the
socket, and loopback does not distinguish the intended client from other local processes or a
DNS-rebound browser origin.

### Allow browser origins through CORS

Rejected for the daemon. A browser-facing surface requires a separately designed same-origin,
CSRF, credential-delivery, and content-security boundary. Relaxing CORS would widen the daemon
without providing that design.

### Move Host, Origin, and token checks into Chronicle Core

Rejected. These checks describe HTTP request authenticity, not whether a Chronicle operation is
authorized. Core authorization must be reusable by HTTP, MCP, CLI, and future transports without
depending on HTTP headers.

## Consequences

### Positive

- Unauthenticated health checks cannot disclose the session token or Chronicle paths.
- DNS-rebinding requests retain the attacker-controlled `Host` value and fail before route logic.
- Browser fetches that carry `Origin` fail closed even when another condition is misconfigured.
- The design preserves one future authorization policy while allowing each transport to enforce
  its own request-authenticity boundary.

### Negative / Cost

- Clients must use one of two exact loopback authorities and include the active port.
- Browser-based clients cannot call the daemon directly.
- Session-token authentication still represents one local daemon session, not per-operation or
  multi-user authorization.
- A separate authorization/capability implementation is still required before MCP or broader
  connector release readiness.

## Verification Contract

Tests must cover:

- the exact minimal health body;
- accepted `127.0.0.1:<port>` and `localhost:<port>` authorities;
- rejected foreign, missing, duplicated, and wrong-port `Host` headers;
- rejected Origin-bearing GET and POST requests;
- no Chronicle primary-record mutation after a rejected request.

## T-RDE Notes

### Preserved

- Explicit foreground execution, loopback binding, session-token authentication, and JSONL
  primary-record authority.

### Transformed

- Loopback changes from the sole network assumption into one part of a request-authenticity
  boundary.
- Health changes from an operational metadata dump into a liveness-only response.

### Supplemented

- Host allowlisting, Origin rejection, constant-time token comparison, and explicit separation of
  transport authentication from Core authorization.

### Unresolved

- Transport-neutral Core authorization and capability enforcement.
- A separate DNS-rebinding and request-origin audit for the browser-based local UI.

### Deviation Risks

- Treating these HTTP guards as complete local-process isolation.
- Reusing the daemon as a browser endpoint by weakening Origin rejection.
- Duplicating authorization policy independently in future MCP and HTTP transports.

