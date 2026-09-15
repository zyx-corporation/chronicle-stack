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

## Authorization boundary clarification (2026-09-15)

Authority here means source-of-truth status, not permission or the owner scope in
[ADR-0109](../adr/0109-yard-owner-scope-permission-model.md).
`cloud_owns_chronicle=False` does not define resource ownership or grant rules.

The Cloud/Federation draft's `team_sync.consent_required=False` is inspection data,
not an authorization decision. It must not be interpreted as same-organization access
permission or as an exemption from default-deny. A future sync implementation needs
explicit grants and a separately specified consent policy before consuming this model.
The draft field's naming and semantics must be resolved before operational use.

At commit `717a23bea3d5166262f2cdf9edfa6e4e19e79bfc`, the factory is called by
`daemon cloud federation-boundary` for serialization/display only. The package also
exports the model for import. No sync or authorization consumer was found in repository
source, scripts, or daemon routes. This is a repository-bounded finding, not a claim about
external clients. See the [audit record](../chronicles/2026-09-15-cy1-preflight-clarifications.md).

## Follow-up before Cloud implementation

Whether Cloud sync or authorization is planned in another repository/service was outside
the reachability audit; the existence or absence of such a plan has not been established.
Cloud alignment must identify the implementation location and consumers of these contracts.
When implementation begins, repeat the data-flow and default-deny review across the actual
service/repository boundaries, including imports, serialized configuration, and copied policy
values. Complete that review before operational use. The current repository-only finding
does not carry forward as approval of future Cloud behavior.
