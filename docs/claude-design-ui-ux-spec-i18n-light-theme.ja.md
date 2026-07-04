# Chronicle Stack UI/UX 仕様書

Status: Claude Design 依頼用  
Scope: 現行 local web UI を前提にしつつ、将来 desktop shell にも移植できる最終 UI/UX 方針  
Priority: concise / high-clarity / i18n-first / light-theme

## 1. 目的

この文書は、Claude Design に Chronicle Stack の UI/UX デザインを依頼するための実務仕様書です。
目的は、Chronicle Stack の中核境界を壊さず、冗長さを抑え、一目で状況が分かる高 UX なローカル作業 UI を設計してもらうことです。

この UI は次を速く再構成できなければなりません。

- いま何が起きているか
- どの artifact / context / decision が関係しているか
- 何が derived view で、何が source of truth か
- どこに warning / review / boundary があるか
- 次に安全に何ができるか

## 2. 絶対条件

以下は必須要件です。

- local-first であること
- `.chronicle/chronicle.jsonl` が primary record のままであること
- UI は authority source ではなく derived surface であることが分かること
- review / proposal / apply の境界を壊さないこと
- hosted SaaS、social feed、generic admin panel に寄せないこと
- 冗長な表示を避け、短く、意味単位で整理すること
- 一目で現在地が分かること
- 背景色は明色とすること
- i18n 対応を前提とすること
- 設定画面で表示言語を変更できること
- 画面右上隅に表示フォント倍率プルダウンを配置すること

## 3. デザインの性格

求める体験:

- calm
- exact
- readable
- compact
- evidence-oriented
- high-trust

避けるもの:

- 派手な attention trap
- 濃い装飾
- 長い説明文の常時表示
- dense すぎる表
- クリックしないと意味が分からない曖昧なカード
- dark theme 前提

## 4. ユーザー像

Primary user:

- ローカル環境で Chronicle を扱う operator
- writing / design / research / development の再構成を行う人
- provenance、review、boundary を重視する人

Secondary user:

- 同一マシン上で点検する reviewer
- package handoff 経由で確認する collaborator

## 5. 最重要 UX 原則

### 5.1 一画面一目的

各画面は「何のための画面か」が瞬時に分かること。
overview 画面に detail を詰め込みすぎないこと。

### 5.2 One-glance comprehension

主要画面の first viewport だけで最低限次が分かること。

- 現在の workspace
- 現在の対象
- current state
- warning の有無
- review / boundary の有無
- 次の safe action

### 5.3 Progressive disclosure

詳細は drill-down で見せる。
ただし summary が貧弱で「開くまで何か分からない」状態にしない。

### 5.4 Meaning over quantity

件数や raw log より、意味のある変化、pending review、重大 warning、現在の focus を優先する。

### 5.5 Derived view stays visibly derived

overview、summary、AI hint、preview、federation guidance、runtime guidance は、
必ず「derived / advisory / preview」であることが分かる表現にする。

## 6. i18n 方針

UI は i18n-first で設計すること。
既存 ADR に従い、UI locale と artifact language は混同しない。

### 6.1 初期対応言語

- 日本語 `ja`
- English `en`
- 简体中文 `zh-CN`

### 6.2 言語切替

言語切替は設定画面で行う。
設定画面には明確な `表示言語 / Language / 显示语言` セクションを置く。

要件:

- 現在選択中の言語が一目で分かる
- 3 言語を正式な選択肢として表示する
- UI 表示言語のみを切り替える
- source language / artifact language / report language とは別概念であること
- 設定はローカルに永続化されること

推奨ラベル:

- 日本語
- English
- 简体中文

### 6.3 言語切替の UX

- 設定変更後は即時反映
- リロード不要が望ましい
- 長い説明文ではなく 1 行の補足で十分
- fallback は English

## 7. 表示フォント倍率

画面右上隅に、常時アクセス可能なフォント倍率プルダウンを置く。

### 7.1 必須選択肢

- 100%
- 120%
- 140%
- 160%
- 180%
- 200%

### 7.2 要件

- 全画面で同じ位置に置く
- utility control として軽く見せる
- setting screen の奥に隠さない
- 選択後は全 UI に即時反映
- ローカルに永続化する
- 表示倍率変更でレイアウトが破綻しない
- 200% でも主要操作が可能であること

### 7.3 見せ方

- 右上ユーティリティエリアに配置
- 文字は簡潔に `100%` 形式で見せる
- icon only にしない

## 8. 視覚デザイン方針

### 8.1 背景

- 明色背景を必須とする
- 全体は light theme
- 純白一色ではなく、少し柔らかい light neutral を基調にしてよい
- 強いグラデーションや重いテクスチャは不要

推奨方向:

- base background: warm light gray / soft ivory / pale neutral
- panel background: base より少し白い
- warning / boundary / review は色で補助しつつ、文字でも意味を伝える

### 8.2 情報密度

- compact だが cramped ではない
- 余白は「意味のグルーピング」に使う
- section 数を増やしすぎない
- 罫線より階層と spacing で整理する

### 8.3 見出し

- 強い display typography は不要
- section title は短く、意味を即断できるものにする
- ラベルの言い換え遊びをしない

## 9. グローバルレイアウト

推奨は desktop / laptop first の 3 層構造です。

- 左: workspace navigation
- 中央: 主表示領域
- 右: detail rail / evidence rail / boundary rail

### 9.1 ヘッダー

ヘッダーには最低限次を含めること。

- product / workspace identity
- current location
- right-top utility area

### 9.2 右上 utility area

必須:

- font scale dropdown
- settings entry

推奨:

- locale の現在値を小さく表示
- help よりも setting を優先

## 10. 主要画面

Claude Design は最低限次の画面を設計対象とすること。

- Home / Overview
- Chronicle Objects
- Context & Artifact Workbench
- Review Workspace
- Audit / Boundary / Lifecycle
- Federation Workspace
- Trust Workspace
- Runtime / Retrieval Workspace
- Settings

## 11. Home / Overview 要件

Overview は「全部入りの dashboard」ではなく、現在地の要約面とする。

最初の表示で分かるべきこと:

- current focus
- pending review
- warning
- boundary issues
- recent meaningful change
- shortcut to next workspace

表示ルール:

- 1 枚 1 意味の summary card
- card 内文章は短く
- raw table を置かない
- “important now” が埋もれない

## 12. Settings 画面要件

### 12.1 目的

設定画面は「オペレーターが UI の見え方と基本挙動を整える場所」とする。
複雑な system settings の倉庫にしない。

### 12.2 必須セクション

- 表示言語
- 表示フォント倍率
- 表示スタイル

### 12.3 表示言語セクション

含める内容:

- 現在の UI language
- 3 言語の選択肢
- 短い補足:
  - UI 表示だけが切り替わる
  - record content 自体は翻訳しない

### 12.4 表示フォント倍率セクション

含める内容:

- current scale
- 100/120/140/160/180/200%
- preview 的な見本 1 行

### 12.5 表示スタイル

今回の前提では light theme のみ。
よって、theme toggle を主役にしない。

表示例:

- Theme: Light
- explanation: local review readability optimized

## 13. コンポーネント要件

必須パターン:

- concise summary card
- structured table with strong row labeling
- detail rail
- warning / boundary badge
- review state badge
- derived / preview marker
- breadcrumb
- filter / search input
- segmented tab or mode switch

### 13.1 Badge

badge は装飾でなく意味ラベルとして使う。
種類を増やしすぎない。

### 13.2 Table

- 行ヘッダを強くする
- 重要列を左に寄せる
- 列数を欲張らない
- raw JSON をそのまま主表示しない

### 13.3 Empty / Warning / Blocked

Empty:

- 何がまだ存在しないか
- それが failure か normal initial state か

Warning:

- 何に注意すべきか
- どの boundary に関係するか

Blocked:

- 何が止めているか
- 何を満たせば進めるか

## 14. 文章量のガイド

- 画面上の説明文は短く
- paragraph の常設は最小限
- 可能なものは label + summary に変える
- “詳しく読む” は detail / drawer / panel に退避する

## 15. 禁止事項

- dark mode を前提にした色設計
- 設定導線が深すぎること
- フォント倍率変更を設定画面のみに閉じ込めること
- 言語切替を hidden menu に入れること
- 情報の意味が hover しないと分からないこと
- 長文説明で UI を成立させること
- raw chronology を最上位の default にすること
- cloud collaboration 前提の affordance を混ぜること

## 16. Claude Design への要求出力

Claude Design には次を出力してもらうこと。

1. concise design thesis
2. information architecture
3. top-level navigation
4. light-theme visual direction
5. screen-by-screen layout
6. Settings screen の詳細
7. language selector UX
8. top-right font scale dropdown の詳細
9. component system
10. empty / warning / blocked / preview-only state design
11. provenance / audit / boundary の見せ方

## 17. 成功条件

この仕様に沿った良いデザインは、最初の 5 秒で次が分かります。

- ここが Chronicle Stack であること
- これは local-first の reasoning workbench であること
- いま何を見るべきか
- どこで言語を変えるか
- どこで文字サイズを変えるか
- どこに warning / review / boundary があるか

