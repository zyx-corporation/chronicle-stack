# ADR-0018: Local UI Read-only Navigation Boundary

Status: Accepted  
Date: 2026-06-18  
Scope: Chronicle Stack `chronicle ui` local interactive inspection surface  
Related: ADR-0005, ADR-0012, ADR-0016, `docs/v1.7-phase-h-auth-ui-design.md`, `docs/v1.7-phase-f-g-h-plan.md`

## Context

Chronicle Stack already exposes a local interactive UI through `chronicle ui`.

That UI has expanded from simple endpoint inspection into a richer read-only operator surface with:

```text
overview triage cards
runtime record lists
review queue lists
detail drill-down
related-link navigation
client-side filters
client-side sorting
trail / breadcrumb context
related-list shortcuts
active-view summaries
```

These additions improve inspection speed, but they also create a risk:

```text
interactive convenience could be misread as record authority, mutation capability, approval state, or security enforcement
```

The project already has design notes stating that GUI mutation must remain disabled by default and that auth/authz work must precede any write-capable GUI review flow.

However, the specific architectural decision for local interactive UI state has not yet been captured as an ADR.

That missing ADR matters because the new navigation features introduce multiple kinds of derived UI-only state:

```text
active filters
active sort mode
recent detail trail
current list/detail location
triage drill-down shortcuts
related-list reopen shortcuts
active-view summaries
```

Without an ADR, future work could accidentally blur:

```text
derived UI state        vs primary Chronicle records
inspection convenience  vs review approval semantics
local navigation        vs authorization enforcement
read-only summaries     vs audit-worthy mutation
```

## Decision

Chronicle Stack adopts the following rule for the local interactive UI:

```text
`chronicle ui` is a derived read-only inspection surface.
Its navigation and interaction state is ephemeral local UI state, not Chronicle record state.
```

The local interactive UI may provide richer operator affordances, including:

```text
filtering
sorting
breadcumbs / trail history
related-detail navigation
related-list shortcuts
triage drill-down
active-view summaries
```

But those affordances must remain:

```text
client-side or derived-view state only
non-authoritative with respect to Chronicle JSONL
non-mutating with respect to record content
non-certifying with respect to review, security, or approval
```

No local interactive UI control may be treated as:

```text
record mutation
review approval
authorization enforcement
audit insertion
persistence of operator intent
replacement for CLI review flow
```

Until a future ADR explicitly changes the boundary:

```text
GUI mutation remains disabled by default
CLI review remains the primary write path
interactive UI state remains ephemeral and local
```

## Boundary

The accepted boundary is:

```text
primary JSONL                  = source of truth
derived API payloads           = read-only projections
interactive UI navigation      = ephemeral local view state
review capability summaries    = advisory derived signals
identity assurance summaries   = derived boundary interpretation
active-view summaries          = current UI context only
```

The local UI may summarize or derive:

```text
which records are visible
how rows are ordered
which detail path was recently visited
which review slice was reopened
which filter/sort is active
```

It must not imply:

```text
that any Chronicle record changed
that approval was granted
that warnings were resolved
that an audit event was inserted
that authorization policy was enforced
```

## Rationale

This boundary preserves the core Chronicle Stack principles already used elsewhere:

1. Primary Chronicle records remain authoritative.
2. Derived surfaces may improve visibility without gaining authority.
3. Read-only local UI convenience should not become hidden workflow state.
4. Mutation requires explicit security framing, audit insertion points, and command-layer parity.

The newer UI affordances are valuable precisely because they are lightweight.

Keeping them ephemeral and derived allows Chronicle Stack to improve operator ergonomics without silently introducing:

```text
session-owned review state
browser-owned approval semantics
hidden mutable workflow memory
informal access-control claims
```

This also keeps future auth/authz work cleaner. A later mutation-capable UI can build on top of a clear boundary instead of inheriting ambiguous behavior from convenience-only features.

## Consequences

### Positive

- UI ergonomics can continue improving without changing record authority.
- Client-side filters, sorting, and navigation stay cheap to implement and rebuildable.
- Review and runtime summaries remain clearly advisory.
- Future mutation-capable UI work has a cleaner starting boundary.
- Operators can inspect faster without creating hidden durable state.

### Negative / Cost

- Useful browser state is intentionally non-persistent unless a future ADR changes that.
- Some users may expect richer session memory than the current boundary allows.
- Future feature proposals must explicitly justify any move from ephemeral UI state to persisted workflow state.
- UI convenience alone cannot replace CLI review commands for write workflows.

## Required Future Pattern

Future local UI enhancements should follow this rule:

```text
If a feature only changes visibility, ordering, or navigation, keep it client-side/derived.
If a feature changes Chronicle meaning, review state, approval state, or durable workflow state, require a new ADR and explicit write-path design.
```

Examples that remain inside this ADR:

```text
new filters
new sort modes
better trail summaries
additional related-list shortcuts
derived badges and list summaries
```

Examples that require a future ADR:

```text
persisted per-user view state
GUI approve/reject/request-changes
server-side session state for review progress
browser-triggered audit insertion
authorization-enforced mutation routes
```

## Non-goals

This ADR does not:

- add GUI mutation
- add persisted browser/session preferences
- add authorization enforcement
- add authentication implementation
- change review CLI semantics
- change audit insertion policy
- change package persistence semantics
- change primary JSONL authority

## RDE Review

### Preserved

- Chronicle JSONL remains authoritative.
- Local UI remains read-only.
- Derived review/runtime/package surfaces remain derived.
- CLI review remains the primary write path.
- Audit significance remains attached to actual write operations, not view-state changes.

### Transformed

- A growing collection of UI convenience behaviors is normalized into one explicit architectural boundary.
- Local UI navigation state is treated as a first-class design concern rather than an incidental implementation detail.

### Added

- An explicit rule for filters, sorting, trail history, shortcuts, and active-view summaries.
- A separation between inspection ergonomics and durable workflow semantics.
- A future-pattern rule for deciding when UI enhancements need a new ADR.

### Unresolved

- Whether any future local preferences should be persisted.
- Whether a future authenticated local UI should keep some session-scoped durable state.
- How CLI/UI parity should be enforced if mutation-capable UI work begins later.
- Whether multi-user local-machine scenarios need stricter UI-state isolation semantics.

### Deviation Risks

- Treating derived UI warnings or badges as authoritative decisions.
- Letting browser convenience pressure introduce hidden mutable workflow state.
- Mistaking navigation history for review history.
- Reusing this ADR to justify GUI mutation without a later auth/audit ADR.
