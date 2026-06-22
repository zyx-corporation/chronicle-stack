# ADR-0025: Local UI i18n Presentation Boundary

Status: Accepted  
Date: 2026-06-22  
Scope: Chronicle Stack `chronicle ui` local interactive presentation layer  
Related: ADR-0018, ADR-0019, ADR-0021, ADR-0022, `docs/adr/ADR-002-i18n-and-language-selection.md`, `docs/cli-reference.md`

## Context

Chronicle Stack already has a project-wide i18n decision in `ADR-002: i18n and Language Selection`.

That ADR establishes that user-facing UI text, CLI messages, labels, warnings, and future dashboard surfaces must be locale-aware.

However, the current local UI has grown into a substantial operator-facing surface with:

```text
overview cards
slice labels
filter labels
sort labels
review readiness summaries
preview-only mutation notices
runtime record summaries
detail headings
empty states
copy affordances
```

This creates a local architectural risk:

```text
UI wording drift could change operator interpretation of read-only, preview-only,
authorization, review, or recovery semantics before any underlying record contract changes
```

The existing local UI ADRs already establish that:

- Chronicle JSONL remains authoritative
- local UI state is derived and ephemeral
- review semantics in the UI must remain descriptive and CLI-parity-aware
- GUI mutation must stay explicitly gated and fail closed

Without a local UI i18n ADR, future translation work could blur:

```text
localized presentation        vs authoritative record meaning
human-friendly labels         vs machine-readable status values
translated UI copy            vs approval or enforcement semantics
language preference           vs durable Chronicle record content
```

## Decision

Chronicle Stack adopts the following rule for local UI internationalization:

```text
`chronicle ui` visible copy may be localized, but localization remains a presentation-layer concern.
It must not change Chronicle record authority, machine-readable payload values,
review/write-path semantics, or security-boundary meaning.
```

This means:

1. Local UI headings, labels, helper text, empty states, filter names, sort names, and read-only summaries should be resolved through stable translation keys rather than ad hoc inline literals.
2. Machine-readable payload fields, identifiers, codes, route names, and canonical CLI commands remain stable and are not translated in transport.
3. Human-facing labels derived from those stable values may be localized in the UI shell.
4. Boundary-critical wording such as `read-only`, `preview only`, `mutation enabled`, `authorization failed`, `rollback`, and `recovery path` must preserve the same operational meaning across supported locales.
5. Localization must not make advisory or preview-only state sound stronger than it is.
6. Local UI locale preference is UI/session presentation state unless a later ADR explicitly promotes it to a persisted Chronicle setting.

## Boundary

The accepted i18n presentation boundary is:

```text
Chronicle JSONL / stored records        = authoritative record content
API payload codes / ids / booleans      = stable machine-readable contract
CLI-equivalent recovery commands        = canonical operational text
localized UI labels / summaries         = presentation only
locale selection for local UI           = presentation preference only
```

The local UI may localize:

```text
section headings
overview card titles
filter and sort labels
empty states
warning/explanatory helper copy
review readiness summaries
runtime list labels
button text for read-only affordances
```

It must not localize or reinterpret:

```text
record ids
event ids
artifact ids
decision ids
route paths
machine-readable status codes
boolean contract meaning
canonical CLI recovery commands
```

## Rationale

This rule preserves both usability and reconstructability:

1. The UI can become friendlier for Japanese, English, and Simplified Chinese operators.
2. Durable Chronicle meaning stays anchored in stable records and stable wire contracts.
3. Boundary-sensitive wording is treated as a design concern rather than cosmetic copy.
4. Future UI localization can progress incrementally without silently weakening fail-closed or preview-only semantics.

This is especially important for Chronicle because wording such as:

```text
read-only
preview only
needs review
authorization failed
request changes
recovery path
```

is operational, not decorative.

## Consequences

### Positive

- Local UI copy can be translated without changing stored Chronicle data.
- Human-facing labels and machine-readable payloads remain clearly separated.
- Future UI i18n work has an explicit boundary for review/auth/mutation wording.
- Shared label helpers can reduce wording drift across overview/list/detail surfaces.

### Negative / Cost

- Translation work must review operational wording, not just literal wording.
- Some labels may need dual treatment: stable raw value plus localized display label.
- Future locale persistence work needs a separate ADR if it should become durable project state.

## Required Future Pattern

Future local UI i18n work should follow this rule:

```text
If a change only affects how local UI copy is presented, keep it in translation keys/helpers.
If a change alters durable record meaning, API payload contract, or write-path semantics,
require a new ADR or an update to the governing boundary ADR.
```

Examples that remain inside this ADR:

```text
localizing overview card labels
localizing filter/sort names
localizing read-only helper text
localizing empty-state copy
localizing review warning summaries while preserving semantics
```

Examples that require a future ADR:

```text
persisting ui locale into Chronicle project metadata
changing API payload field values by locale
translating canonical CLI recovery commands
making locale selection part of review/write authorization context
```

## Non-goals

This ADR does not:

- require immediate translation of every local UI string
- define the full translation catalog structure for all surfaces
- persist local UI locale into Chronicle JSONL
- localize machine-readable API payload values
- change CLI mutation semantics
- change auth/authz enforcement rules
- change read-only or preview-only boundaries
