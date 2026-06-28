# Chronicle Stack v1.7.0 Release Notes

Related: `../../adr/0018-local-ui-read-only-navigation-boundary.md`, `../../adr/0019-local-ui-review-semantics-parity-boundary.md`, `../../adr/0021-gated-local-ui-mutation-write-path.md`, `../../adr/0023-browser-triggered-review-write-semantics.md`, `../../adr/0024-explicit-configured-provider-execution-boundary.md`, `../../adr/0026-local-reviewer-session-proof-representation.md`

## Summary

Chronicle Stack v1.7.0 is a local AI/runtime/review/package observability release over v1.6.0.

It bundles the Phase D/E/F/G/H repository-side slices into one inspectable local release target: placeholder AI index surfaces, explicit local runtime and retrieval-plan contracts, and Phase H read-only + gated-local-write preparation.

## Highlights

### Local AI index visibility

v1.7.0 includes:

- `chronicle ai-index status`
- `chronicle ai-index vector add`
- `chronicle ai-index vector search`
- `chronicle ai-index graph add-node`
- `chronicle ai-index graph add-edge`
- `chronicle ai-index graph neighbors`
- read-only UI visibility for AI index overview / vector / graph surfaces

These remain placeholder local surfaces over file-backed derived state.

### Explicit local runtime and retrieval-plan surfaces

v1.7.0 includes:

- `chronicle runtime summarize`
- `chronicle runtime invoke`
- `chronicle runtime execute-plan`
- `chronicle runtime retrieve-plan`
- `chronicle runtime invoke-plan`
- read-only visibility for invocation-plan / retrieval-plan / provider-response summaries

These surfaces keep runtime execution explicit, inspectable, and contract-first.

### Phase H auth-readiness and gated local mutation preparation

v1.7.0 adds or consolidates:

- overview/list/detail auth-readiness, identity, and mutation-readiness visibility
- blocked-route preview and CLI fallback guidance
- explicit local reviewer/session/ui-intent contract visibility
- fail-closed local review action contract summaries
- shared helper-driven copy alignment across overview/detail surfaces

The UI remains read-only by default, with local write-path behavior available only behind explicit enablement.

## Boundary

v1.7.0 does not add:

- hosted runtime
- daemon or service installation
- default-on GUI mutation
- authenticated GUI mutation
- authorization enforcement beyond descriptive metadata
- hidden provider execution
- GraphRAG runtime
- vector DB
- graph DB
- correctness proof
- security certification
- legal/governance finalization

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
chronicle 1.7.0
```

## Warning classification

- Release warning: repository-side preparation is not external release publication.
- Mutation warning: gated local write-path preparation does not imply default GUI mutation.
- Auth warning: auth/authz placeholders remain descriptive metadata, not enforcement.
- Runtime warning: explicit local runtime/provider contracts do not imply hidden/background execution.
- Security warning: smoke evidence is not security certification.
- Semantics warning: smoke evidence and advisory UI wording are not correctness proof.
- Legal warning: commercial/contributor documents remain draft completed / counsel review pending.

## RDE review

Preserved: Chronicle JSONL authority, local-first read-only UI boundary, CLI-first mutation semantics, evidence-based release workflow.

Transformed: separate v1.7 phase notes become one release-framed local observability milestone.

Supplemented: release notes for AI index, runtime, retrieval-plan, and gated-local-write preparation in one place.

Unresolved: stronger authenticated mutation, broader provider execution, deeper retrieval-plan composition, and external `v1.7.0` release publication.

Deviation risks: over-signaling provider maturity, confusing preview contracts with approval authority, or treating smoke as certification.
