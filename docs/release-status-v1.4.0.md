# Chronicle Stack v1.4.0 Release Status

## Status

Repository-side release preparation for v1.4.0 is complete, and external v1.4.0 release execution has been completed.

Latest published release for this track:

```text
v1.4.0
```

Current post-release documentation track:

```text
v1.5 release operator guide
```

## Scope

v1.4.0 is a local installer hardening release.

It includes:

- requested branch/tag ref refresh before checkout
- default forced refresh of requested local release tags from origin
- `CHRONICLE_STACK_ALLOW_MOVED_TAG=0` opt-out
- `pip install --force-reinstall`
- checked-out commit logging
- moved/recreated tag documentation
- v1.4 smoke profile
- v1.4 release notes
- v1.4 release readiness document

## Release documents

- [Release Operator Guide](release-operator-guide.md)
- [v1.4 Smoke Test Profile](smoke-test-v1.4.md)
- [v1.4 Release Readiness](release-readiness-v1.4.md)
- [v1.4 Release Notes](release-notes-v1.4.0.md)
- [curl-based Local Deployment](local-deployment-curl.md)

## Boundary

v1.4.0 does not add daemon/service installation, hosted UI, external model APIs, GraphRAG runtime, vector DB, graph DB, correctness proof, security certification, or legal/governance finalization.

Moving release tags remains exceptional and should be evidence-recorded.

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Installer warning: moved tags remain exceptional and evidence-recorded.
- Runtime warning: installer hardening does not imply hosted runtime or background service.
- Security warning: installer smoke is not security certification.
- Semantics warning: installer smoke is not correctness proof.

## RDE review

Preserved: local-first release discipline, inspect-first installer, no-daemon/no-external-runtime boundary.

Transformed: v1.3 corrective retag incident becomes v1.4 release hardening.

Supplemented: release status page now links the reusable release operator guide.

Unresolved: future full release automation, package publishing, and immutable tag governance.
