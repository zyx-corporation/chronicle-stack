# Chronicle Stack v1.8.0 Release Status

## Status

Repository-side release preparation for `v1.8.0` is complete, and external `v1.8.0` release publication has been completed.

Latest published release before this track:

```text
v1.7.0
```

Current repository-side release target:

```text
v1.8.0
```

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
- explicit read-only status-code contract exposure for the local review route family
- preserved CLI-equivalent route semantics for each supported local review action
- explicit `v1.8.0` release-notes and remaining-issues entry points

## Current release documents

- `docs/adr/0027-local-gui-review-route-contract.md`
- `docs/release-readiness-v1.8.md`
- `docs/release-notes-v1.8.0.md`
- `docs/smoke-test-v1.8.md`
- `docs/v1.8-release-remaining-issues.md`

## Historical context

These older records still provide adjacent historical context for the current release lane:

- `docs/v1.7-phase-f-g-h-remaining-issues.md`
- `docs/v1.7-phase-h-gated-gui-mutation-preview.md`

## Repository-side verification

Current repository-side release-preparation verification for `v1.8.0` now includes:

- editable reinstall refreshed package metadata to `1.8.0`
- local CLI reported `chronicle 1.8.0`
- full repository test suite passed
- local `ui-smoke --json` passed from `/tmp/chronicle-stack-v1.8.0-repo-smoke.HZj8ST/ui-smoke.json`

## External release execution state

The following external release-execution evidence has also been captured:

- `origin/main` and `v1.8.0` both resolved to `b81f7e1a441685b6a00db63da7c52b49fa643dcb`
- GitHub Release URL: [Chronicle Stack v1.8.0](https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.8.0)
- clean tag-based installer smoke completed in `/tmp/chronicle-stack-v1.8.0-install-smoke`
- installed tag-based CLI reported `chronicle 1.8.0`
- installed tag checkout `HEAD` and `v1.8.0^{}` matched
- tag-based `ui-smoke` evidence was recorded from `/tmp/chronicle-stack-v1.8.0-tag-ui-smoke/ui-smoke.json`
- moved-tag opt-out installer smoke completed in `/tmp/chronicle-stack-v1.8.0-optout-smoke`

## Boundary notes

This release-status document still does not imply:

- default-on GUI mutation
- hosted authentication or multi-user operator flows
- hidden provider execution
- GraphRAG/runtime proof or non-local runtime coupling

## RDE review summary

Current repository-side review for `v1.8.0` preserves the following:

- `v1.7.0` was the latest published release before this track
- the next release lane stays local-first and contract-driven
- repository-side readiness and smoke entry points now exist for the `v1.8.0` lane
- release-notes and remaining-issues entry points now also exist for the `v1.8.0` lane
- version bump and changelog update are now complete for the `v1.8.0` lane
- repository-side version and smoke verification now also pass at `1.8.0`
- external publication and tag-based installer / `ui-smoke` evidence are now also complete
- unresolved work moves to whatever release lane follows `v1.8.0`
