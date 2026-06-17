# Chronicle Stack v1.5.0 Release Status

## Status

Repository-side release preparation for v1.5.0 is in progress.

Latest published release before this track:

```text
v1.4.0
```

Current repository-side release target:

```text
v1.5.0
```

## Scope

v1.5.0 is a release-operator documentation release.

It includes:

- release operator guide
- release status discoverability link
- release notes
- release readiness
- smoke profile
- version bump to `1.5.0`

## Release documents

- [Release Operator Guide](release-operator-guide.md)
- [v1.5 Smoke Test Profile](smoke-test-v1.5.md)
- [v1.5 Release Readiness](release-readiness-v1.5.md)
- [v1.5 Release Notes](release-notes-v1.5.0.md)

## Boundary

v1.5.0 does not add release automation, GitHub Actions release publishing, package publishing, daemon/service installation, hosted UI, external model APIs, GraphRAG runtime, vector DB, graph DB, correctness proof, security certification, or legal/governance finalization.

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Runtime warning: documentation release does not imply hosted runtime or background service.
- Security warning: smoke is not security certification.
- Semantics warning: smoke is not correctness proof.

## RDE review

Preserved: manual evidence-based release execution and no-runtime boundary.

Transformed: release execution practice becomes versioned release documentation.

Supplemented: v1.5 release status page.

Unresolved: external v1.5.0 tag publication and release smoke evidence.
