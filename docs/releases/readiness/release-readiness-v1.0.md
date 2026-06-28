# Chronicle Stack v1.0.0 Release Readiness

Issues: #165, #167, #168, #169, #170, #171

## Decision

Chronicle Stack v1.0.0 is ready for release execution when the following are complete:

- release criteria and compatibility policy
- README release-status polish
- installer smoke profile
- CLI compatibility audit
- Sayane / CSG-RAG integration boundary note
- release execution plan
- release notes
- version finalization
- changelog update

## Readiness checklist

- [x] v1.0 release criteria documented.
- [x] Compatibility policy documented.
- [x] README release docs list and release status prepared.
- [x] v1.0 smoke profile documented.
- [x] v1.0 CLI compatibility audit documented.
- [x] Sayane / CSG-RAG integration boundary documented.
- [x] v1.0 release execution plan documented.
- [x] v1.0 release notes documented.
- [x] `pyproject.toml` version finalized as `1.0.0`.
- [x] `CHANGELOG.md` includes v1.0.0.

## Release-operator checklist

These checks must be executed from `main` after finalization PR merge and before tag publication:

```bash
git checkout main
git pull --ff-only
python -m pip install -e ".[dev]"
chronicle --version
ruff check src/ tests/
pytest
```

Expected version:

```text
chronicle 1.0.0
```

## Publication checklist

- Create annotated `v1.0.0` tag.
- Publish GitHub Release using `../notes/release-notes-v1.0.0.md`.
- Execute installer smoke from the `v1.0.0` tag.
- Capture installer smoke evidence.
- Close the release execution issue and parent roadmap after evidence is captured.

## Boundary confirmation

v1.0.0 does not introduce:

- server
- daemon
- web runtime
- model API
- GraphRAG engine
- vector DB
- graph DB
- hosted memory service
- enforcement layer

## Warning classification

- Release warning: readiness is not complete until release-operator verification and tag smoke are captured.
- Runtime warning: stable release does not imply hidden services or external runtime dependencies.
- Legal warning: legal/governance drafts remain counsel-review pending.
- Semantics warning: advisory metadata and diagnostic review remain non-enforcing.

## RDE review

### Preserved

- v0.7 / v0.8 / v0.9 technical achievements remain the foundation.
- v1.0 remains local-first and inspectable.
- Release evidence remains required.

### Transformed

- Release-candidate state becomes stable release readiness.

### Supplemented

- Consolidated checklist.
- Publication sequence.
- Boundary confirmation.

### Deviation risks

- Treating checklist completion as tag smoke evidence before the tag exists.
- Treating stable release as legal finalization.
- Treating advisory metadata as enforcement.
