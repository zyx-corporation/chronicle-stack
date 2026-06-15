# Chronicle Stack v0.9 Smoke Test

Status: v0.9 release candidate smoke profile  
Scope: local CLI workflow verification only

## Purpose

This smoke profile verifies the v0.9 release candidate after v0.7 and v0.8 technical tracks.

It checks:

- CLI version
- initialization
- doctor
- context classification
- audit event workflow
- lifecycle marker workflow
- package review workflow
- derived export availability

## Workspace

```bash
rm -rf /tmp/chronicle-stack-v09-smoke
mkdir -p /tmp/chronicle-stack-v09-smoke
cd /tmp/chronicle-stack-v09-smoke
```

## Version

```bash
chronicle --version
```

Expected:

```text
chronicle 0.9.0
```

## Initialize

```bash
chronicle init --title "v0.9 Smoke"
```

## Create Context

```bash
chronicle add-context \
  --title "v0.9 Release Candidate Context" \
  --summary "context for v0.9 release candidate smoke" \
  --scope task \
  --visibility private \
  --json >/tmp/chronicle-stack-v09-smoke/context.json

CONTEXT_ID=$(python - <<'PY'
import json
print(json.load(open('/tmp/chronicle-stack-v09-smoke/context.json'))['context_id'])
PY
)
```

## v0.7 operational workflows

```bash
chronicle context classification set \
  --context "$CONTEXT_ID" \
  --layer internal \
  --sensitivity internal \
  --owner release-smoke \
  --reason "v0.9 smoke"

chronicle audit record \
  --operation export \
  --purpose "v0.9 smoke" \
  --target local \
  --summary "v0.9 audit smoke"

chronicle lifecycle record \
  --target "$CONTEXT_ID" \
  --target-kind context \
  --action seal \
  --reason "v0.9 smoke"
```

## v0.8 package review

```bash
chronicle package review \
  --purpose "v0.9 smoke" \
  --target local \
  --context "$CONTEXT_ID"
```

Expected status: `pass`.

## Doctor

```bash
chronicle doctor
```

Expected:

- classification check is ok
- audit log check is ok
- lifecycle log check is ok
- graph export remains available
- HTML export remains available

## Derived exports

```bash
chronicle export --format yaml >/tmp/chronicle-stack-v09-smoke/export.yaml
chronicle export --format graph-json -o /tmp/chronicle-stack-v09-smoke/graph.json
chronicle export --format html -o /tmp/chronicle-stack-v09-smoke/dashboard.html
```

Expected:

- YAML export is created
- graph-json export is created
- HTML dashboard export is created

## Boundary

This smoke profile does not call a model API, run GraphRAG, run a server, or require vector/graph databases.