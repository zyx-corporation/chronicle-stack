# ADR 0094: Local Query-Engine Bundle Includes Trial Report Template

- Status: Accepted
- Date: 2026-06-28

## Context

After `v1.74.0`, Chronicle Stack could emit a handoff bundle with an acceptance checklist, but real downstream consumer trials still lacked a standard repository-side template for recording structural findings and sufficiency decisions.

## Decision

Chronicle Stack will include a trial report template alongside the local handoff bundle and document its use in-repo. The template captures review outcomes without turning Chronicle Stack into a downstream runtime or implementation host.

## Consequences

- downstream trials become easier to compare across attempts
- implementation-repo escalation can be justified from recorded trial outcomes
- Chronicle Stack still stays descriptive, local, and read-only
