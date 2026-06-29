# Chronicle Stack 最終 UI 追補仕様書

Status: Claude Design 向け追補仕様書  
Scope: `Context & Artifact Workbench`, `Audit / Boundary / Lifecycle`, `Trust Workspace`, `Runtime / Retrieval Workspace`

## 1. 目的

この文書は、`docs/final-ui-design-spec.ja.md` を補完する画面仕様レベルの追補仕様書です。
特に、Claude Design が曖昧なまま解釈しやすい 4 つの workspace について、以下を具体化します。

- 画面の役割
- レイアウト
- 主要コンポーネント
- 一覧 / 詳細 / ドリルダウンの関係
- 状態設計
- 主要導線
- 禁止事項

この文書は visual mock の指示書ではなく、情報設計と interaction を具体化するための設計仕様です。

## 2. 共通前提

4 つの workspace すべてに共通する前提:

- local-first
- `.chronicle/chronicle.jsonl` が primary record
- 画面は derived surface であり authority source ではない
- operator が「何を見ているか」「何が derived か」「何が次の safe action か」を見失わないこと
- detail を開くたびに provenance、related record、boundary note を辿れること
- write-capable action が将来入るとしても proposal/review/apply を崩さないこと

## 3. Context & Artifact Workbench

### 3.1 目的

この workspace は、artifact 単体の閲覧画面ではありません。
artifact がどの context によって形作られ、どの decision を経て、どの diff と RDE を持つのかを再構成するための作業卓です。

### 3.2 主要ユースケース

- ある artifact の現行状態を理解する
- その artifact がどの context と decision に支えられているか確認する
- version 履歴と source event を辿る
- meaningful diff と RDE の関係を見る
- proposal が存在する場合、その apply 候補と review 状態を把握する

### 3.3 推奨レイアウト

デスクトップ前提の 3 カラム構成を基本とします。

- 左カラム: navigation / object locator
- 中央カラム: artifact の主表示面
- 右カラム: provenance / boundary / review / related context

#### 左カラム

表示内容:

- artifact list または related object navigator
- filter
- current selection summary
- open question / related decision shortcut

性格:

- file tree ではなく semantic locator
- title、type、review state、recent diff の有無が短く読める

#### 中央カラム

表示内容:

- artifact header
- current version summary
- main content preview
- version timeline
- diff / RDE section
- proposal/apply status section

中央は「今この artifact で何が本体なのか」を読む場所です。

#### 右カラム

表示内容:

- source event
- linked context summary
- linked decision summary
- boundary warning
- audit relevance
- next safe actions

右カラムは evidence rail です。

### 3.4 主要コンポーネント

#### Artifact Header

表示項目:

- artifact title
- artifact type
- artifact id
- current version id
- visibility
- review state
- last meaningful change summary

要件:

- title の近くに raw ID を見せてもよい
- 派手な primary CTA は置かない
- currentness と review state を同列で見せる

#### Version Timeline

表示項目:

- version 順序
- source event id
- changed at
- changed by
- summary
- proposal-originated かどうか

要件:

- 単なる日付列ではなく、意味のある change chain として見せる
- current version と historical version の差が一目で分かること

#### Diff / RDE Panel

表示項目:

- current meaningful diff summary
- linked RDE record
- preserved / transformed / supplemented / unresolved
- deviation risks
- next update policy

要件:

- code diff viewer のように見せすぎない
- Chronicle は source-code-only プロダクトではないため、semantic change が主役
- "何が変わったか" だけでなく "意味がどう変わったか" を読ませる

#### Context Linkage Panel

表示項目:

- related contexts
- context scope
- visibility
- provenance note
- context warning

要件:

- artifact に対する context の関与が分かる
- context が複数ある場合は dominance や relevance を整理して見せる

#### Decision Linkage Panel

表示項目:

- accepted / rejected / pending decision
- decision rationale summary
- decision event id
- linked review state

要件:

- artifact は単独で存在せず、decision chain の一部だと分かること

#### Proposal / Apply Panel

表示項目:

- proposal 有無
- pending / reviewed / approved / applied
- proposal summary
- apply blocker
- explicit CLI parity hint

要件:

- 将来 write-capable UI が入っても direct-edit に見せない
- proposal と current artifact を混同させない

### 3.5 一覧 / 詳細 / ドリルダウン

導線:

- artifact list -> artifact detail
- artifact detail -> version detail
- artifact detail -> linked context detail
- artifact detail -> linked decision detail
- artifact detail -> linked RDE detail
- artifact detail -> proposal / review detail

ルール:

- detail を開いても「どこから来たか」が breadcrumb で残る
- back したとき filter や selection state を失わない

### 3.6 状態設計

Empty:

- artifact は存在するが linked context / decision / RDE がまだない
- 「未接続」であることを failure ではなく current state として表現する

Warning:

- visibility mismatch
- missing provenance
- unresolved RDE
- pending review

Blocked:

- apply candidate があるが review prerequisite 不足

Ready:

- review/apply prerequisites がそろっている
- ただし authority 付与の色にはしない

### 3.7 禁止事項

- Google Docs のような free-form editor に寄せない
- artifact を file browser のように扱わない
- provenance / context / decision を secondary tab に押し込めない

## 4. Audit / Boundary / Lifecycle Workspace

### 4.1 目的

この workspace は governance console です。
Chronicle の state を運用・境界・履歴の観点から点検するための場所であり、単なる event log viewer ではありません。

### 4.2 主要ユースケース

- export / review / lifecycle / boundary に関する audit を確認する
- blocker や warning の由来を確認する
- boundary rule がどこに影響しているかを把握する
- lifecycle state の変化と理由を追跡する

### 4.3 推奨レイアウト

2 カラム + 上部 summary rail を基本にします。

- 上部: current governance summary
- 左: event timeline / audit stream
- 右: boundary and lifecycle interpretation panel

#### 上部 summary rail

表示内容:

- recent audit count
- active boundary warning count
- sealed / redacted / tombstoned target count
- current high-priority blocker

#### 左カラム

表示内容:

- audit timeline
- filterable event stream
- event family tabs

#### 右カラム

表示内容:

- selected audit detail
- related boundary rule
- related lifecycle marker
- affected target
- operational implication

### 4.4 主要コンポーネント

#### Governance Summary Header

表示項目:

- current risk summary
- current blocker summary
- recent review-related audit activity
- current boundary-sensitive target count

要件:

- KPI dashboard にしない
- "今の governance 状態" を読む場所にする

#### Audit Timeline

表示項目:

- timestamp
- operation
- actor
- purpose
- target
- severity/result
- linked object

要件:

- chronological だが、ただの log ではなく inspectable record
- operation family ごとの filter を強くする

#### Boundary Rules Table

表示項目:

- rule id
- rule type
- field
- operator
- value
- reason
- current relevance

要件:

- 条件式を読みやすくする
- current UI state と関係ある rule が何か分かる

#### Lifecycle State Panel

表示項目:

- target id
- target kind
- current lifecycle state
- last lifecycle action
- reason class
- reason

要件:

- seal / redact / tombstone を badge に閉じず、意味説明を添える

#### Blocker Detail Panel

表示項目:

- blocker family
- blocker source
- impacted workflow
- recovery hint
- CLI parity / follow-up hint

要件:

- "失敗した" で止めず、何を確認すべきかを示す

### 4.5 一覧 / 詳細 / ドリルダウン

導線:

- governance summary -> filtered audit stream
- audit row -> audit detail
- audit detail -> affected target detail
- audit detail -> related boundary rule
- audit detail -> related lifecycle marker

### 4.6 状態設計

Empty:

- no audit yet
- no active boundary warning
- no lifecycle marker

Warning:

- active warning-level audit
- boundary-sensitive target exists

Blocked:

- apply/review/export workflow が blocker 付き

Ready:

- no critical blocker
- operator can continue with inspection or explicit next step

### 4.7 禁止事項

- security theater 的な見せ方
- meaningless green dashboard
- audit を raw JSON dump に寄せること

## 5. Trust Workspace

### 5.1 目的

Trust Workspace は設定画面ではなく、関係性の意味を読むための場所です。
node、subject、trust relation、withdrawal を、domain / purpose / capability 単位で把握できる必要があります。

### 5.2 主要ユースケース

- 特定 node をどの範囲で trust しているか確認する
- trust relation の purpose / capability の違いを理解する
- package / message workflow にどの trust condition が効くか見る
- assertion と withdrawal の履歴を確認する

### 5.3 推奨レイアウト

3 ペイン構成を推奨します。

- 左: node / subject navigator
- 中央: selected trust graph summary
- 右: relation detail / history / implications

### 5.4 主要コンポーネント

#### Node / Subject Navigator

表示項目:

- node id
- subject id
- relation count
- latest trust activity

要件:

- node と subject を混同させない
- organization、persona、agent proxy を将来区別しやすい構造にする

#### Trust Summary Card

表示項目:

- trust domains
- trust purposes
- capability set
- current level
- active / withdrawn state

要件:

- 単一の trust score に還元しない
- matrix 的に見せてもよいが、読みにくい表にはしない

#### Relation Detail Panel

表示項目:

- relation id
- target node
- subject
- domain
- purpose
- capability
- trust level
- asserted at
- withdrawn at

要件:

- relation の意味を短い natural-language summary でも補助する

#### Trust History Timeline

表示項目:

- assertion
- withdrawal
- delegated actor metadata
- related package / message reference

要件:

- "いま信頼しているか" だけでなく、どう変わったかが重要

#### Federation Impact Panel

表示項目:

- この trust relation が package creation / review / message preview にどう関係するか
- advisory implication
- no-authority note

要件:

- trust が即 permission ではないことを明確にする

### 5.5 一覧 / 詳細 / ドリルダウン

導線:

- node list -> node detail
- node detail -> relation detail
- relation detail -> package / message / consent / audit への関連ジャンプ

### 5.6 状態設計

Empty:

- trust relation not recorded

Warning:

- trust exists but capability is narrower than operator assumption
- withdrawn relation still referenced by operator expectation

Blocked:

- workflow expectation と trust relation が噛み合わない

Ready:

- relevant trust relation is present and current
- ただし authority granted と誤読させない

### 5.7 禁止事項

- trust を reputation score のように見せること
- SNS 的 follower/following 表現に寄せること
- trust = approval = permission と読める UI にすること

## 6. Runtime / Retrieval Workspace

### 6.1 目的

この workspace は AI magic panel ではありません。
Chronicle core の外にある query/runtime を含めた AI-adjacent work を、derived and bounded evidence として読むための場所です。

### 6.2 主要ユースケース

- runtime record を inspect する
- summary job の状態を確認する
- query-engine handoff と downstream trial outcome を確認する
- escalation cue を読み、次に external repo 側で何をすべきか判断する
- AI index / graph summary を derived support として見る

### 6.3 推奨レイアウト

上部 summary + 2 カラム構成を推奨します。

- 上部: runtime posture summary
- 左: runtime records / summary jobs / trials list
- 右: selected detail / handoff / escalation / evidence panel

### 6.4 主要コンポーネント

#### Runtime Posture Summary

表示項目:

- runtime record count
- summary job count
- trial sufficiency trend
- escalation cue count
- advisory auth / mutation / package readiness summary

要件:

- "AI が動いている感" を誇張しない
- 今どこまで inspect できていて、どこから先が external かを示す

#### Runtime Records List

表示項目:

- record kind
- summary
- provider response presence
- advisory / preview-only status
- trial-related status
- linked review state

要件:

- runtime record と query-engine trial を区別できる
- list row だけでも大まかな readiness が読める

#### Summary Jobs List

表示項目:

- summary job id
- target
- current status
- package readiness
- identity / auth advisory
- mutation readiness

要件:

- summary job を単独タスクではなく Chronicle state の一部として見せる

#### Handoff / Trial Detail Panel

表示項目:

- downstream handoff contract summary
- reviewed files
- bundle path
- import-readiness note
- trial sufficiency
- operator next step

要件:

- Chronicle core 内で実行されるものと downstream で実行されるものを明確に分離する
- handoff は execution panel ではなく inspection panel

#### Escalation Cue Panel

表示項目:

- repeated insufficiency signal
- why escalation is suggested
- related runtime records
- local-only issue template or follow-up hint

要件:

- escalation は urgency ではなく evidence-based next step として見せる

#### AI Index / Graph Support Panel

表示項目:

- AI index status
- vector entry summary
- graph node / edge summary
- graph export contract note

要件:

- core product の主役にしない
- derived support layer であることを見失わせない

### 6.5 一覧 / 詳細 / ドリルダウン

導線:

- overview runtime summary -> runtime records filtered list
- runtime row -> runtime detail
- runtime detail -> handoff detail
- handoff detail -> related trial records
- escalation cue -> filtered runtime slice

### 6.6 状態設計

Empty:

- no runtime record yet
- no trial yet
- no handoff generated

Warning:

- advisory only
- preview only
- insufficient trial

Blocked:

- downstream import readiness not met
- required review/audit context missing

Ready:

- sufficient local evidence is present for the next explicit downstream step
- ただし "Chronicle が query engine を実行できる" とは見せない

### 6.7 禁止事項

- AI copilot dashboard のように見せること
- runtime を magical execution surface として描くこと
- Chronicle core と external query runtime の境界を曖昧にすること

## 7. Claude Design への追加指示

Claude Design には、元の仕様書に加えて次の点を必ず反映させてください。

- 4 workspace それぞれに desktop-first の明確な layout grammar を与える
- 右カラムは単なる補助情報置き場ではなく、evidence rail / implication rail として設計する
- list -> detail -> related detail の reconstruction trail を UI の中核に据える
- proposal/review/apply と trust/consent/boundary の位置関係を曖昧にしない
- runtime/retrieval は "AI power" の演出ではなく、bounded evidence と downstream handoff の点検面として描く

## 8. Summary

この追補仕様書の目的は、4 つの workspace を generic な「一覧 + 詳細」画面にしないことです。
それぞれが Chronicle Stack の思想に沿った意味を持つ必要があります。

- Context & Artifact Workbench は semantic revision desk
- Audit / Boundary / Lifecycle は governance console
- Trust Workspace は relation semantics inspector
- Runtime / Retrieval Workspace は bounded evidence and downstream handoff console
