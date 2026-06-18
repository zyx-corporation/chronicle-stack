# Chronicle Stack v1.1 GUI Smoke Profile

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

Issue: #184

## Purpose

This smoke profile validates Chronicle Stack v1.1.0 as a GUI/readability release.

It focuses on:

- package version
- static Review Console export
- explicit `chronicle ui` command surface
- read-only local UI endpoint behavior
- runtime boundary preservation

## Boundary

The v1.1 GUI smoke profile must not imply that Chronicle Stack is a daemon, hosted service, access-control layer, model runtime, GraphRAG engine, vector DB, or graph DB.

`chronicle ui` is an explicitly launched foreground local UI.

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
chronicle 1.1.0
```

## Static Review Console smoke

```bash
rm -rf /tmp/chronicle-v11-review-console-smoke
mkdir -p /tmp/chronicle-v11-review-console-smoke
cd /tmp/chronicle-v11-review-console-smoke

chronicle init --title "v1.1 Review Console Smoke"
chronicle add-context --title "Smoke Context" --summary "Review console context" --visibility public
chronicle audit record --operation export --purpose "v1.1 smoke" --target local
chronicle lifecycle record --target ctx_dummy --target-kind context --action seal --reason "smoke marker"
chronicle export --format html -o review-console.html
```

Inspect `review-console.html` and confirm:

- `Chronicle Stack Review Console`
- Review Console boundary panel
- Package Review Snapshot
- Audit Events
- Lifecycle Markers
- no-daemon / no-server / no-external-runtime notes

## Local UI command smoke

```bash
chronicle ui --help
```

Expected:

- command exists
- options include `--host`, `--port`, `--open`, `--root`, `--json`

## Local UI startup metadata smoke

From an initialized Chronicle root:

```bash
chronicle ui --json --port 8765
```

Expected startup metadata before serving:

```json
{
  "host": "127.0.0.1",
  "port": 8765,
  "url": "http://127.0.0.1:8765",
  "read_only": true,
  "runtime": "foreground-local-ui",
  "external_runtime": false
}
```

Terminate with `Ctrl-C`.

## Local UI endpoint smoke

Start the UI in one terminal:

```bash
chronicle ui --port 8765
```

From another terminal:

```bash
curl -fsSL http://127.0.0.1:8765/ | grep "Chronicle Stack Local UI"
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
curl -fsSL http://127.0.0.1:8765/review-console | grep "Chronicle Stack Review Console"
```

Expected:

- `/` returns the lightweight local UI shell.
- `/review-console` returns the static Review Console.
- API endpoints return JSON.
- UI notes preserve the read-only / no-daemon / no-external-runtime boundary.

## Installer smoke from tag

After `v1.1.0` tag publication, run:

```bash
rm -rf /tmp/chronicle-stack-v11-install-smoke
mkdir -p /tmp/chronicle-stack-v11-install-smoke
cd /tmp/chronicle-stack-v11-install-smoke

curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/v1.1.0/scripts/install-local.sh -o install-local.sh
less install-local.sh

CHRONICLE_STACK_REF=v1.1.0 \
INSTALL_DIR=/tmp/chronicle-stack-v11-install-smoke/app \
BIN_DIR=/tmp/chronicle-stack-v11-install-smoke/bin \
bash install-local.sh

command /tmp/chronicle-stack-v11-install-smoke/bin/chronicle --version
command /tmp/chronicle-stack-v11-install-smoke/bin/chronicle ui --help
```

Expected:

```text
chronicle 1.1.0
```

## Warning classification

- Release warning: repository-side readiness is not tag/release publication.
- Runtime warning: UI smoke must not imply daemon, hosted service, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: localhost UI is still a browser-exposed local surface.
- Semantics warning: UI visibility is not access control or correctness proof.

## RDE review

Preserved: local-first, inspect-first, read-only, advisory/diagnostic semantics.

Transformed: v1.1 adds human-facing GUI/readability smoke to the release process.

Supplemented: Review Console smoke, `chronicle ui` command smoke, endpoint smoke, installer smoke from tag.

Unresolved: external tag/GitHub Release publication and final tag-based smoke evidence.
