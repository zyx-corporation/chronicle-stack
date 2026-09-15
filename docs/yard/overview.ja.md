# Chronicle Yard Overview

Status: Active
Date: 2026-08-08
Scope: Chronicle Yard の概要、製品群の位置づけ、境界ルール
Related: `README.md`, `../product-overview.md`, `../future/chronicle-yard-naming-note.md`,
`../roadmaps/chronicle-yard-product-family-milestones.md`

## 1. Chronicle Yard とは

Chronicle Yard は、Chronicle Stack とその周辺製品を束ねる製品群の総称です。

AIとの共同作業で生まれる問い、判断、根拠、成果物、差分、出所、境界ルールを、
後から再構成できる形で保管し、必要な場面で確認、受け渡し、検索、検証、共有できる
ようにするための「場」を表します。

短く言えば:

```text
Chronicle Yard は、AI時代の仕事の来歴を、ローカル優先で記録し、
人間とエージェントが再利用できるよう整える製品群である。
```

この名前は、現在の実装名である Chronicle Stack を置き換えるものではありません。
Chronicle Stack は引き続き、クロニクル記録を保管する中核機構、CLI、パッケージ、
リポジトリ名として扱います。

## 2. 中心価値

Chronicle Yard が守る中心価値は **再構成可能性** です。

最終成果物だけではなく、次の情報を辿れるようにします。

- どの文脈から作られたのか
- どの指示、根拠、出所が影響したのか
- どの案が採用、棄却、保留されたのか
- どの差分が意味を変えたのか
- どの境界や注意事項が残っているのか
- 人間がどこで判断したのか

Chronicle Yard は、AIにすべての記憶を預けるための名前ではありません。人間側が
文脈、判断、出所、境界を保持し、必要に応じて選び直せるようにするための製品群です。

## 3. 製品群の位置づけ

| 名称 | 役割 | 現在の位置づけ |
|---|---|---|
| Chronicle Yard | 製品群の傘概念 | Stack と関連製品を束ねる名称レイヤー |
| Chronicle Stack | クロニクル保管機構 | 現在のリポジトリ、CLI、JSONL一次記録、エクスポート |
| Chronicle API | 接続インターフェース | 将来のローカルAPI契約面 |
| Chronicle Cloud | サービス層 | 将来の同期、共有、監査、権限、バックアップ構想 |
| CSG-RAG | Governed GraphRAG runtime | Stack core 外のローカル検索・回答・review-store実行面 |
| chronicle-external-query | 下流 query / evaluation workspace | handoff bundle を消費する検索・検証・評価面 |
| Kazane / agent runtimes | 実行レイヤー連携 | Chronicle context を使って動くが、Chronicle を所有しない |

重要なのは、Chronicle Yard が単一の巨大アプリや monorepo を意味しないことです。
各製品は責務を分け、明示的な契約、handoff bundle、API、verifier artifact を通じて
接続します。

## 4. 利用者から見た流れ

Chronicle Yard の利用体験は、次の流れとして説明できます。

1. 記録する
   Chronicle Stack が、文脈、イベント、成果物、判断、RDE Diff Record、境界情報を
   local-first なクロニクルとして保存します。

2. 整える
   出所、可視性、ライフサイクル、採用・棄却・保留、意味変化を確認できる形にします。

3. 受け渡す
   export、graph export、integration package、query-engine handoff bundle、federation
   package など、明示的な受け渡し面を作ります。

4. 問う、検証する
   CSG-RAG や chronicle-external-query が、Chronicle由来の bundle を消費し、検索、
   GraphRAG、runtime evaluation、verifier report を担います。

5. 共有、同期、連携する
   将来の Chronicle API、Chronicle Cloud、Kazane / agent runtime、federation surface が、
   権限、監査、同期、共同利用、外部連携を扱います。

この流れの中で、一次記録の権威は Chronicle Stack の `.chronicle/chronicle.jsonl` に
残ります。派生index、GraphRAG projection、query結果、verifier出力、cloud上の表示は、
正本そのものではなく、明示された契約やreview artifactとして扱います。

## 5. 境界ルール

- Chronicle Yard は、現時点でリリース済みのhosted suiteではありません。
- Chronicle Yard は、Chronicle Stack の正式改名ではありません。
- Chronicle Stack は、クラウド型AIメモリではありません。
- Chronicle Cloud は、将来のサービス層であり、Chronicle の所有者ではありません。
- CSG-RAG と chronicle-external-query の runtime / query 責務を Stack core に戻しません。
- 下流製品は、Stack の private state や derived index を安定契約として扱いません。
- エージェントや外部製品からの write-back は、明示的な契約とreviewを通じて扱います。
- 公開文言では、現在実装済みのもの、計画中のもの、構想段階のものを分けて書きます。

## 6. 現在の状態

Chronicle Yard は、製品群を整理するための名称・責務・契約レイヤーとして文書化中です。

現在のマイルストーン状態:

- CY-0: Yard vocabulary and product boundary は、現在の境界切りとして完了。
- CY-1: Stack preservation baseline and handoff contracts は進行中。
- CY-2: Downstream query and GraphRAG product mapping は進行中。
- CY-3: Chronicle API contract readiness は初期スケルトン段階で進行中。
- CY-4以降: runtime interoperability、operator journey、Cloud authority、federation
  governance は今後の整理対象。

## 7. 読む順番

Chronicle Yard の概要から設計境界まで確認する場合は、次の順番で読むとよいです。

1. この概要
2. [Chronicle Yard Product Map](README.md)
3. [Yard Responsibility Matrix](responsibility-matrix.md)
4. [Stack Handoff Contract Review](handoff-contracts.md)
5. [Chronicle Yard Naming Note](../future/chronicle-yard-naming-note.md)
6. [Chronicle Yard Product Family Milestones](../roadmaps/chronicle-yard-product-family-milestones.md)
