# Release Readiness v1.94

## Checklist

- [x] `/api/federation-package-preview` returns a parameter-required contract when no `package_dir` is supplied
- [x] `/api/federation-package-preview?package_dir=...` exposes preview and `mode=import-preview` read models for explicit local bundle directories
- [x] UI smoke and data-service tests cover structured `message_key` and `boundary_note_key` fields for the new route
- [x] behavior remains local-first, advisory, and non-authoritative over Chronicle JSONL
