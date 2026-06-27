# Downstream Query-Engine Handoff Bundle

This document describes the local read-only bundle that Chronicle Stack can generate for downstream query-engine consumers.

## Generate

```bash
chronicle package query-engine-bundle --query "release planning context" --output-dir handoff-bundle
```

## Bundle contents

- `bundle_manifest.json`
- `query_engine_handoff.json`
- `query_engine_adapter_skeleton.json`
- `graph.json`
- `ACCEPTANCE_CHECKLIST.md`
- `TRIAL_REPORT_TEMPLATE.md`

## Intended use

- inspect the current handoff contract
- inspect the non-executable adapter skeleton
- inspect the derived `graph-json` export
- review the bundled acceptance checklist before asking for a separate implementation repo
- record the real downstream trial outcome with the bundled trial report template
- persist the trial result back into Chronicle with the trial-record command when needed
- hand the bundle to a downstream consumer repo without making Chronicle Stack itself executable as a query engine

## Boundary

- local output only
- read-only and descriptive only
- no hosted query engine
- no downstream import execution inside Chronicle Stack
- no mutation of `.chronicle/chronicle.jsonl`
