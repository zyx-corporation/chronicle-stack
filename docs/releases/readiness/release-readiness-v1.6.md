# Chronicle Stack v1.6.0 Release Readiness

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #213

## Decision

Chronicle Stack v1.6.0 is ready for repository-side release preparation when this document, release notes, smoke profile, release status, version bump, and release tag policy are merged with passing CI.

## Scope

v1.6.0 is a release tag immutability policy documentation release.

It includes:

- `../operations/release-tag-policy.md`
- v1.6 release notes
- v1.6 smoke profile
- v1.6 release readiness
- v1.6 release status
- version bump to `1.6.0`

## Required verification

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
chronicle 1.6.0
```

## Boundary confirmation

v1.6.0 does not introduce:

- automated tag protection
- release automation
- GitHub Actions release publishing
- package publishing
- installer behavior changes
- daemon/service installation
- hosted UI
- external model API
- GraphRAG runtime
- vector DB
- graph DB
- correctness proof
- security certification
- legal/governance finalization

## Release-operator steps after merge

Use:

```text
../operations/release-operator-guide.md
../operations/release-tag-policy.md
```

The external release execution should be tracked separately with tag, GitHub Release, installer smoke, reinstall smoke, opt-out smoke, and `ui-smoke` evidence.

## Warning classification

- Release warning: repository-side readiness is not publication.
- Corrective warning: retagging remains exceptional and evidence-recorded.
- Runtime warning: documentation release does not imply hosted/background runtime.
- Security warning: smoke is not security certification.
- Semantics warning: smoke is not correctness proof.
- Legal warning: commercial/contributor drafts remain draft completed / counsel review pending.

## RDE review

Preserved: local-first release evidence model, inspect-first installer smoke, no-runtime boundary.

Transformed: retag caution becomes release-ready policy documentation.

Supplemented: v1.6 readiness checklist and release execution handoff.

Unresolved: external `v1.6.0` release publication and future platform-enforced tag protection.

Deviation risks: normalizing retagging, treating smoke as certification, or confusing operational policy with legal terms.
