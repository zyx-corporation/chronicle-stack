# Chronicle Stack CLI Reference

Chronicle Stack v0.6 の CLI コマンド一覧です。

CLIの通常出力は人間向けです。機械処理を行う場合は、利用可能なコマンドでは `--json` を使用してください。CLI JSON出力の安定性については [インターフェース契約](interface-contracts.md) を参照してください。

v0.6 以降の文書例では primary CLI alias を優先します。補助CLIである `chronicle-context`, `chronicle-export`, `chronicle-package`, `chronicle-graph` は互換目的で維持されています。詳細は [ADR-0017](adr/0017-auxiliary-cli-integration-boundary.md) を参照してください。

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

## chronicle doctor

```bash
chronicle doctor
chronicle doctor --json
```

現在のChronicle projectをread-onlyで診断します。

主な確認項目:

- `.chronicle/` の存在
- `chronicle.jsonl` の存在とparse可否
- `metadata.yaml` の存在とparse可否
- known EventType
- derived index の存在
- Artifact file の存在
- recorded InjectionPlanが参照するContext
- graph-json export生成可否
- HTML dashboard export生成可否

`doctor` はJSONLやindexを変更しません。indexが欠損していても自動rebuildは行わず、`chronicle index rebuild` を推奨するwarningを返します。

Exit code:

| status | exit code |
|---|---|
| `ok` | 0 |
| `warning` | 0 |
| `error` | non-zero |

`doctor --json` は `status`, `chronicle_id`, `checks` を含むJSONを返します。

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
| `yaml` | Semi-public | 機械可読snapshot。top-level `export_manifest` を含む |
| `markdown` | Human-facing | 人間向けreport。manifest埋め込み対象外 |
| `graph-json` | Semi-public / derived | GraphRAG接続準備用のnode/edge export。top-level `export_manifest` を含む |
| `html` | Human-facing | 静的・読み取り専用Dashboard。Export Manifest sectionを含む |

### chronicle export profile

```bash
chronicle export profile --format yaml --profile public-review
chronicle export profile --format yaml --profile restricted-summary --output export.yaml --json
chronicle export profile --format html --profile public-review --output dashboard.html
```

Security-aware export profile を使った派生exportです。`chronicle-export profile ...` と同じ実装を共有する primary CLI alias です。

注意:

- exportは派生ビューです。
- JSONLを変更しません。
- Export Manifestは来歴メタデータであり、暗号学的証明ではありません。
- `graph-json` はGraphRAGエンジンではありません。

## chronicle ai-index

`ai-index` は local file-backed placeholder vector / graph surface です。一次記録ではなく、補助的な派生面です。

境界:

- LLM は呼びません
- embedding provider は呼びません
- vector DB は呼びません
- graph DB は呼びません
- GraphRAG runtime は呼びません
- external service は呼びません
- 検索結果は assistive であり、正しさの証明ではありません
- `.chronicle/chronicle.jsonl` が引き続き正本です

### chronicle ai-index status

```bash
chronicle ai-index status
chronicle ai-index status --json
```

`.chronicle/ai_indexes/vector_index.json` と `.chronicle/ai_indexes/graph_index.json` の placeholder 状態を表示します。

### chronicle ai-index vector

```bash
chronicle ai-index vector add --record evt_xxx --text "local placeholder text" --type event
chronicle ai-index vector add --record evt_xxx --text "local placeholder text" --metadata source=manual --json
chronicle ai-index vector search --query "placeholder" --limit 5
chronicle ai-index vector search --query "placeholder" --json
```

`vector search` は token overlap と substring による placeholder scoring です。本格 embedding ではありません。

### chronicle ai-index graph

```bash
chronicle ai-index graph add-node --id evt_xxx --label event --property title="Example"
chronicle ai-index graph add-edge --source evt_xxx --target ctx_xxx --relation references
chronicle ai-index graph neighbors --id evt_xxx
chronicle ai-index graph neighbors --id evt_xxx --json
```

graph surface は単純 adjacency です。graph DB ではありません。

## chronicle ui / chronicle ui-smoke

Related: `docs/adr/0018-local-ui-read-only-navigation-boundary.md`

```bash
chronicle ui
chronicle ui --host 127.0.0.1 --port 8765
chronicle ui --mutation-capability-flag
chronicle ui --auth-mode loopback_local --authorization-mode reviewer_declared
chronicle ui --json
chronicle ui-smoke
chronicle ui-smoke --json
```

`chronicle ui` は明示起動型 foreground local web UI です。read-only であり、daemon、autostart、hosted service ではありません。

現段階では auth/authz 未実装のため、bind host は loopback (`127.0.0.1`, `localhost`, `::1`) のみ許可されます。`--auth-mode` と `--authorization-mode` は placeholder boundary config であり、UI review detail の assurance 表示に反映されます。`--mutation-capability-flag` は将来の GUI mutation work への preview intent を metadata に記録するだけで、write route は有効化しません。

read-only endpoint:

- `/api/overview`
- `/api/events`
- `/api/contexts`
- `/api/artifacts`
- `/api/decisions`
- `/api/rde`
- `/api/boundary`
- `/api/audit`
- `/api/lifecycle`
- `/api/runtime-records`
- `/api/review-queue`
- `/api/ui-boundary`
- `/api/package-review`
- `/api/graph-summary`
- `/api/ai-index-status`
- `/api/ai-index-vector`
- `/api/ai-index-graph-nodes`
- `/api/ai-index-graph-edges`

`chronicle ui-smoke` はサーバーを起動せず、ブラウザも使わず、local UI の read-only データ面だけを検証します。

`/api/review-queue` は `review_status=needs_review` の record を preview-only で返します。ここでは write action は有効化されず、`suggested_cli_family` で関連 CLI family の目安だけを表示します。

`/api/ui-boundary` は bind scope, mutation capability flag, auth/authz mode を read-only で返します。現在は mutation disabled が前提で、`mutation_capability_flag=true` でも write route は有効化されません。placeholder config により `auth_mode` / `authorization_mode` / `session_gating` を明示できます。

## chronicle runtime

`runtime` は explicit local runtime boundary を表す補助CLIです。

### chronicle runtime status

```bash
chronicle runtime status
chronicle runtime status --json
```

status は local placeholder runtime の境界を表示します。

### chronicle runtime summarize

```bash
chronicle runtime summarize --text "Source text"
chronicle runtime summarize --text "Source text" --max-sentences 2
chronicle runtime summarize --text "Source text" --record
chronicle runtime summarize --text "Source text" --record --json
```

方針:

- explicit manual invocation only
- no LLM call
- no external runtime call
- generated output requires review
- `--record` 指定時のみ `assistant_output` event として記録

### chronicle runtime retrieve-plan

```bash
chronicle runtime retrieve-plan --query "release note context"
chronicle runtime retrieve-plan --query "release note context" --limit 3
chronicle runtime retrieve-plan --query "release note context" --record
chronicle runtime retrieve-plan --query "release note context" --json
```

`retrieve-plan` は local dry-run の retrieval composition を表示します。

対象:

- placeholder vector hits
- graph export node hits
- Chronicle search hits

境界:

- dry-run only
- no LLM call
- no GraphRAG runtime
- no external retrieval service
- `--record` 指定時のみ `assistant_output` event として記録
- `html` はWebアプリケーションではありません。
- visibility hintはredactionではないため、デフォルトでは隠蔽されません。
- profile export は公開承認やアクセス制御ではありません。

## chronicle review

`review` は append-only review workflow の CLI skeleton です。

### chronicle review queue

```bash
chronicle review queue
chronicle review queue --include-resolved
chronicle review queue --json
```

`queue` は `review_status=needs_review` の target event を派生的に列挙します。approve / reject 済み target はデフォルトでは隠れ、`request-changes` は pending のまま残ります。

### chronicle review approve / reject / request-changes

```bash
chronicle review approve --event evt_xxx --reviewer alice
chronicle review approve --event evt_xxx --reviewer alice --reviewer-kind local_operator --session terminal-1
chronicle review reject --event evt_xxx --reviewer alice --note "reason"
chronicle review request-changes --event evt_xxx --reviewer alice --note "revise section 2"
chronicle review approve --event evt_xxx --reviewer alice --json
```

方針:

- append-only reviewer event を追加する
- target event 自体は直接変更しない
- reviewer identity は `label`, `kind`, `session` の構造で保持する
- `review_decision` audit event も同時に追加する
- GUI mutation の代わりに CLI parity を先に整える
- UI review queue はこの reviewer event を読んで pending / resolved を派生表示する
- UI review queue list は CLI parity badge も派生表示し、detail を開かずに command drift の有無を確認できる
- overview triage からも `aligned` / `drift_detected` の parity slice へ直接 drilldown できる
- review queue list は `CLI drift first` sort で parity drift 行を先頭に寄せられる
- review queue list の warning codes は badge と説明文の両方で派生表示される
- review queue list の warning badges 自体も clickable で、同じ warning code の slice へその場で絞り込める
- overview triage からも `ui_auth_not_enabled` など主要 warning slice へ直接 drilldown できる
- overview triage の warning 集計は priority 順でも整形され、主要 blocker が上に出る
- overview triage の warning badges は summary 駆動で並び、warning code ごとの review queue filter に直接つながる
- warning code filter が有効な間は review queue sort もその warning を持つ rows を優先する
- その状態は active view の sort label にも `warning-first:<code>` として表示される
- review queue detail は reviewer / audit timeline を read-only で表示する
- review queue detail は current UI boundary と reviewer identity を照合した assurance も表示する
- review queue detail の warning / capability 表示からも related review slices へ戻れる
- review queue は current boundary での capability/warning surface も表示する
- local UI shell は capability / assurance を notice と badge で目立つ形に描画する
- warning codes are expanded into user-facing explanation text in the local UI

## chronicle package

```bash
chronicle package context --purpose "Sayane review" --target local
chronicle package context --purpose "External review" --target external --persist
chronicle package list
chronicle package show --package pkg_xxx
chronicle package records --package pkg_xxx --json
```

Controlled integration package を生成・永続化・検査します。`chronicle-package ...` と同じ実装を共有する primary CLI alias です。

Package は transport contract であり、外部送信、許可付与、アクセス制御ではありません。

## chronicle context

```bash
chronicle context check --target local --purpose "internal review"
chronicle context check --target external --purpose "draft public summary" --json
```

Context records を model-facing context として使う前の dry-run check です。`chronicle-context ...` と同じ実装を共有する primary CLI alias です。

このコマンドは外部モデルAPIを呼びません。

## chronicle graph

```bash
chronicle graph summary
chronicle graph summary --json
chronicle graph nodes --json
chronicle graph nodes --type context
chronicle graph edges --json
```

Read-only graph export inspection です。`chronicle-graph ...` と同じ実装を共有する primary CLI alias です。

`graph-json` はGraphRAG接続準備用の派生viewであり、GraphRAG engine ではありません。

## Auxiliary CLI compatibility

v0.6 では以下の補助CLIも互換目的で維持されています。

```bash
chronicle-context check ...
chronicle-export profile ...
chronicle-package context ...
chronicle-graph summary
```

文書例では primary CLI alias を優先しますが、補助CLIを削除・非推奨化するものではありません。primary/auxiliary の挙動差分は Observation E2E の観測対象であり、semantic correctness certification ではありません。

## chronicle index rebuild

```bash
chronicle index rebuild
```

`chronicle.jsonl` から派生インデックスを再生成します。

`indexes/` は一次記録ではありません。破棄しても `chronicle index rebuild` で再生成可能です。
