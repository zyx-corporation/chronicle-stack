# Claude Design Prompt for Chronicle Stack Final UI

Use the following prompt with Claude Design.

---

You are designing the final target UI for Chronicle Stack.

Read the attached specification first and follow it closely.

Project identity:

- Chronicle Stack is a local-first system for reconstructable AI-assisted work
- it records context, artifacts, decisions, diffs, provenance, audit, review, trust, and federation state
- it is not a hosted SaaS dashboard, not a social feed, and not a generic CRUD admin app
- its current UI is a local web-based read model, but this task is to design the final target UI, not merely restyle the current implementation

Hard boundaries you must preserve:

- local-first
- `.chronicle/chronicle.jsonl` remains the primary record
- derived views must remain visibly derived
- proposal/review/apply is preferred over direct mutation
- federation is preview-first, inspect-first, and consent-aware
- no auto-import, no hidden sync, no hosted GraphRAG runtime, no graph DB/vector DB product drift

Your task:

Produce a final UI design concept that is implementable later in either a local web UI or a desktop shell such as Tauri, but do not constrain the design to the current HTML structure.

What to deliver:

1. A concise design thesis for the product
2. Information architecture
3. Top-level navigation model
4. Visual direction and design language
5. Detailed description of the main screens:
   - Home / Overview
   - Chronicle Objects
   - Context and Artifact Workbench
   - Review Workspace
   - Audit / Boundary / Lifecycle Workspace
   - Federation Workspace
   - Trust Workspace
   - Runtime / Retrieval Workspace
6. A clear concept for proposal -> review -> apply flows
7. Key component patterns
8. Important empty / warning / blocked / preview-only / ready states
9. Rationale for how the design expresses provenance, auditability, and safe action boundaries

Output style requirements:

- be specific and product-designer-like, not generic
- avoid bland admin-dashboard language
- do not produce a social timeline concept
- do not optimize for engagement
- optimize for operator trust, reconstruction speed, and cognitive clarity
- make the design feel calm, exact, and evidence-oriented
- prefer a laptop/desktop-first design

Important product truths to reflect in the design:

- the landing experience should emphasize current questions, pending review, meaningful diffs, and actionable boundary state more than raw chronology
- review is a first-class workflow, not a small modal
- federation should feel like an inspection desk for controlled handoff, not a send-message toy
- trust and consent should be visible near the workflows they affect
- AI/runtime surfaces should appear as bounded assistance and derived evidence, not magical authority

Please structure your answer as:

1. Design Thesis
2. Product Principles
3. Information Architecture
4. Navigation Model
5. Screen-by-Screen Design
6. Component System
7. State Design
8. Why This Fits Chronicle Stack

If useful, include:

- wireframe-style textual layout descriptions
- component naming suggestions
- visual motifs
- typography direction
- color system direction

Do not:

- assume cloud collaboration
- assume direct free-form document editing as the default core interaction
- assume public web deployment
- assume network federation is already active
- collapse provenance, review, and boundary information into hidden secondary panels

The output should read like a serious final-product UI concept proposal for Chronicle Stack.

---
