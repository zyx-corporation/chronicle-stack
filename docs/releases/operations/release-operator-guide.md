# Chronicle Stack Release Operator Guide

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Status: v1.5 release-operator guide  
Scope: manual release execution checklist

## Purpose

This guide captures the recurring manual release execution steps used for Chronicle Stack releases.

It exists so release execution evidence does not depend on chat memory.

The guide covers:

- local pre-tag verification
- annotated tag creation
- GitHub Release publication
- already-existing release handling
- tag/main equivalence checks
- annotated tag dereference checks
- installer smoke from tag
- existing-checkout reinstall smoke
- moved-tag opt-out smoke
- `ui-smoke` continuity evidence
- release issue evidence and close criteria

## Boundary

This guide does not automate release publication.

It does not add:

- daemon
- service
- hosted UI
- HTTP runtime
- external model API
- GraphRAG runtime
- vector DB
- graph DB
- package publishing
- legal/governance finalization

Smoke evidence is diagnostic. It is not correctness proof, security certification, access-control enforcement, or legal compliance certification.

Moving release tags remains exceptional and should be evidence-recorded.

## Inputs

Set the release version before starting:

```bash
VERSION=vX.Y.Z
```

Examples:

```bash
VERSION=v1.4.0
VERSION=v1.5.0
```

Expected release artifacts:

```text
docs/releases/notes/release-notes-${VERSION}.md
```

For versions with semantic file names, use the actual release notes path, for example:

```text
../notes/release-notes-v1.4.0.md
```

## 1. Pre-tag verification

Run from local `main`:

```bash
git checkout main
git pull --ff-only
git status --short
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected:

```text
chronicle X.Y.Z
```

`chronicle ui-smoke --json` should include:

```json
{
  "passed": true,
  "read_only": true,
  "server_started": false,
  "browser_required": false,
  "external_runtime": false
}
```

## 2. Create annotated tag

```bash
git tag -a "$VERSION" -m "Chronicle Stack $VERSION"
git push origin "$VERSION"
```

Record the push output in the release execution issue.

## 3. Verify tag/main equivalence

Use connector comparison, or locally:

```bash
git fetch origin main --tags
git rev-parse origin/main
git rev-parse "${VERSION}^{}"
```

For annotated tags, do not compare raw `git rev-parse $VERSION` to `HEAD` unless you intend to compare tag objects.

Annotated tag behavior:

```bash
git rev-parse "$VERSION"
```

may return the tag object SHA.

Use dereference syntax for the commit SHA:

```bash
git rev-parse "${VERSION}^{}"
```

Expected: `origin/main` and `${VERSION}^{}` point to the same commit for a release cut from latest `main`.

## 4. Publish GitHub Release

```bash
gh release create "$VERSION" \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack $VERSION" \
  --notes-file "docs/releases/notes/release-notes-${VERSION}.md"
```

When the notes path differs, pass the actual path:

```bash
gh release create v1.4.0 \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack v1.4.0" \
  --notes-file ../notes/release-notes-v1.4.0.md
```

### Already-existing release

If GitHub returns:

```text
Release.tag_name already exists
```

Interpretation:

- a GitHub Release for the tag already exists
- this can be accepted as release-existence evidence if the tag/main equivalence and release notes state are acceptable

If release notes need correction, use:

```bash
gh release edit "$VERSION" \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack $VERSION" \
  --notes-file "docs/releases/notes/release-notes-${VERSION}.md"
```

Record either creation URL or already-exists output in the release execution issue.

## 5. Clean installer smoke from tag

Use a version-specific smoke directory:

```bash
SMOKE=/tmp/chronicle-stack-${VERSION}-install-smoke
rm -rf "$SMOKE"
mkdir -p "$SMOKE"
cd "$SMOKE"

curl -fsSL "https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/${VERSION}/scripts/install-local.sh" -o install-local.sh
less install-local.sh

CHRONICLE_STACK_REF="$VERSION" \
INSTALL_DIR="$SMOKE/app" \
BIN_DIR="$SMOKE/bin" \
bash install-local.sh

"$SMOKE/bin/chronicle" --version
grep 'version =' "$SMOKE/app/pyproject.toml"
git -C "$SMOKE/app" rev-parse HEAD
git -C "$SMOKE/app" rev-parse "${VERSION}^{}"
```

Expected:

```text
chronicle X.Y.Z
version = "X.Y.Z"
```

`HEAD` and `${VERSION}^{}` should match.

## 6. Existing-checkout reinstall smoke

Run the installer again against the same install directory:

```bash
CHRONICLE_STACK_REF="$VERSION" \
INSTALL_DIR="$SMOKE/app" \
BIN_DIR="$SMOKE/bin" \
bash install-local.sh

"$SMOKE/bin/chronicle" --version
```

Expected logs include:

```text
Updating existing checkout
Fetching tag ref if available
Refreshing local tag from origin
Checked out commit
```

Expected version:

```text
chronicle X.Y.Z
```

## 7. Moved-tag opt-out smoke

The installer can preserve non-forced tag fetch semantics:

```bash
CHRONICLE_STACK_ALLOW_MOVED_TAG=0 \
CHRONICLE_STACK_REF="$VERSION" \
INSTALL_DIR="$SMOKE/app" \
BIN_DIR="$SMOKE/bin" \
bash install-local.sh

"$SMOKE/bin/chronicle" --version
```

Expected logs include:

```text
Moved-tag refresh disabled
```

Expected version:

```text
chronicle X.Y.Z
```

This confirms the opt-out path. It does not normalize moving release tags.

## 8. UI smoke continuity

Create a temporary Chronicle root:

```bash
UI_SMOKE=/tmp/chronicle-${VERSION}-ui-smoke
rm -rf "$UI_SMOKE"
mkdir -p "$UI_SMOKE"
cd "$UI_SMOKE"

"$SMOKE/bin/chronicle" init --title "$VERSION UI Smoke"
"$SMOKE/bin/chronicle" record --type user_input --actor user --summary "$VERSION ui-smoke event"
"$SMOKE/bin/chronicle" ui-smoke
"$SMOKE/bin/chronicle" ui-smoke --json
```

Expected JSON fields:

```json
{
  "passed": true,
  "read_only": true,
  "server_started": false,
  "browser_required": false,
  "external_runtime": false
}
```

## 9. Evidence comment checklist

Record evidence in the release execution issue.

Recommended comment sections:

```text
## Tag evidence
## GitHub Release publication evidence
## Clean installer smoke evidence
## Existing-checkout reinstall smoke evidence
## Opt-out moved-tag refresh smoke evidence
## UI smoke continuity evidence
## Release completion assessment
## Boundary note
```

Each comment should include enough output to verify:

- version
- tag or release status
- checked-out commit where applicable
- `chronicle --version`
- smoke pass flags
- no-daemon/no-service/no-external-runtime boundary

## 10. Close criteria

Close the release execution issue only after all required evidence is present:

- tag exists
- tag/latest-main equivalence is confirmed
- GitHub Release exists or already-exists output is recorded
- clean installer smoke passes
- existing-checkout reinstall smoke passes
- opt-out smoke passes when applicable
- installed `chronicle --version` matches release version
- installed `chronicle ui-smoke --json` passes
- boundary note is recorded

## Warning classification

- Release warning: this guide does not automate release execution.
- Installer warning: moved tags remain exceptional and evidence-recorded.
- Runtime warning: release execution must not imply daemon, service, hosted UI, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: smoke evidence is not security certification.
- Semantics warning: smoke evidence is not correctness proof or access-control enforcement.
- Legal warning: release execution does not finalize commercial/contributor legal documents.

## RDE review

### Preserved

- Evidence-based release execution.
- Local-first installer smoke.
- Inspect-first installer review.
- No-daemon/no-service/no-external-runtime boundaries.

### Transformed

- Repeated chat-driven release execution patterns become reusable repository documentation.

### Supplemented

- Already-existing release handling.
- Annotated tag dereference guidance.
- Existing-checkout and opt-out smoke guidance.
- Issue evidence comment structure.

### Unresolved

- Future release automation.
- Package publishing.
- Immutable tag governance.
- Full legal/governance finalization.

### Deviation risks

- Treating smoke evidence as certification.
- Normalizing moved release tags.
- Confusing repository-side readiness with release publication.
- Automating release publication before the evidence model is stable.
