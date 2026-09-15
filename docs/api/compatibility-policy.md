# Chronicle API Compatibility Policy

Status: Draft
Date: 2026-08-07
Roadmap phase: Daemon/API Phase 6

## Contract Level

The current API schema version is `chronicle-api/v0.1-draft`.

The following are draft public contracts:

- request and response model names in `src/chronicle/api/contracts.py`;
- JSON field names required by contract tests;
- endpoint names listed in `docs/api/README.md`;
- daemon startup metadata and smoke report JSON shape;
- the daemon health response `{"status":"ok"}`.

## Compatible Changes

- Adding optional request fields.
- Adding optional response fields.
- Adding warning codes.
- Adding connector prototype kinds marked as `production_surface=false`.
- Tightening validation for committed writes when failure happens before persistence.
- Tightening loopback request-authenticity checks before route or service execution.

## Breaking Changes

- Removing or renaming required request fields.
- Removing idempotency or origin metadata requirements.
- Changing endpoint semantics from Chronicle-native records to generic logs.
- Making daemon startup hidden, autostarted, remote-bound, or hosted by default.
- Treating API responses as truth proof, identity proof, or permission grants.

## Versioning Rule

Before leaving draft status, any breaking change must either:

- increment `schema_version`; or
- provide a compatibility adapter and contract test for the old shape.

## CY-1 security cut (ADR-0107)

The unreleased daemon startup contract changes to `chronicle-daemon-startup/v2`, exposed as
`startup_schema_version`. It removes `session_token` and adds `token_file`; `--session-token` is
removed in favor of generated-file delivery. There is intentionally no credential-disclosing
compatibility adapter. The `schema_version` field continues to identify the unchanged API payload
contract, `chronicle-api/v0.1-draft`. Consumers of startup metadata must migrate explicitly.
