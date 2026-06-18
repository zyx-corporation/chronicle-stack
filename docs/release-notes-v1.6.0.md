# Chronicle Stack v1.6.0 Release Notes

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

## Summary

Chronicle Stack v1.6.0 is a release tag immutability policy documentation release over v1.5.0.

It documents the operational policy that published release tags are immutable by default, and that corrective retags are exceptional, evidence-recorded events requiring fresh smoke evidence.

## Highlights

### Release Tag Policy

v1.6.0 adds:

```text
docs/release-tag-policy.md
```

The policy defines:

- published release tags are immutable by default
- corrective retags are exceptional
- corrective retags require issue evidence
- fresh installer and `ui-smoke` evidence is required after corrective retags
- annotated tag commit comparisons should use `vX.Y.Z^{}`
- `Release.tag_name already exists` can be treated as release-existence evidence when tag/main equivalence and notes are acceptable

### Connected release operations layer

The release tag policy complements:

- [Release Operator Guide](release-operator-guide.md)
- [curl-based Local Deployment](local-deployment-curl.md)

Together, v1.4, v1.5, and v1.6 form a release operations layer:

- v1.4: installer moved-tag hardening
- v1.5: release operator guide
- v1.6: release tag immutability policy

## Boundary

v1.6.0 does not add:

- automated tag protection
- release automation
- GitHub Actions release publishing
- package publishing
- installer behavior changes
- daemon or service installation
- hosted UI
- external model API calls
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof
- security certification
- legal/governance finalization

## Verification

Repository-side verification expected before release:

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

## Warning classification

- Release warning: release tags are immutable by default.
- Corrective warning: retagging is exceptional and requires evidence.
- Runtime warning: policy documentation does not imply hosted/background runtime.
- Security warning: smoke evidence is not security certification.
- Semantics warning: smoke evidence is not correctness proof.
- Legal warning: commercial/contributor documents remain draft completed / counsel review pending.

## RDE review

Preserved: evidence-based release execution, local-first smoke discipline, annotated tag verification, no-runtime boundary.

Transformed: repeated retag caution becomes versioned release policy.

Supplemented: v1.6 release notes and policy framing.

Unresolved: platform-enforced tag protection, future release automation, package publishing, and legal/governance finalization.

Deviation risks: normalizing retagging, treating smoke as certification, or confusing operational policy with legal terms.
