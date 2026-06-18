# Local AI Index Placeholder

Chronicle Stack の `ai-index` は、local-first な adapter contract と file-backed placeholder index を提供する補助面です。

対象:

- `chronicle ai-index status`
- `chronicle ai-index vector add`
- `chronicle ai-index vector search`
- `chronicle ai-index graph add-node`
- `chronicle ai-index graph add-edge`
- `chronicle ai-index graph neighbors`
- read-only local UI endpoint

保存先:

- `.chronicle/ai_indexes/vector_index.json`
- `.chronicle/ai_indexes/graph_index.json`

境界:

- No LLM invoked
- No embedding provider invoked
- No vector DB invoked
- No graph DB invoked
- No GraphRAG runtime invoked
- No external services
- Indexes are local file-backed placeholder derived surfaces
- Search result is assistive, not correctness proof
- Primary Chronicle records remain authoritative

vector search は本格 embedding ではなく、token overlap と substring を用いた placeholder scoring です。

local UI では次の read-only endpoint で可視化できます:

- `/api/ai-index-status`
- `/api/ai-index-vector`
- `/api/ai-index-graph-nodes`
- `/api/ai-index-graph-edges`

これらは GUI mutation を伴いません。Chronicle の一次記録は引き続き `.chronicle/chronicle.jsonl` です。
