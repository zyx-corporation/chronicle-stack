# Chronicle Stack v0.9 Release Deployment Procedure

Status: v0.9 release execution checklist  
Target: v0.9.0

## Scope

This document covers the v0.9.0 technical release execution path:

- local verification
- tag creation
- GitHub Release creation
- curl local installer smoke

It does not cover commercial licensing or contributor rights policy. #26 and #27 remain on hold until explicitly directed.

## Preconditions

```bash
git checkout main
git pull --ff-only

git status --short
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest -v
```

Expected:

```text
git status is clean
chronicle 0.9.0
ruff pass
pytest pass
```

## Tag

```bash
git tag -a v0.9.0 -m "Chronicle Stack v0.9.0"
git push origin v0.9.0
```

## GitHub Release notes

Suggested title:

```text
Chronicle Stack v0.9.0
```

Suggested summary:

```md
Chronicle Stack v0.9.0 is the Release Candidate Hardening and Version Finalization release.

Highlights:

- v0.7 operational workflows: classification, audit, lifecycle, and doctor remediation.
- v0.8 verified package review workflow.
- v0.9 project version finalization to `0.9.0`.
- v0.9 release readiness, smoke, and deployment procedure documentation.

Boundary:

- local-first CLI workflow
- no model API calls
- no GraphRAG runtime
- no vector DB or graph DB dependency
- no server or daemon runtime
- no commercial-license or CLA/DCO finalization
```

## curl installer smoke

```bash
rm -rf /tmp/chronicle-stack-v09-install-smoke
mkdir -p /tmp/chronicle-stack-v09-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v0.9.0/scripts/install-local.sh \
  -o /tmp/chronicle-install-local.sh

INSTALL_DIR=/tmp/chronicle-stack-v09-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v09-install-smoke/bin \
CHRONICLE_STACK_REF=v0.9.0 \
bash /tmp/chronicle-install-local.sh

/tmp/chronicle-stack-v09-install-smoke/bin/chronicle --version
```

Expected:

```text
chronicle 0.9.0
```

## Post-release smoke

Run the v0.9 smoke profile:

```text
../smoke/smoke-test-v0.9.md
```

## Completion criteria

- `v0.9.0` tag exists.
- GitHub Release exists.
- curl installer smoke reports `chronicle 0.9.0`.
- v0.9 smoke profile passes locally.
- #26 and #27 remain open/on hold unless explicitly directed otherwise.