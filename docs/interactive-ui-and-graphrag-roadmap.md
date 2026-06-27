# Interactive UI and GraphRAG Roadmap

This roadmap records the recommended sequencing for Chronicle Stack's next interactive UI and GraphRAG-adjacent phases.

## Guiding boundary

- `.chronicle/chronicle.jsonl` remains the primary record
- interactive UI remains local-first and loopback-local
- GraphRAG-facing data remains derived and reconstructable
- Chronicle Stack itself does not become a hosted GraphRAG runtime, vector DB, or graph DB

## Recommended execution order

### 1. Safe interactive UI

- harden browser-triggered review write routes
- keep CLI parity explicit for every UI mutation path
- preserve fail-closed success semantics: no applied success unless decision persistence and audit insertion both succeed

Current state:

- per-session local mutation token boundary is implemented
- reviewer/session validation and write-route contracts remain explicit

### 2. Mutation session hardening

- add stronger session-intent continuity across preview and apply flows
- add duplicate-submit protection for local review actions
- make current mutation-session state more visible in UI boundary/readiness surfaces

Current state:

- local mutation session continuity metadata is implemented for browser-triggered review apply routes
- duplicate local mutation request identifiers are rejected within the current local UI server session

### 3. Proposal-first editing flows

- introduce append-only proposal surfaces for artifact/context changes
- require review/apply rather than direct in-place editing
- keep proposal records reconstructable from Chronicle events

Current state:

- append-only proposal records are available for artifact/context update intent
- proposal records surface in local UI artifact/context read models and `/api/proposals`
- approved proposals can be applied through explicit CLI apply commands with duplicate-apply protection

### 4. Graph export hardening and local retrieval adapter

- version graph-ready node/edge export contracts
- define incremental export expectations from Chronicle events
- add a local retrieval adapter that consumes derived export data without turning Chronicle into a GraphRAG runtime

Current state:

- graph export now carries a versioned machine-readable export contract
- incremental expectations are stated against Chronicle events, `event_id`, and full rebuild compatibility

### 5. External GraphRAG integration and query engine

- keep graph/vector/embedding/query runtime outside Chronicle Stack core
- treat Chronicle as the record layer and GraphRAG as a downstream derived consumer
- only after adapter and export stability should a query engine be considered release-ready

## Completion criteria by lane

### Interactive UI completion

- all browser-triggered writes remain explicit, audited, and fail-closed
- proposal/review/apply flows are available for the intended editable surfaces
- local operator boundaries remain visible and understandable in UI

### GraphRAG completion

- graph-ready export contract is stable and versioned
- retrieval outputs retain provenance, boundary cues, and evidence traces
- Chronicle Stack core does not gain hard dependencies on external GraphRAG runtimes
