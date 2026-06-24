# Chronicle Stack v1.19.0 Navigation, Provider Response, and Runtime Preview Structured i18n Smoke Profile

Related: `docs/release-readiness-v1.19.md`, `docs/release-status-v1.19.0.md`, `docs/release-notes-v1.19.0.md`, `docs/v1.19-release-remaining-issues.md`, `docs/adr/0038-local-navigation-provider-response-and-runtime-preview-structured-i18n.md`

## Purpose

This smoke profile validates the `v1.19.0` release track as a local navigation-provider-response-runtime-preview structured-i18n slice.

It is expected to confirm that:

- related-link navigation payloads expose stable keys plus readable fallback labels
- provider-response summaries expose stable keys plus readable fallback messages
- runtime-preview titles expose stable keys plus readable fallback titles
- HTML shell still renders navigation and runtime-observability notices as read-only explanatory surfaces
- no new write capability is implied by the structured navigation/provider/runtime fields

## Required verification

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected current version baseline:

```text
chronicle 1.19.0
```

## Manual spot checks

Confirm that:

- related links include both stable keys and readable fallback labels
- provider-response summaries include both stable keys and readable fallback messages
- runtime-preview titles include both stable keys and readable fallback titles

## Boundary reminder

`v1.19.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
