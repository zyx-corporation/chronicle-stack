# Chronicle Stack v1.3.0 Release Notes

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

## Summary

Chronicle Stack v1.3.0 is an automated UI smoke / release-verification release over v1.2.0.

The main change is that the v1.2 manual UI detail smoke workflow is now available as a repeatable local command:

```bash
chronicle ui-smoke
chronicle ui-smoke --json
```

## Highlights

### Automated read-only UI smoke

`chronicle ui-smoke` validates the local UI data surface without starting a server or requiring a browser.

It checks:

- collection payloads
- available detail payloads
- missing-detail behavior
- package review payload
- graph summary payload

### Machine-readable smoke reports

`chronicle ui-smoke --json` emits a machine-readable report with:

```text
passed
read_only
server_started
browser_required
external_runtime
checks
```

This makes release verification easier to record and compare without turning the smoke result into a certification artifact.

## Compatibility

`chronicle ui` remains available as an explicit foreground local web UI.

v1.2 detail endpoints remain available:

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

CLI workflows remain canonical and scriptable.

## Boundary

v1.3.0 does not add:

- write-capable GUI actions
- authentication or authorization
- public network binding by default
- daemon or autostart behavior
- hosted service
- browser automation requirement
- cloud sync
- external model API calls
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof
- security certification

`chronicle ui-smoke` is a read-only diagnostic command.

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
chronicle 1.3.0
```

UI smoke is defined in:

```text
docs/smoke-test-v1.3.md
```

## Legal / governance status

The commercial license and contributor policy drafts remain draft completed / counsel review pending.

v1.3.0 does not finalize legal terms.

## Warning classification

- Release warning: tag creation, GitHub Release publication, and tag-based installer smoke remain explicit release-operator steps.
- Runtime warning: UI smoke automation must not imply daemon, hosted service, browser automation, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: smoke pass is not security certification.
- Semantics warning: smoke pass is not access control, enforcement, or correctness proof.
- Legal warning: commercial/contributor documents remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- CLI as canonical automation surface.
- Static Review Console as read-only derived export.
- Explicit foreground local UI boundary.
- Advisory/diagnostic semantics.

### Transformed

- The local UI smoke process moves from manual endpoint checks toward repeatable diagnostic automation.

### Supplemented

- `chronicle ui-smoke`.
- JSON smoke report.
- Missing-root failure check.
- v1.3 smoke profile.

### Unresolved

- External v1.3.0 tag publication.
- GitHub Release publication.
- Tag-based installer smoke evidence.
- Full browser E2E automation.
- Desktop packaging.
- Visual regression testing.

### Deviation risks

- Mistaking smoke pass for certification.
- Treating UI smoke as access-control enforcement.
- Expanding smoke into hosted-app behavior.
- Adding mutation through convenience pressure.
