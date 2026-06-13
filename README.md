# Chronicle Stack

Chronicle Stack は、AIとの共同作業で生まれる文脈、判断、生成物、差分、出所、境界ルールを、後から再構成できる形で記録する local-first な基盤です。

> Chronicle Stack is a local-first context and artifact chronicle for AI-assisted work.

中心にある価値は **再構成可能性** です。AIとの共同作業では、最終成果物だけでなく、そこに至る文脈、判断、出所、差分、意味変化が後から辿れるべきだと考えます。

## 解決したい課題

AIを使った執筆、設計、調査、開発では、成果物だけが残りやすくなります。しかし、本当に後から必要になるのは、しばしば成果物そのものではなく、そこへ至る過程です。

Chronicle Stack は、次のような情報の喪失を防ぐことを目指します。

- どの文脈から生成されたのか
- どの指示で変更されたのか
- どの案が採用、棄却、保留されたのか
- どの差分が意味を変えたのか
- 出所や根拠がどこにあるのか
- 注意が必要な文脈がいつ混入したのか
- 人間が最終的に何を判断したのか

この問題を、Chronicle Stack では **文脈の喪失**、**判断履歴の喪失**、**生成物の来歴不明化**、**AI memory への過度な依存** として捉えます。

## Chronicle Stack が目指すもの

Chronicle Stack は、AIにすべてを記憶させるための仕組みではありません。人間側が自分の文脈、問い、判断、生成物の来歴を保持し、必要に応じて選び直せるようにするための基盤です。

主な価値は次の通りです。

- **再構成可能性**: 後から生成過程と判断を辿れる
- **文脈主権**: 文脈をAI任せにせず、人間側で保持・選択する
- **Artifact履歴**: 成果物をバージョンとして追跡する
- **Decision記録**: 採用、棄却、保留の理由を残す
- **RDE Diff Record**: 意味変化を構造的に記録する
- **Source Provenance**: 出所を記録する
- **Visibility / Boundary Rules**: 文脈の扱いに注意点と境界を与える

## Chronicle Stack ではないもの

Chronicle Stack は、次のものではありません。

- 汎用ベクトルデータベース
- 完成済みのGraphRAG実装
- 正しさを自動判定する仕組み
- 利用権限を管理する仕組み
- クラウド型AIメモリサービス
- LLMエージェント実行基盤
- 人間のレビューを置き換える仕組み
- 出所を数学的に証明する仕組み

RDEは意味変化を構造的に記録するための枠組みですが、正しさを証明するものではありません。Boundary Rules は文脈利用の警告や分類を支援するものですが、強制的な保護機構ではありません。

## コア概念

- **Chronicle**: 作業、研究、設計、執筆、開発に関する時系列の構造化記録
- **Chronicle Event**: `chronicle.jsonl` に追記される最小記録単位
- **Context**: 生成や判断の背景となる情報
- **Artifact**: 仕様書、エッセイ、コード、レポートなどの成果物
- **ArtifactVersion**: Artifactのスナップショット履歴
- **Decision**: 採用、棄却、修正、保留などの判断記録
- **RDE Diff Record**: 意味変化を6項目で記録する差分記録
- **Context Scope**: Contextが有効な範囲
- **Visibility Hint**: ContextやArtifactの可視性に関する軽量ヒント
- **Source Provenance**: 情報や成果物の出所記録
- **Boundary Rule**: Context利用時の include / exclude / warn ルール

関連用語は [用語集](docs/glossary.md) を参照してください。

## システム全体像

```mermaid
flowchart TD
    U[利用者] --> CLI[Chronicle CLI]
    CLI --> S[Chronicle Services]
    S --> E[Chronicle Events]
    S --> C[Contexts]
    S --> A[Artifacts]
    S --> D[Decisions]
    S --> R[RDE Diff Records]
    S --> B[Boundary Rules]
    E --> J[(chronicle.jsonl 一次記録)]
    J --> I[(派生Index)]
    I --> Search[Search]
    I --> Export[Export]
    I --> History[Artifact History]
    I --> Check[Boundary Check]
    Check --> Plan[次段階: Context Injection Plan]
```

`chronicle.jsonl` が一次記録です。派生Indexは、検索、エクスポート、履歴表示、Boundary Check のために再構築される補助データです。

詳細は [アーキテクチャ](docs/architecture.md) を参照してください。

## 現在の状態

| 領域 | 状態 |
|---|---|
| JSONL一次記録 | v0.1完了 |
| Artifact履歴 | v0.1完了 |
| Decision記録 | v0.1完了 |
| RDE Diff Record | v0.1完了 |
| Context Scope Model | v0.2実装済み |
| Visibility Hint | v0.2実装済み |
| Source Provenance | v0.2実装済み |
| Boundary Rules | v0.2実装済み |
| Context Injection Plan | 次段階 |
| GraphRAG | 将来構想 |
| Dashboard | 将来構想 |

## インストール

```bash
pip install -e ".[dev]"
```

## クイックスタート

```bash
chronicle init --title "My Project"
chronicle record --type user_input --actor user --summary "仕様書を作成する"

chronicle add-context \
  --title "Task Context" \
  --summary "このタスクだけで使う文脈" \
  --scope task \
  --visibility private \
  --source-type conversation \
  --source-tool chatgpt

chronicle artifact create \
  --title "Basic Spec" \
  --type specification \
  --file docs/spec.md \
  --visibility private

chronicle boundary add \
  --type warn \
  --field visibility \
  --operator equals \
  --value sensitive \
  --reason "注意が必要な文脈は利用前に確認する"

chronicle search "Decision Model"
chronicle export --format yaml
chronicle show
```

## 重要な動作仕様

- `.chronicle/chronicle.jsonl` が一次記録です。
- `indexes/` は再構築可能な派生データです。
- `ArtifactVersion.source_event_id` は、それを記録したイベントを指します。
- `Decision.event_id` は、その判断を記録したイベントを指します。
- Artifactの更新には `--file` または明示的なcontent指定が必要です。
- RDEは意味変化の構造化記録であり、正しさの判定ではありません。
- Boundary Rules は助言的な分類であり、強制的な保護機構ではありません。

## ディレクトリ構成

```text
.chronicle/
  chronicle.jsonl
  metadata.yaml
  artifacts/
    <artifact_id>/
      current.md
      versions/
        <version_id>.md
  indexes/
    artifact_index.json
    context_index.json
    decision_index.json
    rde_index.json
    boundary_rule_index.json
  reports/rde/
```

## 開発

```bash
pytest
ruff check src/ tests/
```

CI は GitHub Actions で実行されます。

## ドキュメント

最初に読む文書:

- [用語集](docs/glossary.md)
- [アーキテクチャ](docs/architecture.md)
- [CLI リファレンス](docs/cli-reference.md)
- [データモデル](docs/data-model.md)
- [ストレージ形式](docs/storage-format.md)
- [テスト戦略](docs/testing-strategy.md)
- [v0.2 バックログ](docs/backlog-v0.2.md)

仕様書:

- [基本仕様書](docs/specs/chronicle-stack-basic-spec-v0.1.md)
- [Chronicle Event Model 仕様書](docs/specs/chronicle-event-model-spec-v0.1.md)
- [Artifact Model 仕様書](docs/specs/artifact-model-spec-v0.1.md)
- [Decision Model 仕様書](docs/specs/decision-model-spec-v0.1.md)
- [RDE Diff Record 仕様書](docs/specs/rde-diff-record-spec-v0.1.md)
- [Roadmap Linkage](docs/specs/roadmap-linkage-v0.1.md)

## 変更履歴

- [CHANGELOG.md](CHANGELOG.md)

## リリース

- Latest release: **v0.1.0**
- GitHub Release: https://github.com/zyx-corporation/chronicle-stack/releases/tag/v0.1.0

## ライセンス

MIT
