# Release Status v1.128.0

- lane: workspace table query helper
- status: implemented
- scope: normalize repeated list-query predicate composition across workspace tables without changing filter semantics or row payloads
- boundary: shared query helpers remain a read-only client-side filtering refactor and do not alter sort order, mutation controls, or review contracts
