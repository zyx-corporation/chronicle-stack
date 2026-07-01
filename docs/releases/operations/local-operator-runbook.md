# Chronicle Stack Local Operator Runbook

Related: `../../local-deployment-curl.md`, `../../doctor.md`, `local-backup-and-restore.md`, `local-web-ui-operator-validation-v1.0.md`

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

## Boundary

This runbook does not certify:

- hosted deployment
- multi-user concurrency safety
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
scripts/backup-local.sh
```

Custom output directory:

```bash
scripts/backup-local.sh "$PWD" "$HOME/.chronicle-backups"
```

This backup is local, file-based, and read-only with respect to the source Chronicle root.

## 5. Routine Operation

Common local commands:

```bash
chronicle record --type user_input --actor user --summary "Operator session started"
chronicle add-context --title "Session Context" --summary "Local operating context" --scope session --visibility private
chronicle review queue
chronicle graph summary
chronicle ui
```

Use `chronicle ui` for inspection. Treat it as:

- foreground only
- loopback-local only
- read-only by default
- descriptive, not authoritative over primary records

## 6. Pre-Change Safety Checks

Before bulk edits, imports, or review actions:

```bash
chronicle doctor --json
chronicle ui-smoke --json
scripts/backup-local.sh
```

If you need browser-side review-route validation, use:

`docs/releases/operations/local-web-ui-operator-validation-v1.0.md`

## 7. Shutdown / End-Of-Day

Minimum close-out:

```bash
chronicle doctor --json
scripts/backup-local.sh
```

Recommended operator note:

```bash
chronicle record --type user_input --actor user --summary "Operator session closed"
```

## 8. Escalate Instead Of Assuming

Stop and investigate if any of these happen:

- `chronicle doctor` returns `error`
- `chronicle ui-smoke --json` reports `passed: false`
- `.chronicle/chronicle.jsonl` is missing or unreadable
- derived views disagree with primary record expectations
- write-route behavior appears enabled unexpectedly

## 9. Related Guides

- install/update: `../../local-deployment-curl.md`
- doctor semantics: `../../doctor.md`
- backup/restore: `local-backup-and-restore.md`
- UI walkthrough: `local-web-ui-operator-validation-v1.0.md`
