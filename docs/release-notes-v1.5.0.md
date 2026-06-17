# Chronicle Stack v1.5.0 Release Notes

## Summary

Chronicle Stack v1.5.0 is a release-operator documentation release over v1.4.0.

It turns the manual release execution practices used across v1.3.0 and v1.4.0 into repository documentation so future releases are less dependent on chat memory.

## Highlights

### Release Operator Guide

v1.5.0 adds:

```text
docs/release-operator-guide.md
```

The guide covers:

- local pre-tag verification
- annotated tag creation
- tag/main equivalence checks
- annotated tag dereference with `vX.Y.Z^{}`
- GitHub Release creation
- `Release.tag_name already exists` handling
- clean installer smoke
- existing-checkout reinstall smoke
- moved-tag opt-out smoke
- `ui-smoke` continuity evidence
- release issue evidence comments
- close criteria

### Release status linkage

The v1.4.0 release status page now links to the release operator guide, making the guide easier to discover from a release-status surface.

## Boundary

v1.5.0 does not add:

- release automation
- GitHub Actions release publishing
- package publishing
- daemon or service installation
- hosted UI
- external model API calls
- GraphRAG runtime
- vector DB
- graph DB
- access-control enforcement
- correctness proof
- security certification
- legal/governance finalization

Smoke evidence remains diagnostic.

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
chronicle 1.5.0
```

## Warning classification

- Release warning: this is documentation for manual release execution, not release automation.
- Runtime warning: documentation must not imply daemon, service, hosted UI, or external runtime.
- Security warning: smoke evidence is not security certification.
- Semantics warning: smoke evidence is not correctness proof.
- Legal warning: commercial/contributor documents remain draft completed / counsel review pending.

## RDE review

Preserved: evidence-based release execution, local-first installer smoke, explicit boundary language.

Transformed: repeated release execution behavior becomes reusable repository documentation.

Supplemented: release notes and v1.5 release framing for the release operator guide.

Unresolved: future full release automation, package publishing, immutable tag governance, and legal/governance finalization.

Deviation risks: over-signaling automation, treating smoke as certification, or treating documentation release as runtime behavior.
