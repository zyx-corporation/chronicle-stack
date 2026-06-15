# Chronicle Stack v0.8 Smoke Test

Status: v0.8 package review smoke profile  
Scope: local CLI workflow verification only

## Purpose

This smoke profile verifies the v0.8 package review workflow.

It checks:

- classified local Context package review returns `pass`
- unclassified Context package review returns `warning`
- sensitive Context targeted externally returns `blocked`
- persisted package review works

This smoke is a confidence check, not a formal proof of correctness.

## Workspace

```bash
rm -rf /tmp/chronicle-stack-v08-smoke
mkdir -p /tmp/chronicle-stack-v08-smoke
cd /tmp/chronicle-stack-v08-smoke
```

## Initialize

```bash
chronicle init --title "v0.8 Smoke"
```

## Create and classify Context

```bash
chronicle add-context \
  --title "Review Context" \
  --summary "safe context for package review" \
  --scope task \
  --visibility private \
  --json >/tmp/chronicle-stack-v08-smoke/context.json

CONTEXT_ID=$(python - <<'PY'
import json
print(json.load(open('/tmp/chronicle-stack-v08-smoke/context.json'))['context_id'])
PY
)

chronicle context classification set \
  --context "$CONTEXT_ID" \
  --layer internal \
  --sensitivity internal \
  --owner release-smoke \
  --reason "v0.8 smoke"
```

## Review selected local package

```bash
chronicle package review \
  --purpose "v0.8 smoke" \
  --target local \
  --context "$CONTEXT_ID"
```

Expected status: `pass`.

## Persist and review package

```bash
chronicle package context \
  --purpose "v0.8 persisted smoke" \
  --target local \
  --context "$CONTEXT_ID" \
  --persist

chronicle package list
chronicle package review --package <PACKAGE_ID>
```

Expected status: `pass`.

## Warning smoke

```bash
chronicle add-context \
  --title "Unclassified Review Context" \
  --summary "warning example" \
  --json >/tmp/chronicle-stack-v08-smoke/unclassified.json

UNCLASSIFIED_ID=$(python - <<'PY'
import json
print(json.load(open('/tmp/chronicle-stack-v08-smoke/unclassified.json'))['context_id'])
PY
)

chronicle package review \
  --purpose "v0.8 warning smoke" \
  --target local \
  --context "$UNCLASSIFIED_ID"
```

Expected status: `warning` with `unclassified_context`.

## Blocked smoke

```bash
chronicle add-context \
  --title "Sensitive External Review Context" \
  --summary "sensitive context" \
  --json >/tmp/chronicle-stack-v08-smoke/sensitive.json

SENSITIVE_ID=$(python - <<'PY'
import json
print(json.load(open('/tmp/chronicle-stack-v08-smoke/sensitive.json'))['context_id'])
PY
)

chronicle context classification set \
  --context "$SENSITIVE_ID" \
  --layer sensitive_context \
  --sensitivity sensitive \
  --owner release-smoke \
  --reason "v0.8 blocked smoke"

chronicle package review \
  --purpose "v0.8 blocked smoke" \
  --target external \
  --context "$SENSITIVE_ID"
```

Expected status: `blocked` with `external_sensitive_context_not_allowed`.

## Boundary

This smoke profile does not call a model API, run GraphRAG, run a server, or require vector/graph databases.
