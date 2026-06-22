# ADR-0024: Explicit Configured Provider Execution Boundary

Status: Accepted  
Date: 2026-06-22  
Scope: `chronicle runtime summarize` / `chronicle runtime invoke` / `chronicle summary run` explicit configured-provider execution  
Related: ADR-0020, `docs/cli-reference.md`, `docs/v1.7-phase-f-g-h-plan.md`, `docs/v1.7-phase-f-g-h-closeout-summary.md`

## Context

Chronicle Stack already separated:

```text
stored provider configuration
from
explicit/manual runtime invocation
```

That rule was fixed by ADR-0020.

However, once the repository added a real non-local execution slice, one more boundary still needed to be stated explicitly:

```text
when a configured provider may actually be invoked,
and what must remain fail-closed before that invocation happens
```

Without this ADR, future runtime work could drift into:

- treating stored HTTP configuration as permission to run automatically
- silently switching `runtime summarize` from local placeholder mode to configured HTTP mode
- hiding credential / network / base URL prerequisites behind one generic execution path
- persisting externally produced drafts without clearly marking that an external call happened

## Decision

Chronicle Stack adopts the following execution rule:

```text
Configured-provider execution must require
1. stored provider configuration,
2. a command-local explicit execution flag,
3. a ready invocation contract, and
4. review-oriented persistence semantics.
```

In the current repository-side slice this means:

1. `chronicle runtime summarize` stays local-placeholder by default.
2. `chronicle runtime invoke` stays blocked unless the operator passes `--execute-configured-provider`.
3. `chronicle summary run` stays local-placeholder by default.
4. Configured HTTP execution happens only when the operator passes `--execute-configured-provider`.
5. HTTP execution must remain blocked unless:
   - provider kind is `http`
   - `allow_network=true`
   - `allow_external_context=true` when external source references are passed
   - `base_url` exists
   - `model_name` exists
   - `api_key_env` exists
   - the named env var is actually present
6. Configured-provider output remains derived and review-required.
7. Persisted summary-job provenance must mark `external_call_made=true` for configured-provider execution.
8. When configured-provider output is persisted as a generic artifact, that artifact remains a draft and does not become primary authority.

## Boundary

The accepted boundary is:

```text
runtime config set-http                 = stored contract only
runtime invoke-plan                     = dry-run readiness visibility
runtime summarize                       = local placeholder unless explicit execute flag is passed
runtime invoke                          = configured-provider text operation only when explicit execute flag is passed
summary run                             = local placeholder unless explicit execute flag is passed
execute-configured-provider flag        = per-command permission to cross the provider boundary
persisted draft output                  = pending-review derived artifact with provenance
```

Chronicle must not imply:

```text
that HTTP config alone authorizes execution
that a ready invoke-plan means execution already happened
that configured-provider output is authoritative
that external provider output may skip review
```

## Response contract

For the current HTTP text-operation contract:

- the request body is explicit JSON carrying operation, model, input text, and summarization limit
- optional external source refs and prompt notes may be included only when the stored contract allows external context
- optional operation-specific params may be included as explicit key/value metadata
- the response must be JSON
- one of `output_text`, `generated_text`, or `summary` must contain the generated text
- response metadata such as `response_id`, `finish_reason`, and `usage.*` may be retained as reviewable derived metadata

If any prerequisite fails, Chronicle must fail closed with a specific error class instead of silently falling back to another provider.

## Consequences

### Positive

- non-local execution can exist without weakening ADR-0020
- the operator can choose local-only or configured-provider execution per command
- persisted provenance now distinguishes local manual output from configured-provider output
- configured-provider text operations can persist reviewable draft artifacts without implying acceptance
- future provider adapters inherit a clearer activation rule

### Negative / Cost

- runtime commands gain another explicit option
- tests and docs must cover both local and configured-provider paths
- the current HTTP contract is intentionally narrow and may need future extension

## Non-goals

This ADR does not:

- define background execution
- enable automatic fallback to configured providers
- define multi-provider routing
- authorize hidden network activity
- remove review requirements from generated output
