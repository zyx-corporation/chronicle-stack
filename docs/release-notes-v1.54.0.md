# Chronicle Stack v1.54.0 Release Notes

Chronicle Stack `v1.54.0` is a local write-route compact-badge i18n release over the published `v1.53.0` baseline.

## Added

- key-first localized compact badges for request fields, transaction order, authorization checks, and target-state checks
- structured reuse of status-code summaries for compact `success-status=` and `blocked-status=` badges
- regression coverage for localized compact write-route summaries

## Kept stable

- local-first read-only preview-contract behavior
- append-only Chronicle record authority
- existing review route, authorization, and target-state semantics
