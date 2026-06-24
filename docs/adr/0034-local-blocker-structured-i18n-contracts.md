# ADR-0034: Local Blocker Structured i18n Contracts

- Status: Accepted
- Date: 2026-06-24

## Context

`v1.14.0` completed and published the local reviewer-boundary derived-fallback-copy lane.

That lane reduced wording drift for reviewer-boundary drilldown payloads by making fallback copy deterministic and template-aligned.

The next narrow local-UI i18n follow-on is adjacent but distinct:

- auth-boundary blocker details still rely on raw fallback strings
- mutation blocker details and summaries still rely on raw fallback strings
- HTML rendering still has to treat blocker strings as opaque localized text rather than explicit structured presentation contracts

This creates a smaller but real i18n risk:

- read-only blocker wording can drift between payload JSON and renderer formatting
- summary strings can become partially localized while detail strings remain ad hoc
- future locale expansion would need to infer blocker semantics from prose rather than stable keys

Related records:

- `docs/adr/0025-local-ui-i18n-presentation-boundary.md`
- `docs/adr/0033-local-reviewer-boundary-derived-fallback-copy.md`
- `docs/release-status-v1.14.0.md`
- `docs/v1.14-release-remaining-issues.md`

## Decision

`v1.15.0` begins as the local blocker structured-i18n-contract lane after the published `v1.14.0` release.

This lane may:

1. add stable `message_key` fields to auth-boundary and mutation blocker detail payloads
2. add stable `summary_key` plus params to blocker summary payloads
3. preserve fallback `message` and `summary` strings as derived presentation fallbacks
4. let the embedded HTML renderer prefer structured keys while preserving read-only fallback behavior
5. extend smoke/test coverage for those explicit blocker presentation contracts

This lane must not:

- change blocker meaning or fail-closed semantics
- translate machine-readable blocker codes
- widen write capability or hosted identity scope
- make localized blocker wording authoritative over JSON/CLI contracts

## Consequences

Repository-side work in `v1.15.0` should keep blocker payloads descriptive and read-only while making their presentation contracts explicit and key-driven.

This keeps the slice narrow:

- i18n work moves forward without changing Chronicle authority boundaries
- payload consumers can localize blocker wording through stable keys
- fallback strings remain available for CLI-compatible inspection and degraded render paths

## Rationale

After reviewer-boundary summaries gained structured fallback contracts, blocker summaries became the next most obvious presentation-only seam with repeated local wording.

Making blocker copy structured is the smallest next step that improves i18n discipline across:

- overview mutation-readiness panels
- auth-readiness notices
- mutation-enablement notices
- read-only smoke assertions

