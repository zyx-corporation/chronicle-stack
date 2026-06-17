# Chronicle Stack v1.5.0 Release Readiness

Issue: #208

## Decision

Chronicle Stack v1.5.0 is ready for repository-side release preparation when this document, release notes, smoke profile, release status, version bump, and related release-operator documentation are merged with passing CI.

## Scope

v1.5.0 is a release-operator documentation release.

It includes:

- `docs/release-operator-guide.md`
- release status linkage from `docs/release-status-v1.4.0.md`
- v1.5 release notes
- v1.5 smoke profile
- v1.5 release readiness
- v1.5 release status
- version bump to `1.5.0`

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
chronicle 1.5.0
```

## Boundary confirmation

v1.5.0 does not introduce:

- release automation
- GitHub Actions release publishing
- package publishing
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
docs/release-operator-guide.md
```

The external release execution should be tracked separately with tag, GitHub Release, installer smoke, reinstall smoke, opt-out smoke, and `ui-smoke` evidence.

## Warning classification

- Release warning: repository-side readiness is not publication.
- Runtime warning: documentation release does not imply hosted/background runtime.
- Security warning: smoke is not security certification.
- Semantics warning: smoke is not correctness proof.
- Legal warning: commercial/contributor drafts remain draft completed / counsel review pending.

## RDE review

Preserved: local-first release evidence model, inspect-first installer smoke, no-runtime boundary.

Transformed: release execution knowledge becomes release-ready repository documentation.

Supplemented: v1.5 readiness checklist and release execution handoff.

Unresolved: external `v1.5.0` release publication and future release automation policy.

Deviation risks: treating docs as automation, treating smoke as certification, or normalizing moved tags.
