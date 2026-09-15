# 2026-08-28 - Browser UI Session Bootstrap Boundary

## Chronicle Entry

- Date: 2026-08-28
- Task: Close the P0 browser request and credential-delivery boundary for `chronicle ui`.
- Baseline: The browser shell could not be treated as a trusted credential channel, and loopback
  binding alone did not distinguish the intended browser from other local or browser-originated
  callers.
- Changed: Recorded ADR-0106; made `--open` the supported one-time fragment-bootstrap path;
  documented a data-free locked public shell, host-only cookie sessions, independent mutation
  tokens, exact Host/Origin validation, no CORS, OPTIONS rejection, and pre-persistence failure
  ordering across the operator references.
- Preserved: Foreground loopback operation, read-only default mode, explicit write enablement,
  existing reviewer/mutation semantics, CLI recovery, and JSONL authority.
- Why: Prevent unauthenticated Chronicle-derived reads, successful DNS-rebinding or cross-origin
  access and mutation, and one leaked credential from collapsing both read-session and mutation
  gates.
- Evidence: The final implementation passed 51 focused UI server tests, 559 full-suite tests, and
  Ruff for `src/` and `tests/`. Tests include one-time and expired bootstrap, sensitive-GET cookie
  gates, exact Host/Origin checks, no CORS, OPTIONS
  rejection, credential separation, and unchanged JSONL bytes after rejected writes.
- Next: Evaluate Unix-domain sockets and a browser credential handoff that avoids a
  fragment-bearing `webbrowser` launch URL as defense in depth.
- Re-evaluate when: The UI moves beyond plain loopback HTTP, adds another browser transport or
  POST route, claims shared-machine use, or changes session/credential lifetime.

## Failure Note

- What happened: No documentation-stage failure was observed.
- Why it happened: Not applicable.
- What changes next time: Keep browser request-boundary tests adjacent to every new route and avoid
  treating a manually opened base URL as an authenticated session.
- What to check again: Startup output/metadata/HTML secrecy, fragment removal, cookie attributes,
  rejection order, and JSONL byte invariance.
