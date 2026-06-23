# Chronicle Stack v1.9.0 Release Status

## Status

Repository-side release preparation for `v1.9.0` is in progress.

- Latest published release before this track: `v1.8.0`
- Current repository-side release target: `v1.9.0`

## Release scope

This release track currently means:

- local reviewer/session enforcement-boundary clarification
- contract-aligned strengthening of reviewer/session mutation semantics
- local mutation-boundary wording hardening after `v1.8.0`

## Current repository-side progress

Current `v1.9.0` repository progress now includes:

- ADR-0028 defining the local reviewer/session enforcement boundary
- a release-lane handoff from the completed `v1.8.0` contract-hardening release

## Current release documents

- `docs/adr/0028-local-reviewer-session-enforcement-boundary.md`
- `docs/v1.9-release-remaining-issues.md`

## Historical context

These records provide the immediate upstream context for the `v1.9.0` lane:

- `docs/release-status-v1.8.0.md`
- `docs/v1.8-release-remaining-issues.md`
- `docs/adr/0026-local-reviewer-session-proof-representation.md`
- `docs/adr/0027-local-gui-review-route-contract.md`

## Boundary notes

This release-status document does not yet imply:

- version bump execution
- external release publication
- hosted authentication or multi-user authority
- default-on GUI mutation
- non-local review operators
- hidden runtime/provider execution

## RDE review summary

Current repository-side review for `v1.9.0` preserves the following:

- `v1.8.0` is the latest published release
- the next release lane remains local-first and contract-driven
- unresolved work starts with reviewer/session enforcement-boundary wording and validation alignment
