# Chronicle Daemon API Operator Runbook

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 6

This runbook covers the explicit local Chronicle API daemon. It does not cover hosted API,
remote access, Chronicle Cloud, or federation transport.

## Preflight

```bash
chronicle doctor
chronicle daemon smoke --json
ruff check src/ tests/
pytest
```

`chronicle daemon smoke` does not start a server, open a browser, call external runtimes, or
commit a primary record. It validates initialized root state, loopback metadata, endpoint
contract, read adapter behavior, and dry-run write behavior.

## Start

```bash
chronicle daemon start --host 127.0.0.1 --port 8776
```

The daemon creates `<root>/.chronicle/daemon.token` with mode 0600 and prints only its path.
Use `--token-file /private/directory/new.token` to choose another new output file. Existing files,
symlinks and non-0600 creation are rejected; files are never reused or overwritten. The removed
`--session-token` option must not be used. `--json` returns non-secret metadata only and does not
start the server or create a credential.

Clients read the file into process memory and send its value in the header below. Do not expand
its contents into shell commands, process arguments, logs, or copied diagnostic output.
Read and write endpoints require:

```text
X-Chronicle-Daemon-Token: <session-token>
```

Clients must send exactly one of these authorities, using the active daemon port:

```text
Host: 127.0.0.1:8776
Host: localhost:8776
```

Normal non-browser HTTP clients generate this header from the request URL. The daemon rejects all
requests carrying an `Origin` header and is not a browser/CORS endpoint.

## Endpoints

| Endpoint | Status | Notes |
|---|---|---|
| `GET /health` | Available without token | Returns only `{"status":"ok"}` |
| `GET /context` | Token required | Boundary-aware context read |
| `GET /timeline` | Token required | Derived timeline read |
| `GET /boundaries` | Token required | Advisory boundary rules |
| `POST /events` | Token required | Core Event write with idempotency and audit |
| `POST /diffs` | Token required | RDE write with idempotency and audit |
| `POST /assertions` | Token required | Reviewable Chronicle Object assertion write |

## Stop

Use `Ctrl-C` in the foreground process. The daemon has no autostart path and should not be run
as a background sync service without a later ADR. Normal shutdown, Ctrl-C, SIGTERM and startup
failures remove the newly created token file. SIGKILL/power loss can leave a stale file. Verify the
old daemon has stopped before manually removing a stale credential. Cleanup never deletes a
replacement file. These permissions do not isolate hostile processes running as the same user.

## Backup / Restore

Before using committed write endpoints in an operator validation session:

```bash
chronicle-backup-local
```

Restore behavior follows `local-backup-and-restore.md`. The daemon writes through the same
JSONL-backed Core services as CLI commands, so restore remains file-level and local-first.

## Failure Handling

- `401 unauthorized`: missing or incorrect `X-Chronicle-Daemon-Token`.
- `403 origin_not_allowed`: request carried an `Origin` header and was rejected before route logic.
- `421 invalid_host`: request Host was missing, duplicated, foreign, or used the wrong port.
- `400 validation_error`: request body failed API contract validation or service validation.
- `405 method_not_allowed`: unsupported HTTP method, including OPTIONS, after Host/Origin checks;
  `Allow: GET, POST`. No CORS headers are emitted.
- `405 write_endpoint_not_implemented`: endpoint is outside the local daemon MVP.
- Duplicate idempotency keys return the existing event/RDE/assertion reference when possible.

## Boundaries

- Loopback-only.
- Session-token gated.
- Exact Host authority required.
- Browser Origin requests rejected.
- No hosted API.
- No remote multi-user authorization claim.
- No cloud sync.
- No external connector runtime.
- Chronicle JSONL remains authoritative.
