# GitHub Project Kanban setup

This document defines the recommended GitHub Project configuration for Chronicle Stack.

It follows ADR-0004: Prototype First / MVP / Agile development methodology.

## Principle

GitHub Issues are the planning source of truth.

GitHub Project Kanban is a derived state view over those Issues. It must not become a second task database.

Important requirements, decisions, acceptance criteria, non-goals, RDE review, implementation rationale, and links belong in the Issue, PR, ADR, or Chronicle record. They should not exist only as board-only card notes.

## Recommended Project name

```text
Chronicle Stack Development
```

## Views

### Board view: Flow

Use this as the primary Kanban view.

Group by `Status`.

Recommended columns:

- `Backlog`
- `Ready`
- `In Progress`
- `Review`
- `Done`
- `Deferred`
- `Rejected / Not planned`

### Table view: Planning

Use this to inspect classification and decision metadata.

Recommended visible fields:

- `Title`
- `Status`
- `Work Type`
- `Decision State`
- `RDE Required`
- `Target Stage`
- `Linked PR`
- `Linked ADR`
- `Priority`

### Roadmap view: Stage / Milestone

Optional. Use this when coordinating broader work against the integrated roadmap.

Group or filter by `Target Stage`.

## Fields

### Status

Type: Single select

Values:

- `Backlog`
- `Ready`
- `In Progress`
- `Review`
- `Done`
- `Deferred`
- `Rejected / Not planned`

Meaning:

- `Backlog`: unstarted question, request, defect, or opportunity.
- `Ready`: sufficiently specified and unblocked.
- `In Progress`: active implementation or investigation.
- `Review`: PR opened, decision pending, or review required.
- `Done`: merged, completed, or explicitly closed.
- `Deferred`: intentionally postponed.
- `Rejected / Not planned`: rejected, invalid, duplicate, or intentionally not pursued.

### Work Type

Type: Single select

Values:

- `Prototype`
- `MVP`
- `Research Spike`
- `Demo`
- `Production Candidate`
- `Bug`
- `Docs`
- `ADR`
- `Security / Boundary`
- `RDE Review`
- `Maintenance`
- `Release`

Meaning:

- `Prototype`: exploratory; may be discarded.
- `MVP`: validates a value hypothesis with a user or adoption context.
- `Research Spike`: answers a technical or conceptual uncertainty.
- `Demo`: communicates a possibility; not proof of value or architecture.
- `Production Candidate`: intended for hardening, tests, documentation, and compatibility review.

### Decision State

Type: Single select

Values:

- `Question`
- `Hypothesis`
- `Adopt`
- `Revise`
- `Defer`
- `Reject`
- `Discard`
- `Completed`

### RDE Required

Type: Single select or checkbox

Recommended values if single select:

- `No`
- `Yes`
- `Completed`

Use `Yes` when the work affects architecture, context boundaries, AI behavior, project methodology, security boundaries, product direction, or public-facing semantics.

### Target Stage

Type: Single select

Values should follow `docs/roadmaps/overall-roadmap.md`:

- `Stage A: Core Baseline Preservation`
- `Stage B: Operational Readiness Baseline`
- `Stage C: Security and Boundary Baseline`
- `Stage D: AI / Retrieval Boundary Expansion`
- `Stage E: Federation Package Foundation`
- `Stage F: Signed Manifest and Integrity`
- `Stage G: Chronicle Object Expansion`
- `Stage H: Federation Message MVP`
- `Stage I: Node Trust Model`
- `Stage J: Context SNS Surface`
- `Stage K: Networked Federation`
- `Stage L: Future Concept Graduation`

### Linked PR

Type: Text

Use the PR number or URL.

### Linked ADR

Type: Text

Use an ADR path such as:

```text
docs/adr/0004-prototype-mvp-agile-development-methodology.md
```

### Priority

Type: Single select

Values:

- `P0`
- `P1`
- `P2`
- `P3`

## State transition rules

### Backlog -> Ready

Allowed when:

- the Issue has a clear question, defect, request, or opportunity;
- the Work Type is set;
- acceptance criteria or a clear next action exists;
- obvious blockers are absent or documented.

### Ready -> In Progress

Allowed when:

- someone is actively working on the Issue;
- the intended outcome is still consistent with the Issue body;
- Prototype / MVP / Research Spike / Production Candidate classification is clear.

### In Progress -> Review

Allowed when:

- a PR exists, or a decision review is explicitly needed;
- the Issue links to the PR or review artifact;
- the PR contains Summary, Boundary, Verification, Warning classification, and RDE review when required.

### Review -> Done

Allowed when:

- the PR is merged; or
- the Issue is explicitly closed as completed; or
- the decision outcome is recorded and no code change is required.

### Any -> Deferred

Allowed when:

- the reason for deferral is written in the Issue;
- the next review trigger is clear, if known.

### Any -> Rejected / Not planned

Allowed when:

- the Issue is closed or marked with a clear reason such as invalid, duplicate, rejected, or not planned;
- the rejection reason is visible in the Issue.

## Automation guidance

GitHub Project automation should follow these rules when available:

- New Issue -> `Backlog`.
- Draft PR linked -> `In Progress` or `Review`, depending on project preference.
- Ready-for-review PR linked -> `Review`.
- Merged PR linked -> `Done`.
- Closed Issue with not planned / duplicate / invalid -> `Rejected / Not planned`.
- Closed Issue with completed -> `Done`.

Do not automate state changes that require semantic judgment unless the Issue or PR carries the necessary evidence.

## Issue template alignment

Issue templates should ask for:

- Work Type.
- Originating question.
- Hypothesis or expected value.
- Acceptance criteria.
- Non-goals.
- RDE requirement.
- Target Stage, if applicable.

## PR template alignment

PR templates should ask for:

- Linked Issue.
- Work Type.
- Summary.
- Boundary.
- Verification.
- Warning classification.
- RDE review.
- Local act CI result, when CI changes or release readiness are affected.

## Manual setup steps

The current connector cannot create or update GitHub Projects directly. Configure the project in the GitHub UI or through a GitHub Projects API client using the fields and transitions above.

Recommended manual sequence:

1. Create a repository or organization project named `Chronicle Stack Development`.
2. Add the repository to the project.
3. Add the fields listed in this document.
4. Create the `Flow` board view grouped by `Status`.
5. Create the `Planning` table view with Work Type, Decision State, RDE Required, Target Stage, Linked PR, Linked ADR, and Priority visible.
6. Add automation rules only where they do not require semantic judgment.
7. Use `.github/ISSUE_TEMPLATE/work-item.yml` for new work items.
8. Use `.github/PULL_REQUEST_TEMPLATE.md` for PR evidence.

## RDE review

### Preserved

- Issues remain the planning source of truth.
- Kanban remains useful for flow visibility.
- PRs remain implementation evidence.
- ADRs remain stable decision records.

### Transformed

- Kanban is explicitly reduced from a task authority to a derived state view over Issues.

### Completed

- Recommended Project name, views, fields, state transitions, automation guidance, manual setup steps, and template alignment.

### Unresolved

- This document does not itself create the GitHub Project because Project administration is not available through the current connector.
- Exact GitHub Project field IDs and automation rules must be configured in the GitHub UI or an appropriate GitHub Projects API client.

### Deviation risks

- Board-only notes may become hidden requirements.
- Status movement may be treated as a decision without Issue or PR evidence.
- Kanban flow optimization may override Prototype / MVP / RDE learning goals.
