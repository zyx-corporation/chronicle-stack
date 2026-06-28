# Chronicle Stack v1.2 UI Detail Smoke Profile

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #189

## Purpose

This smoke profile validates Chronicle Stack v1.2.0 as a UI drill-down / inspectability release.

It focuses on:

- package version
- `chronicle ui` collection endpoints
- `chronicle ui` read-only detail endpoints
- static Review Console availability
- runtime boundary preservation

## Boundary

The v1.2 UI smoke profile must not imply that Chronicle Stack is a daemon, hosted service, access-control layer, model runtime, GraphRAG engine, vector DB, or graph DB.

`chronicle ui` is an explicitly launched foreground local UI. Detail endpoints are read-only derived views over local Chronicle files.

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
chronicle 1.2.0
```

## Local UI fixture setup

```bash
rm -rf /tmp/chronicle-v12-ui-smoke
mkdir -p /tmp/chronicle-v12-ui-smoke
cd /tmp/chronicle-v12-ui-smoke

chronicle init --title "v1.2 UI Detail Smoke"
chronicle record --type user_input --actor user --summary "v1.2 detail smoke event"
chronicle add-context --title "Smoke Context" --summary "v1.2 detail smoke context" --visibility public
printf 'smoke artifact body\n' > artifact.md
chronicle artifact create --title "Smoke Artifact" --type document --file artifact.md --visibility private
chronicle boundary add --type warn --field visibility --operator equals --value private --reason "Smoke private visibility warning"
chronicle audit record --operation export --purpose "v1.2 smoke" --target local
chronicle lifecycle record --target smoke-target --target-kind context --action seal --reason "v1.2 smoke marker"
chronicle export --format html -o review-console.html
```

Confirm static output:

```bash
grep "Chronicle Stack Review Console" review-console.html
```

## Local UI startup smoke

Start the UI in one terminal:

```bash
chronicle ui --port 8765
```

From another terminal:

```bash
curl -fsSL http://127.0.0.1:8765/ | grep "Chronicle Stack Local UI"
curl -fsSL http://127.0.0.1:8765/review-console | grep "Chronicle Stack Review Console"
```

## Collection endpoint smoke

```bash
curl -fsSL http://127.0.0.1:8765/api/overview
curl -fsSL http://127.0.0.1:8765/api/events
curl -fsSL http://127.0.0.1:8765/api/contexts
curl -fsSL http://127.0.0.1:8765/api/artifacts
curl -fsSL http://127.0.0.1:8765/api/decisions
curl -fsSL http://127.0.0.1:8765/api/rde
curl -fsSL http://127.0.0.1:8765/api/boundary
curl -fsSL http://127.0.0.1:8765/api/audit
curl -fsSL http://127.0.0.1:8765/api/lifecycle
curl -fsSL http://127.0.0.1:8765/api/package-review
curl -fsSL http://127.0.0.1:8765/api/graph-summary
```

Expected:

- all endpoints return JSON
- `/api/overview` includes `counts`
- no endpoint mutates primary Chronicle records

## Detail endpoint smoke

Extract IDs from collection endpoints, then request detail endpoints:

```bash
EVENT_ID=$(curl -fsSL http://127.0.0.1:8765/api/events | python -c 'import json,sys; print(json.load(sys.stdin)["events"][0]["event_id"])')
CONTEXT_ID=$(curl -fsSL http://127.0.0.1:8765/api/contexts | python -c 'import json,sys; print(json.load(sys.stdin)["contexts"][0]["context_id"])')
ARTIFACT_ID=$(curl -fsSL http://127.0.0.1:8765/api/artifacts | python -c 'import json,sys; print(json.load(sys.stdin)["artifacts"][0]["artifact_id"])')
BOUNDARY_ID=$(curl -fsSL http://127.0.0.1:8765/api/boundary | python -c 'import json,sys; print(json.load(sys.stdin)["boundary_rules"][0]["rule_id"])')
AUDIT_ID=$(curl -fsSL http://127.0.0.1:8765/api/audit | python -c 'import json,sys; print(json.load(sys.stdin)["audit_events"][0]["audit_id"])')
LIFECYCLE_ID=$(curl -fsSL http://127.0.0.1:8765/api/lifecycle | python -c 'import json,sys; print(json.load(sys.stdin)["lifecycle_markers"][0]["lifecycle_id"])')

curl -fsSL "http://127.0.0.1:8765/api/events/$EVENT_ID"
curl -fsSL "http://127.0.0.1:8765/api/contexts/$CONTEXT_ID"
curl -fsSL "http://127.0.0.1:8765/api/artifacts/$ARTIFACT_ID"
curl -fsSL "http://127.0.0.1:8765/api/boundary/$BOUNDARY_ID"
curl -fsSL "http://127.0.0.1:8765/api/audit/$AUDIT_ID"
curl -fsSL "http://127.0.0.1:8765/api/lifecycle/$LIFECYCLE_ID"
```

Expected:

- each detail endpoint returns JSON with a `record` field
- artifact detail includes `versions`

## Not-found smoke

```bash
curl -i http://127.0.0.1:8765/api/contexts/missing
```

Expected:

```text
HTTP/1.0 404 Not found
```

## Installer smoke from tag

After `v1.2.0` tag publication, run:

```bash
rm -rf /tmp/chronicle-stack-v12-install-smoke
mkdir -p /tmp/chronicle-stack-v12-install-smoke
cd /tmp/chronicle-stack-v12-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v1.2.0/scripts/install-local.sh -o install-local.sh
less install-local.sh

CHRONICLE_STACK_REF=v1.2.0 \
INSTALL_DIR=/tmp/chronicle-stack-v12-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v12-install-smoke/bin \
bash install-local.sh

command /tmp/chronicle-stack-v12-install-smoke/bin/chronicle --version
command /tmp/chronicle-stack-v12-install-smoke/bin/chronicle ui --help
```

Expected:

```text
chronicle 1.2.0
```

## Warning classification

- Release warning: repository-side readiness is not tag/release publication.
- Runtime warning: UI drill-down must not imply daemon, hosted service, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: localhost UI remains a browser-exposed local surface.
- Semantics warning: detail views are not access control or correctness proof.

## RDE review

Preserved: local-first, inspect-first, read-only, advisory/diagnostic semantics.

Transformed: v1.2 adds record-level inspection smoke to the UI release process.

Supplemented: collection endpoint smoke, detail endpoint smoke, not-found smoke, installer smoke from tag.

Unresolved: external tag/GitHub Release publication and final tag-based smoke evidence.
