# Local Runtime Placeholder

Chronicle Stack の `runtime` CLI は、explicit local runtime boundary を表す最小 surface です。

現時点の MVP:

- `chronicle runtime status`
- `chronicle runtime summarize`
- `chronicle runtime retrieve-plan`

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

その場合も、記録された生成出力は正本ではなく、review 前提の補助出力です。
