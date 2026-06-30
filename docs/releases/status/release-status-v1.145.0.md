# Release Status v1.145.0

- lane: review queue detail path fix
- status: implemented
- scope: restore review-queue first-column detail affordances by resolving row detail paths from `target_event_id`
- boundary: this release fixes read-only local UI navigation wiring only; it does not change review payloads, route contracts, mutation gates, or audit semantics
