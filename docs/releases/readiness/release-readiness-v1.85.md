# Release Readiness v1.85

## Checklist

- [x] `chronicle federation message create` saves stable JSON message envelopes into local inbox/outbox queues
- [x] `chronicle federation inbox inspect` and `chronicle federation outbox inspect` expose preview-only message summaries
- [x] `/api/federation-inbox` and `/api/federation-outbox` provide read-only local inspect surfaces
- [x] `revoke_context` and `decay_notice` inbox messages record audit events without mutating Chronicle primary records
