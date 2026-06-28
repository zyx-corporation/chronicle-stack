# Chronicle Stack v1.2.0 Release Notes

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

## Summary

Chronicle Stack v1.2.0 is a UI drill-down / inspectability release over v1.1.0.

The main change is that `chronicle ui` can now inspect individual records through read-only detail endpoints and lightweight browser drill-down affordances.

## Highlights

### Read-only detail endpoints

v1.2.0 adds record-level detail endpoints for the local UI:

```text
/api/events/<id>
/api/contexts/<id>
/api/artifacts/<id>
/api/decisions/<id>
/api/rde/<id>
/api/boundary/<id>
/api/audit/<id>
/api/lifecycle/<id>
```

These endpoints return JSON derived from local Chronicle files.

### Artifact versions in detail view

Artifact detail payloads include version metadata so users can inspect artifact history from the local UI surface.

### Lightweight drill-down affordance

The local browser shell now includes JSON drill-down buttons for table rows where a supported record identifier is available.

This makes `chronicle ui` useful for record inspection without adding write-capable actions or a framework dependency.

## Compatibility

The v1.1 local UI collection endpoints remain available:

```text
/api/overview
/api/events
/api/contexts
/api/artifacts
/api/decisions
/api/rde
/api/boundary
/api/audit
/api/lifecycle
/api/package-review
/api/graph-summary
```

The static Review Console remains available at:

```text
/review-console
```

CLI workflows remain canonical and scriptable.

## Boundary

v1.2.0 does not add:

- write-capable GUI actions
- authentication or authorization
- public network binding by default
- daemon or autostart behavior
- hosted service
- cloud sync
- external model API calls
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof

Detail endpoints are read-only inspection surfaces.

## Verification

Repository-side verification expected before release:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version:

```text
chronicle 1.2.0
```

UI-specific smoke is defined in:

```text
../smoke/smoke-test-v1.2.md
```

## Legal / governance status

The commercial license and contributor policy drafts remain draft completed / counsel review pending.

v1.2.0 does not finalize legal terms.

## Warning classification

- Release warning: tag creation, GitHub Release publication, and tag-based installer smoke remain explicit release-operator steps.
- Runtime warning: UI drill-down must not imply daemon, hosted service, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: localhost UI remains browser-exposed.
- Semantics warning: detail views are not access control, enforcement, or correctness proof.
- Legal warning: commercial/contributor documents remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- CLI as canonical automation surface.
- Static Review Console as read-only derived export.
- Explicit foreground local UI boundary.
- Advisory/diagnostic semantics.

### Transformed

- The local UI moves from collection browsing toward record-level inspection.

### Supplemented

- Detail endpoints.
- Artifact version detail payloads.
- Lightweight drill-down buttons.
- Detail endpoint smoke profile.

### Unresolved

- External v1.2.0 tag publication.
- GitHub Release publication.
- Tag-based installer smoke evidence.
- Future write-preview workflows.
- Desktop packaging.
- Richer visual design.

### Deviation risks

- Mistaking detail views for access-control enforcement.
- Treating UI drill-down as correctness proof.
- Expanding local UI into hosted-app responsibilities.
- Adding mutation through convenience pressure.
