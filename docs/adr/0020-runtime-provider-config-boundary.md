# ADR-0020: Runtime Provider Configuration Boundary

Status: Accepted  
Date: 2026-06-20  
Scope: Chronicle Stack `chronicle runtime config` provider-contract persistence  
Related: ADR-0017, ADR-0018, ADR-0019, `docs/local-runtime-placeholder.md`, `docs/cli-reference.md`, `docs/v1.7-phase-f-g-h-plan.md`

## Context

Phase F introduced explicit local runtime commands and review-oriented runtime draft persistence, but one design gap remained:

```text
how provider configuration can exist without being mistaken for provider execution
```

Chronicle already established that:

- generated output requires explicit/manual invocation
- no external runtime is invoked implicitly
- Primary Chronicle records remain authoritative
- provider/runtime expansion must not hide behind convenience configuration

Without an explicit rule, a stored HTTP or local provider contract could be misread as:

```text
an active runtime session
permission to auto-call a model
a hidden network enablement toggle
proof that generated output exists or is trusted
```

## Decision

Chronicle Stack adopts the following rule for runtime provider configuration:

```text
Stored runtime provider configuration is contract metadata only.
It does not, by itself, invoke a runtime, authorize network activity, or create generated output.
```

This means:

1. `chronicle runtime config` persists provider-contract metadata under `.chronicle/runtime.yaml`.
2. `runtime status` may report both the actual local placeholder execution surface and the separately configured provider contract.
3. `set-http` stores downstream intent only; it does not create an active network session.
4. Any future model or HTTP invocation still requires an explicit/manual command path.
5. Generated output remains review-oriented derived output even when provider configuration exists.

## Boundary

The accepted boundary is:

```text
.chronicle/runtime.yaml         = stored provider contract metadata
chronicle runtime status        = descriptive runtime/config visibility
chronicle runtime summarize     = explicit/manual generated-output path
chronicle summary run           = explicit/manual re-run path
HTTP provider configuration     = stored downstream contract only
generated output                = review-oriented derived artifact/event, not authority
```

The configuration surface may describe:

```text
provider kind
model name
base URL
API key env name
allow-network intent
allow-external-context intent
review-required expectation
```

It must not imply:

```text
that configuration itself invoked a provider
that HTTP configuration created a live runtime session
that allow-network metadata means automatic network use
that configured providers replace the local placeholder boundary by default
that stored configuration changes Chronicle record authority
```

## Rationale

This rule keeps Phase F incremental and honest:

1. Provider contract work can proceed before any real runtime adapter is added.
2. Operators can inspect intended downstream configuration without hidden execution risk.
3. Future provider adapters inherit a clearer execution precondition: explicit/manual invocation remains separate from setup.
4. Provenance stays interpretable because configuration presence is not confused with runtime action.

## Consequences

### Positive

- Provider-contract work becomes inspectable and testable before real runtime calls exist.
- HTTP configuration can be modeled without violating the no-hidden-network boundary.
- `runtime status` can communicate both active local behavior and future-oriented contract intent.
- Future adapters have a clear config-vs-execution separation point.

### Negative / Cost

- Some runtime-related metadata now lives in a separate file in addition to event/artifact records.
- Future execution code must be careful not to silently treat stored config as approval to run.
- Users may need both `runtime config show` and runtime command output to understand the full picture.

## Required Future Pattern

Future runtime/provider work should follow this rule:

```text
If a change only stores, displays, or validates provider intent, keep it inside the config boundary.
If a change can invoke a provider, open a separate explicit/manual command path and document that invocation boundary directly.
```

Examples that remain inside this ADR:

```text
additional stored provider metadata
config display improvements
more precise downstream contract warnings
read-only UI visibility for runtime provider config
```

Examples that require a future ADR or boundary note:

```text
real HTTP provider invocation
automatic fallback from local placeholder to configured HTTP provider
background runtime execution
implicit provider selection during record creation
```

## Non-goals

This ADR does not:

- implement a real external runtime adapter
- enable automatic model invocation
- authorize hidden network access
- change review requirements for generated output
- make provider configuration authoritative Chronicle content
