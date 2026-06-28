# Release Notes v1.96.0

## Added

- `matching_federation_consent_summary` on review-queue rows when consent audit references overlap
- `matching_federation_consent_summary` on runtime-record rows and runtime/review detail payloads
- overlap-count contracts and tests for consent-audit/read-model matching behavior

## Boundary

- overlap summaries remain advisory read-only joins over existing audit metadata
- no automatic package creation, persistence, transport, or import execution was added
