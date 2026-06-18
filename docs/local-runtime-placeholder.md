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

## Persistence

`chronicle runtime summarize` は、デフォルトでは非永続です。

`--record` を指定した場合のみ、`assistant_output` event として Chronicle に記録します。

その場合も、記録された生成出力は正本ではなく、review 前提の補助出力です。
