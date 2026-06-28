# Release Notes v1.86.0

## Added

- `chronicle trust` node/relation commands for local node profiles, trust assertions, and trust withdrawals
- read-only `/api/trust-nodes` and `/api/trust-relations` surfaces
- advisory trust summaries embedded into federation message envelopes and context package metadata

## Boundary

- trust remains local registry metadata rather than a global identity or automated scoring system
- delegated actor and AI proxy metadata are recorded for auditability, but Chronicle Stack still does not enforce remote identity proof or distributed trust verification
