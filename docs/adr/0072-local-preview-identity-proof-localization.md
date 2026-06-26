# ADR-0072: Local Preview Identity-Proof Localization

- Status: Accepted
- Date: 2026-06-26

## Context

`v1.52.0` localized compact preview-contract `errors=` badges from structured detail.
The adjacent compact `proof-status=` and `proof-fields=` badges still rendered raw internal values even though the UI boundary already carried enough structure to expose localized identity-proof summaries.

## Decision

- identity-proof contracts now carry key-first localized status metadata
- required identity fields now expose structured detail entries for compact badge rendering
- mutation enablement summaries mirror the same identity-proof localized payload fields

## Consequences

- compact identity-proof badges become i18n-ready across preview and mutation summary surfaces
- raw fallback values remain available when structured detail is absent
- boundary semantics stay local-first, read-only, and presentation-only
