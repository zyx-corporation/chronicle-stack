# ADR 0095: Local Query-Engine Trial Outcome Is Recorded As Assistant Output

- Status: Accepted
- Date: 2026-06-28

## Context

After `v1.75.0`, Chronicle Stack could emit a handoff bundle, an acceptance checklist, and a trial report template. However, the result of a real downstream trial still was not captured back into Chronicle as a structured record.

## Decision

Chronicle Stack will provide a local CLI command that records the outcome of a downstream handoff-bundle trial as a review-oriented `assistant_output` event. The payload remains descriptive metadata about the trial and does not execute or certify downstream runtime behavior.

## Consequences

- real downstream trials can be preserved inside Chronicle history
- sufficiency decisions can be traced without introducing a new runtime subsystem
- Chronicle Stack still remains local-first, descriptive, and non-executing for downstream query runtimes
