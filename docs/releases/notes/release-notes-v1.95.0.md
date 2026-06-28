# Release Notes v1.95.0

## Added

- structured `federation_preflight_summary` on audit and overview read models
- structured `federation_consent_summary` on consent-record audit rows and audit detail payloads
- smoke and UI data-service coverage for the new read-only federation preflight audit contracts

## Boundary

- federation boundary check remains an explicit local CLI preflight surface
- no automatic boundary-check persistence, package creation, transport, or import execution was added
