# Chronicle Stack v1.0.0 CLI Compatibility Audit

Issues: #165, #169

## Purpose

This document records the v1.0.0 CLI compatibility audit for Chronicle Stack.

The goal is to identify the user-facing command surfaces that should be treated as stable after v1.0.0 without freezing private implementation details or accidental internals.

## Stable entry points

The following entry points are treated as v1.0 stable user-facing surfaces:

- `chronicle`
- `chronicle-context`
- `chronicle-export`
- `chronicle-package`
- `chronicle-graph`
- `chronicle-audit`
- `chronicle-lifecycle`

## Primary command posture

Documentation should prefer primary `chronicle ...` command forms where available:

- `chronicle context ...`
- `chronicle export ...`
- `chronicle package ...`
- `chronicle graph ...`
- `chronicle audit ...`
- `chronicle lifecycle ...`

Auxiliary command entry points remain compatibility surfaces for scripting and transition stability.

## Compatibility expectations

After v1.0.0, the following changes should be treated as breaking unless explicitly scheduled for a major release:

- removing a documented stable command
- renaming a documented option
- changing a documented required argument
- changing the meaning of documented status values
- changing documented JSON field meanings
- making a previously local-only command require a daemon, server, model API, GraphRAG engine, vector DB, or graph DB

The following changes are not automatically breaking:

- adding optional flags
- adding new output fields while preserving existing documented fields
- improving diagnostic wording
- refactoring internal modules
- adding new docs or smoke profiles

## Workflow surfaces

### Context classification

Classification commands are stable as advisory metadata workflows. They are not access-control commands.

### Audit

Audit commands are stable as traceability metadata workflows. They are not enforcement commands.

### Lifecycle

Lifecycle commands are stable as advisory marker workflows. They do not mutate primary records by themselves.

### Package review

Package review commands are stable as diagnostic workflows. A `pass` result is not a correctness proof, a `warning` is not automatic approval, and a `blocked` result indicates review is required before handoff.

### Export

Export commands are stable as local derived-output workflows. Export does not imply publication, permission grant, legal compliance, or external submission.

### Graph

Graph commands are stable as local graph-ready export and inspection surfaces. They do not embed a GraphRAG query engine, vector database, or graph database.

### Doctor

Doctor remains a local diagnostic workflow. Doctor guidance should point users toward relevant CLI workflows without implying enforcement.

## Audit result

No v1.0 rename is required before finalization. The current command family is coherent enough to stabilize as a documented compatibility surface.

Future compatibility work should add deprecation notes rather than silently breaking command names or status semantics.

## Warning classification

- Compatibility warning: stable user-facing commands must not be casually renamed after v1.0.0.
- Boundary warning: graph/export/package commands must not imply unavailable external runtimes.
- Semantics warning: diagnostic and advisory commands must not be described as enforcement.

## RDE review

### Preserved

- Existing command family remains recognizable.
- Primary CLI aliases and auxiliary compatibility entry points both remain available.
- Local-first boundaries remain explicit.

### Transformed

- CLI convenience is promoted into a compatibility contract.

### Supplemented

- Stable/auxiliary command mapping.
- Breaking-change criteria.
- Workflow-specific boundary notes.

### Deviation risks

- Freezing accidental implementation details.
- Overstating graph/export/package commands as external runtime integrations.
- Treating doctor or package review as proof or enforcement.
