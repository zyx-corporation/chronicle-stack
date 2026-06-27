# ADR 0089: Downstream Consumer Example Fixture Stays Descriptive

- Status: Accepted
- Date: 2026-06-27

## Context

After `v1.69.0`, Chronicle Stack could describe and validate a query-engine handoff contract, but downstream consumers still lacked a stable example fixture that showed how to read that contract without inferring a real query runtime.

## Decision

Chronicle Stack will ship a descriptive example fixture and companion guide for downstream consumers. The fixture may demonstrate handoff and import-validation fields, but it will remain a documentation artifact rather than an executable adapter or runtime integration.

## Consequences

- Downstream implementers get a concrete contract example to align against.
- Tests can pin the example shape to the current runtime models.
- Chronicle Stack still avoids embedding a downstream import adapter or query runtime.
