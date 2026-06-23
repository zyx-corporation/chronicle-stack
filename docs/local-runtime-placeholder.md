# Local Runtime Placeholder

Chronicle Stack の `runtime` CLI は、explicit local runtime boundary を表す最小 surface です。

現時点の MVP:

- `chronicle runtime status`
- `chronicle runtime summarize`
- `chronicle runtime retrieve-plan`
- `chronicle runtime invoke-plan`
- `chronicle runtime config`

## Boundary

- No LLM invoked
- No external runtime invoked
- No background worker
- Explicit manual invocation only
- Generated output requires review
- Primary Chronicle records remain authoritative

## Retrieval dry-run

`chronicle runtime retrieve-plan` は、query に対して local surface をどう組み合わせるかを表示する dry-run です。

含まれる候補:

- placeholder vector index hit
- graph export hit
- Chronicle search hit

これは GraphRAG engine ではありません。

`--record` を指定した場合のみ、その retrieval dry-run plan を review 前提の `assistant_output` event として Chronicle に残します。

## Read-only UI visibility

runtime 記録は local UI の read-only endpoint から確認できます。

- `/api/runtime-records`
- `/api/runtime-records/<event_id>`
- `/api/runtime-config`
- `/api/summary-jobs`
- `/api/summary-jobs/<summary_job_id>`

retrieval plan の detail view では、downstream runtime へ渡す前の handoff contract を read-only で確認できます。

- hit count summary
- referenced record IDs
- recommended next CLI commands
- package review required boundary note
- package handoff preview for eligible `ctx_*` records
- derived package review snapshot before persistence or sharing

この handoff 表示は GraphRAG runtime を実装するものではなく、どの local surface が候補になっているかを operator が確認するための dry-run です。

`/api/runtime-config` では、stored provider contract を read-only で確認できます。

- source (`implicit-default` / `stored`)
- provider kind / provider name / model name
- allow-network / allow-external-context intent
- boundary warnings

この表示も configuration only の境界を可視化するものであり、runtime 実行や network session を意味しません。

## Persistence

`chronicle runtime summarize` は、デフォルトでは非永続です。

`--record` を指定した場合のみ、`assistant_output` event として Chronicle に記録します。

`--draft-title` を指定した場合は、同じ explicit manual invocation の結果を pending-review の summary job / draft artifact としても保存できます。

この draft persistence でも:

- no external runtime invoked
- external_call_made = false
- invocation_mode = explicit-manual
- generated output remains draft until reviewed

`--record` / `--draft-title` のどちらを使っても、記録された生成出力は正本ではなく、review 前提の補助出力です。

## Provider configuration

`chronicle runtime config` は provider contract を `.chronicle/runtime.yaml` に保存する surface です。

利用例:

- `chronicle runtime config show`
- `chronicle runtime config set-local --model local-placeholder`
- `chronicle runtime config set-http --base-url https://runtime.example.invalid/v1 --model manual-http-model --api-key-env OPENAI_API_KEY --allow-network`
- `chronicle runtime config disable`

この設定 surface でも:

- configuration alone does not invoke any model or external runtime
- `set-http` も stored contract であり active network session ではない
- `runtime status` は actual local placeholder execution と configured provider contract を区別する
- generated output remains review-oriented derived output after an explicit/manual invocation
- Primary Chronicle records remain authoritative

## Invocation dry-run

`chronicle runtime invoke-plan` は、stored provider contract を explicit/manual invocation path に接続する dry-run です。

利用例:

- `chronicle runtime invoke-plan --text "Source text"`
- `chronicle runtime invoke-plan --text "Source text" --record`

この surface でも:

- no provider execution
- no external call performed
- `invocation_ready` は contract boundary 上の ready / blocked を示すだけ
- HTTP provider では `allow_network` が false の場合に block される
- `--source` / `--prompt` / `--param key=value` を含む execution request contract を plan と一緒に保持できる
- `--record` 指定時のみ runtime invocation plan を review-oriented record として残せる

runtime invocation plan を記録した場合は、local UI の `/api/runtime-records/<event_id>` detail から read-only で確認できます。

その detail では request preview に加えて execution request contract も read-only で見え、`downstream_commands` に含まれる `chronicle runtime execute-plan ...` などの CLI をその場で copy できます。

runtime execution record では、navigation notice から生成済み summary job / artifact に直接 jump できます。

overview の Runtime Records / Summary Jobs panel でも、provider response がある場合は最新 detail へ直接 jump できます。

同様に Auth Boundary / Triage panel でも、response-backed review detail があれば最新 review detail へ直接 jump できます。

`chronicle runtime execute-plan --event evt_xxx --execute-configured-provider` は、その recorded invocation plan に含まれる execution request contract を使って explicit/manual 再実行します。ここでも hidden execution は起きず、configured provider への crossing は毎回明示 flag が必要です。

summary job 由来の invocation dry-run では、runtime record detail から対応する `/api/summary-jobs/<summary_job_id>` へ辿れます。

`/api/summary-jobs` / `/api/summary-jobs/<summary_job_id>` では次を read-only で確認できます。

- summary title / status
- derived review capability / package readiness / CLI parity
- source-ref count
- runtime provider kind
- related Chronicle record links
- suggested follow-up CLI family

一覧 view では local-only filter / sort で review capability や package readiness の派生状態を絞り込めます。

overview でも summary job status / review capability / package readiness / provider kind の派生集計を read-only で確認できます。

summary job 一覧からは matching review target detail や review queue slice へ jump できます。

overview の auth / identity panel からも auth warning, authorization warning, reviewer identity warning, boundary-aligned slice へ read-only jump できます。

review detail / summary detail では、Phase H readiness をまとめた auth readiness notice から blocker と next step を read-only で確認できます。

review detail の `Action Preview` では disabled approve / reject / request-changes buttons に加えて、fail-closed な `POST /api/review-actions/<event_id>/<action>` route preview を read-only で試せます。返るのは常に blocked response と CLI fallback contract だけで、mutation は有効化されません。

review queue 一覧でも auth readiness badge を通じて advisory / boundary-aligned slice を read-only で辿れます。また preview 列から blocked route preview を read-only で試せるため、detail を開かずに CLI fallback contract を確認できます。

summary job 一覧でも matching review target 由来の auth readiness badge を read-only で確認できます。さらに identity/session 由来の advisory/aligned 状態も read-only で辿れます。また preview 列から同じ blocked route preview を read-only で試せるため、summary row からも CLI fallback contract を辿れます。

overview の summary jobs panel でも auth readiness の派生集計を read-only で確認できます。

runtime record 一覧 / detail でも matching review target 由来の auth readiness を read-only で確認できます。

overview の runtime records panel でも auth readiness の派生集計を read-only で確認できます。

`chronicle ui-smoke` でも overview/runtime/review/summary の auth readiness 派生面を read-only smoke check として確認します。

## Summary job re-run

`chronicle summary run --id sum_xxx` は、既存の summary job を explicit runtime boundary に通し直し、`summarize` では短縮結果を、他の operation では configured-provider runtime output を新しい pending-review draft として保存します。

この再実行でも:

- no external runtime invoked
- source refs are carried forward
- prompt provenance is preserved
- generated_by = runtime_manual
- Primary Chronicle records remain authoritative

configured provider を explicit に使う場合は:

- `--execute-configured-provider` が必須
- `--operation rewrite` など summarize 以外の operation も使える
- `--record` で review-oriented `assistant_output` event としても残せる
- `--artifact-title` で draft artifact としても残せる
- `--param key=value` で operation-specific parameter を repeatable に渡せる

## Summary job invocation dry-run

`chronicle summary invoke-plan --id sum_xxx` は、既存 summary draft を configured provider contract に接続する dry-run です。

この surface でも:

- no provider execution
- no external call performed
- summary job ID / title / prompt / source-ref count を request preview に含める
- recorded plan には対応する execution request contract も残る
- `--record` 指定時のみ review-oriented runtime invocation plan record として残せる
