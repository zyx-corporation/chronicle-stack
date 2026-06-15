# Chronicle Stack v0.9 Release Readiness

Status: v0.9 release candidate readiness  
Theme: Release Candidate Hardening and Version Finalization

## Summary

v0.9 finalizes the current technical release candidate after the v0.7 operational hardening and v0.8 package review tracks.

The release candidate includes:

- v0.7 classification, audit, lifecycle, and doctor remediation workflows
- v0.8 package review workflow
- v0.9 project version finalization
- v0.9 smoke and release deployment guidance

## Version

Expected package version:

```text
0.9.0
```

Expected CLI output:

```bash
chronicle --version
```

```text
chronicle 0.9.0
```

## Verification target

Run:

```bash
ruff check src/ tests/
pytest -v
```

Expected:

```text
all tests pass
```

## Release candidate smoke

Use:

```text
docs/smoke-test-v0.9.md
```

The smoke profile should verify:

- CLI version reports `chronicle 0.9.0`
- doctor remains available
- v0.7 operational workflows remain available
- v0.8 package review remains available
- derived exports remain available

## Boundary

v0.9 remains a local-first technical release candidate.

It does not introduce:

- server runtime
- daemon runtime
- model API calls
- GraphRAG execution
- vector database dependency
- graph database dependency

## Out of scope

The following remain intentionally held until explicit direction:

- #26 commercial license template
- #27 CLA / DCO final policy

## Release checklist

- `pyproject.toml` version is `0.9.0`.
- `CHANGELOG.md` includes v0.9.0.
- README points to v0.7, v0.8, and v0.9 technical docs.
- v0.9 smoke doc exists.
- v0.9 deployment procedure exists.
- local verification passes.
- tag and GitHub Release are created only after explicit release execution.