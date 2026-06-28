# Chronicle Stack v1.2.0 Release Readiness

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #189

## Decision

Chronicle Stack v1.2.0 is ready for repository-side release preparation when this document, release notes, smoke profile, version bump, and changelog update are merged with passing CI.

## Scope of v1.2.0

v1.2.0 is a UI drill-down / inspectability release.

It includes:

- read-only detail endpoints for `chronicle ui`
- artifact detail payloads with versions
- lightweight browser-shell drill-down affordance
- service and HTTP tests for detail endpoints
- v1.2 UI smoke profile
- v1.2 release notes

## Readiness checklist

- [x] `chronicle ui` collection endpoints exist.
- [x] Detail endpoints implemented for supported record types.
- [x] Artifact detail includes version metadata.
- [x] Missing detail records return 404 through HTTP.
- [x] UI shell includes drill-down affordance.
- [x] Detail endpoint tests exist.
- [x] README documents v1.2 detail endpoints.
- [x] v1.2 UI smoke profile exists.
- [x] v1.2 release notes exist.
- [x] Project version set to `1.2.0`.
- [x] CHANGELOG includes v1.2.0.

## Required repository verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version:

```text
chronicle 1.2.0
```

## Required UI smoke

See:

```text
../smoke/smoke-test-v1.2.md
```

Minimum checks:

- `chronicle ui --help`
- `/` returns local UI shell
- `/review-console` returns static Review Console
- collection endpoints return JSON
- detail endpoints return JSON with a `record` field
- missing detail endpoint returns 404

## Release-operator steps after merge

After this repository-side preparation is merged:

1. Run local verification from `main`.
2. Create annotated `v1.2.0` tag.
3. Publish GitHub Release using `../notes/release-notes-v1.2.0.md`.
4. Run installer smoke from `v1.2.0` tag.
5. Record evidence in a separate release execution issue.

## Boundary confirmation

v1.2.0 does not introduce:

- write-capable GUI actions
- authentication or authorization
- public network binding by default
- daemon/autostart service
- hosted app
- cloud sync
- external model API
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof
- legal/governance finalization

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Runtime warning: UI drill-down does not imply hosted runtime or background service.
- Security warning: localhost UI is browser-exposed and remains a local risk surface.
- Semantics warning: detail views are not enforcement or correctness proof.
- Legal warning: commercial/contributor drafts remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- CLI canonical surface.
- Static Review Console.
- Explicit no-daemon/no-external-runtime boundary.
- Advisory/diagnostic semantics.

### Transformed

- Chronicle Stack local UI becomes a record-level inspection surface.

### Supplemented

- Detail endpoint smoke.
- v1.2 release notes.
- v1.2 release readiness checklist.
- External release execution boundary.

### Unresolved

- Actual `v1.2.0` tag creation.
- GitHub Release publication.
- Installer smoke from tag.
- Future write-preview UI design.

### Deviation risks

- Claiming v1.2.0 as a hosted app.
- Treating local UI as access control.
- Treating detail view as correctness proof.
- Treating repository readiness as release publication.
