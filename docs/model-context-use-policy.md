# Chronicle Stack Model Context Use Policy

Status: v0.5 dry-run policy  
Related: #63, [ADR-0001](adr/0001-context-assets-security.md), [Operation Permission Model](operation-permission-model.md)

## Purpose

This document defines the v0.5 dry-run policy for using Chronicle Context records as model context.

The command introduced by this policy is:

```bash
chronicle-context check --target local --purpose "internal review"
chronicle-context check --target external --purpose "draft public summary" --json
```

This command does not submit any record to any model service.

It only checks selected Context records against advisory metadata.

## Why this is separate from view

Chronicle records are context assets.

A record being viewable does not mean it is appropriate to use as model context.

```text
view != model-context use
local model context != external model context
```

## Inputs

The dry-run check uses:

- target environment: `local` or `external`
- purpose
- selected Context IDs, or all Contexts if omitted
- ClassificationMetadata, where present
- AllowedOperation metadata
- LlmPolicy metadata

## Status

A check report has one of three statuses.

| Status | Meaning |
|---|---|
| `ok` | No warning or block was found. |
| `warning` | Use is not clearly approved or requires review / masking. |
| `blocked` | Use should not proceed under the default policy. |

`blocked` exits non-zero in the CLI.  
`warning` exits zero but must be recorded and classified before closing an issue, following ADR-0002.

## Rules

### Unclassified Context

If a Context has no ClassificationMetadata, the check emits a warning.

Reason:

```text
Unclassified context is not reliable enough for context-use decisions.
```

### Layer 4 / Restricted Secret

Layer 4 Context is blocked by default.

Reason:

```text
Restricted Secret records should not be placed in model context by default.
```

Layer 4 content should not be stored directly in Chronicle body text. It should be referenced from a dedicated secret manager or external controlled system.

### Missing inject operation

If `inject` is not listed in `allowed_operations`, the check emits a warning.

This is advisory, not enforcement.

### External target

For external target use:

- Layer 3+ without explicit external allowance emits a warning.
- Any context without `llm_policy.external_allowed=true` emits a warning.
- Any context with `masking_required=true` emits a warning.

### Local target

For local target use:

- If `llm_policy.local_allowed=false`, the check emits a warning.

## Auxiliary CLI boundary

The v0.5 implementation exposes this as an auxiliary console command:

```bash
chronicle-context check
```

rather than adding nested commands directly into the primary `chronicle` CLI.

This mirrors the v0.4 `chronicle-graph` approach and avoids unnecessary risk to the primary CLI structure.

A future version may add a nested primary command after the surface is stable.

## Non-goals

This policy and command do not implement:

- model API calls
- automatic context submission
- external model runtime
- authentication
- full access control
- complete data-loss prevention
- perfect prompt-injection protection

## RDE Review

### Preserved

- JSONL remains primary.
- Context records are not mutated by checks.
- Injection Plan remains non-submitting by default.
- Classification metadata remains advisory.

### Transformed

- Model-context use becomes an explicit checked boundary.

### Added

- `chronicle-context check` auxiliary command.
- ContextUse dry-run report.
- Target distinction between local and external.
- Warning/block status model.

### Unresolved

- Exact future nested primary CLI shape.
- Warning vs hard-fail policy beyond Layer 4.
- Explicit approval representation.
- Audit logging for context-use checks.

### Deviation Risks

- Treating dry-run as complete security.
- Treating warnings as ignorable.
- Accidentally adding actual model submission.
- Allowing Layer 3/4 context into external workflows without review.
