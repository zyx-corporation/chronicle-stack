# Release Notes v1.111.0

- enriched `/api/audit` rows with related boundary and lifecycle ids, impacted target summaries, and operational implications
- added a `governance_summary` aggregate to `/api/audit` so the Audit / Boundary / Lifecycle workspace can start from a top summary rail
- aligned `/api/audit/<audit_id>` detail payloads with the enriched audit stream contract
