# Chronicle Stack Local Operator Runbook

Related: `../../local-deployment-curl.md`, `../../doctor.md`,
`../../adr/0106-browser-ui-session-bootstrap-request-boundary.md`,
`local-backup-and-restore.md`, `local-web-ui-operator-validation-v1.0.md`

Status: current local operator runbook  
Scope: single-operator local deployment and day-to-day operation

## Purpose

This runbook captures the minimum repeatable workflow for operating Chronicle Stack locally without relying on chat memory.

It is for the current product boundary:

- local-first
- single-operator
- local filesystem as the source of truth
- read-only local web UI by default
- explicit foreground commands only
- browser data access only after an explicit `--open` one-time bootstrap

## Boundary

This runbook does not certify:

- hosted deployment
- multi-user concurrency safety
- same-UID process isolation or shared-machine safety
- default-on GUI mutation
- external runtime correctness
- security certification
- legal or governance approval

## 1. Install Or Update

Inspect-first local install:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh -o /tmp/chronicle-install-local.sh
less /tmp/chronicle-install-local.sh
bash /tmp/chronicle-install-local.sh
```

Post-install verification:

```bash
chronicle --version
chronicle --help
chronicle doctor --help
chronicle ui-smoke --json
```

## 2. Create Or Open A Chronicle Root

New local Chronicle:

```bash
mkdir -p /path/to/project
cd /path/to/project
chronicle init --title "Local Chronicle"
```

Existing Chronicle:

```bash
cd /path/to/project
test -d .chronicle
chronicle doctor
```

## 3. Start-Of-Day Checklist

Run from the Chronicle root:

```bash
chronicle doctor
chronicle doctor --json
chronicle ui-smoke --json
```

Expect:

- `doctor` is `ok` or only expected `warning`
- `ui-smoke --json` reports `passed: true`
- no command implies hidden background runtime activity

If `doctor` reports missing derived indexes:

```bash
chronicle index rebuild
chronicle doctor --json
```

## 4. Backup Before Meaningful Work

Create a local backup of `.chronicle/`:

```bash
chronicle-backup-local
```

Custom output directory:

```bash
chronicle-backup-local "$PWD" "$HOME/.chronicle-backups"
```

This backup is local, file-based, and read-only with respect to the source Chronicle root.

If you are operating from a source checkout instead of an installed CLI environment, `scripts/backup-local.sh` remains equivalent.

## 5. Routine Operation

Common local commands:

```bash
chronicle record --type user_input --actor user --summary "Operator session started"
chronicle add-context --title "Session Context" --summary "Local operating context" --scope session --visibility private
chronicle review queue
chronicle graph summary
chronicle ui --open
```

Use `chronicle ui --open` for browser inspection. Treat it as:

- foreground only
- loopback-local only
- read-only by default
- descriptive, not authoritative over primary records
- single-operator only; not safe against a hostile process running as the same user

The command prints a non-secret base URL and startup metadata, then passes a short-lived one-time
fragment URL directly to the default browser. Confirm that `#chronicle-bootstrap=...` disappears
from the address bar immediately. The bootstrap secret must not appear in terminal output or page
HTML.

Running without `--open` is intentionally locked. Manually opening the printed base URL shows only
a credential-, Chronicle-title-, root-, and data-free shell. If browser opening fails, the fragment
persists, or the 60-second bootstrap expires, stop the foreground server and start it again with
`chronicle ui --open`; do not try to recover or publish the internal bootstrap URL.

The session cookie is host-only, `HttpOnly`, and `SameSite=Strict`. It does not grant mutation by
itself: enabled writes also require a separately generated mutation header token, mutation session,
and one-use request id. Because the UI uses plain local `http://`, the cookie intentionally does not
set `Secure` and therefore cannot use the `__Host-` prefix.

The fragment-bearing URL passes through Python `webbrowser` and OS/browser opener plumbing. The
one-time TTL and immediate fragment removal reduce, but do not eliminate, this local exposure.

## 6. Pre-Change Safety Checks

Before bulk edits, imports, or review actions:

```bash
chronicle doctor --json
chronicle ui-smoke --json
chronicle-backup-local
```

If you need browser-side review-route validation, use:

`docs/releases/operations/local-web-ui-operator-validation-v1.0.md`

## 7. Shutdown / End-Of-Day

Close the UI tab and stop the foreground `chronicle ui` process with Ctrl-C before the minimum
close-out:

```bash
chronicle doctor --json
chronicle-backup-local
```

Recommended operator note:

```bash
chronicle record --type user_input --actor user --summary "Operator session closed"
```

## 8. Recovery Shortcut

Restore the latest known-good backup when local Chronicle state needs rollback:

```bash
chronicle-restore-local /path/to/chronicle-backup-....tar.gz
chronicle doctor --json
chronicle ui-smoke --json
```

## 9. Escalate Instead Of Assuming

Stop and investigate if any of these happen:

- `chronicle doctor` returns `error`
- `chronicle ui-smoke --json` reports `passed: false`
- `.chronicle/chronicle.jsonl` is missing or unreadable
- derived views disagree with primary record expectations
- write-route behavior appears enabled unexpectedly
- an unauthenticated shell shows a Chronicle title, root, record data, or credential
- `#chronicle-bootstrap=...` remains in the browser address bar
- a sensitive GET succeeds without the session cookie
- an OPTIONS response or any UI response enables CORS

## 10. Related Guides

- install/update: `../../local-deployment-curl.md`
- doctor semantics: `../../doctor.md`
- backup/restore: `local-backup-and-restore.md`
- UI walkthrough: `local-web-ui-operator-validation-v1.0.md`
