# ADR-0035: Stage 2 Transport Boundary Skeleton

- Status: Accepted
- Date: 2026-07-13

## Context

External message sources may eventually feed Chronicle, but transport identities, attachments, and short messages are not trustworthy commands or Chronicle actors.

## Decision

External input is normalized as `ExternalInteractionEnvelope`. Identity is stored as evidence only. Attachments are bounded references; embedded bytes and secret-bearing metadata keys are rejected. `ExternalInteractionService` records accepted messages as review-required `user_input` events.

Command promotion is a separate, explicit operator action. Promotion records a preview-only candidate referencing a registered capability and never executes it. `MockTransportAdapter` validates this contract; real platform adapters remain outside Chronicle Core and outside Stage 2.

## Consequences

- receiving a message cannot invoke a capability
- platform credentials do not enter Chronicle payloads
- transport-specific APIs remain outside Core
- future adapters must verify signatures before constructing an envelope
