# Chronicle Stack v0.7 Smoke Test

Status: v0.7 operational hardening smoke profile  
Scope: local CLI workflow verification only

## Purpose

This smoke profile verifies the v0.7 operational hardening path:

- Context classification metadata workflow
- local audit event workflow
- advisory lifecycle marker workflow
- doctor guidance
- derived export availability after the above workflows

This smoke test is a confidence check. It is not a formal proof of correctness.

## Workspace

```bash
rm -rf /tmp/chronicle-stack-v07-smoke
mkdir -p /tmp/chronicle-stack-v07-smoke
cd /tmp/chronicle-stack-v07-smoke
```

## Initialize and create Context

```bash
chronicle init --title "v0.7 Smoke"
chronicle add-context \
  --title "Operational Context" \
  --summary "context for v0.7 smoke" \
  --scope task \
  --visibility private \
  --json >/tmp/chronicle-stack-v07-smoke/context.json

CONTEXT_ID=$(python - <<'PY'
import json
print(json.load(open('/tmp/chronicle-stack-v07-smoke/context.json'))['context_id'])
PY
)
```

## Observe initial warnings

```bash
chronicle doctor
```

Expected early warnings may include missing classification metadata, missing audit log, and missing lifecycle log. These are expected before the remediation steps below.

## Classification metadata workflow

```bash
chronicle context classification missing
chronicle context classification set \
  --context "$CONTEXT_ID" \
  --layer internal \
  --sensitivity internal \
  --owner release-smoke \
  --reason "v0.7 smoke"
chronicle context classification show --context "$CONTEXT_ID"
```

Boundary: classification metadata is advisory metadata.

## Audit event workflow

```bash
chronicle audit record \
  --operation export \
  --purpose "v0.7 smoke" \
  --target local \
  --summary "audit smoke"
chronicle audit list
```

Boundary: audit events improve traceability.

## Lifecycle marker workflow

```bash
chronicle lifecycle record \
  --target "$CONTEXT_ID" \
  --target-kind context \
  --action seal \
  --reason "v0.7 smoke"
chronicle lifecycle list
```

Boundary: lifecycle markers are advisory metadata.

## Doctor after remediation

```bash
chronicle doctor
```

Expected:

- `security_context_classification_present` is ok
- `security_audit_log_parseable` is ok
- `security_lifecycle_log_parseable` is ok
- graph export remains available
- HTML export remains available

## Derived export checks

```bash
chronicle export --format yaml >/tmp/chronicle-stack-v07-smoke/export.yaml
chronicle export --format graph-json -o /tmp/chronicle-stack-v07-smoke/graph.json
chronicle export --format html -o /tmp/chronicle-stack-v07-smoke/dashboard.html
```

Expected:

- YAML export is created
- graph-json export is created
- HTML dashboard export is created
- no external model/runtime service is called

## Non-goals

This smoke profile does not install or run a server, daemon, model API, GraphRAG engine, vector DB, or graph DB.

## RDE review

### Preserved

- local-first CLI workflow
- JSONL primary record boundary
- derived export boundary
- diagnostic doctor posture

### Transformed

- v0.6 advisory warnings become v0.7 actionable workflows

### Complemented

- classification, audit, and lifecycle surfaces now have smoke-visible paths
