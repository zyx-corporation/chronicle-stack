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

# Artifact を更新
chronicle artifact update --artifact art_xxx --file docs/spec-v2.md --summary "Decision Model を追加"

# 判断を記録
chronicle decision record --artifact art_xxx --type accepted --reason "v0.1 として採用"

# RDE Diff を記録
chronicle rde record --artifact art_xxx --from ver_aaa --to ver_bbb --summary "詳細化"

# 検索
chronicle search "Decision Model"

# エクスポート
chronicle export --format yaml
chronicle export --format markdown -o chronicle-export.md

# 概要表示
chronicle show
```

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
  reports/rde/
```

## 開発

```bash
pytest
```

## ドキュメント

- [基本仕様書](docs/specs/chronicle-stack-basic-spec-v0.1.md)
- [データモデル](docs/data-model.md)
- [CLI リファレンス](docs/cli-reference.md)
- [ストレージ形式](docs/storage-format.md)
- [テスト戦略](docs/testing-strategy.md)

## ライセンス

MIT
