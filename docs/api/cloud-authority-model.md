# Chronicle Cloud Authority Model

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 8

This model defines future Chronicle Cloud authority labels without implementing cloud sync,
storage, tenancy, or remote authorization.

Executable models live in `src/chronicle/api/cloud_authority.py`.

## CLI

```bash
chronicle daemon cloud authority --json
```

## Authority Surfaces

| Surface | Source authority | Role |
|---|---:|---|
| `local_primary_record` | yes | Current local Chronicle JSONL authority anchor |
| `cloud_replica` | no | Future sync copy |
| `cloud_index` | no | Rebuildable cloud-side index |
| `cloud_cache` | no | Temporary service acceleration surface |
| `collaboration_view` | no | Team-facing view with provenance back to Chronicle records |
| `shared_export` | no | Disclosure artifact, not automatic federation or publication |

## Boundary Rules

- Chronicle Cloud must not own the Chronicle.
- Cloud AI memory positioning is disallowed.
- Local recovery remains required.
- Backup/sync is not publication.
- Federation remains distinct from team cloud sharing.
- Cloud copies, indexes, caches, and views require authority labels.

## Unresolved

- Sync conflict resolution.
- Team permission model.
- Tenant isolation.
- Offline recovery protocol.
