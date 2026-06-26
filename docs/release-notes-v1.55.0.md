# Chronicle Stack v1.55.0 Release Notes

Chronicle Stack `v1.55.0` is a local transaction-and-rollback compact-badge i18n release over the published `v1.54.0` baseline.

## Added

- key-first localized compact `rollback=`, `transaction=`, and `durable-on-failure=` badges
- structured success/failure contract summaries reused by both preview and detail rendering
- regression coverage for localized success/failure compact summaries

## Kept stable

- local-first read-only preview-contract behavior
- append-only Chronicle record authority
- existing review success/failure semantics and fail-closed routing behavior
