# Release Status v1.146.0

- lane: artifacts workspace renderer
- status: implemented
- scope: add a dedicated read model and renderer for `/api/artifacts` with route summary counts, richer list-level artifact context, and primary detail affordances
- boundary: this release improves read-only local UI presentation for artifact records only; it does not change artifact storage, proposal decision semantics, mutation gates, or audit contracts
