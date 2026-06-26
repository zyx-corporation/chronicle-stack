# ADR-0004: Prototype First / MVP / Agile development methodology

Status: Accepted

## Context

Chronicle Stack is developed in an environment where LLM-assisted implementation can produce working code, UI sketches, CLI surfaces, tests, documentation, and demos at high speed. This changes the cost structure of development. It becomes easier to build before fully understanding, easier to iterate before stabilizing, and easier to mistake a convincing prototype for a production-ready design.

The project therefore needs an explicit development methodology that preserves the benefits of rapid exploration while preventing accidental hardening of temporary implementation choices.

The adopted evaluation is:

> Prototype First discovers unknowns.  
> MVP validates value.  
> Agile repeats learning.  
> Chronicle Stack preserves the lineage of that learning.  
> RDE audits the semantic change.  
> TDD stabilizes the intended behavior.

This ADR records that evaluation as a project-level development guideline.

## Decision

Chronicle Stack will use Prototype First, MVP, and Agile as distinct but connected development modes. They must not be treated as interchangeable.

The project will classify exploratory and delivery work according to the question being answered:

- Prototype First answers: **Can this be made, and what unknowns become visible when it is made?**
- MVP answers: **Does this provide value to a real user, customer, or adoption context?**
- Agile answers: **What should be improved next, based on validated learning and current constraints?**

Every substantial LLM-assisted development cycle should preserve the learning lineage: the originating question, the hypothesis, the prototype or MVP boundary, the decision made, the delta from the prior state, and any RDE review.

Kanban will be integrated with GitHub Issues as a state and flow view. Issues are the planning source of truth; Kanban boards are derived views over those Issues, not a separate task database.

## Definitions

### Prototype First

Prototype First means building a small, often disposable implementation to expose unknowns in design, UI, data flow, CLI ergonomics, integration boundaries, or technical feasibility.

A prototype is not a product commitment. It is a learning instrument.

A Prototype First task should identify:

- the question being explored;
- the hypothesis being tested;
- whether the result is throwaway, reusable, or a candidate for redesign;
- which assumptions were confirmed, weakened, or rejected;
- what must be rebuilt before production use.

### MVP

MVP means Minimum Viable Product, but in this project it is interpreted as a **minimum viable learning experiment**, not merely a small product.

An MVP is valid only when it names the value hypothesis it is intended to test. A small demo without a falsifiable adoption, usage, business, or workflow hypothesis is not an MVP.

An MVP should identify:

- the user or adoption context;
- the value hypothesis;
- the minimum experience required to test that value;
- the success, failure, or continuation criteria;
- the decision after observation: adopt, revise, defer, or reject.

### Agile

Agile means iterative development under changing knowledge and constraints. In this project it is not equivalent to issue throughput, sprint velocity, or incremental patching alone.

Agile is acceptable when each iteration preserves what was learned and why the next change is justified. Without lineage, Agile can become drift.

An Agile iteration should identify:

- what prior decision or feedback motivates the next step;
- what behavior is intended to change;
- what should remain preserved;
- what tests or checks stabilize the change;
- what RDE review says about semantic drift.

### Kanban

Kanban is the visual flow layer for Issue-based work. It shows where an Issue is in the delivery stream, but it does not replace the Issue as the source of planning truth.

Kanban cards should not contain unique requirements, decisions, acceptance criteria, RDE review, or implementation rationale that are absent from the Issue. Those details belong in the Issue, linked PRs, ADRs, or Chronicle records.

The recommended minimum columns are:

- `Backlog`: unstarted question, request, defect, or opportunity.
- `Ready`: sufficiently specified and unblocked.
- `In Progress`: active implementation or investigation.
- `Review`: PR opened, decision pending, or review required.
- `Done`: merged, completed, or explicitly closed.
- `Deferred`: intentionally postponed.
- `Rejected / Not planned`: rejected, invalid, duplicate, or intentionally not pursued.

## Methodology

Chronicle Stack development should follow this order when exploring uncertain features:

1. Record the originating question.
2. State the hypothesis.
3. Classify the work as Prototype, MVP, Agile iteration, Research Spike, Demo, or Production Candidate.
4. Build the smallest artifact that answers the current question.
5. Evaluate what was learned.
6. Record the decision: adopt, revise, defer, reject, or discard.
7. If adopted, convert the result into specification, tests, and stable boundaries.
8. Run RDE review to compare the result against the original intent.
9. Use TDD or equivalent tests to stabilize behavior before treating it as production-path code.

## Issue / Kanban / PR / ADR responsibilities

The project will use the following responsibility split:

- `Issue`: planning source of truth. Holds the question, hypothesis, work label, acceptance criteria, non-goals, context, and links.
- `Kanban`: derived state view. Shows flow and bottlenecks, but does not hold unique planning truth.
- `PR`: implementation evidence. Holds Summary, Boundary, Verification, Warning classification, and RDE review for the concrete change.
- `ADR`: stable decision record. Holds accepted architectural, methodological, or policy decisions.
- `Chronicle`: long-term lineage record. Preserves the wider context, decision history, deltas, and later reconstruction surface.

This means that moving a card on a Kanban board is not itself a decision record. The decision must be visible in the Issue, PR, ADR, or Chronicle record.

## LLM-assisted development rule

LLM-generated output must not be treated as authoritative merely because it runs.

LLM support is suitable for:

- creating exploratory prototypes;
- generating alternative implementations;
- drafting tests and documentation;
- surfacing edge cases;
- implementing narrow, reviewable changes;
- summarizing deltas for human review.

LLM support is not sufficient for:

- declaring a prototype production-ready;
- deciding that a value hypothesis has been validated;
- converting a temporary implementation into architecture;
- treating AI interpretation as a durable fact;
- bypassing RDE review, TDD, security review, or context-boundary review.

## Required labels for work products

Substantial work products should be explicitly labeled as one of the following:

- `Prototype`: exploratory; may be thrown away.
- `MVP`: validates a value hypothesis with a user or adoption context.
- `Research Spike`: answers a technical or conceptual uncertainty.
- `Demo`: communicates a possibility; not proof of value or architecture.
- `Production Candidate`: intended for hardening, tests, documentation, and compatibility review.
- `Deprecated / Discarded`: retained only for lineage or comparison.

The label should appear in the issue, PR body, design note, or related Chronicle record. When a Kanban board is used, the same classification should be visible through Issue labels or fields rather than board-only card text.

## Consequences

### Positive

- Rapid LLM-assisted prototyping can be used without allowing prototypes to become accidental architecture.
- MVP work remains tied to value validation instead of becoming a vague early product label.
- Agile iteration remains grounded in learning, not just issue throughput.
- TDD and RDE become explicit phase gates for moving from exploration to stable implementation.
- Kanban can show work flow without becoming a competing source of truth.
- Chronicle Stack dogfoods its own principle: the value is not only what was built, but what was learned and preserved.

### Negative

- More lightweight metadata must be written around development work.
- Some fast prototypes may be discarded even if they appear to work.
- The team must resist pressure to treat a convincing demo as validated product value.
- Work may appear slower when moving from prototype to production candidate because tests, boundary review, and RDE are required.
- Kanban cards must be kept synchronized with Issue state to avoid misleading flow views.

## Acceptance guidance

A feature may move from Prototype to Production Candidate only if:

- the explored question is answered;
- the surviving behavior is restated as a requirement or design note;
- tests exist or are explicitly planned;
- the data and context boundaries are identified;
- RDE review records preserved, transformed, completed, unresolved, and deviation-risk elements.

An MVP may move toward productization only if:

- the user or adoption context is identified;
- the value hypothesis was tested;
- the observation result is recorded;
- the next decision is explicit.

An Agile iteration is acceptable only if:

- it is connected to a prior decision, defect, user observation, or roadmap item;
- it does not silently rewrite core assumptions;
- it leaves enough evidence for later reconstruction.

A Kanban state transition is acceptable only if:

- the underlying Issue contains the relevant planning truth;
- the Issue state, labels, or linked PRs justify the movement;
- board-only notes do not contain unique requirements or decisions;
- Done means merged, explicitly completed, or intentionally closed with a reason.

## RDE review

### Preserved

- Prototype First remains valuable for exposing unknowns quickly.
- MVP remains valuable for testing user, adoption, or business value.
- Agile remains valuable for iterative learning and adaptation.
- TDD remains the mechanism for stabilizing intended behavior.
- GitHub Issues remain a practical unit for planning and traceability.

### Transformed

- These methods are not treated as generic development slogans. They are converted into Chronicle Stack-specific development modes with required lineage and decision recording.
- Kanban is treated as a derived state view over Issues rather than a separate planning authority.

### Completed

- Distinct definitions for Prototype First, MVP, Agile, and Kanban.
- A methodology for LLM-assisted development cycles.
- Work-product labels for prototypes, MVPs, research spikes, demos, production candidates, and discarded artifacts.
- Criteria for moving from exploration to production candidate.
- Responsibility split between Issue, Kanban, PR, ADR, and Chronicle.

### Unresolved

- Exact CLI or Chronicle object support for recording these classifications is not defined in this ADR.
- PR templates and issue templates may need later updates to include work-product labels and RDE review fields.
- The exact GitHub Project fields / Kanban columns are not automated by this ADR.

### Deviation risks

- Treating a prototype as production because it runs.
- Calling a demo an MVP without a value hypothesis.
- Letting Agile devolve into issue throughput without preserving decision lineage.
- Letting Kanban become a competing task database instead of an Issue view.
- Letting board-only card notes contain decisions that are not preserved in Issues, PRs, ADRs, or Chronicles.
- Letting LLM-generated implementation details overwrite the project’s core design principles.

### Next update policy

Future work should add issue and PR templates that ask contributors to identify whether a change is Prototype, MVP, Research Spike, Demo, or Production Candidate, and to include a minimal RDE review when the change affects architecture, context boundaries, AI behavior, or product direction.

Future work should also add GitHub Project / Kanban guidance that makes Issue labels and fields the source for work classification and board state.
