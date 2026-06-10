# ADR-001: T-RDE, TDD, and Design-Pattern Principles

## Status

Accepted

## Date

2026-06-09

## Related documents

- [Chronicle Stack v0.1 基本仕様書](../specs/chronicle-stack-basic-spec-v0.1.md) — §3, §19, §23, §27, §28
- [Chronicle Event Model 仕様書](../specs/chronicle-event-model-spec-v0.1.md)
- [Artifact Model 仕様書](../specs/artifact-model-spec-v0.1.md)
- [Decision Model 仕様書](../specs/decision-model-spec-v0.1.md)
- [RDE Diff Record 仕様書](../specs/rde-diff-record-spec-v0.1.md)
- [Roadmap Linkage Document](../specs/roadmap-linkage-v0.1.md)
- [Testing Strategy](../testing-strategy.md)

## Context

Chronicle Stack は、人間とAIの共同思考において発生する文脈、入力、生成物、判断、修正、差分、意味変化を記録し、後から再構成・監査・再利用できるようにするための基盤である（基本仕様書 §2）。

Chronicle Stack はただのロギングツールではない。その目的は、ある成果物がどの文脈から生じ、どの指示によって変化し、どの判断によって採用・棄却・保留されたかを、時間軸に沿って追跡可能にすることである。

Chronicle Core v0.1 は、その最小中核として Chronicle Event、Context、Artifact、ArtifactVersion、Decision、RDE Diff Record という中核レコードを導入する。これらは v0.2 Context Sovereignty Layer、v0.3 RDE Integration、v0.4 CSG-RAG、v0.5 Human Review Decision Model、v0.6 Sayane Integration、v0.7 Dashboard、v0.8 Research Observatory という後続段階すべての基礎となる（基本仕様書 §23、Roadmap Linkage Document）。

Chronicle Stack が人間とAIの協働履歴を記録するという性質上、実装上の省略が隠れた意味的主張になりやすい。たとえば、イベント参照の欠落によって Artifact Version が実際の判断経路から切り離されているように見えること、RDE レコードの接続が弱いために意味変化監査が完全に見えても再構成できないこと、エクスポート形式が実際のレコードが持つよりも強いレビュー状態を暗示してしまうことが、この種のリスクの典型例である。

基本仕様書 §3 が指摘する五つの問題（生成過程の消失、判断理由の再利用不能、AIと人間の採用境界の曖昧化、意図保存の検証困難、文脈がAI最適化に吸収される）は、これらの設計上の欠如から生じる。

Therefore, Chronicle Stack adopts three engineering principles from the beginning:

1. T-RDE: RDE指向テスト（RDE-oriented testing）
2. TDD: テスト駆動開発（Test-Driven Development）
3. 移植可能性・交換可能性・監査可能性を指針とした明示的なデザインパターン使用

## Decision

T-RDE、TDD、デザインパターン規律を第一級のアーキテクチャ原則として扱う。

本 ADR が確立する基準規則：

> すべての重要な機能は、振る舞いレベルと意味再構成レベルの両方でテスト可能でなければならない。

Chronicle Stack において、ある機能はファイルを書き込んだり、CLI出力を生成したり、ハッピーパスのテストを通過したりするだけでは完了したとは見なされない。既知の制約のもとで、文脈・イベント・成果物・バージョン・判断・RDE レコード間の関係を保持するか、または明示的に変換しなければならない。

## T-RDE principle

T-RDE は RDE 指向テストを意味する。

RDE（Resonant Deviation Evaluator）は、変換ステップをまたいで意味がどのように変化するかを検査する方法である。

Chronicle Stack において T-RDE は、あるプロセスがレコード、成果物、または解釈を受容可能・可視的・再構成可能な形で変化させているかどうかをテストするために使用する。

典型的な対象：

- イベント記録（event recording）
- 文脈登録（context registration）
- Artifact 作成・更新・バージョン化
- Decision 記録
- RDE Diff Record 作成
- JSONL 永続化
- index 再生成（`chronicle index rebuild`）
- 検索・エクスポート
- CLI コマンド振る舞い
- スキーマ変換
- 将来の Graph 投影（v0.4+）
- 将来の Dashboard ラベル（v0.7+）
- 将来の CSG-RAG 検索（v0.4+）

T-RDE テストが問うべき問い：

1. 何の意味が保存されたか？
2. 何の意味が変換されたか？
3. 何の意味が補完されたか？
4. 何の意味が失われたか？
5. どの根拠のない主張が導入されてしまったか？
6. ユーザーに対してどの不確実性または不完全性を可視的に残さなければならないか？

Chronicle Stack では、これらの問いを自然言語の成果物だけでなく構造的レコードにも適用しなければならない。壊れた参照は技術的欠陥ではなく意味的欠陥である。

## TDD principle

すべてのコアロジックは、現実的な範囲でテストファーストで開発する。

TDD を必須とする領域：

- Chronicle Event モデル検証
- Artifact・ArtifactVersion 永続化
- Decision 記録
- RDE Diff Record 記録
- JSONL 追記・読み取り振る舞い
- 壊れた JSONL 行の処理（`skip_corrupt`）
- index 再生成振る舞い
- 検索振る舞い
- エクスポート振る舞い
- CLI コントラクト
- エラー処理
- データ境界ロジック
- 将来の Context スコープ・可視性ロジック（v0.2+）

TDD を強く推奨する領域：

- Markdown・YAML レンダリング
- レポートフォーマット
- 将来の Dashboard 状態遷移（v0.7+）
- 将来の Graph 投影（v0.4+）
- 将来の CSG-RAG 検索振る舞い（v0.4+）
- 将来の Sayane インポート・エクスポート（v0.6+）

使い捨て実験には TDD を必須としないが、プロトタイプコードはテストなしに黙って本番パスに昇格させてはならない。

## Test categories

プロジェクトは少なくとも以下のテストカテゴリを区別する。

### Unit tests

決定論的関数とモデルに使用する。

例：

- ID prefix 生成（`ids.py`）
- enum 検証
- スキーマ検証
- パス構築（`store/paths.py`）
- JSONL 行パース
- Markdown レポートフォーマット
- エラーオブジェクトシリアライズ

### Service tests

ドメインサービスの振る舞いに使用する。

例：

- Chronicle 初期化（`chronicle_service.py`）
- イベント記録
- 文脈追加（`context_service.py`）
- Artifact 作成・更新・履歴再構成（`artifact_service.py`）
- Decision 記録（`decision_service.py`）
- RDE 記録（`rde_service.py`）
- index 再生成（`search_service.py`）

### CLI integration tests

コマンドレベルの振る舞いに使用する。

例：

- `chronicle init`
- `chronicle record`
- `chronicle add-context`
- `chronicle artifact create`
- `chronicle artifact update`
- `chronicle artifact history`
- `chronicle decision record`
- `chronicle rde record`
- `chronicle search`
- `chronicle export`
- `chronicle index rebuild`

### Contract tests

リファクタリングをまたいで安定でなければならない境界に使用する。

例：

- `chronicle.jsonl` イベントフォーマット（`schema_version: "chronicle-core-0.1"`）
- `metadata.yaml` フォーマット
- `artifact_index.json` フォーマット
- `context_index.json` フォーマット
- `decision_index.json` フォーマット
- RDE レポートフォーマット（`reports/rde/<rde_record_id>.md`）
- CLI `--json` 出力フォーマット

### Golden tests

安定した代表的な例に使用する。

例：

- 1 つの Artifact・2 バージョン・1 Decision・1 RDE レコードを持つ既知の Chronicle
- 壊れた JSONL 行を含む既知のフィクスチャ
- 既知の Markdown エクスポート
- 既知の YAML エクスポート
- 既知の RDE レポート

### Regression tests

バグまたは意味的ドリフトが発見されたときに使用する。

すべての重要な修正は、リグレッションテストを作成または更新しなければならない。

例：

- ArtifactVersion は index 再生成後も `source_event_id` を失ってはならない
- Decision は index 再生成後も `event_id` を失ってはならない
- RDE レコードは対象の ArtifactVersion に対して発見可能な状態でリンクされ続けなければならない
- Artifact 更新は空のボディでコンテンツを誤って上書きしてはならない

### T-RDE tests

意味保存と意味変化の検査に使用する。

例：

- ArtifactVersion は、それを生成したイベントへのリンクを維持しなければならない
- Decision は、それを記録したイベントへのリンクを維持しなければならない
- 棄却された Artifact が採用済みとしてエクスポートされてはならない
- ドラフト状態の Artifact がレビュー済みとしてレンダリングされてはならない
- RDE レコードは、6 項目がすべて空の場合に意味変化フィールドがレビューされたことを暗示してはならない
- 再生成された index は、JSONL 一次記録が支持しない関係を創作してはならない
- 検索結果は、格納されたイベントに存在しない来歴を暗示してはならない

## Development phase gate

すべての開発フェーズは、実装開始前にプランニングゲートを通過しなければならない。

フェーズは main ブランチへの直接コーディングとして開始してはならない。

非自明な開発フェーズを開始する前に、以下の成果物が存在しなければならない：

1. 詳細なフェーズ記述
2. 作業を記述した 1 つ以上の Issue
3. 現在の main ブランチから作成された実装ブランチ
4. 初期テストケースまたはテストケース仕様
5. フェーズが意味・再構成・レビュー状態・来歴・エクスポート解釈に影響する場合の T-RDE 受け入れ基準
6. フェーズの明示的な前提条件と非目標

これは MVP フェーズを含むすべてのフェーズに適用される。

使い捨て実験は別途行ってよいが、Issue・ブランチ・テストを持つフェーズに変換されない限り本番パスへマージしてはならない。

## Issue requirement

各開発 Issue には以下を含めること：

- 目的
- スコープ
- 非目標
- 期待される振る舞い
- 期待される意味境界
- テスト計画
- T-RDE チェックリスト（該当する場合）
- デザインパターンへの含意（該当する場合）
- 完了基準

Issue が格納された関係、レビュー状態、来歴、エクスポートされたレポート、またはユーザー可視の解釈に影響する場合、主張を過大評価しないことを明示しなければならない。

## Branch requirement

各フェーズまたは非自明な Issue は専用ブランチで開発する。

推奨ブランチ命名：

- `phase/<phase-name>`
- `feature/<short-feature-name>`
- `fix/<short-fix-name>`
- `docs/<short-doc-name>`
- `experiment/<short-experiment-name>`

main ブランチは受け入れ済みのプロジェクト状態を表す。

main への直接コミットは、リポジトリ初期化・緊急のドキュメント修正・明示的に受け入れられた管理上の更新に限定する。

## Test-case requirement before implementation

実装開始前に、Issue またはブランチには以下の少なくとも 1 つが含まれなければならない：

- 具体的な失敗テスト
- 実行可能なテストスタブ
- フィクスチャ定義
- ゴールデン例
- コントラクト例
- T-RDE シナリオ記述

実行可能なテストをまだ定義できないフェーズは、コーディング前にテスト可能なシナリオを散文で定義しなければならない。

これらのシナリオは、フィーチャーが完了と見なされる前に実行可能なテストに変換されなければならない。

## Phase completion rule

フェーズは以下のすべてを満たした時点のみ完了とする：

1. 実装が Issue スコープを満たしている
2. 計画されたすべてのテストが通過している
3. 発見されたバグに対してリグレッションテストが追加されている
4. T-RDE 受け入れ基準がレビューされている（該当する場合）
5. ドキュメントが更新されている
6. 残存する不確実性が記録されている
7. ブランチが合意されたレビューパスを通じてマージ準備済みまたはマージ済みである

## Design-pattern usage principle

デザインパターンは、明確さ・交換可能性・監査可能性を向上させる場合にのみ使用する。

本プロジェクトは装飾的なパターン使用を排除する。

パターンはアーキテクチャ的な装飾ではない。意味・永続化・実装の境界を明示的に保つためのツールである。

## Recommended patterns

### Repository pattern

永続化と外部境界アクセスに使用する。

例：

- `JsonlStore`
- `ArtifactStore`
- `IndexStore`
- 将来の `ContextRepository`（v0.2+）
- 将来の `GraphRepository`（v0.4+）

目的：

- ストレージ振る舞いの分離
- コントラクトテストの有効化
- JSONL・SQLite・Graph ストレージの交換を可能にする
- 永続化の詳細がドメインロジックに漏れるのを防ぐ

### Adapter pattern

外部または取り込まれたレコードを内部正規モデルへ変換するために使用する。

例：

- `MarkdownArtifactAdapter`
- `ExternalConversationAdapter`
- `GitHubIssueAdapter`
- `SayaneContextAdapter`（v0.6+）

目的：

- 外部スキーマが Chronicle モデルに漏れるのを防ぐ
- 来歴保存変換を明示的にする
- 将来のインポート・エクスポートワークフローをサポートする

### Strategy pattern

交換可能な意味変化・差分・エクスポート・検索ロジックに使用する。

例：

- `RdeEvaluationStrategy`
- `ArtifactDiffStrategy`
- `SearchStrategy`
- `ExportStrategy`
- 将来の `ContextSelectionStrategy`（v0.2+）

目的：

- アルゴリズム交換を可能にする
- 意味変化ロジックの A/B 比較をサポートする
- 前提条件をテスト可能に保つ

### Pipeline pattern

多段変換に使用する。

例：

- ingest → normalize → record → version → evaluate → index → export

目的：

- 変換ステージを明示的にする
- 障害モードを分離する
- 部分的な再計算をサポートする
- 意味ドリフトの特定を容易にする

### Specification pattern

バリデーション・フィルタリング・ポリシー的な条件に使用する。

例：

- `ArtifactExistsSpec`
- `VersionExistsSpec`
- `DecisionTargetExistsSpec`
- `NonEmptyArtifactContentSpec`
- `ExportVisibilitySpec`
- 将来の `ContextBoundarySpec`（v0.2+）

目的：

- 判定基準を監査可能にする
- CLI ハンドラ内部に隠れたビジネスロジックを避ける
- 将来の Context スコープ・可視性ルールを準備する

### Observer / Event pattern

監査・可観測性イベントに使用する。

例：

- `ChronicleCreated`
- `ContextAdded`
- `ArtifactCreated`
- `ArtifactVersioned`
- `DecisionRecorded`
- `RdeDiffRecorded`

目的：

- 監査ログのサポート
- 将来のイベント駆動アーキテクチャのサポート
- 変換を追跡可能にする

### Factory pattern

交換可能なストア・エクスポーター・ストラテジー・将来の検索コンポーネントの構築に限定的に使用する。

目的：

- 交換可能コンポーネントの生成を一元化する
- ハードコードされた依存関係を避ける
- テストをシンプルに保つ

## Patterns to avoid by default

### Singleton

不変の設定または明示的に制御されたインフラストラクチャハンドルを除き、使用を避ける。

理由：

- テストを困難にする
- 依存境界を隠す
- グローバル状態の漏れを引き起こしうる

### Service Locator

使用を避ける。

理由：

- 依存関係を隠す
- テスタビリティを弱める
- アーキテクチャを不明瞭にする

### Over-layered architecture

時期尚早な抽象化を避ける。

理由：

- Chronicle Core v0.1 は MVP である（基本仕様書 §28 逸脱リスク）
- 過度なレイヤーは意味変換を明確化するのではなく隠しうる
- v0.1 は JSONL・成果物・決定・RDE レコードを理解可能な状態に保つべきである

## Record design rule

格納されたレコードは、基礎となるデータが支持するよりも強いレビュー・来歴・再構成状態を暗示してはならない。

以下は別個に保たれなければならない：

- イベント発生（event occurrence）
- 成果物コンテンツ（artifact content）
- 成果物バージョン（artifact version）
- 判断状態（decision status）
- RDE 評価（RDE evaluation）
- レビュー状態（review status）
- 来歴（provenance）
- 確信度（confidence）
- 信頼度（trust）

特に：

- イベントの存在は人間の承認ではない
- Artifact 作成は採用ではない
- Artifact 更新はレビュー完了ではない
- RDE レコードの存在は完全な意味検証ではない
- confidence は真実ではない
- 来歴は正確さではない
- Delta-M は価値ではない

これらの次元を単一の修飾されない status に折り畳むコード・CLI 出力・エクスポートドキュメント・将来の Dashboard ビューは、本 ADR に違反する。

## Provenance and reconstructability rule

すべての重要な派生ビューは、一次レコードによって説明可能でなければならない。

派生ビューは以下を保持するか、リンク可能でなければならない：

- ソース Chronicle Events
- Artifact バージョン
- Decisions
- RDE レコード
- 入力タイムスタンプ
- 生成またはキャルキュレーションのバージョン
- 既知の制限

Chronicle Core v0.1 において JSONL イベントログは一次記録である。

インデックスは派生データである。ルックアップ振る舞いを強化してよいが、イベントまたは明示的な派生ルールに遡れない関係を黙って創作してはならない（基本仕様書 §8、Roadmap Linkage §横断的な防衛線）。

再構成できない関係は、暗示されるのではなく、missing・unresolved・experimental としてマークされなければならない。

## CLI and report rule

CLI とエクスポートレポートは、格納されたレコードが支持するよりも強い主張をしてはならない。

誤った表現の例：

- `artifact_created` イベントのみが存在するときに "Artifact accepted" と表示する
- 6 つの RDE フィールドがすべて空のときに "RDE complete" と表示する
- `review_status` が absent または `unreviewed` のときに "Reviewed" と表示する
- ソースメタデータが欠落しているときに "Source verified" と表示する

推奨される表現：

- "Artifact created, no decision recorded."
- "RDE record exists; no preserved/transformed/supplemented fields provided."
- "Review status: unreviewed."
- "Source reference unavailable."

## Development workflow

すべての非自明なフィーチャーについて：

1. 期待される振る舞いを定義する
2. 期待される意味境界を定義する
3. Issue を作成またはリンクする
4. 実装ブランチを作成する
5. 初期テストまたはテストケース仕様を定義する
6. 現実的な範囲でテストを書く
7. 最小の動作するバージョンを実装する
8. 発見されたバグに対してリグレッションテストを追加する
9. フィーチャーが再構成・レビュー・来歴・エクスポート・解釈に影響する場合、前提条件を記録する
10. 完了前に T-RDE 受け入れ基準をレビューする

## Immediate application to Chronicle Core v0.1

以下の領域は、本 ADR の即時適用対象である（Roadmap Linkage §5 残作業との対応を付記する）。

1. **ArtifactVersion は `source_event_id` を一次レコードまたは明確に再構成可能な形で永続化しなければならない。**（Roadmap Linkage P0: source_event_id / event_id の事前生成・整合性修正）
2. **Decision は `event_id` を一次レコードまたは明確に再構成可能な形で永続化しなければならない。**（同 P0）
3. **RDE Diff Record は対象 ArtifactVersion に対して発見可能な状態でリンクされ続けなければならない。**（Roadmap Linkage P1: RDE の index 化と Version リンク）
4. **Artifact 更新は空のボディでコンテンツを誤って上書きしてはならない。**
5. **CLI 振る舞いは統合テストでカバーされなければならない。**（Roadmap Linkage P2: CLI 統合テスト・E2E デモテスト）
6. **エクスポートされた Markdown と YAML はレビューまたは RDE 完了を過大表現してはならない。**
7. **`decision record` CLI は `alternatives` と `notes` を受け付けなければならない。**（Roadmap Linkage P1: decision record CLI の alternatives / notes 対応）

これらの要件は追加のプロダクトスコープではない。Chronicle Core v0.1 の意味を保持するために必要である。

## Consequences

### Benefits

- Chronicle 履歴が再構成可能であり続ける
- Event・Artifact・Decision・RDE の境界が明示的であり続ける
- 意味的関係のバグがテスト可能になる
- 将来の CSG-RAG（v0.4）がクリーンな一次レコードに依拠できる
- 将来の Dashboard ビュー（v0.7）が主張の過大評価を避けられる
- 将来の Sayane インポート・エクスポート（v0.6）が文脈境界を保持できる
- 開発フェーズが実装開始前にレビュー可能になる

### Costs

- コアロジックのテストとドキュメント作業の前払いコスト
- コアロジックの早期プロトタイピングの遅延
- フィクスチャとゴールデン例の維持が必要
- 一次レコードと派生インデックスの区別を管理する必要がある
- 早期開発段階でも Issue とブランチの管理が必要になる

## Non-goals

本 ADR は GraphRAG の最終的な振る舞いを定義しない。

本 ADR は Chronicle Core v0.1 の JSONL 一次記録を超えた特定のデータベースを義務付けない。

本 ADR は Dashboard UI の振る舞いを定義しない。

本 ADR はすべての実験的スケッチに本番グレードの TDD を要求しない。

ただし、プロトタイプロジックが永続化レコード・エクスポートドキュメント・レビュー状態・来歴・ユーザー可視の解釈に影響を及ぼした時点で、本 ADR の管理下に置かれなければならない。

## Related concepts

- Chronicle Stack / Chronicle Core v0.1
- Context Sovereignty（v0.2）
- CSG-RAG（v0.4）
- Human Review Decision Model（v0.5）
- Sayane Integration（v0.6）
- RDE Diff Record / Resonant Deviation Evaluator
- Delta-M
- Test-Driven Development
- Provenance-aware systems
- Auditability / Reconstructability
