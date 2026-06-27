# ADR 0090: Downstream Import Adapter Skeleton Stays Non-Executable

- Status: Accepted
- Date: 2026-06-27

## Context

After `v1.70.0`, downstream consumers had a fixture and guide, but they still lacked a stable skeleton that expressed the recommended import sequence and non-goals. The next safe step is a descriptive adapter skeleton rather than a real adapter implementation.

## Decision

Chronicle Stack will ship a non-executable query-engine import adapter skeleton. The skeleton may define required inputs, recommended sequence, prohibited capabilities, and non-goals, but it will not execute imports or become a downstream runtime component.

## Consequences

- Downstream implementers get a reusable sequence and boundary checklist.
- Tests can pin the skeleton shape as part of the contract surface.
- Chronicle Stack still avoids embedding real downstream import logic.
