# Chronicle Stack v0.9.0 Release Status

Status: ready for explicit tag and GitHub Release execution

## Prepared

- `pyproject.toml` version: `0.9.0`
- release notes: `../notes/release-notes-v0.9.0.md`
- release execution checklist: `../operations/release-execution-v0.9.0.md`
- release readiness: `../readiness/release-readiness-v0.9.md`
- smoke profile: `../smoke/smoke-test-v0.9.md`

## Verification reported

```text
283 passed
```

## Next manual commands

```bash
git checkout main
git pull --ff-only
git status --short
chronicle --version
ruff check src/ tests/
pytest -v

git tag -a v0.9.0 -m "Chronicle Stack v0.9.0"
git push origin v0.9.0

gh release create v0.9.0 \
  --repo zyx-corporation/chronicle-stack \
  --title "Chronicle Stack v0.9.0" \
  --notes-file ../notes/release-notes-v0.9.0.md
```
