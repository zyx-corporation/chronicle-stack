# Chronicle Stack v1.4 Installer Hardening Smoke Profile

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #201

## Purpose

This smoke profile validates Chronicle Stack v1.4.0 as a local installer hardening release.

It focuses on:

- package version
- clean installer smoke
- existing checkout reinstall smoke
- moved/recreated tag awareness
- `CHRONICLE_STACK_ALLOW_MOVED_TAG` boundary
- continued no-daemon/no-service/no-external-runtime installer semantics

## Boundary

The local installer remains an inspect-first CLI installer.

It does not install:

- daemon
- service
- hosted UI
- HTTP runtime
- external model API
- GraphRAG runtime
- vector DB
- graph DB

Installer success is diagnostic, not correctness proof or security certification.

## Pre-release verification

Run from a clean checkout:

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
chronicle 1.4.0
```

## Clean installer smoke from tag

After `v1.4.0` tag publication:

```bash
rm -rf /tmp/chronicle-stack-v14-install-smoke
mkdir -p /tmp/chronicle-stack-v14-install-smoke
cd /tmp/chronicle-stack-v14-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v1.4.0/scripts/install-local.sh -o install-local.sh
less install-local.sh

CHRONICLE_STACK_REF=v1.4.0 \
INSTALL_DIR=/tmp/chronicle-stack-v14-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v14-install-smoke/bin \
bash install-local.sh

/tmp/chronicle-stack-v14-install-smoke/bin/chronicle --version
grep 'version =' /tmp/chronicle-stack-v14-install-smoke/app/pyproject.toml
git -C /tmp/chronicle-stack-v14-install-smoke/app rev-parse HEAD
git -C /tmp/chronicle-stack-v14-install-smoke/app rev-parse v1.4.0
```

Expected:

```text
chronicle 1.4.0
version = "1.4.0"
```

The two `rev-parse` commands should resolve to the same commit.

## Existing checkout reinstall smoke

Rerun installer against the same checkout:

```bash
CHRONICLE_STACK_REF=v1.4.0 \
INSTALL_DIR=/tmp/chronicle-stack-v14-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v14-install-smoke/bin \
bash install-local.sh

/tmp/chronicle-stack-v14-install-smoke/bin/chronicle --version
```

Expected:

```text
chronicle 1.4.0
```

Installer logs should include:

```text
Updating existing checkout
Fetching tag ref if available
Refreshing local tag from origin
Checked out commit
```

## Opt-out smoke

The forced moved-tag refresh can be disabled:

```bash
CHRONICLE_STACK_ALLOW_MOVED_TAG=0 \
CHRONICLE_STACK_REF=v1.4.0 \
INSTALL_DIR=/tmp/chronicle-stack-v14-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v14-install-smoke/bin \
bash install-local.sh
```

Expected log includes:

```text
Moved-tag refresh disabled
```

This mode preserves ordinary non-forced tag fetch semantics.

## UI smoke continuity

After install, confirm v1.3 UI smoke still works:

```bash
rm -rf /tmp/chronicle-v14-ui-smoke
mkdir -p /tmp/chronicle-v14-ui-smoke
cd /tmp/chronicle-v14-ui-smoke

/tmp/chronicle-stack-v14-install-smoke/bin/chronicle init --title "v1.4 UI Smoke"
/tmp/chronicle-stack-v14-install-smoke/bin/chronicle record --type user_input --actor user --summary "v1.4 ui-smoke event"
/tmp/chronicle-stack-v14-install-smoke/bin/chronicle ui-smoke
/tmp/chronicle-stack-v14-install-smoke/bin/chronicle ui-smoke --json
```

Expected JSON fields:

```text
passed: true
server_started: false
browser_required: false
external_runtime: false
```

## Warning classification

- Release warning: repository-side readiness is not tag/release publication.
- Installer warning: moved tags remain exceptional and evidence-recorded.
- Runtime warning: installer hardening must not add daemon, service, hosted UI, model API, GraphRAG runtime, vector DB, or graph DB.
- Semantics warning: installer smoke is diagnostic, not correctness or security certification.

## RDE review

Preserved: inspect-first, local-first, no daemon, no service, no external runtime.

Transformed: v1.4 turns a v1.3 retag incident into installer hardening and release smoke guidance.

Supplemented: clean installer smoke, existing checkout smoke, opt-out smoke, tag resolution checks.

Unresolved: external tag/GitHub Release publication and final v1.4.0 installer smoke evidence.
