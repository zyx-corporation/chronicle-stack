# Chronicle Stack v1.1.0 Release Readiness

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #184

## Decision

Chronicle Stack v1.1.0 is ready for repository-side release preparation when this document, release notes, smoke profile, version bump, and changelog update are merged with passing CI.

## Scope of v1.1.0

v1.1.0 is a GUI/readability release.

It includes:

- Static read-first Review Console
- Explicit `chronicle ui` command
- Foreground loopback local UI server
- Lightweight browser shell
- Read-only local UI API endpoints
- GUI smoke profile
- Release notes

## Readiness checklist

- [x] Static Review Console implemented.
- [x] `chronicle ui` minimal local server implemented.
- [x] `chronicle ui` read-only endpoints implemented.
- [x] Lightweight browser shell implemented.
- [x] UI tests added.
- [x] README documents `chronicle ui`.
- [x] v1.1 local web UI design exists.
- [x] v1.1 GUI smoke profile exists.
- [x] v1.1 release notes exist.
- [x] Project version set to `1.1.0`.
- [x] CHANGELOG includes v1.1.0.

## Required repository verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version:

```text
chronicle 1.1.0
```

## Required GUI smoke

See:

```text
docs/smoke-test-v1.1.md
```

Minimum checks:

- `chronicle ui --help`
- `chronicle export --format html`
- `chronicle ui` foreground server starts on loopback
- `/` returns local UI shell
- `/review-console` returns static Review Console
- `/api/overview` returns JSON
- all read-only UI endpoints return JSON

## Release-operator steps after merge

After this repository-side preparation is merged:

1. Run local verification from `main`.
2. Create annotated `v1.1.0` tag.
3. Publish GitHub Release using `docs/release-notes-v1.1.0.md`.
4. Run installer smoke from `v1.1.0` tag.
5. Record evidence in a separate release execution issue.

## Boundary confirmation

v1.1.0 does not introduce:

- daemon/autostart service
- hosted app
- cloud sync
- external model API
- GraphRAG runtime
- vector DB
- graph DB
- write-capable GUI actions
- access-control enforcement
- correctness proof
- legal/governance finalization

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Runtime warning: GUI/readability does not imply hosted runtime or background service.
- Security warning: localhost UI is browser-exposed and remains a local risk surface.
- Semantics warning: UI review states are not enforcement or correctness proof.
- Legal warning: commercial/contributor drafts remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- CLI canonical surface.
- Static Review Console.
- Advisory/diagnostic semantics.
- Explicit no-daemon/no-external-runtime boundary.

### Transformed

- Chronicle Stack moves from CLI-first public foundation toward human-facing local review.

### Supplemented

- Release readiness checklist for GUI/readability.
- v1.1 GUI smoke profile.
- v1.1 release notes.
- External release execution boundary.

### Unresolved

- Actual `v1.1.0` tag creation.
- GitHub Release publication.
- Installer smoke from tag.
- Future interactive/write-capable GUI design.

### Deviation risks

- Claiming v1.1.0 as a hosted app.
- Treating local UI as access control.
- Treating GUI review as proof.
- Treating repository readiness as release publication.
