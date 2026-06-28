# Chronicle Stack v1.6 Release Tag Policy Smoke Profile

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #213

## Purpose

This smoke profile validates v1.6.0 as a release tag immutability policy documentation release.

It checks that release tag policy documentation exists and that existing runtime smoke remains unchanged.

## Documentation checks

Confirm these documents exist:

```text
../operations/release-tag-policy.md
../notes/release-notes-v1.6.0.md
../readiness/release-readiness-v1.6.md
../status/release-status-v1.6.0.md
```

Confirm the release tag policy covers:

- immutable-by-default release tags
- corrective retags as exceptional operations
- required evidence after corrective retags
- annotated tag dereference with `vX.Y.Z^{}`
- `Release.tag_name already exists` interpretation
- release operator guide link
- local deployment moved-tag handling link

## Runtime continuity checks

Run:

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

Expected JSON smoke fields:

```json
{
  "passed": true,
  "read_only": true,
  "server_started": false,
  "browser_required": false,
  "external_runtime": false
}
```

## Boundary

v1.6.0 is documentation/release-policy preparation.

It does not add automated tag protection, release automation, daemon/service installation, hosted UI, external model APIs, GraphRAG runtime, vector DB, graph DB, correctness proof, security certification, or legal/governance finalization.

## Warning classification

- Release warning: release tags are immutable by default.
- Corrective warning: retagging is exceptional and requires evidence.
- Runtime warning: no daemon/service/hosted runtime is introduced.
- Semantics warning: smoke remains diagnostic, not certification or proof.
- Legal warning: legal/governance drafts remain draft completed / counsel review pending.

## RDE review

Preserved: local-first release discipline and diagnostic smoke boundaries.

Transformed: retag caution becomes versioned release policy.

Supplemented: document existence and content smoke criteria.

Unresolved: external v1.6.0 tag publication and release smoke evidence.
