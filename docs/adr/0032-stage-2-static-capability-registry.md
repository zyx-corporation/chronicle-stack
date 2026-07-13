# ADR-0032: Stage 2 Static Capability Registry

- Status: Accepted
- Date: 2026-07-13

## Context

Stage 2 needs explicit names and safety metadata for executable or proposal-producing operations. Dynamic package discovery would expand the trust boundary beyond the current local-first product.

## Decision

Chronicle uses a built-in, static `CapabilityRegistryService` backed by `CapabilityManifest` records. Capability IDs are provider-neutral dotted names. Duplicate, unknown, and out-of-scope capabilities fail closed. The registry is a derived application surface and is never written to `chronicle.jsonl` as authoritative state.

Capability code receives access only through `ScopedCapabilityRuntime`: selected context and artifact readers, a proposal-only writer, and a deny-by-default network policy.

## Consequences

- capability discovery works without external communication
- arbitrary plugin loading remains outside Stage 2
- access decisions are explicit and testable
- adding a capability requires a manifest and scoped-access review
