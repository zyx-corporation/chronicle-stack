# ADR-0031: Stage 2 Runtime Backend Port

- Status: Accepted
- Date: 2026-07-13

## Context

`RuntimeService` previously combined provider selection, HTTP/local execution, orchestration, and Chronicle recording. Stage 2 requires provider-specific behavior to remain replaceable without giving a backend access to Chronicle storage.

## Decision

Runtime execution uses the provider-neutral `RuntimeBackend` protocol and `RuntimeOrchestrator`. Local, HTTP, disabled, and fake implementations live under `chronicle.runtime.backends`. Backends return normalized values and never write Chronicle records. `RuntimeService` remains the compatibility facade, while `RuntimeRecordingService` owns persistence.

Disabled behavior is fail-closed. Configured-provider execution remains explicit, and provider failures are translated into `ChronicleError` subclasses before reaching the CLI.

## Consequences

- backend behavior can be tested without network or Chronicle storage
- provider response objects do not become stable service contracts
- recording policy can evolve separately from execution
- cancellation and timeout remain explicit backend contract concerns
