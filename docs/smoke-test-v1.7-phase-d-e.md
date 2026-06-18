# Chronicle Stack v1.7 Phase D/E Placeholder AI Index Smoke Profile

## Purpose

This smoke profile validates the local placeholder AI index surface and its read-only UI visibility.

It focuses on:

- `chronicle ai-index status`
- placeholder vector add / search
- placeholder graph add-node / add-edge / neighbors
- read-only local UI AI index endpoints
- no-external-runtime boundary preservation

## Boundary

The Phase D/E placeholder AI index surface:

- does not call an LLM
- does not call an embedding provider
- does not use a vector DB
- does not use a graph DB
- does not start a GraphRAG runtime
- does not call external services
- does not turn derived helper state into a primary record
- does not add GUI mutation

## Pre-verification

Run:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

## Local fixture setup

```bash
rm -rf /tmp/chronicle-v17-ai-index-smoke
mkdir -p /tmp/chronicle-v17-ai-index-smoke
cd /tmp/chronicle-v17-ai-index-smoke

chronicle init --title "v1.7 AI Index Smoke"
chronicle record --type user_input --actor user --summary "v1.7 ai-index smoke event"
chronicle add-context --title "Smoke Context" --summary "v1.7 ai-index smoke context" --scope task
```

Find the created event and context IDs:

```bash
chronicle search "smoke" --json
```

## CLI smoke

```bash
chronicle ai-index status
chronicle ai-index status --json

chronicle ai-index vector add --record <EVENT_ID> --text "local placeholder vector text" --type event
chronicle ai-index vector search --query "placeholder vector"
chronicle ai-index vector search --query "placeholder vector" --json

chronicle ai-index graph add-node --id <EVENT_ID> --label event --property title="Smoke Event"
chronicle ai-index graph add-node --id <CONTEXT_ID> --label context --property title="Smoke Context"
chronicle ai-index graph add-edge --source <EVENT_ID> --target <CONTEXT_ID> --relation references
chronicle ai-index graph neighbors --id <EVENT_ID>
chronicle ai-index graph neighbors --id <EVENT_ID> --json
```

Expected:

- all commands exit 0
- vector status shows `embedding_provider=disabled`
- vector search returns local placeholder matches
- graph neighbors returns adjacency without external services

## Read-only UI smoke

```bash
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected read-only AI index payloads:

- `/api/ai-index-status`
- `/api/ai-index-vector`
- `/api/ai-index-graph-nodes`
- `/api/ai-index-graph-edges`

Expected JSON smoke fields remain:

```json
{
  "passed": true,
  "read_only": true,
  "server_started": false,
  "browser_required": false,
  "external_runtime": false
}
```

## Warning classification

- Runtime warning: placeholder AI index does not imply model runtime integration.
- Retrieval warning: placeholder search is assistive only.
- Storage warning: `.chronicle/ai_indexes/*` is derived helper state.
- UI warning: read-only visibility does not imply approval automation or GUI mutation.

## RDE review

Preserved: local-first primary record authority, no-external-runtime boundary, read-only UI posture.

Transformed: local graph-ready inspection now extends into placeholder adapter contracts.

Supplemented: CLI smoke and UI smoke expectations for placeholder AI index surfaces.

Unresolved: local LLM invocation, GraphRAG pipeline behavior, and mutation-capable GUI review flow.
