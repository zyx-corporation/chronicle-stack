# ADR-0098: Local `act` as the Primary CI Execution Surface

Status: Accepted  
Date: 2026-08-07  
Scope: Chronicle Stack v2.3 and later  
Related: ADR-0002, ADR-0011, `.github/workflows/ci.yml`, `docs/testing-strategy.md`

## Context

ADR-0002 defines Core CI as a project-wide T-RDE execution surface and phase gate, but it
does not require that the workflow run on a hosted service. Chronicle Stack needs the gate to
remain executable when GitHub Actions is unavailable, queued indefinitely, or fails before
repository steps start.

During the v2.3.0 release, hosted runs repeatedly failed while resolving action downloads with
`Service Unavailable`. The same workflow was then executed locally with `act`, where lint,
all 519 tests, and the UI smoke check completed successfully. That run also exposed an
unbounded Ruff dependency and led to constraining Ruff to the validated `<0.16` series.

The project therefore needs one workflow definition with a locally controllable primary
execution path, rather than treating hosted-run availability as part of product correctness.

## Decision

Chronicle Stack will use local `act` execution as the primary Core CI execution surface.

- `.github/workflows/ci.yml` remains the canonical workflow definition.
- Contributors and release operators run that workflow locally with `act` before merge or
  release closeout.
- A successful local `act` run may satisfy the Core CI phase gate when its commit, command,
  platform, and result are recorded.
- GitHub Actions remains a secondary hosted mirror and collaboration signal. A hosted-service
  outage or pre-job infrastructure failure is not a code failure when the same commit passes
  the canonical workflow locally.
- A hosted run that reaches repository steps and reports a lint, test, smoke, or contract
  failure remains blocking until the discrepancy is explained or fixed.
- Observation E2E remains a separate surface under ADR-0011 and is not silently absorbed into
  Core CI.

The standard local command is:

```bash
act pull_request -j test --matrix python-version:3.11 \
  -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

On Apple Silicon, the native Linux arm64 image is preferred. Emulating `linux/amd64` may cause
action post-steps to resolve tools differently from the main job even when all repository
checks have passed.

## Evidence Contract

The merge or release record must include:

```text
- commit SHA
- act command and act version
- container image and architecture
- workflow/job name
- lint result
- test count and result
- smoke result
- any hosted-run failure and whether it occurred before repository steps
```

Local success is evidence for the tested commit only. Changes after the run require another
Core CI execution.

## Consequences

### Positive

- Core CI is runnable without waiting for hosted-runner availability.
- The repository workflow remains the shared definition for local and hosted execution.
- Infrastructure outages can be distinguished from repository failures.
- Release evidence becomes reconstructable and tied to an exact commit.

### Negative / Cost

- Operators need Docker and `act` installed locally.
- Container image downloads consume local bandwidth and storage.
- Local and hosted runner behavior can differ, so discrepancies require explicit review.
- A local gate depends on the operator recording evidence accurately.

## Non-goals

This decision does not:

- remove `.github/workflows/ci.yml`;
- disable GitHub Actions for all repository events;
- treat local CI success as correctness or security certification;
- replace browser validation, external-integration checks, or Observation E2E;
- permit ignoring repository-step failures from a hosted run.

## RDE Review

### Preserved

- Core CI remains project-wide and remains the ordinary phase gate.
- `.github/workflows/ci.yml` remains the canonical workflow definition.
- CI pass remains non-certifying.

### Transformed

- The primary execution location changes from an implicitly hosted runner to local `act`.
- Hosted GitHub Actions changes from required execution dependency to secondary mirror.
- CI evidence is explicitly bound to the commit and local execution environment.

### Added

- A standard local `act` command.
- Evidence requirements for local CI.
- Failure classification between hosted infrastructure and repository steps.

### Unresolved

- Whether repository event triggers should later be reduced or changed to manual dispatch.
- Whether a checked-in `.actrc` should standardize the container mapping.
- How local CI evidence should be attached automatically to pull requests.

### Deviation Risks

- Running a different job or workflow locally while claiming Core CI passed.
- Reusing evidence after the commit changed.
- Treating all hosted failures as infrastructure failures without checking the failed step.
- Allowing local runner configuration to drift from the canonical workflow.
