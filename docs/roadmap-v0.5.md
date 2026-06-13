# Chronicle Stack v0.5 Roadmap

Status: Initial planning draft  
Theme: Composition and Integration Layer

## Theme

**Composition and Integration Layer**

v0.4で整えたOperational Readiness Layerの上に、Chronicle recordsをより自然に組み合わせ、外部ツールや将来のCSG-RAG / Sayane / Kotomi連携へ接続しやすくする。

## Background

v0.4では以下を実装しました。

- `chronicle doctor`
- Export Manifest
- Redaction-aware export
- Dashboard navigation/filtering
- Graph export inspection

v0.5では、これらを土台に、Chronicle Stackを単なる記録・診断・exportから、外部システムが扱いやすい構造へ進めます。

## Candidate Scope

### 1. Nested Graph CLI

v0.4では安全性のため、graph inspectionを `chronicle-graph` 補助コマンドとして導入しました。

v0.5では、必要ならprimary CLIに以下を統合します。

```bash
chronicle graph summary
chronicle graph nodes
chronicle graph edges
```

非目的:

- GraphRAG engine
- graph DB
- embeddings
- semantic retrieval

### 2. Export Sidecar Manifest

v0.4ではYAML / graph-json / HTMLにmanifestを埋め込みました。

v0.5候補:

```bash
chronicle export --format markdown --manifest-sidecar manifest.json
chronicle export --format html --manifest-sidecar manifest.json
```

非目的:

- cryptographic signing
- remote attestation

### 3. Redaction Policy Profiles

v0.4では `--redact-sensitive` / `--exclude-sensitive` の明示optionを追加しました。

v0.5候補:

```bash
chronicle export --format yaml --redaction-profile strict
chronicle export --format html --redaction-profile public-review
```

注意:

- Redaction policy remains export disclosure control.
- It is not access control.

### 4. Import / Validate Workflows

Chronicle recordsの外部受け渡しに備えて、import前validateやexport artifactの検査を追加する。

候補:

```bash
chronicle validate
chronicle validate --json
chronicle import --dry-run
```

非目的:

- 自動merge
- trustless validation
- cryptographic proof

### 5. CSG-RAG / Structured RAG Integration Prep

Graph exportをCSG-RAGやGraphRAG風の外部pipelineへ接続しやすくする。

候補:

- graph export schema documentation hardening
- node / edge type registry
- context selection export contract
- query input package format

非目的:

- built-in GraphRAG engine
- vector DB adapter
- LLM query runtime

### 6. Sayane / Review Pipeline Hooks

RDE / UIB / Sayane 連携を前提に、レビュー対象パッケージを出力できるようにする。

候補:

```bash
chronicle review package --format json
chronicle review package --artifact art_...
```

非目的:

- automatic review judgment
- model evaluation engine

## Recommended Implementation Sequence

```text
1. v0.5 issue planning
2. nested graph CLI or command alias
3. export sidecar manifest
4. redaction policy profiles
5. validate / dry-run workflows
6. CSG-RAG integration prep
7. review package export
```

## Non-goals

v0.5 planning should avoid scope creep into:

- GraphRAG engine
- embeddings
- vector database runtime
- graph database runtime
- external LLM API calls
- access control
- authentication
- cloud sync
- automatic LLM injection
- automatic semantic judgment
- commercial license template unless #26 is explicitly reopened

## RDE Review

### Preserved

- JSONL remains primary.
- Derived exports remain derived.
- Redaction is not access control.
- Export Manifest is not cryptographic proof.
- Graph inspection is not GraphRAG.

### Transformed

- Chronicle Stack begins moving from operational readiness toward integration readiness.

### Added

- Initial v0.5 planning frame.
- Candidate scopes for composition and integration.

### Unresolved

- No v0.5 scope is committed yet.
- No v0.5 implementation issue numbers are assigned yet.
- Prioritization remains open.

### Deviation Risks

- Do not overbuild GraphRAG.
- Do not introduce opaque external dependencies.
- Do not make export redaction sound like security enforcement.
- Do not break v0.4 interface contracts.
