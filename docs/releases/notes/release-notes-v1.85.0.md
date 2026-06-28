# Release Notes v1.85.0

## Added

- `chronicle federation message create`, `chronicle federation inbox inspect`, `chronicle federation inbox show`, and `chronicle federation outbox inspect`
- local preview-only federation inbox/outbox queue storage and read-only `/api/federation-inbox` / `/api/federation-outbox` inspection surfaces

## Boundary

- federation messages remain local queue artifacts rather than auto-applied Chronicle records
- revoke/decay inbox handling records audit trail entries only; it does not delete, revoke, or mutate Chronicle primary records automatically
