# GraphRAG Integration Boundary

この文書は、Chronicle Stack の deterministic graph export、任意のローカル
GraphRAG workspace、および外部 query runtime の責務境界を定義します。

## 位置づけ

v0.3 では GraphRAG そのものを実装せず、graph-ready な node / edge 契約と
deterministic graph export だけを提供していました。この export 契約は現在も、
外部 runtime と接続するための依存なしの基準面です。

v2.3 以降は、明示的に起動する単一利用者向けの
`chronicle ui --workspace` と `chronicle runtime ask` に限り、OpenAI API と
再構築可能なローカル SQLite projection を利用できます。これは hosted query
service や外部repoの汎用runtimeをChronicle coreへ取り込む決定ではありません。

## Chronicle Stack 側の契約

- `.chronicle/chronicle.jsonl` が一次記録である
- graph export は JSONL から再構成可能な **派生ビュー** である
- graph export は mutation しない（JSONL を変更しない）
- graph export は deterministic である
- graph export は graph database や vector database に依存しない
- graph export は embedding 生成や LLM API 呼び出しを必要としない
- graph export contract は versioned であり、incremental expectation は Chronicle event ordering を基準に明示される

## ローカル workspace の追加契約

- 起動は loopback-only、foreground、明示操作に限定する
- 通常の `chronicle ui` は read-only のまま維持する
- `.chronicle/runtime/vector.sqlite3` と `graph.sqlite3` は削除・再構築可能な派生データとする
- rebuild と query のときだけ外部APIを呼び出す
- 回答は source record ID を伴い、常に review-required とする
- Chronicle JSONL を外部回答やSQLite projectionから自動更新しない
- hosted serving、multi-user authorization、継続同期は扱わない

詳細は [ADR-0097](adr/0097-local-graphrag-workspace.md) を参照してください。

## 外部 GraphRAG 側の期待

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

以下はローカル workspaceを追加した後もChronicle coreの対象外です。

- hosted / multi-user GraphRAG query service
- Neo4j 等の外部 graph database の統合
- managed vector database の統合
- daemon、autostart、継続的なembedding更新
- 自動文脈注入
- Graph mutation API
- Chronicle primary record の自動書換え

## 将来の拡張候補

- 時系列順序エッジ（event → event）
- 差分更新検出
- public/private/sensitive によるエッジ分類
- production / hosted GraphRAG query engine（Chronicle Stack 外部）
