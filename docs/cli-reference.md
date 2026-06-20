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
chronicle ui --mutation-capability-flag --enable-ui-mutation --auth-mode loopback_local --authorization-mode reviewer_declared
chronicle ui --auth-mode loopback_local --authorization-mode reviewer_declared
chronicle ui --json
chronicle ui-smoke
chronicle ui-smoke --json
```

`chronicle ui` は明示起動型 foreground local web UI です。既定では read-only であり、daemon、autostart、hosted service ではありません。

現段階でも bind host は loopback (`127.0.0.1`, `localhost`, `::1`) のみ許可されます。`--auth-mode` と `--authorization-mode` は boundary config であり、UI review detail の assurance 表示に反映されます。`--mutation-capability-flag` は preview intent を metadata に記録します。実際の write route は `--enable-ui-mutation` を追加し、さらに `--auth-mode loopback_local --authorization-mode reviewer_declared` が揃った場合にのみ有効化されます。詳細は [ADR-0022](adr/0022-explicit-local-ui-mutation-enable-flag.md) を参照してください。

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

`/api/review-queue` は `review_status=needs_review` の record を返します。既定では preview-only ですが、explicit enable 条件が揃うと GUI review mutation route の server-side gate が有効になります。review detail と review queue / summary jobs list の両方で、そのときだけ明示 reviewer context form と action buttons が現れます。`suggested_cli_family` では引き続き関連 CLI family の目安も表示します。

`/api/ui-boundary` は bind scope, mutation capability flag, explicit mutation enable flag 由来の `mutation_enabled`, auth/authz mode を read-only で返します。`mutation_enabled=true` は `--enable-ui-mutation` と required gate 条件がすべて揃ったときだけ成立します。placeholder / derived config により `auth_mode` / `authorization_mode` / `session_gating` を明示できます。あわせて `auth_boundary_summary` で auth/authz placeholder の derived status / blockers / next steps も返します。overview ではさらに `auth_boundary_overview` / `identity_boundary_summary` により auth warning / reviewer identity / session alignment の集約状態も読めます。
- write-capable route family は `POST /api/review-actions/<event_id>/<action>` です。`reviewer_label`, `reviewer_kind`, `session_label`, `ui_intent` を JSON body で受け、gate 条件が崩れていれば fail closed で戻ります。
- preview payload / action response には `rollback_status`, `possible_error_codes`, `recovery_path` を含む fail-closed contract metadata も含まれます。
- local UI shell では `recovery_path` をそのまま copy できる button も表示されます。
- failure kind に応じて `recovery_commands`、成功時には `follow_up_commands` も返り、UI shell から copy できます。
- overview triage では `Identity aligned` などの quick slice から reviewer identity / assurance 系の review queue slice に直接 drilldown できますが、これは引き続き read-only filter state のみです。
- overview の runtime records / summary jobs panel でも matching-review-derived auth readiness の集約状態を read-only で確認できます。
- overview の summary jobs panel では matching-review-derived identity/session assurance 集約も read-only で確認できます。
- review queue list では `auth` badge により `Auth advisory` / `Auth aligned` の slice を detail を開かずに辿れます。
- runtime records list / summary jobs list でも同じ auth readiness badge vocabulary を使い、matching review target がある行だけ advisory/aligned 状態を read-only で辿れます。
- summary jobs list では reviewer identity / session assurance も matching review target 由来の badge として read-only で確認できます。
- review detail / summary detail では `Auth Readiness` notice により current preview auth boundary, reviewer identity assurance, blocker, next step を read-only で確認できます。
- runtime record detail でも matching review target がある場合は同じ `Auth Readiness` notice を表示します。
この read-only semantic boundary と CLI parity の扱いは [ADR-0019](adr/0019-local-ui-review-semantics-parity-boundary.md) で固定しています。

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
chronicle runtime summarize --text "Source text" --draft-title "Runtime Draft"
chronicle runtime summarize --text "Source text" --record
chronicle runtime summarize --text "Source text" --record --json
```

方針:

- explicit manual invocation only
- no LLM call
- no external runtime call
- generated output requires review
- `--record` 指定時のみ `assistant_output` event として記録
- `--draft-title` 指定時のみ pending-review の summary job / draft artifact としても保存
- draft provenance には provider kind / model name / invocation mode / external_call_made が含まれる

### chronicle summary run

```bash
chronicle summary run --id sum_xxx
chronicle summary run --id sum_xxx --max-sentences 2
chronicle summary run --id sum_xxx --draft-title "Runtime Re-draft"
chronicle summary run --id sum_xxx --json
```

方針:

- 既存の pending-review summary job を explicit runtime boundary 経由で再実行する
- source refs と prompt provenance を runtime-backed draft に引き継ぐ
- no external model API
- no hidden background execution
- generated output remains pending review
- 出力は `runtime_manual` provenance を持つ draft summary job / draft artifact として保存される

### chronicle summary invoke-plan

```bash
chronicle summary invoke-plan --id sum_xxx
chronicle summary invoke-plan --id sum_xxx --operation summarize
chronicle summary invoke-plan --id sum_xxx --record
chronicle summary invoke-plan --id sum_xxx --json
```

方針:

- 既存 summary draft を configured provider contract に接続する dry-run を作る
- no provider execution
- no external call performed
- summary job ID / title / prompt / source-ref count を request preview に含める
- `--record` 指定時のみ review-oriented `assistant_output` event として記録する

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

### chronicle runtime invoke-plan

```bash
chronicle runtime invoke-plan --text "Source text"
chronicle runtime invoke-plan --text "Source text" --operation summarize
chronicle runtime invoke-plan --text "Source text" --record
chronicle runtime invoke-plan --text "Source text" --json
```

方針:

- stored provider contract を explicit/manual invocation dry-run に接続する
- no provider execution
- no external call performed
- `invocation_ready` は contract boundary 上の ready / blocked を示すだけで、実行完了を意味しない
- HTTP provider では `allow_network` が false の場合に block reason を返す
- `--record` 指定時のみ review-oriented `assistant_output` event として記録する

### chronicle runtime config show / set-local / set-http / disable

```bash
chronicle runtime config show
chronicle runtime config show --json
chronicle runtime config set-local --model local-placeholder
chronicle runtime config set-http --base-url https://runtime.example.invalid/v1 --model manual-http-model --api-key-env OPENAI_API_KEY --allow-network
chronicle runtime config disable
```

方針:

- provider configuration は `.chronicle/runtime.yaml` に保存される
- configuration alone does not invoke any model or external runtime
- `set-http` は downstream contract を保存するだけで、その場で network call はしない
- `runtime status` は actual local placeholder execution と configured provider contract を分けて表示する
- generated output は引き続き explicit/manual invocation 後にだけ発生する

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
- review queue list header には現在の active slice が chip として表示され、その場で clear できる
- runtime records list header も同じ active slice chip pattern を使う
- review/runtime の active slice chips は共通 helper で描画され、語彙をそろえている
- active view summary の `filter=` / `sort=` 表示も同じ helper 群に寄せている
- overview triage button labels も同じ helper vocabulary に寄せている
- overview の warning priority badges も同じ helper vocabulary に寄せている
- review queue list の status / package readiness / CLI parity badges も専用 helper に寄せ、同じ read-only badge vocabulary を維持している
- overview shortcut buttons と detail notice の `Open ...` / `More ...` actions も helper 化し、list/detail 間の jump 文言 drift を抑えている
- detail JSON の related link labels も helper 化し、`Open matching ...` / `Open context ...` の語彙を detail payload でも固定している
- overview panel 見出し / detail notice 見出し / triage summary JSON 行も helper に寄せ、read-only UI の見出し語彙を揃えている
- detail notice の `Status:` / list joins / JSON summary 行も helper に寄せ、payload 派生テキストの整形 drift を抑えている
- review queue detail は reviewer / audit timeline を read-only で表示する
- review queue detail は current UI boundary と reviewer identity を照合した assurance も表示する
- review queue detail の warning / capability 表示からも related review slices へ戻れる
- review detail の parity / assurance / package readiness notices からも related review slices へ戻れる
- review detail の action preview notice からも capability/parity の related review slices へ戻れる
- review queue list でも preview 列から blocked review route を read-only で試せ、常に `403` と CLI fallback contract だけを返す
- review timeline の各履歴行からも disposition / identity-assurance の related review slices へ戻れる
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
