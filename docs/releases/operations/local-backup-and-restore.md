# Chronicle Stack Local Backup And Restore

Related: `local-operator-runbook.md`, `../../doctor.md`

Status: current local backup/restore guide  
Scope: local single-operator backup and recovery for `.chronicle/`

## Purpose

This guide describes how to create and restore local file-based backups for a Chronicle root.

## Boundary

This guide covers:

- `.chronicle/` backup
- local tarball restore
- read-only verification after restore

This guide does not cover:

- cloud backup services
- multi-machine replication
- hosted restore automation
- semantic conflict resolution

## What To Back Up

The minimum backup target is:

```text
.chronicle/
```

That includes:

- `chronicle.jsonl`
- `metadata.yaml`
- derived indexes
- generated reports stored under `.chronicle/`

Artifact source files outside `.chronicle/` may still matter operationally. If you rely on them, back them up separately at the project level.

## Create A Backup

From the Chronicle root:

```bash
scripts/backup-local.sh
```

Example output:

```text
.chronicle-backups/chronicle-backup-chr_xxx-20260701T120000Z.tar.gz
```

Custom destination:

```bash
scripts/backup-local.sh "$PWD" "$HOME/.chronicle-backups"
```

Dry run:

```bash
DRY_RUN=1 scripts/backup-local.sh "$PWD" "$HOME/.chronicle-backups"
```

## Recommended Backup Moments

- before enabling any explicit local mutation path
- before import or package-handling experiments
- before bulk artifact or context updates
- at end-of-day for active Chronicle roots

## Restore A Backup

Helper-based restore:

```bash
scripts/restore-local.sh /path/to/chronicle-backup-....tar.gz
```

By default this preserves the current `.chronicle/` as `.chronicle.pre-restore.<timestamp>` before extraction.

Manual restore:

```bash
mv .chronicle ".chronicle.pre-restore.$(date -u +%Y%m%dT%H%M%SZ)"
```

Restore the selected archive:

```bash
tar -C "$PWD" -xzf /path/to/chronicle-backup-....tar.gz
```

If you intentionally want replacement without a preserved pre-restore directory:

```bash
PRESERVE_EXISTING=0 scripts/restore-local.sh /path/to/chronicle-backup-....tar.gz
```

## Verify After Restore

Run:

```bash
chronicle doctor
chronicle doctor --json
chronicle ui-smoke --json
```

If derived indexes are missing or stale:

```bash
chronicle index rebuild
chronicle doctor --json
```

## Recovery Notes

If the restored Chronicle looks wrong:

- keep the restored `.chronicle/` for evidence
- compare it with `.chronicle.pre-restore.*`
- do not overwrite `chronicle.jsonl` repeatedly without preserving snapshots

## Operator Rule

Treat backup creation as a local safety rail, not as proof of consistency or correctness.
