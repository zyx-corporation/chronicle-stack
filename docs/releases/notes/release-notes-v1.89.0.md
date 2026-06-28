# Release Notes v1.89.0

## Added

- `chronicle federation package create` for local-first federation handoff bundle directories
- `chronicle federation package inspect` for read-only manifest and redaction-report inspection
- `chronicle federation package verify` for payload file hash verification with explicit unsigned-signature warnings
- bundle payload files: `manifest.json`, `records.jsonl`, `redaction-report.json`, and `README.md`

## Boundary

- federation packages remain descriptive local bundles rather than transport sessions or auto-import workflows
- hash verification is structural only; unsigned placeholder signatures do not claim identity proof or trust certification
