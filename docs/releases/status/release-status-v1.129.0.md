# Release Status v1.129.0

- lane: shared review attention ranking helper
- status: implemented
- scope: normalize repeated review-oriented sort ranking logic without changing sort semantics or route-specific tie-break rules
- boundary: the helper remains a read-only client-side ordering refactor and does not alter row payloads, query filters, or mutation controls
