# Release Notes v1.92.0

## Added

- `chronicle federation package preview` for a combined manifest, redaction, and verification review surface
- `chronicle federation package import-preview` for manual import-readiness review without performing import
- advisory preview findings for unsigned signatures, consent gaps, sharing restrictions, and blocked verification states
- preview boundary notes that keep Chronicle JSONL authoritative over derived federation review surfaces

## Boundary

- preview and import-preview are descriptive review steps, not import execution or authority transfer
- verification outcomes remain advisory signals layered on top of Chronicle primary records
