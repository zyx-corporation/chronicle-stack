# ADR-0106: Browser UI Session Bootstrap and Request Boundary

Status: Accepted
Date: 2026-08-28
Scope: `chronicle ui` browser session establishment, request authenticity, and credential
confinement
Related: ADR-0016, ADR-0018, ADR-0021, ADR-0022, ADR-0023, ADR-0026, ADR-0028,
ADR-0104, `docs/v1.7-phase-h-ui-mutation-threat-model.md`

## Context

The loopback local UI is intentionally browser-facing and can expose Chronicle-derived reads and,
under explicit gates, review and workspace writes. Loopback binding does not identify the intended
browser. Other local processes can connect to the socket, and a hostile page can attempt a
browser-originated request or DNS-rebinding path to a loopback service.

The UI therefore needs a boundary different from the non-browser daemon in ADR-0104. The daemon
rejects every `Origin`; the UI must accept its own browser origin while preventing an unauthenticated
page from receiving Chronicle metadata or a reusable write credential. The previous HTML shell also
must not be a credential-delivery surface: a public root document can be fetched before a browser
session exists.

This decision concerns browser request authenticity and session credential delivery. It does not
turn local reviewer labels into identity proof, replace the mutation gates in ADR-0021 through
ADR-0028, or isolate the Chronicle from processes running as the same operating-system user.

## Decision

### Public shell and authenticated reads

`GET /` and `GET /index.html` are the only unauthenticated UI documents. They return a static shell
that contains no session or mutation credential, mutation session id, Chronicle title, Chronicle
root path, or Chronicle-derived record data. Generic application copy and client code are allowed;
the shell must not specialize itself with private Chronicle metadata.

Every other GET, including `GET /api/session`, all Chronicle-derived `/api/*` reads, and
`GET /review-console`, requires the UI session cookie. A GET may omit `Origin`, as normal browser
navigation does. If it carries `Origin`, the value must exactly match the accepted local authority.

Starting the server without `--open` does not deliver a credential. A browser that manually opens
the printed base URL receives the public shell and remains locked.

### One-time fragment bootstrap

Each server instance generates a random bootstrap secret. Its only supported delivery path is the
URL passed to the default browser when the operator starts `chronicle ui --open`:

```text
http://<local-authority>/#chronicle-bootstrap=<one-time-secret>
```

The bootstrap secret must not appear in startup metadata, `chronicle ui --json`, normal stdout or
stderr, served HTML, or Chronicle's process-startup arguments. It is not accepted as a CLI argument.
The fragment is not sent in the HTTP request for `/`; client code reads it, immediately removes the
fragment with `history.replaceState`, then exchanges it through same-origin
`POST /api/session/bootstrap`.

The exchange requires an exact local `Origin`. The secret is compared in constant time, expires
after a short TTL (currently 60 seconds), and may establish at most one session. Successful or
expired bootstrap state is retired server-side. Replay must fail.

If the fragment is absent, invalid, expired, or already consumed and no valid session cookie exists,
the shell remains locked and directs the operator to stop the server and restart with `--open`.

### Cookie session and independent mutation credential

A successful bootstrap issues `chronicle_ui_session` as a host-only cookie by omitting `Domain`.
The cookie has `Path=/`, `HttpOnly`, and `SameSite=Strict`.

`Secure` is deliberately not set because the accepted local UI transport is plain
`http://` loopback. Setting it would prevent the current HTTP origin from returning the cookie.
The current cookie also cannot use the `__Host-` prefix because that prefix requires `Secure`.
This omission is not permission to expose the UI over a non-loopback network. A future HTTPS
surface must revisit both attributes.

The cookie value and the mutation header token are separately generated credentials. The cookie
authorizes sensitive reads and is a prerequisite for non-bootstrap POSTs. After cookie
authentication, `GET /api/session` may return the distinct mutation token and mutation session id
to same-origin client memory. The client must not place them in HTML or `sessionStorage`.

### Host, Origin, POST, and preflight rules

Every supported GET, POST, and OPTIONS request must carry exactly one accepted `Host` header for
the actual bound port. The current accepted authorities are the configured loopback bind authority
and the local aliases `127.0.0.1` and `localhost`, each with that exact port. Foreign, missing,
duplicated, or wrong-port Host values fail before route handling.

Every POST and OPTIONS request must carry exactly one `Origin` equal to `http://` plus its validated
Host authority. Missing, duplicated, foreign, wrong-scheme, or wrong-port Origin values fail.

The bootstrap exchange is the sole POST exception to prior cookie authentication: it uses the
one-time fragment secret to create the cookie session. Every other POST requires both the exact
Origin and the UI session cookie. A write that is enabled additionally requires:

```text
X-Chronicle-UI-Mutation-Token
mutation_session_id
mutation_request_id
```

The mutation header token remains independent of the cookie. Mutation mode, workspace/review route,
reviewer, target-state, session-id, and one-use request-id checks continue to apply under their
existing ADRs.

The server does not enable CORS or return `Access-Control-Allow-*` headers. OPTIONS is not a
supported preflight surface: after Host and Origin validation it returns `405 Method Not Allowed`.

Request-boundary failures are ordered to minimize exposure and side effects. Host and Origin are
checked before path dispatch. The bootstrap branch then parses only its exchange body and validates
the one-time secret. Every non-bootstrap POST follows this order:

```text
exact Host
-> exact/present Origin when required
-> cookie session
-> route and mode gates
-> mutation header gate when enabled
-> request-body parsing
-> mutation session/request-id and domain validation
-> persistence
```

Thus a rejected foreign authority, foreign/missing Origin, missing session, disabled route, or
missing mutation header does not reach body parsing or Chronicle persistence. Error responses do
not add CORS permission.

### Security claim boundary

This contract reduces browser-originated cross-site request and credential-disclosure paths. It is
not a same-UID or shared-machine security boundary. A process running with the operator's user
permissions may inspect process/browser state, connect directly to loopback, or read and write the
local Chronicle files according to filesystem permissions. `shared_machine_safe` therefore remains
false.

The host-only cookie is scoped by host and path, not TCP port. A browser may therefore send it to
another local service using the same hostname on a different port. Independent random server
credentials prevent that cookie alone from authenticating to another Chronicle UI instance, but
operators must not treat host-only as port isolation.

A Unix-domain-socket transport with filesystem permissions is a follow-up defense-in-depth option.
It could narrow TCP/DNS-rebinding exposure and improve endpoint ownership, but it does not by itself
make hostile same-UID processes safe and is not part of the current HTTP contract.

### Residual browser-opener exposure

`--open` necessarily passes the fragment-bearing URL to Python's `webbrowser` opener and the
platform/browser launch integration. That handoff may expose the URL to browser launch plumbing,
diagnostics, history, extensions, or another local component before the page removes the fragment.
The fragment-not-in-HTTP property, short TTL, one-time exchange, and immediate removal reduce this
window; they do not eliminate it. A future native or socket-backed credential handoff should be
evaluated if this residual local exposure is unacceptable.

## Alternatives

### Embed a token or Chronicle metadata in the public shell

Rejected. Any unauthenticated reader of `/` would receive the credential or private metadata.

### Print or return the bootstrap URL in startup metadata

Rejected. Terminal logs, automation captures, and `--json` consumers are not credential channels.

### Treat loopback binding as authentication

Rejected. Loopback is reachable by unrelated local processes and is a target for browser-originated
requests and DNS rebinding.

### Reuse the mutation header token as the cookie value

Rejected. Read-session authentication and mutation authorization are separate gates. Credential
reuse would let disclosure or confusion at one gate collapse the other.

### Enable CORS for local convenience

Rejected. Cross-origin browser access is outside the accepted local UI client model.

### Set `Secure` or use a `__Host-` cookie on the current origin

Rejected for the current plain-HTTP origin because compliant browsers would not return it. HTTPS is
a separate transport decision, not a flag that can be added to this loopback server in isolation;
`__Host-` also requires `Secure`.

### Make Unix-domain sockets the P0 transport

Deferred. UDS remains useful defense in depth, but changing transport and browser integration would
widen the P0 change and still would not establish safety against same-UID processes.

## Consequences

### Positive

- The unauthenticated root cannot disclose Chronicle data or a reusable credential.
- Sensitive reads and the review console require a host-only browser session cookie.
- DNS-rebinding and cross-origin POST paths fail before route, body, or persistence work.
- Read-session compromise does not automatically satisfy the independent mutation-token gate.
- Manual base-URL navigation has a clear fail-closed state instead of silently receiving authority.

### Negative / Cost

- Operators must use `--open` to establish a new browser session.
- Bootstrap can fail when browser launch is delayed beyond the TTL, and retry requires a server
  restart.
- Plain HTTP prevents use of the `Secure` cookie attribute and `__Host-` prefix in the current
  design.
- Browser opener handoff retains a short-lived local URL exposure.
- The design does not protect against hostile same-UID processes or direct filesystem access.

## Verification Contract

Automated tests must cover:

- a credential-, title-, root-, and Chronicle-data-free public shell;
- no bootstrap secret in shell HTML or startup metadata;
- fragment removal before bootstrap exchange and no `sessionStorage` credential persistence;
- one-time and expired bootstrap rejection;
- host-only `HttpOnly; SameSite=Strict; Path=/` cookie issuance without `Secure` or `__Host-` on
  HTTP;
- distinct cookie and mutation-token values;
- cookie authentication for every sensitive GET and the review console;
- exact Host and Origin checks, including missing and duplicated headers;
- no CORS response headers and rejected OPTIONS;
- missing-cookie, foreign-Origin, missing-Origin, bad mutation-token/session, and duplicate request-id
  failures;
- unchanged primary JSONL bytes after pre-persistence request-boundary rejection;
- `--open` as the only browser bootstrap delivery path and a locked shell without it.

Operator validation must also inspect the address bar after launch, confirm that the fragment is
removed promptly, and confirm that startup output contains only the base URL and non-secret
metadata.

## Full T-RDE

### Preserved

- Foreground, loopback-only execution and JSONL primary-record authority.
- Read-only default mode, explicit mutation enablement, reviewer/session checks, and CLI recovery.
- Browser navigation state remains derived and non-authoritative.

### Transformed

- The public root changes from an implicit credential/data delivery surface into a generic locked
  shell.
- A UI session changes from an HTML-embedded mutation token to a one-time bootstrap followed by a
  host-only HttpOnly cookie.
- Loopback changes from a trust assumption into one input to Host, Origin, and session validation.

### Supplemented

- Short-lived one-time fragment bootstrap and immediate fragment removal.
- Cookie/mutation-token separation, exact request authority, no-CORS/OPTIONS behavior, and explicit
  rejection ordering.
- Same-UID/shared-machine non-claim and browser-opener residual-risk documentation.

### Unresolved

- UDS or another non-TCP local transport as defense in depth.
- A browser bootstrap mechanism that avoids handing a credential-bearing URL to `webbrowser` and
  platform launch integration.
- HTTPS and a corresponding `Secure` cookie contract, if a future product surface requires it.

### Deviation Risks

- Reintroducing Chronicle title, root, data, or credentials into the public shell.
- Treating the cookie as mutation authorization or reviewer identity proof.
- Adding a browser endpoint without the shared Host/Origin/session gates.
- Claiming shared-machine safety from loopback, SameSite, or UDS alone.
- Logging or returning the bootstrap URL for operator convenience.

### Judgment

`Accept for the foreground single-operator local UI boundary`. The implemented request and
bootstrap controls materially close the browser-originated P0 path, with same-UID isolation and the
browser-opener handoff explicitly left outside the claim.
