# Release Readiness v1.95

## Checklist

- [x] `/api/audit` exposes a structured `federation_preflight_summary` alongside audit rows
- [x] `consent_record` audit rows and `/api/audit/<id>` detail expose structured `federation_consent_summary`
- [x] overview exposes the same preflight summary without implying boundary-check persistence
- [x] behavior remains local-first, advisory, and non-authoritative over Chronicle JSONL
