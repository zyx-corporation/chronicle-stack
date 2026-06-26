# ADR-0003: Use local act CI instead of hosted GitHub Actions

Status: Accepted

## Context

Chronicle Stack is a local-first project. Hosted GitHub Actions previously ran the repository CI workflow on push and pull request events. That created a hosted CI dependency even though the project direction emphasizes local reproducibility, explicit operation, and context sovereignty.

The project still needs a repeatable validation gate for lint, tests, and UI smoke checks. The change is not to remove CI validation, but to move the execution surface from GitHub hosted runners to local `act` execution.

## Decision

Chronicle Stack will not use hosted GitHub Actions as its CI execution layer.

The CI-equivalent workflow will live under:

```text
.act/workflows/ci.yml
```

Developers run it with:

```bash
scripts/act-ci.sh
```

The previous hosted workflow file under `.github/workflows/ci.yml` is removed so push and pull request events do not trigger hosted GitHub Actions.

## Consequences

### Positive

- CI validation is explicit and local-first.
- The project no longer depends on hosted GitHub Actions runners for basic validation.
- The same lint, test, and UI smoke intent remains available through a stable script.

### Negative

- Pull requests will no longer automatically show hosted GitHub Actions check results.
- Developers must remember to run `scripts/act-ci.sh` before merging or releasing.
- Local `act` behavior can differ from hosted GitHub runners due to container image, architecture, mount, or network differences.

## Follow-up

- Add PR template or release readiness fields for local act CI result recording.
- Consider documenting known-good act version and container image if drift becomes an issue.
