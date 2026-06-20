# Local Runtime Placeholder

Chronicle Stack の `runtime` CLI は、explicit local runtime boundary を表す最小 surface です。

現時点の MVP:

- `chronicle runtime status`
- `chronicle runtime summarize`
- `chronicle runtime retrieve-plan`
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

retrieval plan の detail view では、downstream runtime へ渡す前の handoff contract を read-only で確認できます。

- hit count summary
- referenced record IDs
- recommended next CLI commands
- package review required boundary note
- package handoff preview for eligible `ctx_*` records
- derived package review snapshot before persistence or sharing

この handoff 表示は GraphRAG runtime を実装するものではなく、どの local surface が候補になっているかを operator が確認するための dry-run です。

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

## Summary job re-run

`chronicle summary run --id sum_xxx` は、既存の summary job を explicit manual runtime boundary に通し直し、短縮結果を新しい pending-review draft として保存します。

この再実行でも:

- no external runtime invoked
- source refs are carried forward
- prompt provenance is preserved
- generated_by = runtime_manual
- Primary Chronicle records remain authoritative
