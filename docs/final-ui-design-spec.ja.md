# Chronicle Stack 最終 UI デザイン仕様書

Status: Claude Design 向けドラフト

## 1. 目的

この文書は、Chronicle Stack の最終到達形 UI の設計ブリーフを定義するものです。
デザインモデルやデザイナーに渡し、Chronicle Stack の中核境界を壊さずに最終プロダクト UI を提案してもらうことを目的とします。

Chronicle Stack は、汎用ノートアプリでも、ソーシャルフィードでも、ホステッドダッシュボードでもありません。
この UI は、ローカルオペレーターが次のことを再構成できるようにする必要があります。

- なぜその Artifact が存在するのか
- どの Context がそれを形作ったのか
- どの Decision がそれを採用、棄却、保留したのか
- 時間を通じて意味がどう変化したのか
- どの Boundary、Trust、Audit、Federation 条件が適用されるのか

最終 UI は、タイムライン中心のプロダクトではなく、ローカルな reasoning workbench のように感じられるべきです。

## 2. プロダクト境界

UI は次の hard boundary を守る必要があります。

- local-first: ローカル Chronicle root が source of truth である
- `.chronicle/chronicle.jsonl` が primary record であり続ける
- UI surface は Chronicle record から導かれた derived view であり、authority source になってはならない
- 直接の in-place editing よりも proposal/review/apply を優先する
- federation は preview-first、inspect-first、consent-aware である
- Chronicle Stack は hosted GraphRAG runtime、vector DB、graph DB、cloud sync product にならない
- network transport、automatic import、unattended sync は現行ターゲット UI の範囲外である

## 3. デザイン目標

最終 UI は次を満たすべきです。

- 生の CLI や JSON を読むよりも再構成を速くする
- provenance、auditability、boundary state を visual first-class にする
- 現在の task state を単一の landing view から読み取れるようにする
- write-capable action に入る前に、review と proposal workflow を理解しやすくする
- 実装が最初は web-based でも、local deployment にふさわしい desktop-grade な体験を支える
- 将来の operator identity や trust workflow に拡張可能でありつつ、multi-user SaaS 的な意味を暗示しない

## 4. Non-Goals

この UI を次のようには設計しないでください。

- chat app
- social media timeline
- generic CRUD admin panel
- cloud collaboration dashboard
- direct-edit document editor
- 明示 review なしに Chronicle state を変更する hidden automation product

## 5. 主たるユーザー

Primary user:

- AI-assisted writing、design、research、development artifact を扱う local operator
- context、decision、proposal、review state、federation readiness を点検する必要がある人
- speed-at-any-cost より traceability を重視する人

Secondary user:

- 同一ローカルマシン上、または明示的 package handoff を通じて作業する reviewer / collaborator

## 6. プロダクトの性格

目指す体験は次のようであるべきです。

- calm
- high-trust
- inspectable
- exact
- serious but not intimidating
- terminal より豊かだが、playful でも feed-driven でもない

推奨されるトーン:

- editorial desk
- evidence board
- review console
- provenance navigator

避けるべきもの:

- engagement-driven feed pattern
- vanity metric
- bright attention trap
- 汎用 enterprise admin 風スタイリング

## 7. Core UX Principles

### 7.1 Reconstruction first

重要な screen はすべて、少なくとも次に答えられるべきです。

- これは何か
- どこから来たのか
- 何が変わったのか
- 何が pending なのか
- どの boundary が適用されるのか
- 次に何を安全にできるのか

### 7.2 Boundary before action

ある操作に trust、consent、audit、identity、review の影響があるなら、
UI は apply step に入る前にその条件を見せるべきです。

### 7.3 Proposal before mutation

最終ターゲット UI で editing が存在する場合、その基本フローは次であるべきです。

- draft proposal
- inspect diff
- review boundary と audit consequence
- explicit apply

### 7.4 Derived view stays visibly derived

overview、index、trend summary、package preview、AI hint、federation summary は、
silent authority surface ではなく advisory read model として視覚的に提示されるべきです。

### 7.5 Meaning over chronology

デフォルトの navigation は次を優先すべきです。

- active question
- artifacts under review
- unresolved objection
- recent decision
- significant diff

純粋な reverse-chronological log view をデフォルトにしてはいけません。

## 8. 情報設計

最終 UI は次の top-level area を中心に構成します。

### 8.1 Home / Overview

Purpose:

- オペレーターの現在の operating picture を示す

Should include:

- chronicle health and counts
- active review queue summary
- mutation readiness and boundary readiness
- current runtime and summary-job signals
- federation preflight and overlap summary
- trust summary
- warnings and triage shortcuts
- 高シグナルな「今なにに注意すべきか」モジュール

### 8.2 Chronicle Objects

Purpose:

- raw record だけでなく first-class meaning unit を辿れるようにする

Should include:

- question
- decision
- artifact
- delta
- objection
- hypothesis
- decay-related record

### 8.3 Context and Artifact Workbench

Purpose:

- context、artifact、version、decision の関係を点検できるようにする

Should include:

- artifact history
- source event linkage
- related context
- decision linkage
- RDE linkage
- 必要に応じて proposal / apply status

### 8.4 Review Workspace

Purpose:

- review state を安全かつ明瞭にする

Should include:

- pending review queue
- reviewer identity and session state
- enforcement and validation-gate summaries
- CLI parity visibility
- action preview and recovery guidance
- proposal review and apply progression

### 8.5 Audit / Boundary / Lifecycle

Purpose:

- operational / governance state を点検する

Should include:

- audit event
- boundary rule
- lifecycle marker
- blocker detail
- enforcement と advisory の区別

### 8.6 Federation Workspace

Purpose:

- 明示的な local package / message workflow を支える

Should include:

- inbox / outbox inspection
- package inspect / verify / preview / import-preview guidance
- consent record and overlap summary
- trust-aware package context
- read-only boundary-check と consent summary

### 8.7 Trust Workspace

Purpose:

- node trust relationship とその scope を点検する

Should include:

- node
- subject identity
- trust relation
- trust assertion / withdrawal
- domain / purpose / capability の区別

### 8.8 Runtime / Retrieval Workspace

Purpose:

- AI-adjacent derived work を、Chronicle 自体を runtime にせずに点検する

Should include:

- runtime record
- summary job
- AI index status
- graph summary
- query-engine handoff and escalation cue
- downstream trial sufficiency and import-readiness

## 9. 主要画面

### 9.1 Final Home Screen

最終 home screen は、同格の card を並べた dashboard にしてはいけません。
operator judgment を優先すべきです。

推奨構成:

- left navigation rail
- central "current work" column
- right-side evidence / boundary / trust column

Central column priority:

- pending review
- open question
- recent meaningful diff を持つ active artifact
- unresolved objection
- current proposal/apply candidate

Right column priority:

- boundary warning
- audit highlight
- federation readiness
- trust / consent signal

### 9.2 Record Detail Screen

主要な record detail screen では、次を見せるべきです。

- canonical identity
- summary
- provenance
- related record
- timeline
- decision and review state
- warning and boundary note
- next safe action

推奨 tabs or sections:

- summary
- lineage
- diffs / RDE
- review
- audit
- related

### 9.3 Review Detail Screen

これはプロダクトの最重要 screen の一つであるべきです。

明確に示すべきもの:

- 何が review 対象か
- なぜ pending なのか
- 誰が review しているのか
- どの session / identity assumption があるのか
- どの blocker があるのか
- 対応する CLI route は何か
- approve / reject / request changes で何が起きるか
- rollback / recovery path は何か

### 9.4 Federation Package Screen

この screen は file browser ではなく shipping inspection desk のように感じられるべきです。

Must show:

- package purpose
- target node
- visibility and retention semantics
- consent and sharing restriction
- manifest validity state
- trust reference context
- included record summary
- redaction report
- import-preview implication

### 9.5 Question-Centric Workspace

最終 UI は、live question / inquiry を中心に据えた screen を提供するべきです。

そこでは次を結びつけます。

- question
- related context
- linked artifact
- linked decision
- objection
- hypothesis
- relevant runtime or retrieval attempt
- downstream review or federation implication

これは、Chronicle が単なる file storage ではなく、meaning reconstruction の基盤だからです。

## 10. Interaction Rule

### 10.1 Navigation

- overview aggregate から filtered list に jump できること
- list から detail へ、reconstruction trail を失わずに遷移できること
- breadcrumb は route hierarchy だけでなく semantic path を反映すること

### 10.2 Filtering

次の軸で filter を支えること:

- review state
- boundary state
- trust / consent overlap
- object type
- artifact type
- lifecycle state
- AI/runtime involvement
- readiness and blocker family

### 10.3 Mutation affordance

最終 target vision では write-capable control が存在してもよいですが、必ず次を満たすべきです。

- explicit に mark されている
- apply 前に boundary と audit implication を示す
- proposal/review/apply separation を示す
- CLI parity visibility を保つ
- fail closed である

### 10.4 Federation affordance

Federation-related screen は次を決して暗示してはなりません。

- automatic transport
- automatic import
- automatic approval
- hidden authority

### 10.5 AI affordance

AI-related screen は次を決して暗示してはなりません。

- verified truth
- permanent identity claim
- unbounded context sharing
- Chronicle Stack core 内での hosted external execution

## 11. Visual Direction

UI は generic app よりも high-end analysis console に近い印象であるべきです。

推奨される visual trait:

- 強い typography hierarchy
- paper-and-ink を思わせる warm-neutral palette と restrained accent color
- graph / ledger / archival を連想させる subtle cue
- quiet motion
- warning、advisory、ready、blocked、preview の clear state-color semantic
- 情報密度は高くても cramped には見えないこと

避けるべきもの:

- 紫ベースの generic AI aesthetic
- consumer social UI pattern
- toy terminal cosplay
- flat admin template

## 12. Layout Guidance

デザインは次で機能する必要があります。

- laptop-first local use
- wide desktop monitor
- moderate tablet adaptation

desktop layout を primary としてください。
mobile は secondary でよく、全 design system を mobile-first で決める必要はありません。

## 13. Designer に求める成果物

designer / design model は次を出力するべきです。

- product design principles summary
- information architecture
- final navigation model
- high-level visual direction
- overview screen design
- record detail screen design
- review workspace design
- federation workspace design
- trust workspace design
- runtime/retrieval workspace design
- proposal/review/apply interaction concept
- component system summary
- empty / warning / blocked / preview-only / ready の state example

## 14. Designer 向け制約

結果の design は次を満たす必要があります。

- Chronicle Stack の local-first と derived-view boundary を保つ
- hosted multi-user SaaS behavior を前提にしない
- hidden auto-sync や auto-import を前提にしない
- federation は preview-first と inspect-first を保つ
- review と editing は proposal-first を保つ
- future networked federation と full interactive editing は future-compatible として扱い、すでに available であるかのように見せない

## 15. Summary

Chronicle Stack の最終 UI は、単なる「きれいな admin panel」ではありません。
それは context、decision、artifact、review、trust、federation のための local reasoning and provenance workspace です。

デザインは Chronicle を次のように感じさせるべきです。

- local
- trustworthy
- inspectable
- reconstructable
- intellectually calm
- deeper workflow へ向かう準備があるが、まだ存在しない機能をあるかのように装わない
