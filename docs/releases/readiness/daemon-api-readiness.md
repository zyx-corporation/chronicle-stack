# Chronicle Daemon API Readiness

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 6

## Checks

- [ ] `chronicle doctor`
- [ ] `chronicle daemon smoke --json`
- [ ] `ruff check src/ tests/`
- [ ] `pytest`
- [ ] Manual foreground start with `chronicle daemon start`
- [ ] Manual `GET /health`
- [ ] Confirm `GET /health` returns exactly `{"status":"ok"}` with no token, root, or endpoint metadata
- [ ] Accept only `127.0.0.1:<bound-port>` and `localhost:<bound-port>` Host headers
- [ ] Reject foreign, missing, duplicated, and wrong-port Host headers before route logic
- [ ] Reject Origin-bearing requests for every HTTP method before authentication or persistence
- [ ] Token-required read check for `/context`, `/timeline`, and `/boundaries`
- [ ] Token-required write check for `/events`, `/diffs`, and `/assertions`
- [ ] Backup/restore reminder completed before committed write validation

## Required Evidence

- Daemon startup metadata includes root, bind scope, auth mode, auth header, token file path (never a token value),
  endpoint list, and primary record path.
- Smoke report shows `server_started=false` and `external_runtime=false`.
- Committed writes include API metadata and `api_write` audit events.
- Duplicate idempotency keys do not append duplicate Chronicle events.
- Rejected Host/Origin requests do not append Chronicle events or audit records.
- Public copy does not imply hosted API, Chronicle Cloud, remote access, or cloud AI memory.

## Not Ready If

- Host binding accepts non-loopback addresses.
- `/health` exposes startup metadata, paths, endpoint inventory, or credentials.
- Any request accepts an untrusted, missing, duplicated, or wrong-port Host header.
- Any Origin-bearing request reaches daemon route logic.
- Any endpoint works remotely without a later ADR.
- Write endpoints bypass Core services or omit audit metadata.
- API origin/capability metadata is treated as authorization without service-level enforcement.
- Connector prototype output is described as a production connector.
- API responses are described as truth proof, identity proof, or permission grants.

## CY-1 credential and method gates

- Require all-method Host/Origin validation before dispatch; unsupported methods return 405.
- Require private exclusive 0600 token file creation and no argv/stdout/metadata credentials.
- Verify normal shutdown and SIGTERM cleanup; document abrupt-termination stale-file recovery.
- Startup metadata is `chronicle-daemon-startup/v2`; API payload schema is unchanged.
- Broader release remains subject to the unresolved service authorization and scope gates.
