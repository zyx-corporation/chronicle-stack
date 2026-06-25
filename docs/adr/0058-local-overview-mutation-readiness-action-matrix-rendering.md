# ADR-0058: Local Overview Mutation-Readiness Action-Matrix Rendering

- Status: Accepted
- Date: 2026-06-25

## Context

`v1.38.0` moved review target-state action-matrix rows onto stable summary keys for the main write-route detail renderer.
One adjacent overview mutation-readiness panel still rendered the same action-matrix rows through presentation-only concatenation.

## Decision

- the overview mutation-readiness panel reuses action-matrix summary keys when rendering target-state details
- the renderer still falls back to local summary text if a key is unavailable

## Consequences

- adjacent review-write contract surfaces stay aligned on the same structured wording
- local read-only mutation-readiness panels no longer drift from write-route detail wording
