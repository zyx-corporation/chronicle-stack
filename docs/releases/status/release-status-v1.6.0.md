# Chronicle Stack v1.6.0 Release Status

## Status

Repository-side release preparation for v1.6.0 is in progress.

Latest published release before this track:

```text
v1.5.0
```

Current repository-side release target:

```text
v1.6.0
```

## Scope

v1.6.0 is a release tag immutability policy documentation release.

It includes:

- release tag policy
- immutable-by-default release tag rule
- exceptional corrective retag criteria
- required retag evidence guidance
- annotated tag dereference guidance
- release notes
- release readiness
- smoke profile
- version bump to `1.6.0`

## Release documents

- [Release Tag Policy](../operations/release-tag-policy.md)
- [Release Operator Guide](../operations/release-operator-guide.md)
- [v1.6 Smoke Test Profile](../smoke/smoke-test-v1.6.md)
- [v1.6 Release Readiness](../readiness/release-readiness-v1.6.md)
- [v1.6 Release Notes](../notes/release-notes-v1.6.0.md)

## Boundary

v1.6.0 does not add automated tag protection, release automation, GitHub Actions release publishing, package publishing, installer behavior changes, daemon/service installation, hosted UI, external model APIs, GraphRAG runtime, vector DB, graph DB, correctness proof, security certification, or legal/governance finalization.

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Corrective warning: retagging is exceptional and evidence-recorded.
- Runtime warning: documentation release does not imply hosted runtime or background service.
- Security warning: smoke is not security certification.
- Semantics warning: smoke is not correctness proof.

## RDE review

Preserved: manual evidence-based release execution and no-runtime boundary.

Transformed: release tag immutability becomes versioned release documentation.

Supplemented: v1.6 release status page.

Unresolved: external v1.6.0 tag publication and release smoke evidence.
