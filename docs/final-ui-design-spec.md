# Chronicle Stack Final UI Design Specification

Status: Draft for Claude Design

## 1. Purpose

This document defines the target-state UI design brief for Chronicle Stack.
It is intended to be handed to a design model or designer so they can propose
the final product UI without drifting away from Chronicle Stack's core
boundaries.

Chronicle Stack is not a generic note app, social feed, or hosted dashboard.
Its UI should help a local operator reconstruct:

- why an artifact exists
- what context shaped it
- what decisions accepted or rejected it
- how meaning changed over time
- what boundary, trust, audit, and federation conditions apply

The final UI should feel like a local reasoning workbench, not a timeline-first
product.

## 2. Product Boundary

The UI must preserve these hard boundaries:

- local-first: the local Chronicle root remains the source of truth
- `.chronicle/chronicle.jsonl` remains the primary record
- UI surfaces are derived from Chronicle records and must not become the source of authority
- proposal/review/apply is preferred over direct in-place editing
- federation remains preview-first, inspect-first, and consent-aware
- Chronicle Stack does not become a hosted GraphRAG runtime, vector DB, graph DB, or cloud sync product
- network transport, automatic import, and unattended sync are outside the current target UI

## 3. Design Goals

The final UI should:

- make reconstruction faster than reading raw CLI or JSON
- make provenance, auditability, and boundary state visually first-class
- make current task state legible from a single landing view
- make review and proposal workflows understandable before any write-capable action is taken
- support local deployment with a desktop-grade feel even if the implementation remains web-based at first
- scale from solo use to future stronger operator identity and trust workflows without implying multi-user SaaS semantics

## 4. Non-Goals

The UI should not be designed as:

- a chat app
- a social media timeline
- a generic CRUD admin panel
- a cloud collaboration dashboard
- a direct-edit document editor
- a hidden-automation product that mutates Chronicle state without explicit review

## 5. Primary User

Primary user:

- a local operator working with AI-assisted writing, design, research, or development artifacts
- someone who needs to inspect context, decisions, proposals, review state, and federation readiness
- someone who values traceability more than speed-at-any-cost

Secondary user:

- a reviewer or collaborator operating on the same local machine or through explicit package handoff

## 6. Product Character

The target experience should feel:

- calm
- high-trust
- inspectable
- exact
- serious but not intimidating
- richer than a terminal, but not playful or feed-driven

Recommended tone:

- editorial desk
- evidence board
- review console
- provenance navigator

Avoid:

- engagement-driven feed patterns
- vanity metrics
- bright attention traps
- generic enterprise admin styling

## 7. Core UX Principles

### 7.1 Reconstruction first

Every important screen should help answer:

- what is this
- where did it come from
- what changed
- what is pending
- what boundary applies
- what can safely happen next

### 7.2 Boundary before action

If an operation has trust, consent, audit, identity, or review implications,
the UI should surface those conditions before the operator reaches any apply
step.

### 7.3 Proposal before mutation

Where editing exists in the final target vision, it should normally flow as:

- draft proposal
- inspect diff
- review boundary and audit consequences
- explicit apply

### 7.4 Derived views stay visibly derived

Overviews, indexes, trend summaries, package previews, AI hints, and
federation summaries should be visually presented as advisory read models rather
than silent authority surfaces.

### 7.5 Meaning over chronology

Default navigation should emphasize:

- active questions
- artifacts under review
- unresolved objections
- recent decisions
- significant diffs

It should not default to a pure reverse-chronological log view.

## 8. Information Architecture

The final UI should be organized around these top-level areas.

### 8.1 Home / Overview

Purpose:

- provide the operator's current operating picture

Should include:

- chronicle health and counts
- active review queue summary
- mutation readiness and boundary readiness
- current runtime and summary-job signals
- federation preflight and overlap summary
- trust summary
- warnings and triage shortcuts
- high-signal "what needs attention now" modules

### 8.2 Chronicle Objects

Purpose:

- navigate first-class meaning units rather than only raw records

Should include:

- questions
- decisions
- artifacts
- deltas
- objections
- hypotheses
- decay-related records

### 8.3 Context and Artifact Workbench

Purpose:

- inspect the relationship between context, artifacts, versions, and decisions

Should include:

- artifact history
- source event linkage
- related context
- decision linkage
- RDE linkage
- proposal and apply status where applicable

### 8.4 Review Workspace

Purpose:

- make review state legible and safe

Should include:

- pending review queue
- reviewer identity and session state
- enforcement and validation-gate summaries
- CLI parity visibility
- action preview and recovery guidance
- proposal review and apply progression

### 8.5 Audit / Boundary / Lifecycle

Purpose:

- inspect operational and governance state

Should include:

- audit events
- boundary rules
- lifecycle markers
- blocker details
- enforcement versus advisory distinctions

### 8.6 Federation Workspace

Purpose:

- support explicit local package and message workflows

Should include:

- inbox and outbox inspection
- package inspect / verify / preview / import-preview guidance
- consent records and overlap summaries
- trust-aware package context
- read-only boundary-check and consent summaries

### 8.7 Trust Workspace

Purpose:

- inspect node trust relationships and their scope

Should include:

- nodes
- subject identities
- trust relations
- trust assertions and withdrawals
- domain / purpose / capability distinctions

### 8.8 Runtime / Retrieval Workspace

Purpose:

- inspect AI-adjacent derived work without turning Chronicle into the runtime itself

Should include:

- runtime records
- summary jobs
- AI index status
- graph summary
- query-engine handoff and escalation cues
- downstream trial sufficiency and import-readiness

## 9. Key Screens

### 9.1 Final Home Screen

The final home screen should not look like a dashboard full of equal cards.
It should prioritize operator judgment.

Recommended structure:

- left navigation rail
- central "current work" column
- right-side evidence / boundary / trust column

Central column priority:

- pending reviews
- open questions
- active artifacts with recent meaningful diffs
- unresolved objections
- current proposal/apply candidates

Right column priority:

- boundary warnings
- audit highlights
- federation readiness
- trust and consent signals

### 9.2 Record Detail Screen

Every major record detail screen should reveal:

- canonical identity
- summary
- provenance
- related records
- timeline
- decisions and review state
- warnings and boundary notes
- next safe actions

Recommended tabs or sections:

- summary
- lineage
- diffs / RDE
- review
- audit
- related

### 9.3 Review Detail Screen

This should be one of the most important screens in the product.

Must clearly show:

- what is under review
- why it is pending
- who is reviewing
- what session / identity assumptions apply
- what blockers exist
- what the equivalent CLI route is
- what happens on approve / reject / request changes
- what rollback or recovery path exists

### 9.4 Federation Package Screen

This screen should feel like a shipping inspection desk, not a file browser.

Must show:

- package purpose
- target node
- visibility and retention semantics
- consent and sharing restrictions
- manifest validity state
- trust reference context
- included record summaries
- redaction report
- import-preview implications

### 9.5 Question-Centric Workspace

The final UI should provide a screen centered on a live question or inquiry.

It should connect:

- question
- related contexts
- linked artifacts
- linked decisions
- objections
- hypotheses
- relevant runtime or retrieval attempts
- downstream review or federation implications

This is important because Chronicle is about reconstructing meaning, not just storing files.

## 10. Interaction Rules

### 10.1 Navigation

- navigation must support jumping from overview aggregates into filtered lists
- lists must support jumping into detail without losing the reconstruction trail
- breadcrumbs should reflect semantic path, not only route hierarchy

### 10.2 Filtering

Support filters based on:

- review state
- boundary state
- trust / consent overlap
- object type
- artifact type
- lifecycle state
- AI/runtime involvement
- readiness and blocker families

### 10.3 Mutation affordances

In the final target vision, write-capable controls may exist, but they must:

- be explicitly marked
- expose boundary and audit implications before apply
- show proposal/review/apply separation
- preserve CLI parity visibility
- fail closed

### 10.4 Federation affordances

Federation-related screens must never imply:

- automatic transport
- automatic import
- automatic approval
- hidden authority

### 10.5 AI affordances

AI-related screens must never imply:

- verified truth
- permanent identity claims
- unbounded context sharing
- hosted external execution inside Chronicle Stack core

## 11. Visual Direction

The UI should feel more like a high-end analysis console than a generic app.

Recommended visual traits:

- strong typography hierarchy
- warm-neutral or paper-and-ink inspired palette with restrained accent colors
- subtle graph / ledger / archival cues
- quiet motion
- clear state-color semantics for warning, advisory, ready, blocked, preview
- dense information presentation without looking cramped

Avoid:

- purple-on-white default AI aesthetic
- consumer social UI patterns
- toy terminal cosplay
- flat admin templates

## 12. Layout Guidance

The design should work for:

- laptop-first local use
- wide desktop monitors
- moderate tablet adaptation

The desktop layout should be primary.
Mobile should be secondary and does not need to drive the whole design system.

## 13. Required Design Outputs

The designer or design model should produce:

- product design principles summary
- information architecture
- final navigation model
- high-level visual direction
- overview screen design
- record detail screen design
- review workspace design
- federation workspace design
- trust workspace design
- runtime/retrieval workspace design
- proposal/review/apply interaction concept
- component system summary
- state examples for empty, warning, blocked, preview-only, ready

## 14. Output Constraints for the Designer

The resulting design must:

- preserve Chronicle Stack's local-first and derived-view boundaries
- avoid assuming hosted multi-user SaaS behavior
- avoid assuming hidden auto-sync or auto-import
- keep federation preview-first and inspect-first
- keep review and editing proposal-first
- treat future networked federation and full interactive editing as future-compatible, not already available

## 15. Summary

The final Chronicle Stack UI is not "a prettier admin panel."
It is a local reasoning and provenance workspace for context, decisions,
artifacts, review, trust, and federation.

The design should make Chronicle feel:

- local
- trustworthy
- inspectable
- reconstructable
- intellectually calm
- ready for deeper workflows without pretending they already exist
