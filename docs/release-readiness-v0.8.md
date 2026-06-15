# Chronicle Stack v0.8 Release Readiness

Status: readiness notes for v0.8 technical track  
Theme: Verified Package / Export Review Workflow

## Summary

v0.8 introduces a local package review checkpoint before package persistence or handoff.

The review workflow converts package and record warnings into an explicit report with one of three statuses:

- `pass`
- `warning`
- `blocked`

## Implemented surfaces

- `chronicle package review`
- JSON review report output
- persisted package review by package ID
- selected Context review by Context ID
- package review models
- package review service
- v0.8 package review workflow documentation
- v0.8 smoke profile

## Verification target

```bash
ruff check src/ tests/
pytest -v
```

Expected:

```text
all tests pass
```

## Boundary

v0.8 remains local-first and diagnostic.

It does not introduce:

- server runtime
- daemon runtime
- model API calls
- GraphRAG execution
- vector database dependency
- graph database dependency

## Relationship to earlier releases

- v0.6 established release packaging and controlled runtime boundaries.
- v0.7 made classification, audit, lifecycle, and doctor remediation operational.
- v0.8 uses those operational surfaces to review packages before handoff.

## Remaining parallel tracks

The following remain intentionally out of scope until explicitly directed:

- #26 commercial license template
- #27 CLA / DCO final policy
