# Chronicle Stack v1.4.0 Release Notes

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`

## Summary

Chronicle Stack v1.4.0 is a local installer hardening release over v1.3.0.

The release addresses a concrete release-execution incident: after the `v1.3.0` tag was corrected, an existing installer checkout retained a stale local tag and installed an older package until smoke was rerun from a clean install directory.

v1.4.0 turns that incident into explicit installer behavior and documentation.

## Highlights

### Moved-tag hardening

`scripts/install-local.sh` now resolves the requested branch/tag ref before checkout.

For requested tag refs, the installer force-refreshes the local tag from origin by default:

```text
+refs/tags/$REF:refs/tags/$REF
```

This reduces the chance that an existing install checkout silently uses a stale local tag after an exceptional corrective retag.

### Opt-out for non-forced tag fetch semantics

Operators can disable forced tag refresh:

```bash
CHRONICLE_STACK_ALLOW_MOVED_TAG=0 bash install-local.sh
```

This preserves ordinary non-forced tag fetch semantics where desired.

### Reinstall robustness

The installer now uses:

```text
pip install --force-reinstall
```

This reduces stale package installs when reinstalling from an existing checkout.

### Checkout evidence

The installer logs the checked-out commit after checkout, making release smoke evidence easier to verify.

## Compatibility

The installer remains an inspect-first local CLI installer.

It still installs local commands such as:

```text
chronicle
chronicle-context
chronicle-export
chronicle-package
chronicle-graph
```

CLI workflows remain canonical and scriptable.

## Boundary

v1.4.0 does not add:

- daemon or service installation
- hosted UI
- HTTP runtime
- cloud sync
- external model API calls
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof
- security certification

Moving release tags remains exceptional and should be evidence-recorded.

## Verification

Repository-side verification expected before release:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected version:

```text
chronicle 1.4.0
```

Installer smoke is defined in:

```text
../smoke/smoke-test-v1.4.md
```

## Legal / governance status

The commercial license and contributor policy drafts remain draft completed / counsel review pending.

v1.4.0 does not finalize legal terms.

## Warning classification

- Release warning: tag creation, GitHub Release publication, and tag-based installer smoke remain explicit release-operator steps.
- Installer warning: moved release tags remain exceptional and evidence-recorded.
- Runtime warning: installer hardening must not imply daemon, hosted service, model API, GraphRAG runtime, vector DB, or graph DB.
- Security warning: installer smoke is not security certification.
- Semantics warning: installer smoke is not correctness proof.
- Legal warning: commercial/contributor documents remain draft completed / counsel review pending.

## RDE review

### Preserved

- Local-first context sovereignty foundation.
- Inspect-first installer semantics.
- CLI as canonical automation surface.
- No-daemon/no-service/no-external-runtime boundary.

### Transformed

- A v1.3 release execution incident becomes installer hardening and release smoke guidance.

### Supplemented

- Forced requested tag refresh by default.
- Opt-out environment variable for non-forced tag fetch semantics.
- Checkout commit logging.
- v1.4 installer smoke profile.

### Unresolved

- External v1.4.0 tag publication.
- GitHub Release publication.
- Tag-based installer smoke evidence.
- Longer-term immutable release tag policy.

### Deviation risks

- Normalizing release tag movement.
- Treating installer smoke as security certification.
- Treating installer smoke as correctness proof.
- Making installer behavior too opaque or magical.
