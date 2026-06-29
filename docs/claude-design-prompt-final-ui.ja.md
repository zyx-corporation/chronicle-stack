# Chronicle Stack 最終 UI 用 Claude Design プロンプト

以下のプロンプトを Claude Design に渡してください。

---

あなたは Chronicle Stack の最終到達形 UI を設計するデザイナーです。

まず添付された仕様書を読み、それに厳密に従ってください。

プロジェクトの性格:

- Chronicle Stack は、AI-assisted work を再構成可能にする local-first システムです
- context、artifact、decision、diff、provenance、audit、review、trust、federation state を記録します
- hosted SaaS dashboard でも、social feed でも、generic CRUD admin app でもありません
- 現在の UI は local web-based read model ですが、このタスクは現状実装の単なる restyle ではなく、最終プロダクト UI の設計です

必ず守るべき hard boundary:

- local-first
- `.chronicle/chronicle.jsonl` が primary record であり続ける
- derived view は derived であることが視覚的に分かる必要がある
- direct mutation より proposal/review/apply を優先する
- federation は preview-first、inspect-first、consent-aware である
- auto-import、hidden sync、hosted GraphRAG runtime、graph DB / vector DB 方向への product drift を起こさない

あなたのタスク:

将来、local web UI にも desktop shell 例えば Tauri にも実装できる最終 UI design concept を提案してください。
ただし、現在の HTML 構造に縛られてはいけません。

出力してほしい内容:

1. プロダクト全体の concise な design thesis
2. information architecture
3. top-level navigation model
4. visual direction と design language
5. 主要 screen の詳細説明:
   - Home / Overview
   - Chronicle Objects
   - Context and Artifact Workbench
   - Review Workspace
   - Audit / Boundary / Lifecycle Workspace
   - Federation Workspace
   - Trust Workspace
   - Runtime / Retrieval Workspace
6. proposal -> review -> apply flow の明確な concept
7. key component pattern
8. empty / warning / blocked / preview-only / ready state の考え方
9. provenance、auditability、安全な action boundary をこの design がどう表現するかの rationale

出力スタイル要件:

- generic ではなく、具体的で product-designer 的に書くこと
- bland な admin-dashboard language を避けること
- social timeline 的な案を出さないこと
- engagement 最適化を目的にしないこと
- operator trust、reconstruction speed、cognitive clarity を最適化すること
- calm、exact、evidence-oriented な UI として描写すること
- laptop / desktop-first design を優先すること

デザインに必ず反映すべき Chronicle Stack の真実:

- landing experience は raw chronology よりも、current question、pending review、meaningful diff、actionable boundary state を前面に出すべき
- review は小さな modal ではなく、first-class workflow である
- federation は controlled handoff の inspection desk のように感じられるべきであり、軽い send-message UI にしてはいけない
- trust と consent は、それが影響する workflow の近くに見えるべき
- AI/runtime surface は、magic authority ではなく bounded assistance と derived evidence として見えるべき

回答の構成は次にしてください:

1. Design Thesis
2. Product Principles
3. Information Architecture
4. Navigation Model
5. Screen-by-Screen Design
6. Component System
7. State Design
8. Why This Fits Chronicle Stack

必要なら次を含めてかまいません:

- wireframe 風の textual layout description
- component naming suggestion
- visual motif
- typography direction
- color system direction

してはいけないこと:

- cloud collaboration を前提にする
- free-form document editing を core interaction の default とみなす
- public web deployment を前提にする
- network federation がすでに有効だとみなす
- provenance、review、boundary 情報を hidden secondary panel に押し込む

出力は、Chronicle Stack のための serious な final-product UI concept proposal のように読めるものにしてください。

---
