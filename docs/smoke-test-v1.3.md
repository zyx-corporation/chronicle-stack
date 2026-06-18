# Chronicle Stack v1.3 UI Smoke Command Profile

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #194

## Purpose

This smoke profile validates Chronicle Stack v1.3.0 as an automated UI smoke / release-verification release.

It focuses on:

- package version
- `chronicle ui-smoke` text output
- `chronicle ui-smoke --json` machine-readable output
- initialized-root success behavior
- missing-root failure behavior
- no-server/no-browser/no-external-runtime boundary preservation

## Boundary

`chronicle ui-smoke` is a local read-only diagnostic command.

It does not:

- start `chronicle ui`
- bind sockets
- open a browser
- write Chronicle records
- call external model APIs
- embed GraphRAG
- use vector DB
- use graph DB
- certify correctness
- certify security

## Pre-release verification

Run from a clean checkout:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version:

```text
chronicle 1.3.0
```

## Local fixture setup

```bash
rm -rf /tmp/chronicle-v13-ui-smoke
mkdir -p /tmp/chronicle-v13-ui-smoke
cd /tmp/chronicle-v13-ui-smoke

chronicle init --title "v1.3 UI Smoke"
chronicle record --type user_input --actor user --summary "v1.3 ui-smoke event"
chronicle add-context --title "Smoke Context" --summary "v1.3 ui-smoke context" --visibility public
printf 'smoke artifact body\n' > artifact.md
chronicle artifact create --title "Smoke Artifact" --type document --file artifact.md --visibility private
chronicle boundary add --type warn --field visibility --operator equals --value private --reason "Smoke private visibility warning"
chronicle audit record --operation export --purpose "v1.3 smoke" --target local
chronicle lifecycle record --target smoke-target --target-kind context --action seal --reason "v1.3 smoke marker"
```

## Text smoke

```bash
chronicle ui-smoke
```

Expected:

- command exits with status 0
- output includes `Chronicle UI smoke`
- output includes `Mode: read-only, no server, no browser, no external runtime`
- output includes multiple `[PASS]` lines

## JSON smoke

```bash
chronicle ui-smoke --json
```

Expected JSON fields:

```text
passed: true
read_only: true
server_started: false
browser_required: false
external_runtime: false
checks: [...]
```

## Missing-root smoke

```bash
rm -rf /tmp/chronicle-v13-missing-root
mkdir -p /tmp/chronicle-v13-missing-root
chronicle ui-smoke --root /tmp/chronicle-v13-missing-root
```

Expected:

- command exits non-zero
- no server is started
- no browser is opened

## Installer smoke from tag

After `v1.3.0` tag publication, run:

```bash
rm -rf /tmp/chronicle-stack-v13-install-smoke
mkdir -p /tmp/chronicle-stack-v13-install-smoke
cd /tmp/chronicle-stack-v13-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v1.3.0/scripts/install-local.sh -o install-local.sh
less install-local.sh

CHRONICLE_STACK_REF=v1.3.0 \
INSTALL_DIR=/tmp/chronicle-stack-v13-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v13-install-smoke/bin \
bash install-local.sh

command /tmp/chronicle-stack-v13-install-smoke/bin/chronicle --version
command /tmp/chronicle-stack-v13-install-smoke/bin/chronicle ui-smoke --help
```

Expected:

```text
chronicle 1.3.0
```

## Warning classification

- Release warning: repository-side readiness is not tag/release publication.
- Runtime warning: UI smoke automation must not imply daemon, hosted service, browser automation, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: smoke pass is not security certification.
- Semantics warning: smoke pass is not correctness proof.

## RDE review

Preserved: local-first, inspect-first, read-only, advisory/diagnostic semantics.

Transformed: v1.3 makes UI smoke repeatable as a local command.

Supplemented: text smoke, JSON smoke, missing-root smoke, installer smoke from tag.

Unresolved: external tag/GitHub Release publication and final tag-based smoke evidence.
