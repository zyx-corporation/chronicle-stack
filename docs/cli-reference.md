# CLI Reference

Chronicle Core v0.1 CLI コマンド一覧。

## グローバル

すべてのコマンドで `--json` オプションにより JSON 出力が可能。

例:
```bash
chronicle artifact history --artifact art_xxx --json
```

## chronicle init

```bash
chronicle init --title "Project Title"
```

`.chronicle/` ディレクトリ、`chronicle.jsonl`、`metadata.yaml` を作成。

## chronicle add-context

```bash
chronicle add-context \
  --title "Private Task Context" \
  --source-type conversation \
  --scope task \
  --visibility private \
  --summary "Only for this task"
```

`--scope` は正式な ContextScope（global / project / session / task / artifact / temporary）を受け付ける。デフォルトは `project`。明示指定を推奨。
`--visibility` は可視性ヒント（public / private / sensitive / unknown）を指定する。デフォルトは `unknown`。権限管理ではない。

## chronicle record

```bash
chronicle record --type user_input --actor user --summary "Summary"
```

## chronicle artifact

| サブコマンド | 説明 |
|-------------|------|
| `create` | `--title`, `--type`, `--file` |
| `update` | `--artifact`, `--file`（必須）, `--summary` |
| `history` | `--artifact` |
| `list` | 全 Artifact 一覧 |

`update` では `--file` の指定が必須です。指定しない場合 `ARTIFACT_CONTENT_MISSING` エラーが発生します。
存在しないファイルを指定した場合、`SOURCE_FILE_NOT_FOUND` エラーが発生します。

## chronicle decision record

```bash
chronicle decision record \
  --artifact art_xxx \
  --type accepted \
  --reason "v0.1 として採用" \
  --alternative "Option B" \
  --alternative "Option C" \
  --notes "Revisit after v0.2"
```

`--alternative` は繰り返し指定可能。`--notes` で補足メモを記録できる。

## chronicle rde record

```bash
chronicle rde record --artifact art_xxx --from ver_aaa --to ver_bbb --summary "Summary" \
  --preserved "元の意図" --preserved "基本構造" \
  --transformed "詳細セクション追加" \
  --supplemented "新しい例" \
  --unresolved "用語の統一" \
  --deviation-risk "スコープ拡大の可能性" \
  --next-update-policy "四半期レビュー"
```

6 つの RDE フィールド（`--preserved`, `--transformed`, `--supplemented`, `--unresolved`, `--deviation-risk`, `--next-update-policy`）は繰り返し指定可能。

## chronicle show

Chronicle 概要（イベント数、Artifact 数など）を表示。

## chronicle search

```bash
chronicle search "keyword"
```

イベント・Artifact・Decision・Context・RDE をキーワード検索。

## chronicle export

```bash
chronicle export --format yaml
chronicle export --format markdown -o output.md
```

## chronicle index rebuild

```bash
chronicle index rebuild
```

`chronicle.jsonl` から派生インデックスを再生成する。
再生成時に RDE レコードの `to_version_id` をもとに、対応する `ArtifactVersion.rde_record_id` が自動的に設定される。
