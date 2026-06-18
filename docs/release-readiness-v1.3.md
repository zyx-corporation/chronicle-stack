# Chronicle Stack v1.3.0 Release Readiness

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #194

## Decision

Chronicle Stack v1.3.0 is ready for repository-side release preparation when this document, release notes, smoke profile, version bump, and changelog update are merged with passing CI.

## Scope of v1.3.0

v1.3.0 is an automated UI smoke / release-verification release.

It includes:

- `chronicle ui-smoke`
- `chronicle ui-smoke --json`
- read-only UI smoke report models
- collection payload smoke checks
- detail payload smoke checks
- missing-detail smoke behavior
- tests for success and failure paths
- v1.3 smoke profile
- v1.3 release notes

## Readiness checklist

- [x] `chronicle ui-smoke` command exists.
- [x] `chronicle ui-smoke --json` emits a machine-readable report.
- [x] The command does not start a server.
- [x] The command does not require a browser.
- [x] The command does not bind sockets.
- [x] Collection payload checks exist.
- [x] Detail payload checks exist.
- [x] Missing-detail behavior is checked.
- [x] Missing/uninitialized roots fail cleanly.
- [x] README documents `chronicle ui-smoke`.
- [x] v1.3 smoke profile exists.
- [x] v1.3 release notes exist.
- [x] Project version set to `1.3.0`.
- [x] CHANGELOG includes v1.3.0.

## Required repository verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version:

```text
chronicle 1.3.0
```

## Required UI smoke

See:

```text
docs/smoke-test-v1.3.md
```

Minimum checks:

- `chronicle ui-smoke`
- `chronicle ui-smoke --json`
- missing-root failure behavior
- no server startup
- no browser requirement
- no external runtime

## Release-operator steps after merge

After this repository-side preparation is merged:

1. Run local verification from `main`.
2. Create annotated `v1.3.0` tag.
3. Publish GitHub Release using `docs/release-notes-v1.3.0.md`.
4. Run installer smoke from `v1.3.0` tag.
5. Record evidence in a separate release execution issue.

## Boundary confirmation

v1.3.0 does not introduce:

- write-capable GUI actions
- authentication or authorization
- public network binding by default
- daemon/autostart service
- hosted app
- browser automation requirement
- cloud sync
- external model API
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof
- security certification
- legal/governance finalization

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Runtime warning: UI smoke automation does not imply hosted runtime, browser automation, or background service.
- Security warning: smoke pass is not security certification.
- Semantics warning: smoke pass is not enforcement or correctness proof.
- Legal warning: commercial/contributor drafts remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- CLI canonical surface.
- Static Review Console.
- Explicit no-daemon/no-external-runtime boundary.
- Advisory/diagnostic semantics.

### Transformed

- Chronicle Stack UI smoke becomes a repeatable local diagnostic command.

### Supplemented

- v1.3 smoke profile.
- v1.3 release notes.
- v1.3 release readiness checklist.
- External release execution boundary.

### Unresolved

- Actual `v1.3.0` tag creation.
- GitHub Release publication.
- Installer smoke from tag.
- Future browser E2E testing.

### Deviation risks

- Claiming v1.3.0 as certification.
- Treating local smoke as security proof.
- Treating repository readiness as release publication.
