# External Query Runtime Repo Design for `zyx-corporation/chronicle-external-query`

この文書は、Chronicle Stack の外部で並行実装する GraphRAG / query runtime repo
`zyx-corporation/chronicle-external-query` の設計起点を定義します。

## 目的

- Chronicle Stack の primary record 境界を壊さずに、下流の GraphRAG / query runtime 実装を並行開発できるようにする
- Chronicle Stack が既に出力できる handoff contract / graph export / trial record を、そのまま外部 runtime repo の入力契約として使えるようにする
- 実行基盤の責務を Chronicle Stack core から切り離したまま、検証ループを前に進める

## 前提境界

- Chronicle Stack は `.chronicle/chronicle.jsonl` を source of truth とする
- Chronicle Stack は hosted query engine, graph runtime, vector runtime を持たない
- graph export, handoff bundle, trial summaries はすべて derived / read-only である
- 外部 repo は Chronicle Stack の downstream derived consumer であり、Chronicle primary records を上書きしない

## 対象 repo

- repository: `zyx-corporation/chronicle-external-query`
- role: Chronicle Stack の downstream derived consumer
- source boundary: Chronicle primary records を上書きせず、Chronicle から出力された derived contract を入力に使う

## 外部 repo の責務

- graph export / handoff bundle の読込
- vector / graph / hybrid retrieval の実行責務
- ranking / answer synthesis / serving の実行責務
- 外部依存（graph DB, vector DB, embeddings, hosted query runtime）の吸収
- 実験結果の整理と、必要に応じた trial 結果の Chronicle への書き戻し補助

## Chronicle Stack 側の責務

- primary record の保持
- deterministic graph export の生成
- query-engine handoff contract の生成
- import validation の生成
- handoff bundle / acceptance checklist / trial report template の生成
- trial record / escalation cue / issue-template scaffold の read-only 表示

## 入力契約

外部 repo は最低限、以下を読める前提で開始する。

- `.chronicle/chronicle.jsonl`
- `graph.json`
- `query_engine_handoff.json`
- `bundle_manifest.json`

必要に応じて以下も参照する。

- `query_engine_adapter_skeleton.json`
- `ACCEPTANCE_CHECKLIST.md`
- `TRIAL_REPORT_TEMPLATE.md`

## 推奨 repo 構成

```text
chronicle-external-query/
  README.md
  docs/
    architecture.md
    runtime-boundary.md
    evaluation.md
  contracts/
    chronicle/
      query_engine_handoff.schema.json
      graph_export_contract.md
  src/
    ingest/
      handoff_loader.py
      graph_loader.py
      chronicle_loader.py
    retrieval/
      graph_retriever.py
      vector_retriever.py
      hybrid_retriever.py
    runtime/
      answer_runtime.py
      ranking.py
      prompts.py
    evaluation/
      trial_runner.py
      result_serializer.py
  tests/
    contract/
    integration/
    evaluation/
```

## 推奨実装順

### 1. Contract ingest

- `query_engine_handoff.json` を strict に parse
- `graph.json` の contract version を確認
- `bundle_manifest.json` から required file set を確認
- import validation を structural gate として扱う

出口:

- bundle が parse できる
- contract mismatch を fail-fast で返せる

### 2. Local retrieval read path

- graph export のみを使う local graph retrieval を外部 repo 側でも再現
- 必要なら vector store を追加して hybrid retrieval に拡張
- retrieval provenance を response metadata に残す

出口:

- query ごとの referenced records / matched nodes / retrieval trace が見える

### 3. Query runtime

- answer synthesis を外部 runtime で実装
- prompt / ranking / retrieval composition を Chronicle core の外で管理
- hosted runtime / external model API / serving をここで閉じ込める

出口:

- Chronicle 側の handoff contract を入力にして answer generation が動く

### 4. Evaluation loop

- bundle 単位で trial を実行
- insufficient / missing behavior を structured に残す
- Chronicle に書き戻す場合は trial-record command の契約に合わせる

出口:

- repeated insufficiency, repeated consumers, missing behavior が Chronicle UI 側の escalation cue と一致する

### 5. Operational packaging

- local dev 実行
- CI contract check
- optional deployment surface

出口:

- external runtime repo 単独で build / test / serve の責務を持つ

## 最小 milestone

### Milestone A: Parse-only consumer

- handoff bundle parse
- contract version check
- graph export load

### Milestone B: Local retrieval runtime

- graph retrieval
- answer trace
- evaluation output

### Milestone C: Full query runtime

- hybrid retrieval
- synthesis
- ranking
- serving

## Chronicle との接続点

- `chronicle runtime retrieve-plan --query ... --json`
- `chronicle package query-engine-bundle --query ... --output-dir ...`
- `chronicle package query-engine-trial-record --bundle-dir ...`
- `chronicle package query-engine-trial-list --json`
- `chronicle package query-engine-trial-show --event ... --json`

## 非目的

- Chronicle Stack core へ hosted query runtime を戻すこと
- Chronicle Stack core に graph DB / vector DB を埋め込むこと
- Chronicle Stack から直接 issue 作成や downstream import を行うこと

## 実装開始の判断

外部 repo の並行実装は、すでに開始可能とみなしてよい。
理由は以下。

- handoff contract がある
- import validation がある
- bundle と adapter skeleton がある
- trial report と escalation cue がある

Chronicle 側の issue-template scaffold は local-only presentation にとどめ、Chronicle core の export contract には含めない。
外部 repo 側で同等の issue 起票補助を採用する場合も、Chronicle からの直接 export や issue 作成は前提にしない。

## 次の判断点

- external repo の最初の runtime を graph-only にするか、最初から hybrid retrieval にするか
- deployment を repo 初期スコープに含めるか
