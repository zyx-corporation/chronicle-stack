# Chronicle Stack v1.25.0 Release Status

Related: `docs/adr/0044-local-embedded-package-review-structured-contracts.md`, `docs/release-status-v1.24.0.md`

`v1.25.0` is the repository-side local embedded-package-review structured-contract release after the published `v1.24.0` baseline.

- Latest published release: `v1.24.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.24.0`
- Current repository-side release target: `v1.25.0`
- Lane scope: embedded package-review structured contracts on adjacent read-only package surfaces

## Current repository-side progress

Planned `v1.25.0` release progress includes:

- accepted ADR scope for embedded package-review structured contracts
- shared structured package-review payload decoration for nested read-only package surfaces
- smoke/test coverage for explicit embedded package-review contract fields
- version bump and release-readiness documents for `1.25.0`

## Boundary notes

Planned `v1.25.0` preserves:

- local-first single-operator scope
- read-only derived-surface discipline
- i18n presentation-only boundary
- primary Chronicle record authority over derived package-review wording

`v1.25.0` still must not imply:

- hosted auth or multi-user authority
- translated machine-readable status codes or ids
- broader GUI mutation authority
- correctness proof or security certification
