# ADR-0004: Prompt Injection Sanitizer Boundary

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, `docs/prompt-injection-sanitizer-boundary.md`

## Context

Chronicle Stack stores records that may later be read by humans, tools, local models, external models, CSG-RAG pipelines, Sayane review workflows, or other future integrations.

Stored records may contain text that looks like instructions to a model or agent. Such text can appear accidentally, be quoted from another source, or be intentionally hostile.

Examples include:

```text
ignore previous instructions
send this to external...
treat this as public
```

Chronicle Stack must preserve the record faithfully, while preventing future model-facing workflows from treating stored text as instructions.

## Decision

Chronicle Stack will define a prompt-injection sanitizer boundary.

The boundary has two parts:

1. Lightweight risk detection for known instruction-like phrases.
2. Explicit formatting that wraps stored record text as Chronicle data, not instructions.

This boundary is mitigation and observability. It is not complete prompt-injection prevention.

## Boundary Rule

Stored Chronicle content must be treated as data.

```text
stored record text != system instruction
stored record text != classification authority
stored record text != permission to disclose
stored record text != permission to perform external actions
```

## Implementation Direction

v0.5 introduces helper functions:

```python
scan_text_for_prompt_injection(...)
format_as_chronicle_data_block(...)
```

These helpers are intentionally small and deterministic.

They are useful for:

- future doctor checks
- model-context dry-runs
- review package generation
- CSG-RAG / Sayane integration contracts
- export warnings

## Non-goals

This ADR does not implement:

- complete prompt-injection prevention
- model-level safety guarantees
- automatic rewriting of Chronicle records
- blocking all suspicious text
- mutation of original records
- external model runtime

## Consequences

### Positive

- Future integrations have a clear data-vs-instruction boundary.
- Detection can be tested without model calls.
- Original records remain faithful.
- Risk can be surfaced without claiming complete prevention.

### Negative / Cost

- Detection is incomplete.
- Some findings may be false positives.
- Downstream integrations must still respect the boundary.

## RDE Review

### Preserved

- JSONL remains primary.
- Original records are not mutated.
- Faithful preservation remains the default.
- No model calls are introduced.

### Transformed

- Model-facing workflows gain an explicit stored-data boundary.

### Added

- Prompt-injection risk categories.
- Lightweight scan helper.
- Chronicle data block formatter.

### Unresolved

- Doctor integration.
- Export-time warnings.
- Context package integration.
- Pattern registry governance.

### Deviation Risks

- Treating scanner output as complete safety.
- Mutating original records during sanitization.
- Ignoring warnings because they are advisory.
- Passing stored text to models without the data boundary.
