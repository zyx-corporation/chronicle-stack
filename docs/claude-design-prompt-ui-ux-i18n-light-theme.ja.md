# Chronicle Stack UI/UX 依頼プロンプト

以下を Claude Design に渡してください。

---

あなたは Chronicle Stack の UI/UX を設計する product designer です。

まず添付された仕様書 `claude-design-ui-ux-spec-i18n-light-theme.ja.md` を読み、その要件に厳密に従ってください。

この依頼は、generic な dashboard デザインを求めるものではありません。
Chronicle Stack は local-first の reasoning workbench であり、context、artifact、decision、review、boundary、trust、federation、runtime surface を再構成可能に見せるプロダクトです。

今回のデザインで必ず守ること:

- local-first
- derived view が authority source に見えないこと
- UI は concise であること
- 冗長な表示を避けること
- 一目で分かること
- i18n 前提であること
- 設定画面で言語を選べること
- 右上隅にフォント倍率プルダウンを置くこと
- 背景色は明色であること

必須要件:

- settings screen で表示言語を変更可能
- 初期対応言語は `ja`, `en`, `zh-CN`
- font scale dropdown は右上隅に常設
- font scale 選択肢は `100%`, `120%`, `140%`, `160%`, `180%`, `200%`
- light theme を前提とする
- 文章量を抑え、意味単位で整理する
- overview で current focus / warning / pending review / next safe action が分かる

避けること:

- social feed
- cloud SaaS dashboard
- dark theme 前提
- 過度に情報量の多い admin panel
- 長文説明に依存した UI
- setting 導線の深い階層化

出力してほしい内容:

1. design thesis
2. product principles
3. information architecture
4. navigation model
5. visual direction
6. global shell design
7. top-right utility area design
8. settings screen design
9. language selector UX
10. font scale dropdown UX
11. screen-by-screen layout
12. component patterns
13. empty / warning / blocked / preview-only states
14. rationale for provenance / audit / boundary visibility

出力スタイル:

- product designer として具体的に書くこと
- bland な admin-dashboard language を避けること
- implementation-ready な粒度まで落とすこと
- textual wireframe description を含めてよい
- calm, exact, bright, readable, compact な方向でまとめること

特に Settings 画面については、次を具体化してください。

- 言語切替の配置
- ラベル表記
- current locale の見せ方
- 即時反映の考え方
- フォント倍率変更の配置
- 200% でも崩れないレイアウト方針
- light theme を前提にした appearance section

最終提案は「Chronicle Stack のための concise で高 UX な local-first UI proposal」として読めるものにしてください。

---
