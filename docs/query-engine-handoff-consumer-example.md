# Query-Engine Handoff Consumer Example

This example shows how a downstream derived consumer can inspect Chronicle Stack handoff data without turning Chronicle Stack itself into a query engine.

## Fixture

- JSON fixture: `docs/examples/query-engine-handoff-example.json`
- Primary record remains `.chronicle/chronicle.jsonl`
- Graph export remains `graph-json`
- The fixture is descriptive and read-only

## Recommended local sequence

```bash
chronicle runtime retrieve-plan --query "release note context" --json
chronicle graph summary --json
chronicle export --format graph-json -o graph.json
chronicle package review --purpose "runtime query-engine handoff"
```

## What a downstream consumer may trust

- `contract_version`
- `graph_export_contract_version`
- `graph_incremental_mode`
- `referenced_record_ids`
- `eligible_context_ids`
- `import_validation.checks`

## What a downstream consumer must not assume

- Chronicle Stack includes a hosted query engine
- Chronicle Stack includes a graph runtime or vector runtime
- The handoff itself performs an import
- Derived consumer state becomes authoritative over Chronicle primary records

## Import-validation reading

A downstream consumer can treat `import_validation.status=contract_validated` as a structural alignment signal only.
It does not certify semantic correctness, ranking quality, security, or query-runtime behavior.
