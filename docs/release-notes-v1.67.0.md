# Release Notes v1.67.0

## Added

- retrieval dry-run plans now include composed cross-surface coverage across vector, graph, and Chronicle search hits
- runtime retrieval handoff details now expose overlap summaries and composed hit lists in the read-only UI

## Changed

- `chronicle runtime retrieve-plan` text output now reports composed coverage totals without implying any GraphRAG runtime

## Boundary

- composition remains local-only, read-only, and dry-run oriented
- Chronicle Stack still does not execute an external GraphRAG query runtime
