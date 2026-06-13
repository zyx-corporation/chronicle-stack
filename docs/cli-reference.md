# Chronicle Stack CLI Reference

Chronicle Stack v0.3 の CLI コマンド一覧です。

CLIの通常出力は人間向けです。機械処理を行う場合は、利用可能なコマンドでは `--json` を使用してください。CLI JSON出力の安定性については [インターフェース契約](interface-contracts.md) を参照してください。

## グローバル

```bash
chronicle --help
chronicle --version
```

`chronicle --version` はインストール済みpackage metadataからversionを表示します。

## chronicle init

```bash
chronicle init --title "Project Title"
```

`.chronicle/` ディレクトリ、`chronicle.jsonl`、`metadata.yaml` を作成します。

`chronicle.jsonl` が唯一の一次記録です。`indexes/` は再構築可能な派生データです。

## chronicle record

```bash
chronicle record --type user_input --actor user --summary "Summary"
chronicle record --type assistant_output --actor assistant --summary "Summary" --source-tool chatgpt
```

任意のChronicle Eventを記録します。source metadataは出所記録であり、真実性の証明ではありません。

## chronicle add-context

```bash
chronicle add-context \
  --title "Private Task Context" \
  --source-type conversation \
  --scope task \
  --visibility private \
  --summary "Only for this task"
```

`--scope` は正式な ContextScope を受け付けます。

```text
global / project / session / task / artifact / temporary / unknown
```

`--visibility` は可視性ヒントを指定します。

```text
public / private / sensitive / unknown
```

Visibility Hint はアクセス制御やredactionではありません。

## chronicle artifact

| サブコマンド | 説明 |
|---|---|
| `create` | Artifactを作成する |
| `update` | Artifactを更新し、新しいVersionを作成する |
| `history` | Artifactの履歴を表示する |
| `list` | Artifact一覧を表示する |

例:

```bash
chronicle artifact create --title "Spec" --type specification --file docs/spec.md --visibility private
chronicle artifact update --artifact art_xxx --file docs/spec.md --summary "Update spec"
chronicle artifact history --artifact art_xxx
chronicle artifact history --artifact art_xxx --json
```

`artifact update` では `--file` の指定が必須です。指定しない場合 `ARTIFACT_CONTENT_MISSING` エラーが発生します。

## chronicle decision record

```bash
chronicle decision record \
  --artifact art_xxx \
  --type accepted \
  --reason "v0.3 として採用" \
  --alternative "Option B" \
  --notes "Revisit after v0.4"
```

採用、棄却、保留などの判断を記録します。

## chronicle rde record

```bash
chronicle rde record --artifact art_xxx --from ver_aaa --to ver_bbb --summary "Summary" \
  --preserved "元の意図" \
  --transformed "詳細セクション追加" \
  --supplemented "新しい例" \
  --unresolved "用語の統一" \
  --deviation-risk "スコープ拡大の可能性" \
  --next-update-policy "四半期レビュー"
```

RDE Diff Recordは意味変化の構造化記録であり、正しさを証明するものではありません。

## chronicle boundary

Boundary Rulesは文脈利用に関する助言的分類です。アクセス制御や強制削除の仕組みではありません。

### chronicle boundary add

```bash
chronicle boundary add \
  --type warn \
  --field visibility \
  --operator equals \
  --value sensitive \
  --reason "Sensitive context should be reviewed"
```

`--type`:

```text
include / exclude / warn
```

`--field`:

```text
scope / visibility / source_type / source_tool / source_session / source_model / tag
```

`--operator`:

```text
equals / not_equals / in / contains
```

### chronicle boundary list

```bash
chronicle boundary list
chronicle boundary list --json
```

### chronicle boundary check

```bash
chronicle boundary check --context ctx_xxx
chronicle boundary check --context ctx_xxx --json
```

指定したContextに対してBoundary Ruleを評価します。

## chronicle injection plan

```bash
chronicle injection plan --task "Draft v0.3 release notes"
chronicle injection plan --task "Draft v0.3 release notes" --json
chronicle injection plan --task "Draft v0.3 release notes" --record
chronicle injection plan --task "Draft v0.3 release notes" --record --json
```

Boundary Rule評価に基づいてContextを `selected` / `warned` / `excluded` に分類する文脈選択案を生成します。

重要:

- LLMへの自動注入は行いません。
- デフォルトでは `chronicle.jsonl` に永続化しません。
- `--record` を指定した場合のみ `injection_plan_recorded` Eventとして記録します。
- `--json` 出力は `plan`, `recorded`, `event_id` を含みます。

## chronicle search

```bash
chronicle search "keyword"
chronicle search "keyword" --json
```

イベント、Artifact、Decision、Context、RDE、Boundary Ruleなどを検索します。

## chronicle show

```bash
chronicle show
chronicle show --json
```

Chronicle概要を表示します。

## chronicle export

```bash
chronicle export --format yaml
chronicle export --format markdown -o output.md
chronicle export --format graph-json -o graph.json
chronicle export --format html -o chronicle-dashboard.html
```

対応形式:

| format | 契約レベル | 説明 |
|---|---|---|
| `yaml` | Semi-public | 機械可読snapshot |
| `markdown` | Human-facing | 人間向けreport |
| `graph-json` | Semi-public / derived | GraphRAG接続準備用のnode/edge export |
| `html` | Human-facing | 静的・読み取り専用Dashboard |

注意:

- exportは派生ビューです。
- JSONLを変更しません。
- `graph-json` はGraphRAGエンジンではありません。
- `html` はWebアプリケーションではありません。
- visibility hintはredactionではないため、デフォルトでは隠蔽されません。

## chronicle index rebuild

```bash
chronicle index rebuild
```

`chronicle.jsonl` から派生インデックスを再生成します。

`indexes/` は一次記録ではありません。破棄しても `chronicle index rebuild` で再生成可能です。

## Exit codes and errors

不正なenum値、存在しないファイル、必須オプション不足などは非zero exitになります。

例:

```text
Invalid visibility: secret
Allowed values: public, private, sensitive, unknown
```

human-readable error本文は改善のために変更される可能性があります。機械処理契約として扱わないでください。
