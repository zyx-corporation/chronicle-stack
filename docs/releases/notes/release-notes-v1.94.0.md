# Release Notes v1.94.0

## Added

- `/api/federation-package-preview` for explicit local bundle-directory preview inspection
- query-aware UI API routing so read-only endpoints can accept local preview parameters without adding persistence
- smoke and UI data-service coverage for parameter-required and preview/import-preview federation package contracts

## Boundary

- the new UI surface only inspects an explicitly supplied local directory
- no package creation, auto-discovery, persistence, transport, or import execution was added
