# Chronicle Stack Local UI Implementation Roadmap

Status: Active  
Date: 2026-07-03  
Scope: `chronicle ui` を、現行 read-only local web UI から final UI 方針に沿った高可読・i18n-first・light-theme の local workbench へ段階的に進めるための実装ロードマップ

## Related

- `docs/final-ui-design-spec.ja.md`
- `docs/final-ui-design-workspace-addendum.ja.md`
- `docs/final-ui-implementation-gap.ja.md`
- `docs/claude-design-ui-ux-spec-i18n-light-theme.ja.md`
- `docs/claude-design-prompt-ui-ux-i18n-light-theme.ja.md`
- `docs/interactive-ui-and-graphrag-roadmap.md`
- `docs/releases/remaining/v1.105-release-remaining-issues.md`
- `docs/releases/remaining/v1.106-release-remaining-issues.md`
- `docs/releases/readiness/release-readiness-v1.133.md`
- `docs/releases/remaining/v1.135-release-remaining-issues.md`

## 1. Purpose

この文書は、Chronicle Stack の UI 実装を前に進めるために、既存の broad な final UI 仕様と最近の design handoff を、実装可能な順序へ再編するものです。

今回の再考で重視する問いは次の 4 つです。

- 次に何から実装すると UX 改善の体感が最も大きいか
- 何を renderer 再編で進め、何を read model 拡張で進めるか
- i18n / settings / font scale / light theme をどの phase に置くべきか
- Kazane / Work OS handoff から何を取り込み、何を取り込まないか

## 2. Reframed Product Direction

Chronicle Stack は Kazane そのものにはならない。
ただし Kazane handoff からは、次の UI 設計原則を取り込む価値がある。

- current state が一目で分かる landing priority
- Workbench 的な 3 カラム読解
- review / handoff / gate / audit を同一作業系として見せること
- 「停止は失敗ではなく boundary を守る正常系」という見せ方

一方で、次は取り込まない。

- generic business OS への全面的な語彙置換
- Chronicle の既存 object model を越える新しい durable domain model
- SaaS 的 multi-user semantics
- hidden runtime / daemon / sync

つまり、今回の実装ロードマップは:

- Chronicle Stack の既存 read model を活かす
- final UI spec の information architecture に寄せる
- Kazane handoff は layout / operator UX の参考として使う
- source of truth や domain authority は変えない

## 3. Current State

既に揃っているもの:

- local-first foreground UI (`chronicle ui`)
- 広い read-only API surface
- locale 正規化と UI i18n catalog
- localStorage ベースの locale 保存
- final UI design spec と implementation-gap mapping
- artifact workbench 向け summary payload の一部
- operator runbook / backup / restore / local validation docs

まだ弱いもの:

- top-level UI shell の最終形
- settings screen
- visible language selection flow as a first-class settings feature
- top-right utility area
- font scale control
- light-theme optimized visual system
- overview の question / proposal / warning priority
- artifact workbench の multi-column composition

## 3.1 Current Position (2026-07-05)

現在地は、文書初版時点の `Phase 1` 完了直後より前進している。
repo truth ベースでは、次の補正が妥当である。

- `Phase 0`: Completed
- `Phase 1`: Completed
- `Phase 2`: Substantially in progress
- `Phase 3`: Substantially in progress
- `Phase 4`: Partially started
- `Phase 5`: Not closed

今回までに完了したもの:

- shell header の再編
- 右上 utility area の追加
- locale selector の常設化
- settings entry point の追加
- settings view の追加
- font scale dropdown (`100 / 120 / 140 / 160 / 180 / 200%`) の追加
- locale / font scale の localStorage 永続化
- light-theme 寄りの基礎背景色・panel 色調整
- i18n catalog への settings / font scale 文言追加

今回時点で未完了の中核:

- final visual system と spacing / density の再設計
- overview の first viewport 再編
- artifact workbench の multi-column 化
- review / runtime / federation 各 workspace の final layout 化
- manual validation / release docs の最終更新

プロダクト完了へ向けた UI 残務順は、次の通りに固定する。

1. security / boundary semantics と矛盾しない summary-first UI へ各 workspace を揃える
2. review / runtime / federation / trust / audit workspace を final reading flow に寄せる
3. federation package / manifest / verify の operator UX を一貫化する
4. AI / retrieval boundary と handoff / escalation の見せ方を締める
5. manual validation / release / roadmap 文書を current shell に同期する

ローカル検証状況:

- `./.venv/bin/ruff check src/ tests/`
- `./.venv/bin/pytest -q`

いずれも通過済み。

## 4. Guiding Rules

### 4.1 Renderer-first where possible

まず renderer 再編で価値を出す。
新しい endpoint は、複雑な front-end stitching が過剰になった場合だけ追加する。

### 4.2 i18n-first but presentation-only

UI locale は第一級要件だが、artifact language や record content とは混同しない。

### 4.3 Settings before polish

language selector、font scale、light appearance の入口を先に作る。
見た目の polish はその後でよい。

### 4.4 Compact by default

UX の改善は「情報量を増やす」ではなく「優先順位を整理する」で達成する。

### 4.5 Manual validation only when behavior changes

full manual browser walkthrough は、新しい interaction / navigation / settings behavior が入った節目でだけ再実施する。

## 5. Execution Strategy

このロードマップは 6 phase で進める。

### Phase 0: Shell Foundation

Status:

- Completed

目的:

- final UI 実装の土台となる global shell を整える

対象:

- top header
- left workspace navigation
- right-top utility area
- settings entry point
- locale state wiring review

実装項目:

- UI shell を `Overview / Objects / Workbench / Review / Audit / Federation / Trust / Runtime / Settings` 前提で再編
- 右上 utility area を追加
- 現在 locale の可視表示を追加
- settings route / panel の雛形を追加

受け入れ条件:

- どの画面でも current workspace が分かる
- 右上に settings entry がある
- locale の current value が見える
- existing read-only boundary を壊さない

### Phase 1: i18n And Accessibility Controls

Status:

- Completed

目的:

- UI language と font scale を operator が自分で制御できる状態にする

対象:

- settings screen
- language selector
- font scale dropdown
- local persistence

実装項目:

- settings screen に `表示言語` セクションを追加
- `ja / en / zh-CN` の切替 UI を追加
- 右上常設の font scale dropdown を追加
- `100 / 120 / 140 / 160 / 180 / 200%` の 6 段階をサポート
- localStorage に locale / font scale を保存
- 200% でも壊れない shell / table / panel layout を整える

受け入れ条件:

- locale が即時反映される
- font scale が即時反映される
- リロード後も locale / font scale が保持される
- 200% で主要導線が崩れない

備考:

- locale の保存基盤は既にあるため、ここは新規アーキテクチャではなく UI surfaced settings 化が中心

### Phase 2: Light Theme And Visual Simplification

Status:

- Next

目的:

- 現行 UI を明色・簡潔・高可読の方向へ寄せる

対象:

- color system
- card / table / rail density
- heading hierarchy
- warning / review / boundary visual language

実装項目:

- light theme を default にする
- neutral background + elevated panel 構成へ切替
- badge 種類を整理
- raw table / dense list の default presentation を簡潔化
- explanatory paragraph を summary-first に置換
- shell / settings / overview / workspace table に共通 token を導入
- 余白・境界線・見出し階層を CSS 変数ベースで統一

受け入れ条件:

- 第一印象が dark admin console ではない
- warning / review / derived / preview の区別が色以外でも分かる
- cards / rails / tables の hierarchy が明確

### Phase 3: Overview And Workbench Pass

Status:

- Priority

目的:

- UX の中心改善を、まず landing と object/workbench 系へ落とす

対象優先順:

1. Overview
2. Context & Artifact Workbench
3. Audit / Boundary / Lifecycle
4. Trust Workspace

実装項目:

- Overview を question / warning / pending review / next safe action 優先へ再編
- artifact workbench を multi-column composition へ格上げ
- artifact detail を summary / provenance / related action の 3 面読解へ整理
- audit / boundary / lifecycle を status-first cards に再編
- trust workspace を derived / advisory / source-of-truth の区別が即読できる形へ整理

read model 拡張の優先順:

1. overview question-centric aggregate
2. artifact detail workbench summaries
3. trust / audit implication summaries

受け入れ条件:

- raw detail first ではなく summary first で読める
- right rail が provenance / boundary / next safe action の役割を持つ
- workspace ごとの目的が first viewport で分かる

### Phase 4: Review / Runtime / Federation Pass

Status:

- Completed (`../ui-phase-4-closeout.md`)

目的:

- operator workflow 系 workspace を final UI に寄せる

対象優先順:

1. Review Workspace
2. Runtime / Retrieval Workspace
3. Federation Workspace

実装項目:

- review detail を step / blocker / outcome 型へ整理
- runtime / retrieval を posture + trial + handoff + escalation 型へ整理
- federation を package inspection desk 型へ整理

read model 拡張の優先順:

1. review step / blocker / outcome summaries
2. runtime posture summaries
3. federation inspection summaries

受け入れ条件:

- review / runtime / federation の行き先が overview と整合する
- mutation ではなく read-only operator guidance であることが明瞭
- escalation / handoff / manual CLI parity が right rail で迷子にならない

### Phase 5: Validation And Release Lane

Status:

- In progress: automated smoke complete; manual visual walkthrough remains

目的:

- 実装を operator workflow として固定化する

対象:

- browser walkthrough
- `ui-smoke`
- operator docs
- release docs

実装項目:

- settings / locale / font scale を含む manual validation 手順を追加
- light theme 前提の screenshot / walkthrough evidence を更新
- relevant smoke / readiness / remaining docs を更新
- 必要なら `ui-smoke` に shell-level assertions を追加

受け入れ条件:

- operator が chat memory なしで locale / font scale / main workspaces を検証できる
- release docs が current UI shell と矛盾しない

## 6. Milestone View

### Milestone A: Settings-Ready Shell

Status:

- Completed

- shell 再編
- settings entry
- locale visibility

### Milestone B: i18n / Font Controls

Status:

- Completed

- settings language selector
- top-right font scale dropdown
- local persistence

### Milestone C: Light Theme Readability Pass

Status:

- In progress

- bright background
- compact cards
- readable tables

### Milestone D: Overview + Workbench Pass

Status:

- In progress

- question-centric overview
- multi-column artifact workbench

### Milestone E: Review / Runtime / Federation Pass

Status:

- Partially started

- review progression
- runtime posture
- package inspection desk

### Milestone F: Validation + Release Closeout

Status:

- Queued

- manual validation
- docs / smoke / release alignment

## 7. Recommended Task Slices

実際の PR 単位は次のように切るのが安全。

1. light-theme token and shell readability pass
2. overview renderer re-prioritization
3. artifact workbench multi-column renderer
4. audit / boundary / trust workspace simplification
5. review workspace progression renderer
6. runtime / retrieval posture renderer
7. federation inspection-desk renderer
8. docs + validation refresh

現時点の product closeout 順では、これらの slice を次の 5 本へ束ね直して読む。

1. security / boundary alignment and semantics closeout
2. review / runtime / federation / trust / audit renderer closeout
3. federation package and signed-manifest operator flow closeout
4. AI / retrieval boundary and handoff flow closeout
5. docs, smoke, release, and manual validation synchronization

既に完了済みの slice:

- shell / route / utility-area refactor
- settings screen with locale controls
- font scale dropdown and persistence

## 8. Risks

### Risk 1: Shell rewrite without UX gain

対策:

- shell phase では settings / locale / utility visibility まで出す

### Risk 2: Over-design before read model fit

対策:

- renderer-first で進め、API は必要最小限で拡張

### Risk 3: i18n and artifact language confusion

対策:

- settings 文言と ADR-0025 / ADR-002 の boundary を UI 内でも明示

### Risk 4: Bright theme reduces semantic clarity

対策:

- color だけに頼らず badge / heading / structure で区別する

### Risk 5: Kazane drift

対策:

- Kazane は layout / workflow inspiration に限定し、domain authority は Chronicle 既存語彙を保つ

## 9. Stop Rules

次の時点で phase を止めてよい。

- further progress would require a new durable domain model
- multi-user semantics を入れないと成立しない設計に傾いた
- API stitching complexity が renderer-first 原則を超えた
- UI 変更より manual validation refresh の方が先に必要になった

## 10. Summary

今回の再考での結論は明確です。

- 次は helper alignment ではなく feature-facing UI work に戻る
- settings / locale / font scale / shell は基盤として完了した
- 次の主戦場は security / boundary semantics を壊さずに feature workspace を product-grade に閉じることである
- light theme と concise presentation は基盤から feature workspace 全体へ拡張する段階に入っている
- Kazane handoff は Chronicle UI を business OS に変えるためではなく、operator-first のレイアウト判断に使う
- 実装順序は `boundary closeout -> feature workspace closeout -> package/manifest UX -> AI/retrieval flow closeout -> validation` が現時点で最も安全
