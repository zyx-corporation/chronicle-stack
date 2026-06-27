# GraphRAG Integration Boundary

この文書は、Chronicle Stack と将来の GraphRAG / 構造化RAG の接続境界を定義します。

## 位置づけ

GraphRAG は Chronicle Stack の将来の接続先です。v0.3 では GraphRAG そのものを実装しません。

v0.3 Phase 3 の目的は、Chronicle Stack の記録群を graph-ready な node / edge 構造として定義し、deterministic な graph export を提供することです。

## Chronicle Stack 側の契約

- `.chronicle/chronicle.jsonl` が一次記録である
- graph export は JSONL から再構成可能な **派生ビュー** である
- graph export は mutation しない（JSONL を変更しない）
- graph export は deterministic である
- graph export は graph database や vector database に依存しない
- graph export は embedding 生成や LLM API 呼び出しを必要としない
- graph export contract は versioned であり、incremental expectation は Chronicle event ordering を基準に明示される

## GraphRAG 側の期待（将来）

Chronicle Stack がグラフ構造を export することにより、将来の GraphRAG 実装は以下を期待できます。

- ノードとエッジの標準化された入力形式
- event-driven な更新差分の検出
- 文脈、判断、成果物の意味的リンクの活用
- Boundary Rule 評価に基づく文脈選択の前処理活用

## ノード候補

Chronicle Stack の各レコードを node として表現します。

| node_type | source | 意味 |
|-----------|--------|------|
| `chronicle` | ChronicleMetadata | Chronicle 全体 |
| `event` | ChronicleEvent | 個別イベント |
| `context` | Context | 文脈 |
| `artifact` | Artifact | 成果物 |
| `artifact_version` | ArtifactVersion | 成果物バージョン |
| `decision` | Decision | 判断 |
| `rde_diff_record` | RdeDiffRecord | RDE Diff 記録 |
| `boundary_rule` | BoundaryRule | 境界ルール |
| `injection_plan` | InjectionPlan | 文脈注入計画（記録済みのみ） |
| `source_provenance` | SourceProvenance | 出所情報 |
| `tag` | Tag | タグ |

## エッジ候補

| edge_type | from | to | 意味 |
|-----------|------|-----|------|
| `chronicle_has_event` | chronicle | event | Chronicle に属するイベント |
| `event_mentions_context` | event | context | イベントが文脈を参照 |
| `event_creates_artifact` | event | artifact | イベントが成果物を作成 |
| `event_updates_artifact` | event | artifact_version | 成果物バージョン更新 |
| `event_records_decision` | event | decision | 判断記録 |
| `event_records_rde` | event | rde_diff_record | RDE 記録 |
| `event_adds_boundary_rule` | event | boundary_rule | 境界ルール追加 |
| `event_records_injection_plan` | event | injection_plan | 注入計画記録 |
| `artifact_has_version` | artifact | artifact_version | 成果物のバージョン |
| `artifact_version_source_event` | artifact_version | event | バージョン生成イベント |
| `decision_source_event` | decision | event | 判断生成イベント |
| `rde_compares_artifact_versions` | rde_diff_record | artifact_version | 比較対象バージョン |
| `context_has_source` | context | source_provenance | 文脈の出所 |
| `context_has_tag` | context | tag | 文脈のタグ |
| `artifact_has_tag` | artifact | tag | 成果物のタグ |
| `boundary_rule_matches_field` | boundary_rule | context | 境界ルール評価対象 |
| `injection_plan_selects_context` | injection_plan | context | 選択された文脈 |
| `injection_plan_warns_context` | injection_plan | context | 警告付き文脈 |
| `injection_plan_excludes_context` | injection_plan | context | 除外された文脈 |

## 非目的

以下は GraphRAG Integration Boundary の対象外です。

- GraphRAG query engine の実装
- Graph database（Neo4j 等）の統合
- Vector database の統合
- Embedding 生成
- Semantic search
- LLM API 呼び出し
- 自動文脈注入
- Dashboard 可視化
- Graph mutation API

## 将来の拡張候補

- 時系列順序エッジ（event → event）
- 差分更新検出
- public/private/sensitive によるエッジ分類
- GraphRAG query engine（Chronicle Stack 外部）
