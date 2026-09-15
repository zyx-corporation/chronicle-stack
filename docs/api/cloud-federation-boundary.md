# Chronicle Cloud / Federation Boundary

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 9

This boundary separates future Chronicle Cloud service-layer sharing from Chronicle Federation
trust/disclosure relationships.

Executable models live in `src/chronicle/api/cloud_authority.py`.

## CLI

```bash
chronicle daemon cloud federation-boundary --json
```

## Boundary Matrix

| Surface | Belongs to Cloud | Belongs to Federation | Consent | Redaction preview | Trust scope |
|---|---:|---:|---:|---:|---:|
| `team_sync` | yes | no | no | no | no |
| `organization_sharing` | yes | no | yes | yes | no |
| `partner_disclosure` | no | yes | yes | yes | yes |
| `public_material` | no | yes | yes | yes | yes |
| `federation_package` | no | yes | yes | yes | yes |
| `federation_message` | no | yes | yes | yes | yes |

## Rules

- Cloud does not bypass federation consent.
- Federation remains the trust/disclosure relationship layer.
- Cloud sync is not publication.
- Any Cloud-to-Federation bridge requires a later ADR.
- Federation messages and packages remain review-first and cannot auto-apply.
