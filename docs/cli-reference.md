# Chronicle Stack CLI Reference

Chronicle Stack の現行 CLI 参照です。文書例では primary CLI である
`chronicle ...` を優先します。互換目的の補助 CLI (`chronicle-context`,
`chronicle-export`, `chronicle-package`, `chronicle-graph`) は維持されていますが、
新しい利用例では primary alias を使ってください。

CLI の通常出力は人間向けです。機械処理する場合は、対応コマンドで `--json` を
指定してください。JSON 出力の安定性は [Interface Contracts](interface-contracts.md)、
primary/auxiliary CLI の境界は
[ADR-0017](adr/0017-auxiliary-cli-integration-boundary.md) を参照してください。

## 基本原則

- `.chronicle/chronicle.jsonl` が一次記録です。
- `indexes/`, export, graph, AI index, runtime output は派生面です。
- visibility hint は redaction やアクセス制御ではありません。
- runtime / AI / federation / package 系コマンドは、明示オプションなしに外部送信や
  provider 実行を行いません。
- review-required の出力は判断材料であり、信頼済み記録ではありません。

## グローバル

```bash
chronicle --help
chronicle --version
```

`chronicle --version` はインストール済み package metadata と内部 version を照合し、
`chronicle <version>` を表示します。

## コマンド一覧

| コマンド | 用途 |
|---|---|
| `init` | `.chronicle/` を初期化する |
| `doctor` | read-only 診断を実行する |
| `record` | 任意の Chronicle Event を記録する |
| `show` | Chronicle 概要を表示する |
| `search` | Event / Context / Artifact などを検索する |
| `add-context` | Context record を追加する |
| `artifact` | Artifact と Version を管理する |
| `decision` | 判断記録を追加する |
| `rde` | RDE Diff Record を記録・下書きする |
| `index` | 派生 index を再構築する |
| `boundary` | Context 利用境界 rule を管理する |
| `injection` | Context injection plan を作る |
| `export` | YAML / Markdown / graph-json / HTML export を作る |
| `context` | Context 利用チェックと提案適用を行う |
| `plan` | preview-first operation plan を扱う |
| `summary` | local summary draft job を扱う |
| `runtime` | 明示 runtime / GraphRAG / provider contract を扱う |
| `ai-index` | local placeholder vector / graph index を扱う |
| `ai-boundary` | 外部 AI 利用境界を preview する |
| `package` | controlled integration package を扱う |
| `audit` | local audit event を記録・確認する |
| `lifecycle` | advisory lifecycle marker を記録・確認する |
| `graph` | graph-json 派生 export を検査する |
| `review` | append-only review workflow を扱う |
| `object` | explicit Chronicle object を記録・確認する |
| `reaction` | Chronicle object への意味的 reaction を記録・確認する |
| `federation` | federation package / message を preview-first に扱う |
| `trust` | node profile と trust relation を扱う |
| `ui` | local foreground UI を起動する |
| `ui-smoke` | local UI の read-only smoke check を実行する |

## 初期化・診断

```bash
chronicle init --title "Project Title"
chronicle doctor
chronicle doctor --json
chronicle show
chronicle show --json
```

`init` は `.chronicle/`, `chronicle.jsonl`, `metadata.yaml` を作成します。
`doctor` は read-only で storage, metadata, known event type, index, artifact file,
injection plan, export 生成可否などを確認します。index が欠損していても自動 rebuild
はせず、必要に応じて `chronicle index rebuild` を促します。

Exit code:

| doctor status | exit code |
|---|---|
| `ok` | 0 |
| `warning` | 0 |
| `error` | non-zero |

## Event と Context

```bash
chronicle record --type user_input --actor user --summary "Initial request"
chronicle record --type assistant_output --actor assistant --summary "Draft created" --source-tool chatgpt

chronicle add-context \
  --title "Private Task Context" \
  --source-type conversation \
  --scope task \
  --visibility private \
  --summary "Only for this task"

chronicle search "keyword"
chronicle search "keyword" --json
```

`add-context --scope` は `global`, `project`, `session`, `task`, `artifact`,
`temporary`, `unknown` を受け付けます。`--visibility` は `public`, `private`,
`sensitive`, `unknown` です。

## Artifact

```bash
chronicle artifact create --title "Spec" --type specification --file docs/spec.md --visibility private
chronicle artifact update --artifact art_xxx --file docs/spec.md --summary "Update spec"
chronicle artifact history --artifact art_xxx
chronicle artifact history --artifact art_xxx --json
chronicle artifact list
chronicle artifact list --json
```

| サブコマンド | 用途 |
|---|---|
| `create` | Artifact と初期 Version を作成する |
| `update` | 新しい Version を作成する |
| `history` | Artifact の Version 履歴を表示する |
| `list` | Artifact 一覧を表示する |
| `propose-update` | Artifact 更新 proposal event を作る |
| `apply-proposal` | 承認済み proposal を適用する |

```bash
chronicle artifact propose-update --artifact art_xxx --summary "Proposal" --content "proposed body"
chronicle artifact apply-proposal --event evt_xxx
```

`artifact update` は `--file` が必要です。proposal apply は承認済み proposal event のみ
受け付け、同じ proposal の二重 apply を拒否します。

## Decision と RDE

```bash
chronicle decision record \
  --artifact art_xxx \
  --type accepted \
  --reason "Adopt as v0.3" \
  --alternative "Option B" \
  --notes "Revisit after v0.4"

chronicle rde record --artifact art_xxx --from ver_aaa --to ver_bbb --summary "Meaning shift" \
  --preserved "Original intent" \
  --transformed "Expanded details" \
  --supplemented "New examples" \
  --unresolved "Terminology" \
  --deviation-risk "Scope creep" \
  --next-update-policy "Quarterly review"

chronicle rde draft --artifact art_xxx --from ver_aaa --to ver_bbb --summary "Draft RDE"
```

RDE Diff Record は意味変化の構造化記録であり、正しさの証明ではありません。6 sections
(`preserved`, `transformed`, `supplemented`, `unresolved`, `deviation_risks`,
`next_update_policy`) は空の場合 `(none)` として表示されます。

## Index と Boundary

```bash
chronicle index rebuild

chronicle boundary add \
  --type warn \
  --field visibility \
  --operator equals \
  --value sensitive \
  --reason "Sensitive context should be reviewed"

chronicle boundary list
chronicle boundary list --json
chronicle boundary check --context ctx_xxx
chronicle boundary check --context ctx_xxx --json
```

Boundary rule は context 利用の助言的分類です。アクセス制御や強制削除ではありません。

| option | values |
|---|---|
| `--type` | `include`, `exclude`, `warn` |
| `--field` | `scope`, `visibility`, `source_type`, `source_tool`, `source_session`, `source_model`, `tag` |
| `--operator` | `equals`, `not_equals`, `in`, `contains` |

## Injection Plan

```bash
chronicle injection plan --task "Draft release notes"
chronicle injection plan --task "Draft release notes" --record
chronicle injection plan --task "Draft release notes" --record --json
```

`injection plan` は Boundary rule に基づき Context を `selected`, `warned`, `excluded`
へ分類する dry-run です。LLM への自動注入は行いません。`--record` を指定した場合のみ
`injection_plan_recorded` Event として保存します。

## Export

```bash
chronicle export --format yaml
chronicle export --format markdown -o output.md
chronicle export --format graph-json -o graph.json
chronicle export --format html -o chronicle-dashboard.html

chronicle export profile --format yaml --profile public-review
chronicle export profile --format yaml --profile restricted-summary --output export.yaml --json
chronicle export profile --format html --profile public-review --output dashboard.html
```

| format | 契約レベル | 用途 |
|---|---|---|
| `yaml` | Semi-public | 機械可読 snapshot。`export_manifest` を含む |
| `markdown` | Human-facing | 人間向け report |
| `graph-json` | Semi-public / derived | GraphRAG 接続準備用 node / edge export |
| `html` | Human-facing | 静的 read-only dashboard |

Security-aware export profile は派生 export です。公開承認、アクセス制御、暗号学的証明では
ありません。

## Context

```bash
chronicle context check --target local --purpose "internal review"
chronicle context check --target external --purpose "draft public summary" --json

chronicle context classification missing
chronicle context classification show --context ctx_xxx
chronicle context classification set --context ctx_xxx --layer internal --sensitivity internal

chronicle context propose-update --context ctx_xxx --summary "Proposal" --body "Updated summary"
chronicle context apply-proposal --event evt_xxx
```

`context check` は model-facing context として使う前の dry-run check です。外部モデル API は
呼びません。`context apply-proposal` は承認済み proposal を append-only の新しい Context
snapshot として適用します。

## Operation Plan

```bash
chronicle plan artifact-update-preview \
  --artifact art_xxx \
  --summary "Plan update" \
  --content "Replacement content" \
  --source-ref evt_xxx \
  --record

chronicle plan artifact-update-proposal --artifact art_xxx --summary "Proposal" --content "Body"
chronicle plan list
chronicle plan list --json
chronicle plan show --id plan_xxx
```

Operation plan は preview-first です。preview, proposal, review, apply は分離されます。

## Summary

```bash
chronicle summary create --title "Draft summary" --text "Summary body" --source event:evt_xxx
chronicle summary list
chronicle summary show --id sum_xxx

chronicle summary run --id sum_xxx
chronicle summary run --id sum_xxx --operation rewrite --param tone=concise
chronicle summary run --id sum_xxx --execute-configured-provider --record

chronicle summary invoke-plan --id sum_xxx
chronicle summary invoke-plan --id sum_xxx --operation summarize --record --json
```

`summary create` は AI runtime を呼ばない local draft job を作ります。`summary run` は明示
runtime boundary 経由で draft を再実行します。configured provider 実行には
`--execute-configured-provider` が必要です。

## Runtime

```bash
chronicle runtime status
chronicle runtime status --json

chronicle runtime graphrag-status
chronicle runtime graphrag-rebuild
chronicle runtime ask "What changed in the release plan?"

chronicle runtime summarize --text "Source text" --max-sentences 2
chronicle runtime summarize --text "Source text" --draft-title "Runtime Draft" --record

chronicle runtime retrieve-plan --query "release context" --limit 3 --record --json

chronicle runtime invoke-plan --text "Source text" --operation summarize --record
chronicle runtime execute-plan --event evt_xxx --execute-configured-provider --record

chronicle runtime invoke --text "Source text" --operation rewrite --execute-configured-provider
chronicle runtime invoke --text "Source text" --operation rewrite --source event:evt_xxx --param tone=concise
```

Runtime は explicit local runtime boundary です。configured provider execution は
`--execute-configured-provider` が無い限り fail closed します。生成物は review-required の
派生 output です。

### Runtime Config

```bash
chronicle runtime config show
chronicle runtime config show --json
chronicle runtime config set-local --model local-placeholder
chronicle runtime config set-http \
  --base-url https://runtime.example.invalid/v1 \
  --model manual-http-model \
  --api-key-env OPENAI_API_KEY \
  --allow-network
chronicle runtime config disable
```

`set-http` は provider contract を `.chronicle/runtime.yaml` に保存します。その場では
network call を行いません。外部 context を渡す運用では `--allow-external-context` も必要です。

### Runtime Capability

```bash
chronicle runtime capability list
chronicle runtime capability list --json
chronicle runtime capability show --id cap_xxx
```

Static capability registry の read-only inspection です。

## AI Index

```bash
chronicle ai-index status
chronicle ai-index status --json

chronicle ai-index vector add --record evt_xxx --text "local placeholder text" --type event
chronicle ai-index vector add --record evt_xxx --text "local placeholder text" --metadata source=manual --json
chronicle ai-index vector search --query "placeholder" --limit 5

chronicle ai-index graph add-node --id evt_xxx --label event --property title="Example"
chronicle ai-index graph add-edge --source evt_xxx --target ctx_xxx --relation references
chronicle ai-index graph neighbors --id evt_xxx --json
```

`ai-index` は local file-backed placeholder surface です。LLM、embedding provider、vector DB、
graph DB、GraphRAG runtime、external service は呼びません。

## AI Boundary

```bash
chronicle ai-boundary preview \
  --task "External model handoff" \
  --context ctx_xxx \
  --model external:placeholder \
  --prompt "Prompt text" \
  --no-persist-prompt \
  --record \
  --json
```

外部 AI 利用の保存方針と redaction candidates を preview します。外部送信は行いません。
`--persist-prompt`, `--persist-response`, `--persist-model-id`, `--persist-runtime`,
`--persist-timestamp` で保存粒度を制御します。

## Package

```bash
chronicle package context --purpose "Internal review" --target local
chronicle package context --purpose "External review" --target external --persist
chronicle package review --purpose "Review package" --target external
chronicle package review --package pkg_xxx --json

chronicle package query-engine-adapter --query "release planning context" -o adapter-skeleton.json
chronicle package query-engine-bundle --query "release planning context" --output-dir handoff-bundle
chronicle package query-engine-trial-record \
  --bundle-dir handoff-bundle \
  --reviewer "operator" \
  --consumer "downstream-demo" \
  --sufficient
chronicle package query-engine-trial-list --json
chronicle package query-engine-trial-show --event evt_xxx --json

chronicle package list
chronicle package show --package pkg_xxx
chronicle package records --package pkg_xxx --json
```

Package は transport contract であり、外部送信、許可付与、アクセス制御ではありません。
query-engine 系コマンドは downstream handoff bundle / skeleton をローカルに作るだけで、
import 実行や hosted runtime は含みません。

## Audit と Lifecycle

```bash
chronicle audit record --operation export --actor user --purpose "public review" --summary "Exported dashboard"
chronicle audit list
chronicle audit show --id aud_xxx --json

chronicle lifecycle record --target ctx_xxx --target-kind context --action seal --reason "Superseded"
chronicle lifecycle list
chronicle lifecycle show --id life_xxx --json
```

Audit event は traceability metadata であり、enforcement や certification ではありません。
Lifecycle marker は downstream workflow 向けの advisory metadata で、対象 record を直接変更しません。

## Graph

```bash
chronicle graph summary
chronicle graph summary --json
chronicle graph nodes
chronicle graph nodes --type context --json
chronicle graph edges --json
chronicle graph retrieve --query "release planning" --limit 5
```

Read-only graph export inspection です。`graph-json` は GraphRAG 接続準備用の派生 view であり、
GraphRAG engine ではありません。

## Review

```bash
chronicle review queue
chronicle review queue --include-resolved
chronicle review queue --json

chronicle review approve --event evt_xxx --reviewer alice
chronicle review approve --event evt_xxx --reviewer alice --reviewer-kind local_operator --session terminal-1
chronicle review reject --event evt_xxx --reviewer alice --note "reason"
chronicle review request-changes --event evt_xxx --reviewer alice --note "revise section 2"
```

Review workflow は append-only です。target event 自体は直接変更せず、reviewer event と
`review_decision` audit event を追加します。`request-changes` は pending のまま残ります。

## Object と Reaction

```bash
chronicle object record --type hypothesis --summary "Core hypothesis" --artifact art_xxx --visibility private
chronicle object list
chronicle object list --type hypothesis --json
chronicle object show --id obj_xxx

chronicle reaction record --type understood --target-object obj_xxx --summary "Reviewed and understood"
chronicle reaction record --type reference --target-object obj_xxx --source-object obj_yyy --metadata weight=high
chronicle reaction list
chronicle reaction show --id react_xxx --json
```

Object は artifact/context/decision/RDE などを横断する明示的な意味単位です。Reaction は
object 間や既存 record への意味的関係を append-only に記録します。

## Federation

```bash
chronicle federation boundary check --purpose "Share context" --target-node node:partner

chronicle federation package create \
  --purpose "Share context" \
  --target-node node:partner \
  --output-dir federation-bundle \
  --context ctx_xxx \
  --visibility federated
chronicle federation package inspect --package-dir federation-bundle
chronicle federation package verify --package-dir federation-bundle
chronicle federation package preview --package-dir federation-bundle
chronicle federation package import-preview --package-dir federation-bundle --json

chronicle federation consent record \
  --target-node node:partner \
  --purpose "Share context" \
  --scope "ctx_xxx" \
  --granted-by "operator"

chronicle federation message create \
  --type grant_context \
  --source-node node:local \
  --target-node node:partner \
  --purpose "Preview handoff" \
  --object-ref ctx_xxx
chronicle federation inbox inspect
chronicle federation inbox show --message msg_xxx --json
chronicle federation outbox inspect
```

Federation は preview-first local bundle / local queue surface です。自動 import、network sync、
primary-record mutation は行いません。

## Trust

```bash
chronicle trust node add --node-id node:partner --subject-id subject:partner --display-name "Partner"
chronicle trust node list --json

chronicle trust assert \
  --target-node node:partner \
  --domain context-sharing \
  --purpose "Review" \
  --level limited \
  --capability read_context
chronicle trust list
chronicle trust withdraw --relation trust_xxx --reason "No longer needed"
```

Trust relation は node / subject / domain / purpose / capability の advisory model です。

## Local UI

```bash
chronicle ui --open
chronicle ui --workspace --open
chronicle ui --host 127.0.0.1 --port 8765 --open
chronicle ui --mutation-capability-flag --open
chronicle ui --mutation-capability-flag --enable-ui-mutation --auth-mode loopback_local --authorization-mode reviewer_declared --open
chronicle ui --json

chronicle ui-smoke
chronicle ui-smoke --json
```

`chronicle ui` は foreground local web UI です。既定は read-only で、daemon / autostart /
hosted service にはなりません。bind host は loopback (`127.0.0.1`, `localhost`, `::1`) のみ
許可されます。

ブラウザでデータ面を使う場合は `--open` を指定します。サーバーは短時間・一回限りの
bootstrap secret を URL fragment として既定ブラウザへ渡し、クライアントは fragment を
直ちに消して同一 origin で session cookie へ交換します。secret は startup metadata、
`--json`、stdout、HTML には含まれません。`--open` なしで表示されたベース URL を手動で
開くと、Chronicle title / root / data / credential を含まない locked shell だけが表示されます。

session cookie は host-only (`Domain` なし)、`HttpOnly`、`SameSite=Strict`、`Path=/` です。
local UI は plain `http://` のため `Secure` と、それを必須とする `__Host-` prefix は使いません。
cookie token と mutation header token は別の credential です。Chronicle-derived GET と
review console は cookie を要求し、
non-bootstrap POST は cookie と exact Origin を要求します。有効な write route はさらに
mutation header token、mutation session id、one-use request id を要求します。すべての HTTP
メソッドは actual port を含む exact Host を検証します。CORS は許可せず、OPTIONS 等の
未対応メソッドは境界検査後に 405 と `Allow: GET, POST` を返します。

`--workspace` は loopback/auth/authz/browser-session 条件をまとめて有効化し、ローカル保存と
GraphRAG 質問の作業面を開きます。write route は fail-closed で、`--enable-ui-mutation` と
`--auth-mode loopback_local --authorization-mode reviewer_declared` が揃う場合にだけ有効です。

これは same-UID process や shared-machine isolation の保証ではありません。`--open` の
fragment-bearing URL は `webbrowser` と OS/browser の opener 経路を通るため、短い露出窓が
残ります。詳細は ADR-0106 と local operator validation guide を参照してください。

`ui-smoke` はサーバーやブラウザを起動せず、local UI の read-only データ面を検証します。

関連 ADR:

- [ADR-0018](adr/0018-local-ui-read-only-navigation-boundary.md)
- [ADR-0019](adr/0019-local-ui-review-semantics-parity-boundary.md)
- [ADR-0022](adr/0022-explicit-local-ui-mutation-enable-flag.md)
- [ADR-0106](adr/0106-browser-ui-session-bootstrap-request-boundary.md)

## 補助 CLI 互換性

以下の補助 CLI は互換目的で維持されています。

```bash
chronicle-context check ...
chronicle-export profile ...
chronicle-package context ...
chronicle-graph summary
```

文書例では primary CLI alias を優先しますが、補助 CLI を削除・非推奨化するものでは
ありません。primary / auxiliary の挙動差分は Observation E2E の観測対象であり、
semantic correctness certification ではありません。

## Local daemon credentials

`chronicle daemon start` generates a private 0600 `.chronicle/daemon.token` file.
`--token-file PATH` selects a new output file; `--session-token` has been removed. Existing files
and symlinks are rejected. Clients read the credential from the file into memory. Startup output
and `--json` never contain its value; `--json` only inspects metadata and issues no credential.
See [Daemon operator runbook](releases/operations/daemon-api-operator-runbook.md) and
[ADR-0107](adr/0107-daemon-private-token-file.md) for shutdown and stale-file recovery.
