# Chronicle Stack v1.0.0 Release Execution Plan

Issues: #165, #171

## Purpose

This document defines the maintainer execution sequence for the Chronicle Stack v1.0.0 tag, installer smoke, and GitHub Release publication.

The release must not be treated as complete until tag-based installer smoke evidence is captured.

## Blocking conditions

Do not create the `v1.0.0` tag if any of the following are true:

- v1.0.0 release criteria are incomplete.
- README release status is internally inconsistent.
- CLI compatibility audit is incomplete.
- Installer smoke profile is incomplete.
- Sayane / CSG-RAG integration boundary is unclear.
- Legal/governance draft status is described as final rather than counsel-review pending.
- Tests or lint fail during pre-tag verification.

## Pre-tag verification

Run from `main` after all v1.0 finalization PRs are merged:

```bash
git checkout main
git pull --ff-only
git status --short

python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version output:

```text
chronicle 1.0.0
```

## Tag creation

The GitHub connector may not expose tag creation. If so, run locally:

```bash
git tag -a v1.0.0 -m "Chronicle Stack v1.0.0"
git push origin v1.0.0
```

## GitHub Release publication

If GitHub Release creation is not available through the connector, run locally:

```bash
gh release create v1.0.0 \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack v1.0.0" \
  --notes-file ../notes/release-notes-v1.0.0.md
```

## Installer smoke from tag

After the tag is available:

```bash
rm -rf /tmp/chronicle-stack-v10-install-smoke
mkdir -p /tmp/chronicle-stack-v10-install-smoke
cd /tmp/chronicle-stack-v10-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v1.0.0/scripts/install-local.sh -o install-local.sh
less install-local.sh
bash install-local.sh

/tmp/chronicle-stack-v10-install-smoke/bin/chronicle --version
/tmp/chronicle-stack-v10-install-smoke/bin/chronicle --help
```

Expected output includes:

```text
chronicle 1.0.0
```

## Post-release checklist

After release publication and installer smoke pass:

- Confirm the `v1.0.0` tag is available.
- Confirm the GitHub Release page exists.
- Capture installer smoke output.
- Update release execution issue with evidence.
- Close release execution issue as completed.
- Close parent v1.0 roadmap issue as completed.

## Evidence to preserve

- pre-tag verification command output
- test result summary
- lint result summary
- installer smoke output
- release URL
- tag URL or commit SHA

## Legal and governance note

Release execution does not finalize:

- `Commercial-SaaS-License.md`
- `../../contributor-license-policy.md`

Both remain draft completed / counsel review pending until qualified review and transaction-specific execution materials are prepared.

## Warning classification

- Release warning: v1.0.0 must not be tagged before criteria and compatibility policy are complete.
- Tooling warning: GitHub connector may not expose tag/release creation; local commands may be required.
- Evidence warning: release publication is incomplete until installer smoke from tag is captured.
- Legal warning: release execution does not finalize counsel-review pending materials.

## RDE review

### Preserved

- v0.9.0 release execution pattern.
- Tag-based installer smoke evidence.
- Explicit connector limitation handling.

### Transformed

- Release execution becomes stable-release governance rather than only release-candidate operation.

### Supplemented

- Blocking conditions.
- Evidence checklist.
- Post-release closure sequence.

### Deviation risks

- Mistaking procedural completion for semantic readiness.
- Publishing release before tag smoke evidence.
- Treating legal drafts as finalized by release publication.
