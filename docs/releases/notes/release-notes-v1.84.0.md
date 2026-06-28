# Release Notes v1.84.0

## Added

- `chronicle object record`, `chronicle object list`, and `chronicle object show` for append-only Chronicle object records
- `/api/chronicle-objects` read-only list/detail surface for explicit object records and derived Conversation / Artifact / Decision / Delta views

## Boundary

- Chronicle object views remain derived over the primary JSONL record
- Delta Chronicle continues to point back to RDE Diff Records rather than introducing a hosted GraphRAG runtime or writable GUI
