# Chronicle Stack v0.4 Roadmap

## Theme

**Operational Readiness Layer**

Chronicle Stack を「記録できるツール」から「継続運用できるローカル基盤」へ進める。

## Background

v0.3 では以下を確立しました。

- Interface Contracts（`docs/interface-contracts.md`）
- Contract Tests（JSONL、EventType payload、model compat、CLI JSON、rebuild、export）
- 明示的 Injection Plan 永続化（`injection_plan_recorded`、`--record`）
- Graph-ready export（`graph-json`、node/edge 候補定義）
- Static HTML dashboard export（`chronicle export --format html`）
- CLI UX（`--version`、help text、error messages）

v0.4 では、これらの機能を運用レベルで使いやすくすることを目指します。

## Scope

### #45 v0.4: Add Chronicle Health Check Command

local Chronicle project の整合性を診断する `chronicle doctor` コマンド。

- JSONL parse check
- metadata 存在確認
- index rebuild 可否
- artifact file 存在確認
- 記録済み InjectionPlan → Context 参照チェック
- graph export 生成可否
- HTML export 生成可否

非目的: 自動修復、破壊的変更、semantic correctness validation。

### #46 v0.4: Add Export Manifest and Provenance Metadata

export 成果物に生成元情報を付与する。

- `generated_at`、`chronicle_id`、tool version、event count、export format、export options
- 対応形式: YAML / graph-json / HTML（Markdown は sidecar 検討）

非目的: 暗号署名、tamper-proof、リモート検証。

### #47 v0.4: Add Redaction-aware Export Options

visibility hint に基づく明示的な redaction/exclusion を export 時に選択可能にする。

- `--redact-sensitive` / `--exclude-sensitive`（命名は実装時確定）
- デフォルト動作は不変（visibility hint は表示）
- 対応形式: YAML、HTML（graph-json は慎重に検討）

非目的: access control、認証、暗号化、自動分類。

### #48 v0.4: Add Dashboard Filtering and Local Navigation

static HTML dashboard を大規模 Chronicle でも見やすくする。

- anchor navigation / table of contents
- section links（Contexts、Artifacts、Decisions、RDE、Boundary Rules、Injection Plans、Graph Overview）
- 最小限の inline JS filtering（外部依存なし）
- 単一ファイルのまま

非目的: web server、editing UI、認証、frontend framework。

### #49 v0.4: Add Graph Export Inspection Commands

graph-json 構造を CLI から確認しやすくする。

- `chronicle graph summary`
- `chronicle graph nodes [--type <type>]`
- `chronicle graph edges [--type <edge_type>]`
- human-readable + `--json` 出力

非目的: GraphRAG engine、embedding、graph DB、semantic retrieval。

## Recommended Implementation Sequence

```
1. #45 Doctor → 運用診断を最初に確保
2. #46 Export Manifest → export 追跡性を追加
3. #47 Redaction-aware Export → 明示的な開示制御
4. #48 Dashboard Navigation → manifest/redaction の知見を反映
5. #49 Graph Inspection → graph-json の運用性を高める最終段階
```

## Non-goals

v0.4 では以下は対象外とします。

- GraphRAG query engine
- embeddings
- vector database integration
- graph database integration
- external LLM API calls
- automatic LLM injection
- live dashboard server
- dashboard editing UI
- authentication
- cloud sync
- access control
- automatic redaction
- cryptographic signing
- commercial license template（#26 は保留）

特に注意:

- **redaction-aware export は access control ではない**
- **export manifest は cryptographic proof ではない**
- **graph inspection は GraphRAG engine ではない**
- **dashboard filtering は live dashboard ではない**

## Release Readiness Criteria

v0.4 リリース前に以下を満たすこと。

- ruff pass
- pytest pass（全 contract tests 維持）
- v0.4 smoke test 文書が存在する
- `chronicle doctor` が healthy Chronicle で成功する
- `chronicle doctor` が既知の unhealthy 状態を明確に報告する
- export manifest が指定形式で出力される
- redaction-aware export は明示的 opt-in
- デフォルト export 動作は不変
- HTML dashboard は static read-only を維持
- graph inspection は record を変更しない
- JSONL primary contract は不変
- interface contract tests は全 pass

## RDE Review

### Preserved

- JSONL remains primary
- Derived views remain derived
- Interface contracts remain in force
- No GraphRAG engine
- No live dashboard

### Transformed

- Chronicle Stack becomes more operationally reliable

### Added

- v0.4 roadmap and release criteria

### Deviation Risks

- Avoid scope creep into GraphRAG implementation
- Avoid turning dashboard into a web application
- Avoid treating redaction-aware export as access control
