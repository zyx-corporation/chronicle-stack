# Chronicle Stack v1.7.0 Release Status

## Status

Repository-side release preparation for v1.7.0 is complete, and external `v1.7.0` release publication has been completed.

Latest published release before this track:

```text
v1.4.0
```

Current repository-side release target:

```text
v1.7.0
```

## Scope

v1.7.0 is a local AI/runtime/review/package observability and gated-local-mutation-preparation release.

It includes:

- placeholder local AI index CLI and read-only UI visibility
- explicit local runtime summarize / invoke / execute-plan surfaces
- retrieval-plan / invocation-plan dry-run and reviewable record surfaces
- runtime / review / summary / package overview-list-detail triage surfaces
- Phase H auth-readiness, identity, and mutation-readiness visibility
- explicit local gated review write-path preview and fail-closed response contracts
- release notes
- release readiness
- release smoke profile
- version bump to `1.7.0`

## Release documents

- [v1.7 Smoke Test Profile](../smoke/smoke-test-v1.7.md)
- [v1.7 Phase H Auth Readiness Smoke Profile](../smoke/smoke-test-v1.7-phase-h.md)
- [v1.7 Release Readiness](../readiness/release-readiness-v1.7.md)
- [v1.7 Release Notes](../notes/release-notes-v1.7.0.md)
- [v1.7 Phase F/G/H Closeout Summary](../../v1.7-phase-f-g-h-closeout-summary.md)
- [v1.7 Phase H Readiness Status](../../v1.7-phase-h-readiness-status.md)

## Repository-side verification state

Repository-side verification has been completed with:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Observed version after editable reinstall:

```text
chronicle 1.7.0
```

Observed `chronicle ui-smoke --json` top-level release fields:

```json
{
  "passed": true,
  "read_only": true,
  "server_started": false,
  "browser_required": false,
  "external_runtime": false
}
```

## External release execution state

The following external release-execution evidence has also been captured:

- `origin/main` and `v1.7.0^{}` both resolve to `141c08224299311ee380c4216f4c04142a7c5da2`
- GitHub Release URL: [Chronicle Stack v1.7.0](https://github.com/zyx-corporation/chronicle-stack/releases/tag/v1.7.0)
- clean tag-based installer smoke completed in `/tmp/chronicle-stack-v1.7.0-install-smoke`
- installed tag-based CLI reported `chronicle 1.7.0`
- installed tag checkout `HEAD` and `v1.7.0^{}` matched
- tag-based `ui-smoke` evidence was recorded from `/tmp/chronicle-stack-v1.7.0-ui-smoke/ui-smoke.json`

## Boundary

v1.7.0 does not add daemon/service installation, hosted UI, default-on GUI mutation, authenticated GUI mutation, hidden provider execution, GraphRAG runtime, vector DB, graph DB, correctness proof, security certification, or legal/governance finalization.

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Mutation warning: gated local write-path visibility is not approval authority.
- Auth warning: auth/authz placeholders remain descriptive metadata only.
- Runtime warning: explicit runtime/provider contracts do not imply hidden background execution.
- Security warning: smoke is not security certification.
- Semantics warning: readiness and smoke are not correctness proof.

## RDE review

Preserved: local-first runtime and UI boundary, fail-closed local review semantics, explicit release-evidence workflow.

Transformed: v1.7 phase milestones become one release-target status surface.

Supplemented: explicit release-status discoverability for v1.7 repo-side preparation.

Unresolved: stronger auth/authz enforcement and broader provider/runtime expansion.
