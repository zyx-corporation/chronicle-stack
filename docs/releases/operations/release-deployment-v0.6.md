# Chronicle Stack v0.6 Release Deployment Procedure

Status: v0.6 release execution checklist  
Target: v0.6.0  
Scope: Git tag / GitHub Release / local installer verification

## Purpose

This document describes how to deploy the v0.6.0 release of Chronicle Stack.

In this project, release deployment means:

```text
create and push the release tag
publish the GitHub Release
verify the local curl installer against the published ref
confirm documentation and metadata alignment
```

It does not mean deploying a server, daemon, HTTP runtime, model runtime, GraphRAG engine, vector database, or graph database.

## Preconditions

Before release deployment:

- `main` contains the v0.6.0 metadata update.
- `pyproject.toml` reports `0.6.0`.
- `CHANGELOG.md` contains the v0.6.0 section.
- `../readiness/release-readiness-v0.6.md` exists.
- `../smoke/smoke-test-v0.6.md` exists.
- `../../local-deployment-curl.md` exists.
- No v0.6 implementation issue remains open.
- Open legal/commercial issues, if any, are explicitly non-blocking for AGPL OSS technical release.

Known non-blocking legal/commercial issues:

```text
#26 Commercial license template remains private/future work.
#27 CLA/DCO final policy remains future work.
```

These affect commercial licensing and large external contribution handling, not the AGPL public technical release.

## Preflight Commands

From a clean checkout:

```bash
git checkout main
git pull --ff-only

git status --short
python -m pip install -e ".[dev]"
ruff check src/ tests/
pytest -v
chronicle --version
```

Expected:

```text
git status is clean
ruff pass
pytest pass
chronicle 0.6.0
```

If `chronicle --version` does not report `0.6.0`, do not tag.

## Smoke Checklist

Run or consciously defer the manual smoke checklist in:

```text
../smoke/smoke-test-v0.6.md
```

If deferred, record that in the GitHub Release body.

Smoke success is confidence only. It is not semantic correctness or security certification.

## Create the Tag

Use an annotated tag.

```bash
git checkout main
git pull --ff-only

git tag -a v0.6.0 -m "Chronicle Stack v0.6.0"
git push origin v0.6.0
```

Verify the tag points to the expected commit:

```bash
git rev-parse v0.6.0
git rev-parse origin/main
```

The two SHAs should match unless intentionally tagging an earlier commit.

## GitHub Release

Create a GitHub Release for:

```text
Tag: v0.6.0
Title: Chronicle Stack v0.6.0
```

Suggested release body:

```markdown
# Chronicle Stack v0.6.0

Chronicle Stack v0.6.0 is the Observation Gates and Controlled Runtime Integration Boundaries release.

## Highlights

- Observation E2E boundary documentation.
- Package persistence and package inspection.
- Lifecycle-aware exports for Markdown, YAML, HTML, and graph-json.
- Primary CLI aliases:
  - `chronicle package ...`
  - `chronicle context ...`
  - `chronicle graph ...`
  - `chronicle export profile ...`
- curl-based local CLI installer.
- Future HTTP bridge auth dependency boundary guidance.

## Local install

Inspect-first:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v0.6.0/scripts/install-local.sh -o /tmp/chronicle-install-local.sh
less /tmp/chronicle-install-local.sh
CHRONICLE_STACK_REF=v0.6.0 bash /tmp/chronicle-install-local.sh
```

One-liner:

```bash
CHRONICLE_STACK_REF=v0.6.0 \
  curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v0.6.0/scripts/install-local.sh | bash
```

## Boundaries

- Core CI pass is not semantic correctness certification.
- Smoke success is not semantic correctness or security certification.
- Observation E2E is documented but no runner is included.
- Lifecycle-aware export is derived-output filtering, not physical deletion or access-control enforcement.
- Package persistence is a transport artifact, not a permission grant or external submission.
- No external model calls, GraphRAG engine, Sayane runtime, vector DB, graph DB, HTTP runtime, real encrypted backend, or key management are introduced.
- Commercial license template and CLA/DCO final policy remain future/private work.
```

## Verify curl Installer Against Tag

After the tag is pushed, run the installer against the tag in a temporary environment.

Inspect-first:

```bash
rm -rf /tmp/chronicle-stack-install-smoke
mkdir -p /tmp/chronicle-stack-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v0.6.0/scripts/install-local.sh \
  -o /tmp/chronicle-install-local.sh
less /tmp/chronicle-install-local.sh

INSTALL_DIR=/tmp/chronicle-stack-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-install-smoke/bin \
CHRONICLE_STACK_REF=v0.6.0 \
bash /tmp/chronicle-install-local.sh

/tmp/chronicle-stack-install-smoke/bin/chronicle --version
/tmp/chronicle-stack-install-smoke/bin/chronicle --help
```

Expected:

```text
chronicle 0.6.0
```

Then run a minimal local smoke:

```bash
mkdir -p /tmp/chronicle-stack-install-smoke/project
cd /tmp/chronicle-stack-install-smoke/project

/tmp/chronicle-stack-install-smoke/bin/chronicle init --title "Install Smoke"
/tmp/chronicle-stack-install-smoke/bin/chronicle add-context --title "Install Context" --summary "release install smoke" --scope task --visibility private
/tmp/chronicle-stack-install-smoke/bin/chronicle doctor
/tmp/chronicle-stack-install-smoke/bin/chronicle export --format yaml >/tmp/chronicle-stack-install-smoke/export.yaml
```

Expected:

- commands exit successfully unless doctor reports advisory warnings
- `.chronicle/chronicle.jsonl` exists
- YAML export is created
- no external model/runtime service is called

## Post-release Checks

Confirm:

```bash
git ls-remote --tags origin v0.6.0
```

Confirm GitHub Release page exists:

```text
https://github.com/zyx-corporation/chronicle-stack/releases/tag/v0.6.0
```

Confirm README links are valid after release publication.

## Rollback / Correction

If the tag was pushed to the wrong commit and no one has consumed it yet:

```bash
git tag -d v0.6.0
git push origin :refs/tags/v0.6.0
```

Then correct `main`, recreate the tag, and republish the release.

If the release has already been consumed, prefer publishing a corrective patch release such as:

```text
v0.6.1
```

Avoid silently moving a public tag after users may have installed from it.

## Non-goals

This deployment procedure does not:

- install a server
- install a daemon
- publish to PyPI
- create a Docker image
- create a Homebrew formula
- implement an Observation E2E runner
- certify semantic correctness
- certify security
- provide access-control enforcement
- provide physical deletion or lifecycle enforcement

## RDE Review

### Preserved

- local-first release model
- Core CI as primary phase gate
- tag/release separation from runtime deployment
- no-external-runtime boundary

### Transformed

- release execution becomes repeatable and inspectable
- curl installer verification becomes part of the release process

### Complemented

- release notes include explicit non-certification boundaries
- rollback policy is documented

### Unresolved

- actual tag creation
- actual GitHub Release publication
- future PyPI / package-manager distribution
- formal Observation E2E runner

### Deviation Risks

- do not treat release publication as semantic correctness proof
- do not treat `curl | bash` as risk-free
- do not move a public tag after users may have consumed it
- do not imply local CLI install is server deployment
