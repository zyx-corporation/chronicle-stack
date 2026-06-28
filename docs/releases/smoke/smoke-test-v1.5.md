# Chronicle Stack v1.5 Release Operator Guide Smoke Profile

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #208

## Purpose

This smoke profile validates v1.5.0 as a release-operator documentation release.

It checks that release execution guidance is present and that existing runtime smoke remains unchanged.

## Documentation checks

Confirm these documents exist:

```text
../operations/release-operator-guide.md
../notes/release-notes-v1.5.0.md
../readiness/release-readiness-v1.5.md
../status/release-status-v1.5.0.md
```

Confirm the release operator guide covers:

- pre-tag verification
- annotated tag creation
- `vX.Y.Z^{}` dereference checks
- `Release.tag_name already exists`
- clean installer smoke
- existing-checkout reinstall smoke
- opt-out smoke
- `ui-smoke` continuity evidence
- release issue evidence comments
- close criteria

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
chronicle 1.5.0
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

v1.5.0 is documentation/release-operator preparation.

It does not add release automation, daemon/service installation, hosted UI, external model APIs, GraphRAG runtime, vector DB, graph DB, correctness proof, security certification, or legal/governance finalization.

## Warning classification

- Release warning: guide documentation is not automatic release execution.
- Runtime warning: no daemon/service/hosted runtime is introduced.
- Semantics warning: smoke remains diagnostic, not certification or proof.
- Legal warning: legal/governance drafts remain draft completed / counsel review pending.

## RDE review

Preserved: local-first release discipline and diagnostic smoke boundaries.

Transformed: release execution practice becomes inspectable documentation.

Supplemented: document existence and content smoke criteria.

Unresolved: external v1.5.0 tag publication and release smoke evidence.
