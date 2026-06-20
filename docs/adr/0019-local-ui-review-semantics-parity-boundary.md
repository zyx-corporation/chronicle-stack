# ADR-0019: Local UI Review Semantics and CLI Parity Boundary

Status: Accepted  
Date: 2026-06-20  
Scope: Chronicle Stack `chronicle ui` review-oriented read-only semantics  
Related: ADR-0012, ADR-0016, ADR-0018, `docs/cli-reference.md`, `docs/v1.7-phase-h-auth-ui-design.md`, `docs/v1.7-phase-h-ui-mutation-threat-model.md`

## Context

Phase H work expanded the local UI from simple endpoint inspection into a richer read-only review surface with:

```text
mutation-readiness summaries
preview-only mutation capability signaling
CLI-equivalent action previews
review capability / warning badges
package readiness summaries
CLI parity summaries
overview triage drill-down
overview/list/detail helper-based labels
```

Those additions improve operator visibility, but they also introduce a semantic risk:

```text
UI wording can be mistaken for authority, activation, or approval semantics
```

The project already established that:

- Chronicle JSONL remains authoritative
- GUI mutation stays disabled by default
- CLI review remains the primary write path
- local UI state is read-only and derived

However, the specific rule for how review semantics are represented across overview/list/detail surfaces had not been captured as an ADR.

That gap matters because inconsistent wording or duplicated label logic could blur:

```text
preview intent            vs actual mutation enablement
derived readiness signal  vs approval state
UI wording                vs durable review semantics
read-only parity preview  vs actual command-layer contract
```

## Decision

Chronicle Stack adopts the following rule for read-only review semantics in the local UI:

```text
The local UI may summarize review semantics, but those semantics must remain derived,
descriptive, and CLI-parity-aware rather than authoritative or activating.
```

This means:

1. `ui_boundary` is the canonical read-only source for GUI mutation boundary metadata.
2. Derived auth/authz placeholder interpretation should be exposed from that same boundary metadata rather than recomputed inconsistently in each UI surface.
3. Derived reviewer-identity alignment summaries may be aggregated for overview visibility, but they remain descriptive queue-state interpretation rather than approval authority.
4. `mutation_capability_flag` expresses preview intent only and must never imply enabled writes by itself.
5. `mutation_enabled` remains the activation signal, and it stays false until a future ADR explicitly enables GUI writes.
6. `available_actions` and `action_preview.actions` must describe the same review contract through shared derivation logic.
7. `cli_parity.status == "aligned"` is the stable indicator that read-only UI preview semantics still match the current CLI review contract.
8. Overview/list/detail labels for review semantics should be generated from shared helpers so wording drift does not silently change user interpretation.

## Boundary

The accepted semantic boundary is:

```text
CLI review commands             = primary mutation contract
audit-worthy review decisions   = write-path semantics
ui_boundary metadata            = read-only mutation boundary description
mutation capability flag        = preview intent only
action preview controls         = non-mutating CLI-equivalent guidance
parity summaries                = derived contract-alignment signals
helper-based UI labels          = presentation consistency, not authority
```

The local UI may expose:

```text
aligned / drift summaries
warning-focused drill-down
package readiness summaries
identity assurance summaries
disabled approve/reject/request-changes previews
shared labels across overview/list/detail surfaces
```

It must not imply:

```text
that GUI writes are active because a capability flag is present
that aligned preview text grants approval authority
that UI wording itself changes review meaning
that helper-based labels replace CLI or audit contracts
that review warnings are resolved without an actual write-path decision
```

## Rationale

This ADR preserves several important properties at once:

1. Chronicle keeps one real mutation contract: the command layer.
2. The local UI can become more helpful without becoming semantically ambiguous.
3. Review semantics remain inspectable before GUI mutation exists.
4. Label consistency is treated as a boundary concern, not just a cosmetic concern, because wording influences operator interpretation.

Without this rule, future changes could accidentally:

```text
present preview intent as activation
let duplicated UI strings drift away from CLI semantics
hide contract drift behind inconsistent labels
make read-only review summaries appear more authoritative than they are
```

## Consequences

### Positive

- `ui_boundary` remains the single descriptive home for mutation-readiness metadata.
- Preview-only GUI affordances stay useful without weakening the no-write default.
- CLI/UI contract drift becomes explicitly inspectable through parity summaries.
- Shared helpers reduce semantic drift across overview/list/detail surfaces.
- Future GUI mutation work has a clearer pre-activation baseline.

### Negative / Cost

- UI wording changes now deserve boundary review, not just presentation review.
- Shared helper usage adds mild implementation discipline for otherwise simple strings.
- Future write-capable UI work must preserve or explicitly replace these semantics with a later ADR.

## Required Future Pattern

Future local UI review features should follow this rule:

```text
If a feature only describes review state, parity, readiness, or warnings, keep it derived and helper-consistent.
If a feature activates writes, changes approval state, or changes audit semantics, require a new ADR and explicit write-path design.
```

Examples that remain inside this ADR:

```text
new derived review badges
additional parity summaries
new warning drill-down labels
new helper-based phrasing for read-only review notices
read-only CLI-equivalent action previews
overview drill-down for derived identity-alignment slices
```

Examples that require a future ADR:

```text
GUI approve/reject/request-changes execution
capability flag values that enable writes by themselves
server-managed approval sessions
UI-triggered audit insertion
parity signals that replace command-layer verification
```

## Non-goals

This ADR does not:

- enable GUI mutation
- redefine review CLI behavior
- replace audit insertion policy
- define final auth/authz implementation
- guarantee multi-user review semantics
- treat UI label helpers as a security mechanism

## RDE Review

### Preserved

- CLI review remains the primary write path.
- Chronicle JSONL remains authoritative.
- Local UI remains read-only and derived.
- Mutation capability signaling remains non-activating.

### Transformed

- A growing set of read-only review semantics is normalized into one explicit boundary.
- UI label consistency is elevated from implementation detail to semantic design discipline.

### Added

- An explicit rule for `ui_boundary`, `mutation_capability_flag`, and `cli_parity`.
- A helper-consistency requirement for overview/list/detail review wording.
- A future-pattern rule for when review semantics need a new ADR.

### Unresolved

- How parity should be enforced once GUI writes are actually enabled.
- Whether future authenticated local sessions need stronger reviewer-identity guarantees.
- Whether any future persisted UI preferences should affect review semantics.

### Deviation Risks

- Treating preview-only capability as activation.
- Allowing UI strings to drift away from CLI contract wording.
- Mistaking parity alignment for approval state.
- Reusing this ADR to justify GUI mutation without a later auth/audit ADR.
