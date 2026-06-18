# Chronicle Stack v1.1.0 Release Notes

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

## Summary

Chronicle Stack v1.1.0 is a GUI/readability release over the v1.0.0 local-first foundation.

The main change is that Chronicle Stack now has a human-facing review surface beyond CLI-only workflows:

- static read-first Review Console
- explicit foreground local web UI through `chronicle ui`
- read-only JSON endpoints for local browser inspection
- lightweight local browser shell

## Highlights

### Static Review Console

The previous static HTML dashboard has been reframed and extended as a Review Console.

It includes:

- Review Console boundary panel
- local path panels
- package review snapshot
- package review findings
- audit events
- lifecycle markers
- boundary notes
- graph summary counts

### Explicit local UI

`chronicle ui` starts a foreground local UI process.

Default behavior:

```text
host: 127.0.0.1
port: 8765
mode: read-only
runtime: foreground-local-ui
```

### Read-only UI endpoints

`chronicle ui` exposes local read-only endpoints:

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

The static Review Console remains available through:

```text
/review-console
```

### Lightweight browser shell

The `/` route now returns a lightweight local browser shell that fetches the read-only endpoints.

This makes the UI more navigable without adding a framework dependency or a hosted runtime.

## Compatibility

The v1.0 CLI compatibility surface remains intact.

Stable command families include:

- `chronicle`
- `chronicle-context`
- `chronicle-export`
- `chronicle-package`
- `chronicle-graph`
- `chronicle-audit`
- `chronicle-lifecycle`

`chronicle ui` is additive.

## Boundary

v1.1.0 does not add:

- daemon or autostart behavior
- hosted service
- cloud sync
- external model API calls
- GraphRAG runtime
- vector DB
- graph DB
- write-capable GUI actions
- authentication as a false security layer
- access-control enforcement
- correctness proof

`chronicle ui` is a local browser-facing review surface over local Chronicle files.

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
chronicle 1.1.0
```

GUI-specific smoke is defined in:

```text
docs/smoke-test-v1.1.md
```

## Legal / governance status

The commercial license and contributor policy drafts remain draft completed / counsel review pending.

v1.1.0 does not finalize legal terms.

## Warning classification

- Release warning: tag creation, GitHub Release publication, and tag-based installer smoke remain explicit release-operator steps.
- Runtime warning: GUI release must not imply daemon, hosted service, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: localhost UI is still a browser-exposed local surface.
- Semantics warning: UI visibility is not access control, enforcement, or correctness proof.
- Legal warning: commercial/contributor documents remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- CLI as canonical automation surface.
- Static Review Console as read-only derived export.
- Advisory/diagnostic semantics.
- No external model/runtime dependency.

### Transformed

- Chronicle Stack gains a practical human-facing GUI/readability layer.

### Supplemented

- `chronicle ui` foreground local server.
- Read-only local API endpoints.
- Lightweight browser shell.
- GUI smoke profile.

### Unresolved

- External v1.1.0 tag publication.
- GitHub Release publication.
- Tag-based installer smoke evidence.
- Future write-capable preview workflows.
- Tauri or desktop packaging.
- Visual design polish.

### Deviation risks

- Mistaking local UI for hosted service readiness.
- Treating UI visibility as access control.
- Treating GUI review status as correctness proof.
- Expanding GUI into Sayane / CSG-RAG / GraphRAG runtime responsibilities.
