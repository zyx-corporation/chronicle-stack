# Chronicle Stack

Chronicle Core v0.1 — AIとの共同思考における文脈・生成物・判断・差分を、後から再構成できる形で記録するための最小中核。

## 概要

Chronicle Stack は、人間とAIの共同作業で発生する文脈、入力、生成物、判断、修正、差分を時系列で記録し、追跡・監査・再利用可能にする local-first 基盤です。

v0.1 では以下を提供します。

- Chronicle Event による記録（JSONL 一次記録）
- Artifact の作成・更新・バージョン履歴
- Decision（採用・棄却・保留など）の記録
- RDE Diff Record による簡易意味変化監査
- CLI による init / record / search / export

v0.2 では以下を開発中です。

- Context Scope Model の正式化
- Context の有効範囲（global / project / session / task / artifact / temporary）の明示的指定
- Context と Artifact への visibility_hint （public / private / sensitive / unknown）追加
- Source Provenance Metadata 追加
- Context Boundary Rules（include / exclude / warn）追加

## インストール

```bash
pip install -e ".[dev]"
```

## クイックスタート

```bash
# Chronicle を初期化
chronicle init --title "My Project"

# イベントを記録
chronicle record --type user_input --actor user --summary "仕様書を作成する"

# Artifact を作成
chronicle artifact create --title "Basic Spec" --type specification --file docs/spec.md

# Artifact を更新（--file は必須）
chronicle artifact update --artifact art_xxx --file docs/spec-v2.md --summary "Decision Model を追加"

# 判断を記録
chronicle decision record --artifact art_xxx --type accepted --reason "v0.1 として採用"

# RDE Diff を記録（6つのRDEフィールドを繰り返し指定可能）
chronicle rde record --artifact art_xxx --from ver_aaa --to ver_bbb --summary "詳細化" \
  --preserved "元の意図" --preserved "基本構造" \
  --transformed "詳細セクション追加" \
  --supplemented "新しい例" \
  --unresolved "用語の統一" \
  --deviation-risk "スコープ拡大の可能性" \
  --next-update-policy "四半期レビュー"

# 検索
chronicle search "Decision Model"

# エクスポート
chronicle export --format yaml
chronicle export --format markdown -o chronicle-export.md

# 概要表示
chronicle show
```

## 重要な動作仕様

### イベント連携の永続化

- **ArtifactVersion.source_event_id**: 各バージョンは、それを記録したイベントの `event_id` を `source_event_id` として永続化します。`chronicle.jsonl` のペイロードにも正しい `source_event_id` が含まれます。
- **Decision.event_id**: 各 Decision は、それを記録したイベントの `event_id` を永続化します。インデックス再構築後も `event_id` は保持されます。

### Artifact 更新のガード

- Artifact の更新には `--file` または `--content` の指定が必須です。どちらも指定しない場合、`ARTIFACT_CONTENT_MISSING` エラーが発生します。これにより、誤って `current.md` が空になることを防止します。
- 存在しないファイルを指定した場合、`SOURCE_FILE_NOT_FOUND` エラー（`ChronicleError` サブクラス）が発生します。

### RDE-to-Version リンク

- RDE Diff Record を作成すると、`from_version_id` → `to_version_id` のリンクが記録されます。
- インデックス再構築時に、対応する `ArtifactVersion.rde_record_id` が自動的に設定されます。
- RDE レコードは `rde_index.json` に保存され、検索対象になります。

## ディレクトリ構成

```text
.chronicle/
  chronicle.jsonl          # 一次記録（全イベント）
  metadata.yaml
  artifacts/
    <artifact_id>/
      current.md
      versions/
        <version_id>.md
  indexes/                 # 再生成可能な派生データ
    artifact_index.json
    context_index.json
    decision_index.json
    rde_index.json
  reports/rde/
```

## 開発

```bash
pytest
ruff check src/ tests/
```

CI は GitHub Actions で実行されます（`.github/workflows/ci.yml`）。

## ドキュメント

### 仕様書

- [基本仕様書](docs/specs/chronicle-stack-basic-spec-v0.1.md)
- [Chronicle Event Model 仕様書](docs/specs/chronicle-event-model-spec-v0.1.md)
- [Artifact Model 仕様書](docs/specs/artifact-model-spec-v0.1.md)
- [Decision Model 仕様書](docs/specs/decision-model-spec-v0.1.md)
- [RDE Diff Record 仕様書](docs/specs/rde-diff-record-spec-v0.1.md)
- [Roadmap Linkage](docs/specs/roadmap-linkage-v0.1.md)

### ADR

- [ADR-001: T-RDE, TDD, and Design-Pattern Principles](docs/adr/ADR-001-t-rde-tdd-and-design-patterns.md)
- [ADR-002: i18n and Language Selection](docs/adr/ADR-002-i18n-and-language-selection.md)

### 実装ガイド

- [データモデル](docs/data-model.md)
- [CLI リファレンス](docs/cli-reference.md)
- [ストレージ形式](docs/storage-format.md)
- [テスト戦略](docs/testing-strategy.md)
- [スモークテスト手順](docs/smoke-test-v0.1.md)
- [リリース判定](docs/release-readiness-v0.1.md)
- [v0.2 バックログ](docs/backlog-v0.2.md)

## 変更履歴

- [CHANGELOG.md](CHANGELOG.md)

## リリース

- Latest release: **v0.1.0**
- GitHub Release: https://github.com/zyx-corporation/chronicle-stack/releases/tag/v0.1.0

## ライセンス

MIT
