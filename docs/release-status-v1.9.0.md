# Chronicle Stack v1.9.0 Release Status

## Status

Repository-side release preparation and external publication for `v1.9.0` are complete.

- Latest published release: `v1.9.0`
- Release URL: `https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.9.0`
- Current repository-side release target: `v1.10.0`

## Release scope

This release track means:

- local reviewer/session enforcement-boundary clarification
- contract-aligned strengthening of reviewer/session mutation semantics
- local mutation-boundary wording hardening after `v1.8.0`

## Published release progress

Completed `v1.9.0` release work includes:

- ADR-0028 defining the local reviewer/session enforcement boundary
- a release-lane handoff from the completed `v1.8.0` contract-hardening release
- structured `reviewer_enforcement_summary` exposure on UI boundary, mutation-readiness, and review-action surfaces
- wording alignment that distinguishes route-enforced reviewer/session conditions from descriptive read-only metadata
- structured `reviewer_validation_gate_summary` exposure that keeps validation, authorization, target-state, and fail-closed write-path language aligned
- dedicated `v1.9.0` release-readiness, release-notes, and smoke entry points
- version bump and changelog update for `1.9.0`
- published tag and GitHub Release evidence

## Verification evidence

Current repository-side and published-tag verification for `v1.9.0` includes:

- editable reinstall refreshed package metadata to `1.9.0`
- local CLI reported `chronicle 1.9.0`
- `ruff check src/ tests/` passed
- full `pytest` passed
- local `ui-smoke --json` passed for a temporary Chronicle root prepared for `v1.9.0` smoke verification
- repo-side `ui-smoke` text evidence was recorded from `/tmp/chronicle-stack-v1.9.0-repo-smoke.31opkS/ui-smoke.txt`
- repo-side `ui-smoke` JSON evidence was recorded from `/tmp/chronicle-stack-v1.9.0-repo-smoke.31opkS/ui-smoke.json`
- clean install smoke was recorded from `/tmp/chronicle-stack-v1.9.0-install-smoke.bDimjW/install.log`
- installed tag version output was confirmed as `chronicle 1.9.0`
- published-tag `ui-smoke --json` evidence was recorded from `/tmp/chronicle-stack-v1.9.0-tag-ui-smoke.ZYP08E/ui-smoke.json`

## Current release documents

- `docs/adr/0028-local-reviewer-session-enforcement-boundary.md`
- `docs/release-readiness-v1.9.md`
- `docs/release-notes-v1.9.0.md`
- `docs/smoke-test-v1.9.md`
- `docs/v1.9-release-remaining-issues.md`

## Historical context

These records provide the immediate upstream context for the `v1.9.0` lane:

- `docs/release-status-v1.8.0.md`
- `docs/v1.8-release-remaining-issues.md`
- `docs/adr/0026-local-reviewer-session-proof-representation.md`
- `docs/adr/0027-local-gui-review-route-contract.md`

## Boundary notes

This published release does not imply:

- hosted authentication or multi-user authority
- default-on GUI mutation
- non-local review operators
- hidden runtime/provider execution

## RDE review summary

Published `v1.9.0` preserves the following:

- `v1.9.0` is the latest published release
- the next release lane remains local-first and contract-driven
- current repository work exposes explicit route-enforcement vs descriptive-metadata boundaries without widening into hosted auth claims
- published install and tag-side smoke evidence now serve as the release baseline for `v1.10.0`
