# Chronicle Stack v1.4.0 Release Readiness

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #201

## Decision

Chronicle Stack v1.4.0 is ready for repository-side release preparation when this document, release notes, smoke profile, version bump, and changelog update are merged with passing CI.

## Scope of v1.4.0

v1.4.0 is a local installer hardening release.

It includes:

- robust requested branch/tag ref fetching in `scripts/install-local.sh`
- default force-refresh of requested local release tags from origin
- `CHRONICLE_STACK_ALLOW_MOVED_TAG=0` opt-out
- `pip install --force-reinstall`
- checked-out commit logging
- moved/recreated tag documentation
- v1.4 installer smoke profile
- v1.4 release notes

## Readiness checklist

- [x] Installer refreshes requested branch/tag refs before checkout.
- [x] Requested tag refs are force-refreshed from origin by default.
- [x] Forced tag refresh can be disabled with `CHRONICLE_STACK_ALLOW_MOVED_TAG=0`.
- [x] Installer uses `pip install --force-reinstall`.
- [x] Installer logs checked-out commit after checkout.
- [x] Local deployment docs document moved/recreated tag behavior.
- [x] v1.4 smoke profile exists.
- [x] v1.4 release notes exist.
- [x] Project version set to `1.4.0`.
- [x] CHANGELOG includes v1.4.0.

## Required repository verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected version:

```text
chronicle 1.4.0
```

## Required installer smoke

See:

```text
../smoke/smoke-test-v1.4.md
```

Minimum checks:

- clean install from `v1.4.0` tag
- existing checkout reinstall from `v1.4.0` tag
- checked-out commit evidence
- installed `chronicle --version`
- `CHRONICLE_STACK_ALLOW_MOVED_TAG=0` opt-out log path
- `chronicle ui-smoke` continuity check

## Release-operator steps after merge

After this repository-side preparation is merged:

1. Run local verification from `main`.
2. Create annotated `v1.4.0` tag.
3. Publish GitHub Release using `../notes/release-notes-v1.4.0.md`.
4. Run installer smoke from `v1.4.0` tag.
5. Record evidence in a separate release execution issue.

## Boundary confirmation

v1.4.0 does not introduce:

- daemon/service installation
- hosted app
- network service runtime
- cloud sync
- external model API
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof
- security certification
- legal/governance finalization

Moving release tags remains exceptional and should be evidence-recorded.

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Installer warning: moved tags remain exceptional and evidence-recorded.
- Runtime warning: installer hardening does not imply hosted runtime or background service.
- Security warning: installer smoke is not security certification.
- Semantics warning: installer smoke is not enforcement or correctness proof.
- Legal warning: commercial/contributor drafts remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- CLI canonical surface.
- Inspect-first installer.
- Explicit no-daemon/no-external-runtime boundary.
- Advisory/diagnostic semantics.

### Transformed

- Corrective retag lesson becomes release-grade installer hardening.

### Supplemented

- v1.4 installer smoke profile.
- v1.4 release notes.
- v1.4 release readiness checklist.
- External release execution boundary.

### Unresolved

- Actual `v1.4.0` tag creation.
- GitHub Release publication.
- Installer smoke from tag.
- Future immutable tag policy.

### Deviation risks

- Claiming v1.4.0 as certification.
- Treating local install as server deployment.
- Treating repository readiness as release publication.
- Normalizing moved release tags.
