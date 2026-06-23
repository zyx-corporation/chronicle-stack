# Chronicle Stack v1.8.0 Release Status

## Status

Repository-side release preparation for `v1.8.0` is in progress.

- Latest published release before this track: `v1.7.0`
- Current repository-side release target: `v1.8.0`

## Release scope

This release track currently means:

- local GUI review-route design hardening
- architectural framing for the next local GUI mutation slice
- browser-triggered local review route contract hardening
- local single-operator mutation-boundary clarification

## Current repository-side progress

Current `v1.8.0` repository progress now includes:

- ADR-0027 defining the local GUI review-route expansion boundary
- explicit read-only contract exposure of the action route family on UI boundary and mutation-readiness surfaces
- preserved CLI-equivalent route semantics for each supported local review action

## Current release documents

- `docs/adr/0027-local-gui-review-route-contract.md`
- `docs/v1.7-phase-f-g-h-remaining-issues.md`
- `docs/v1.7-phase-h-gated-gui-mutation-preview.md`

## Boundary notes

This release-status document does not yet imply:

- final version-bump execution
- external release publication
- default-on GUI mutation
- hosted authentication or multi-user operator flows
- hidden provider execution
- GraphRAG/runtime proof or non-local runtime coupling

## RDE review summary

Current repository-side review for `v1.8.0` preserves the following:

- `v1.7.0` remains the latest published release
- the next release lane stays local-first and contract-driven
- unresolved work remains implementation readiness, smoke evidence, release notes, and publication evidence
