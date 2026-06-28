# Release Notes v1.91.0

## Added

- federation package consent metadata for granted-by, recorded-at, scope, and third-party sharing restriction fields
- record-level federation visibility mappings in `redaction-report.json`
- append-only audit capture for package-create consent and sharing summaries
- advisory warning when package visibility is broader than recommended record visibility

## Boundary

- consent and sharing metadata remain descriptive Chronicle-side records rather than legal workflow automation
- visibility mappings are advisory recommendations, not access control or automatic redaction guarantees
