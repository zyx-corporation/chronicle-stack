# Release Notes v1.69.0

## Added

- `query_engine_handoff` now includes an `import_validation` preview that checks alignment with the current derived graph export
- runtime detail UI now shows import-validation status, counts, and checks for the query-engine handoff

## Changed

- `chronicle runtime retrieve-plan` text output now summarizes downstream import-validation readiness

## Boundary

- validation remains preview-only and does not perform any downstream import
- Chronicle Stack still does not execute a query engine, graph runtime, or external retrieval runtime
