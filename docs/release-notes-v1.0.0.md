# Chronicle Stack v1.0.0 Release Notes

## Summary

Chronicle Stack v1.0.0 is the stable local-first context sovereignty foundation release.

It consolidates the v0.7 operational hardening workflows, v0.8 package review workflow, v0.9 release-candidate hardening, and v1.0 compatibility/release governance into a stable release boundary.

## Highlights

- Stable release criteria and compatibility policy.
- README release-status and documentation polish.
- v1.0 installer smoke profile.
- v1.0 CLI compatibility audit.
- Sayane / CSG-RAG integration boundary note.
- v1.0 release execution plan.
- Project version finalized as `1.0.0`.

## Stable CLI surface

The following entry points are treated as v1.0 stable command surfaces:

- `chronicle`
- `chronicle-context`
- `chronicle-export`
- `chronicle-package`
- `chronicle-graph`
- `chronicle-audit`
- `chronicle-lifecycle`

## Boundary

Chronicle Stack v1.0.0 remains local-first.

It does not introduce:

- server
- daemon
- web runtime
- model API
- GraphRAG engine
- vector DB
- graph DB
- hosted memory service
- authorization enforcement layer

## Advisory and diagnostic semantics

- Classification metadata is advisory metadata, not access control.
- Audit events are traceability metadata, not enforcement.
- Lifecycle markers are advisory metadata and do not mutate primary records by themselves.
- Package review is diagnostic and is not correctness proof.
- Graph-ready export is a local derived export surface, not a GraphRAG runtime.

## Legal and governance status

The following remain draft completed / counsel review pending:

- `Commercial-SaaS-License.md`
- `docs/contributor-license-policy.md`

The public repository text is not legal advice and is not a transaction-specific final contract package.

## Verification

Release-operator verification should include:

```bash
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version:

```text
chronicle 1.0.0
```

Final publication requires installer smoke from the `v1.0.0` tag as described in `docs/smoke-test-v1.0.md` and `docs/release-execution-v1.0.0.md`.

## Warning classification

- Compatibility warning: v1.0.0 stabilizes documented surfaces, not private internals.
- Runtime warning: v1.0.0 does not install or require a daemon, server, model API, GraphRAG engine, vector DB, or graph DB.
- Semantics warning: advisory and diagnostic workflows must not be described as enforcement or proof.
- Legal warning: commercial and contributor policy drafts remain counsel-review pending.
- Evidence warning: release publication should be paired with tag-based installer smoke evidence.

## RDE review

### Preserved

- Chronicle Stack remains a local-first context sovereignty foundation.
- v0.7 / v0.8 / v0.9 surfaces remain the base.
- No-daemon and no-external-runtime boundaries remain explicit.

### Transformed

- Release-candidate hardening becomes a stable compatibility-aware v1.0 boundary.

### Supplemented

- Compatibility policy.
- Smoke profile.
- Integration boundary.
- Release execution checklist.

### Unresolved

- Final legal review and transaction-specific commercial package.
- Future Sayane / CSG-RAG adapter implementation.
- Future post-v1.0 feature roadmap.

### Deviation risks

- Overstating v1.0.0 as complete enforcement or correctness infrastructure.
- Collapsing downstream integration responsibilities into Chronicle Stack core.
- Treating release publication as legal finalization.
