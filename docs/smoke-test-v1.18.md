# Chronicle Stack v1.18.0 Package, Parity, and Preview Structured i18n Smoke Profile

Related: `docs/release-readiness-v1.18.md`, `docs/release-status-v1.18.0.md`, `docs/release-notes-v1.18.0.md`, `docs/v1.18-release-remaining-issues.md`, `docs/adr/0037-local-package-parity-and-preview-structured-i18n.md`

## Purpose

This smoke profile validates the `v1.18.0` release track as a local package-parity-preview structured-i18n slice.

It is expected to confirm that:

- package-readiness and package-handoff payloads expose stable keys plus readable fallback strings
- action-preview and CLI parity payloads expose stable keys plus readable fallback strings
- HTML shell still renders package/parity/preview notices as read-only explanatory surfaces
- no new write capability is implied by the structured package/parity/preview fields

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
chronicle 1.18.0
```

## Manual spot checks

Confirm that:

- package-readiness and handoff previews include both stable keys and readable fallback messages
- action-preview and CLI parity summaries include both stable keys and readable fallback messages
- overview and detail preview notices keep read-only/local-first wording intact

## Boundary reminder

`v1.18.0` smoke for this slice must not certify hosted auth, multi-user safety, default-on mutation, correctness proof, or security certification.
