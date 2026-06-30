# Release Readiness v1.122

- status: ready
- checks:
  - `./.venv/bin/ruff check src tests`
  - `./.venv/bin/pytest -q`
- notes:
  - runtime records, review queue, and summary jobs workspace panels now share helper lines for counts and latest-response placement
  - panel semantics remain unchanged while presentation vocabulary is more consistent
