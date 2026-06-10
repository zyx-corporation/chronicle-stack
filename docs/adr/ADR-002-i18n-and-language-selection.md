# ADR-002: i18n and Language Selection

## Status

Accepted

## Date

2026-06-09

## Related documents

- [ADR-001: T-RDE, TDD, and Design-Pattern Principles](ADR-001-t-rde-tdd-and-design-patterns.md)
- [Chronicle Stack v0.1 基本仕様書](../specs/chronicle-stack-basic-spec-v0.1.md) — §22, §23
- [Chronicle Event Model 仕様書](../specs/chronicle-event-model-spec-v0.1.md)
- [Artifact Model 仕様書](../specs/artifact-model-spec-v0.1.md)
- [Decision Model 仕様書](../specs/decision-model-spec-v0.1.md)
- [RDE Diff Record 仕様書](../specs/rde-diff-record-spec-v0.1.md)
- [Roadmap Linkage Document](../specs/roadmap-linkage-v0.1.md)
- [CLI リファレンス](../cli-reference.md)
- [Storage Format](../storage-format.md)
- [Testing Strategy](../testing-strategy.md)

## Context

Chronicle Stack は、人間とAIの共同思考において複数の言語・文化的文脈をまたいで文脈・生成物・判断・意味変化を記録・再構成するための基盤である。

このプロジェクトは、日本語エッセイ・英語仕様書・多言語成果物・AI生成翻訳・外部会話インポート・将来の Sayane 文脈バンドル（v0.6+）・将来の Dashboard（v0.7+）・将来の CSG-RAG 検索ビュー（v0.4+）での使用が想定される。

Chronicle Stack が単一言語向けに設計されると、後からの多言語対応は高コストになるだけでなく、Chronicle Stack の中核目的である「文脈・判断・成果物履歴・意味変化境界の保存」を歪めるリスクがある。

たとえば、日本語 CLI が英語仕様書を管理し、日本語 RDE レポートを生成し、将来中国語サマリをエクスポートするという複合ワークフローが想定される。これらの言語を単一フィールドに折り畳んではならない。

したがって、Chronicle Core v0.1 が CLI とファイルベースのレポートのみを提供する段階であっても、プロジェクトは最初から多言語対応の設計基盤を持つ。

初期サポートするユーザー向け言語：

- `ja`：日本語
- `en`：English
- `zh-CN`：中国大陸標準中国語（簡体字）

## Decision

i18n サポートを第一級の要件として扱う。

すべてのユーザー向け UI テキスト・CLI メッセージ・エクスポートレポートラベル・警告メッセージ・将来の Dashboard ラベルは、ロケール対応の翻訳メカニズムを通じて解決できるよう設計しなければならない。

将来の UI はランゲージセレクターを提供しなければならない。

初期ランゲージセレクターは以下をサポートしなければならない：

- 日本語（`ja`）
- English（`en`）
- 简体中文（`zh-CN`）

Chronicle Stack は、ビジネスロジック・永続化ロジック・RDE ロジック・文脈境界ロジック・ソースアダプター・ドメインモデルの内部に、日本語・英語・中国語のユーザー向けテキストをハードコードしてはならない。

Chronicle Core v0.1 は内部の開発者向け文字列を英語で保持してよいが、ユーザー向けメッセージは外部化への準備が整った状態にしなければならない。

## Scope

本 ADR が適用される対象：

- CLI ヘルプテキスト
- CLI 成功メッセージ
- CLI エラーメッセージ
- 空状態（empty states）
- 警告メッセージ
- T-RDE 境界メッセージ
- RDE レポートセクションラベル
- Markdown エクスポートラベル
- YAML エクスポートラベル（ユーザー向けものに限る）
- 将来の Dashboard UI（v0.7+）
- 将来の管理コンソール UI
- 将来のランゲージセレクター
- 将来の文脈バンドルインポート・エクスポートビュー（v0.6+）
- 将来の CSG-RAG 検索結果ラベル（v0.4+）
- 将来の来歴・レビュー状態ラベル（v0.5+）
- 将来の Sayane 連携メッセージ（v0.6+）

プロダクト出力の一部として生成されるユーザー可視レポートにも適用される。

## Non-goals

本 ADR は、すべてのドキュメントをすべてのサポート言語に即時翻訳することを要求しない。

本 ADR は、Chronicle Core v0.1 に完全な UI の実装を要求しない。

本 ADR は、v0.1 での多言語意味整合を要求しない。

本 ADR は、v0.1 での繁体字中国語（`zh-TW`）サポートを要求しない。

本 ADR は機械翻訳を要求しない。

本 ADR は、記録前に成果物コンテンツを翻訳することを要求しない。

本 ADR は、すべての内部コード識別子のローカライズを要求しない。

## Locale model

Chronicle Stack は以下を区別しなければならない：

- UI ロケール（ui_locale）
- CLI 出力ロケール（cli_locale）
- ソース言語（source_language）
- 成果物言語（artifact_language）
- ドキュメント言語（document_language）
- レポート生成言語（report_language）
- RDE レビュー言語（rde_review_language）
- ユーザー設定（user_preferred_locale）

これらを単一フィールドに折り畳んではならない。

例：

```yaml
locale_context:
  ui_locale: ja
  cli_locale: ja
  source_language: en
  artifact_language: en
  document_language: en
  report_language: ja
  rde_review_language: ja
  user_preferred_locale: ja
```

日本語 CLI でユーザーが英語仕様書を管理し、日本語 RDE レポートを生成するというユースケースを支持する。

将来の Dashboard（v0.7+）では、中国語 UI で日本語成果物を閲覧しながら英語サマリをエクスポートするユースケースも支持する。

## Initial locale keys

```yaml
supported_user_locales:
  - ja
  - en
  - zh-CN

default_user_locale: ja
fallback_user_locale: en
```

`ja` が初期プロダクトロケールのデフォルトである。

`en` がフォールバックロケールである。

`zh-CN` は中国大陸標準中国語（簡体字）を意味する初期中国語ユーザー向けロケールである。

`ch` という短縮形は非推奨であり、プロダクト向けロケールキーに使用してはならない。既存の永続化された `ch` 設定が存在する場合は、`zh-CN` に移行するか `en` に安全にフォールバックしなければならない。

## Language selector requirement

将来の UI は可視のランゲージセレクターを提供しなければならない。

最低限、セレクターは以下を許可すること：

- 日本語
- English
- 简体中文

選択された言語は、現実的な範囲でセッションをまたいで永続化されること。

許可される永続化メカニズム：

- 認証済みユーザーのプロファイル設定
- ローカルプロジェクト設定
- ローカル設定ファイル
- ブラウザ UI 用の Cookie またはローカルストレージ
- 一時オーバーライド用の URL パラメータ
- CLI オプション `--locale`
- CLI 自動化用の環境変数

UI での推奨優先度：

1. 明示的な URL パラメータ
2. 認証済みユーザー設定
3. Cookie またはローカルストレージ
4. ブラウザ言語
5. デフォルトロケール

CLI での推奨優先度：

1. 明示的な `--locale` オプション
2. 環境変数
3. プロジェクトレベルの Chronicle metadata 設定
4. ユーザーレベルの設定ファイル
5. システムロケール
6. デフォルトロケール

## Translation key rule

ユーザー向けテキストは安定した翻訳キーを通じて参照しなければならない。

例：

```yaml
cli.init.created: Chronicle created
cli.artifact.created: Artifact created
cli.artifact.no_artifacts: No artifacts found
cli.error.not_initialized: Chronicle is not initialized in this directory
rde.section.preserved: Preserved
rde.section.transformed: Transformed
rde.section.deviation_risks: Deviation Risks
export.review_status.unreviewed: Unreviewed
```

翻訳キーは見た目ではなく意味に基づいていなければならない。

推奨：

```text
cli.artifact.no_artifacts
```

非推奨：

```text
gray_empty_text
```

## T-RDE requirement for i18n

翻訳は意味を変えうる。

したがって、T-RDE（ADR-001）は重要な CLI・UI・レポートの翻訳に適用しなければならない。

T-RDE チェックが問うべき問い：

1. 翻訳は、運用・レビュー・来歴・再構成の境界を保存しているか？
2. 翻訳は、弱い主張をより強く聞こえるようにしていないか？
3. 翻訳は、不確実性マーカーを保存しているか？
4. 翻訳は、イベント・成果物・バージョン・判断・レビュー状態・来歴・確信度・RDE 評価の区別を保存しているか？
5. 翻訳は、運用上の成功を意味的な採用に変えていないか？
6. 翻訳は、概念を文化的に狭めていないか？

## Critical wording boundaries

以下の区別はすべてのサポート言語で保持されなければならない：

- event recorded は decision accepted ではない
- artifact created は artifact approved ではない
- artifact updated は artifact reviewed ではない
- decision recorded は decision correct ではない
- RDE record exists は complete meaning validation ではない
- review status は truth ではない
- provenance は correctness ではない
- confidence は truth ではない
- export success は content validation ではない
- index rebuild success は semantic completeness ではない
- CLI success は human acceptance ではない
- Delta-M は value ではない
- context included は context endorsed ではない
- source language は report language ではない
- artifact language は UI locale ではない

これらの区別を折り畳む翻訳は本 ADR に違反する。

## Translation quality policy

機械翻訳はドラフト補助としてのみ使用してよい。

重要なラベル・警告・CLI エラー・RDE 説明・レビュー状態ラベル・来歴ラベル・エクスポートレポート見出しのプロダクト向け翻訳は、受け入れ済みとして扱われる前に、人間または明示的な T-RDE 翻訳レビュープロセスによってレビューされなければならない。

重要翻訳カテゴリ：

- 警告
- 破壊的操作メッセージ
- Artifact 上書きメッセージ
- レビュー状態ラベル
- Decision ラベル
- RDE セクションラベル
- T-RDE 説明
- 来歴境界メッセージ
- 文脈境界メッセージ
- エクスポートサマリ
- CLI エラーメッセージ
- 将来の Dashboard 状態ラベル（v0.7+）

## Chronicle metadata requirements

Chronicle metadata にロケール設定を含めてよいが、ロケールフィールドは明示的でなければならない。

将来の推奨 metadata 形式：

```yaml
locale_context:
  default_user_locale: ja
  fallback_user_locale: en
  cli_locale: ja
  report_language: ja
```

v0.1 では、これはドキュメントのみの仕様として留まってよい。将来のスキーマ変更は後方互換性を保持しなければならない（基本仕様書 §23）。

## Artifact language metadata

成果物言語は UI およびレポート言語から分離して表現するべきである。

将来の推奨 Artifact metadata（Artifact Model 仕様書 §3 の拡張点）：

```yaml
artifact_language: en
source_language: en
report_language: ja
```

これにより Chronicle Stack は、成果物コンテンツの強制翻訳なしに多言語ワークフローを管理できる。

## CLI implementation requirements

Chronicle Core v0.1 は、完全な翻訳が即時実装されない場合でも、i18n 対応 CLI アーキテクチャを導入するべきである。

最初の実装に含めるべき、または準備すべき構造：

- ロケールレジストリ（locale registry）
- 翻訳辞書またはメッセージカタログ
- デフォルトロケール処理
- フォールバック処理
- CLI ロケール解決
- ロケール振る舞いのテストケース仕様

CLI はユーザー向け文字列をドメインサービス内部に埋め込むことを避けるべきである。

ドメインサービスは構造化データまたはエラーオブジェクトを返してよい（`errors.py`）。CLI レンダリング（`cli.py`）がロケール固有のメッセージに責任を持つ。

推奨ファイル構成：

```text
src/chronicle/i18n/
  locales/
    ja.yaml
    en.yaml
    zh-CN.yaml
  locale_registry.py
  translate.py
  resolver.py
```

## Future UI implementation requirements

Dashboard または管理 UI が導入される場合（v0.7+）、以下を含まなければならない：

- ランゲージセレクターコンポーネント
- ロケールレジストリ
- 翻訳ファイルまたは辞書
- デフォルトロケール処理
- フォールバック処理
- 言語切り替えのテストまたはテストケース仕様

管理 UI は最初の非プロトタイプリリースからランゲージセレクターをサポートしなければならない。

将来の UI 向け推奨ファイル構成：

```text
src/ui/i18n/
  locales/
    ja.json
    en.json
    zh-CN.json
  locale-registry.ts
  translate.ts
  components/
    language-selector.tsx
```

## Testing requirements

最低限、以下のテストまたはテストシナリオを定義しなければならない（ADR-001 TDD 原則および Testing Strategy との整合）：

- デフォルトロケール解決
- フォールバックロケール振る舞い
- サポートされていないロケールが英語にフォールバックする
- 明示的な CLI ロケールがデフォルトロケールを上書きする
- 選択された UI ロケールが現実的な範囲で永続化される
- 旧来の `ch` ロケール設定が安全にマイグレートまたはフォールバックする
- 重要な表現がすべてのロケールで区別を保持する
- CLI 運用ラベルが翻訳後に意味的採用の主張にならない
- RDE セクションラベルがロケールをまたいで6項目の意味変化構造を保持する
- エクスポートラベルがレビュー状態または RDE 完了を過大表現しない

## Design-pattern implications

### Strategy pattern

ロケール解決は、CLI オプション・環境変数・プロジェクト metadata・ユーザー設定・ブラウザ言語・URL パラメータ・フォールバックロジックをサポートするためにストラテジーとして表現できる（ADR-001 Strategy pattern との整合）。

例：

- `CliLocaleResolutionStrategy`
- `UiLocaleResolutionStrategy`（v0.7+）
- `ReportLanguageResolutionStrategy`

### Adapter pattern

プロダクトロケールキーをブラウザ・API・OS・標準準拠のロケール識別子にマッピングする場合、アダプターが必要になりうる（ADR-001 Adapter pattern との整合）。

例：

- `BrowserLocaleAdapter`（v0.7+）
- `SystemLocaleAdapter`
- `LegacyLocaleAdapter`（`ch` → `zh-CN` マイグレーション用）

### Specification pattern

重要な表現制約は翻訳レビュー用の Specification として表現できる（ADR-001 Specification pattern との整合）。

例：

- `ReviewStatusTranslationSpec`
- `RdeBoundaryTranslationSpec`
- `ProvenanceBoundaryTranslationSpec`
- `OperationalVsSemanticStatusSpec`

### Repository pattern

翻訳カタログが交換可能なリソースになる場合、Repository 的な境界を通じてロードしてよい（ADR-001 Repository pattern との整合）。

例：

- `TranslationCatalogRepository`
- `LocalePreferenceRepository`

## Consequences

### Benefits

- 多言語 CLI・レポート・将来の UI が最初から支持される
- 将来の公開リリースが容易になる
- 言語固有の意味ドリフトが監査可能になる
- RDE とレビュー状態の表現が言語をまたいで安全を保てる
- Chronicle Stack が日本語・英語・中国語のワークフローをまたいで動作できる
- 将来の Sayane（v0.6+）と CSG-RAG（v0.4+）連携が言語境界を保持できる

### Costs

- CLI とレポートレンダリングのより多くの前払い構造が必要
- 翻訳メンテナンスの負担
- i18n テストが必要
- 重要なラベルを言語をまたいでレビューする必要がある
- 将来的に `zh-TW` 等の他の中国語ロケール変種の追加が必要になりうる
- 内部ドメインモデルをローカライズされたプレゼンテーションテキストから分離する必要がある

## Non-goals

本 ADR は最終的な Dashboard UI 振る舞いを定義しない。

本 ADR はすべてのドキュメントの即時翻訳を要求しない。

本 ADR は成果物コンテンツの自動翻訳を要求しない。

本 ADR は CSG-RAG の多言語意味検索を定義しない（v0.4+）。

本 ADR はすべての実験的スケッチに本番グレードの i18n を要求しない。

ただし、プロトタイプロジックが永続化されたロケール設定・エクスポートドキュメント・CLI 出力・レビュー状態・来歴・ユーザー可視の解釈に影響を及ぼした時点で、本 ADR の管理下に置かれなければならない。
