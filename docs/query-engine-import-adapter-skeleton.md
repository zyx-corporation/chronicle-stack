# Query-Engine Import Adapter Skeleton

This document defines a descriptive adapter skeleton for downstream consumers that want to import Chronicle Stack handoff data.

You can regenerate the same skeleton shape from the current repository state with:

```bash
chronicle package query-engine-adapter --query "release planning context"
chronicle package query-engine-adapter --query "graph context" -o adapter-skeleton.json
```

## Example artifact

- JSON skeleton: `docs/examples/query-engine-import-adapter-skeleton.json`
- Handoff example: `docs/examples/query-engine-handoff-example.json`

## Purpose

The skeleton exists to show the order and boundaries of a downstream import adapter. It is not an executable adapter, and Chronicle Stack does not run it.

## Recommended sequence

1. Inspect `query_engine_handoff`
2. Inspect graph export contract
3. Materialize `graph-json` export
4. Verify `import_validation`
5. Hand responsibility to a downstream consumer implementation

## Boundary

- no hosted query engine
- no import execution inside Chronicle Stack
- no mutation of `.chronicle/chronicle.jsonl`
- no semantic-correctness certification
