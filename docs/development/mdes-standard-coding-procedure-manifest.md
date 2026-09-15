
## 1. 位置づけ

本マニフェストは、ZYX における標準開発手順を、MDES駆動開発の四相スパイラルに接続するための実行規約である。

MDES は、Manifest–Design–Evolve–Sustain の四相を連続的に回しながら、問題定義、設計、実装、検証、統合、運用、再定義を進める開発メタフレームワークである。

本マニフェストは、その MDES を、GitHub Issue、Roadmap、Milestone、Phase、Epic、Branch、Pull Request、Test、CI、T-RDE に落とし込み、日々のコーディング実務で再現可能にするための標準手順を定義する。

ここで定義する手順は、単なるコーディング規約ではない。  
問題定義から実装、監査、リリース、知識化までを接続する開発プロトコルである。

## 2. 基本思想

ZYX の開発では、コード変更を単なる実装差分として扱わない。

すべての変更は、問題定義、設計意図、検証可能性、意味差分、運用継続性を持つ変更として扱う。

したがって、開発は次の原則に従う。

問題から始める。  
仕様に展開する。  
Roadmap を定義する。  
Milestone を定義する。  
規模に応じて Phase、Epic、Issue に分解する。  
Issue 単位で Branch を切る。  
Prototype First で未知性を下げる。  
Test First / TDD で仕様を実行可能化する。  
CI で再現性を担保する。  
T-RDE で意味差分を監査する。  
main は常に信頼可能な状態に保つ。

ZYX の開発は、速く作るためだけの手順ではない。  
意味を失わず、検証可能な形で、速く深く作るための手順である。

## 3. MDES 四相と開発手順の対応

MDES は、Manifest、Design、Evolve、Sustain の四相からなる。

### 3.1 Manifest

Manifest は、問題空間を明確化するフェーズである。

この段階では、以下を定義する。

問題定義  
背景  
ステークホルダ  
価値仮説  
影響範囲  
KPI  
非目標  
制約条件  
リスク  
受け入れ条件  
撤退条件

Manifest では、何を作るかよりも、なぜ作るのか、何を解くのか、何を解かないのかを明確にする。

GitHub Issue は Manifest の最小単位として扱うことができる。  
ただし、大きな課題では、Issue だけに押し込めず、Problem Canvas、Roadmap、Milestone、Epic、ADR を併用する。

### 3.2 Design

Design は、Manifest で定義された問題に対して、解決構造を設計するフェーズである。

この段階では、以下を作成する。

詳細仕様  
ADR  
API 仕様  
データ構造  
状態遷移  
権限モデル  
エラー処理方針  
テスト設計  
プロトタイプ計画  
T-RDE 観点

Design は、実装前の固定設計ではない。  
脱構築と再設計を含む、仮説形成のフェーズである。

Design フェーズでは、前提を疑い、代替案を比較し、実装可能性だけでなく、意味的整合性と将来運用性を確認する。

### 3.3 Evolve

Evolve は、設計を実装・検証・改善するフェーズである。

この段階では、以下を行う。

Issue 単位の Branch 作成  
Prototype First  
Test First  
TDD  
実装  
リファクタリング  
local act による CI  
テストレポート作成  
Pull Request 作成

Evolve では、動くものを早く作る。  
ただし、検証不能な変更を main に入れてはならない。

Prototype First は、不確実性を下げるための探索である。  
Test First / TDD は、仕様を実行可能な形に固定するための検証である。

### 3.4 Sustain

Sustain は、実装された成果を統合し、運用可能な知識として定着させるフェーズである。

この段階では、以下を行う。

Pull Request Review  
T-RDE  
Release Note  
KPI 確認  
運用ドキュメント更新  
既知制約の記録  
Follow-up Issue 作成  
次サイクルの Manifest 生成

Sustain は完了ではない。  
次の Manifest への接続点である。

MDES における開発は、Sustain で閉じるのではなく、Sustain から次の Manifest に戻ることで継続的に進化する。

## 4. 標準開発フロー

ZYX の標準開発フローは以下とする。

Manifest  
→ Roadmap  
→ Milestone  
→ Phase 分解  
→ Epic 分解  
→ Issue 分解  
→ Design Spec  
→ ADR  
→ Issue Branch  
→ Prototype  
→ Test First  
→ TDD Implementation  
→ local CI  
→ T-RDE  
→ Pull Request  
→ Review  
→ Merge to main  
→ Sustain Review  
→ Next Manifest

このフローは反復可能である。

途中で矛盾、不整合、過剰設計、仕様不足、検証不能性、意味的逸脱が見つかった場合は、前フェーズに戻ることを認める。

ただし、戻った場合は、必ず Issue、仕様、ADR、テスト、T-RDE、Release Note のいずれかに変更理由を記録する。

## 5. Roadmap

Roadmap は、基本仕様を時間軸上に展開した計画である。

Roadmap は、完成形を一度に実装する計画ではない。  
価値を段階的に検証するための順序である。

Roadmap には、以下を含める。

全体目的  
対象プロダクトまたはプロジェクト  
主要 Milestone  
各 Milestone の目的  
想定 Phase  
主要リスク  
主要 KPI  
依存関係  
リリース想定  
撤退または見直し条件

Roadmap は、将来の確定計画ではなく、検証順序を定めるための作業仮説である。

## 6. Milestone

Milestone は、Roadmap 上の検証可能な到達点である。

Milestone は、単なる期限や作業束ではない。  
特定の価値仮説、機能群、運用状態、またはリリース判断を検証するための単位である。

Milestone には、以下を含める。

名称  
目的  
背景  
対象範囲  
非対象範囲  
含める成果物  
含めない成果物  
主要 KPI  
完了条件  
テスト条件  
T-RDE 判定条件  
リリース可否判断  
次 Milestone への接続条件

Milestone は、規模に応じて Phase、Epic、Issue に分解する。

小規模な変更では、Milestone を作らず Issue のみで管理してよい。  
中規模の変更では、Milestone を複数 Issue に分解する。  
大規模な変更では、Milestone を MDES Phase に分解する。  
さらに大規模な変更では、各 Phase の下に Epic を置き、Epic を Issue に分解する。

したがって、標準階層は以下とする。

Project / Product  
→ Roadmap  
→ Milestone  
→ Phase  
→ Epic  
→ Issue  
→ Branch  
→ Pull Request

ただし、これは最大構成であり、すべての開発で全階層を必須とするものではない。

## 7. Phase

Phase は、Milestone を MDES の四相に沿って分解した進行単位である。

標準 Phase は以下とする。

Manifest  
Design  
Evolve  
Sustain

Phase は、Milestone の中で現在どの種類の作業を行っているかを示す。

Manifest Phase では、問題、背景、価値仮説、ステークホルダ、KPI、非目標を定義する。

Design Phase では、仕様、ADR、アーキテクチャ、テスト設計、プロトタイプ計画を定義する。

Evolve Phase では、Prototype First、Test First、TDD、実装、CI を行う。

Sustain Phase では、統合、T-RDE、リリース、運用知識化、次サイクルへの接続を行う。

Phase は、GitHub Label としても表現できる。  
ただし、Phase はラベルそのものではない。

Label は Phase を可視化する補助メタデータであり、管理単位そのものではない。

## 8. Epic

Epic は、Phase 内の大きな問題領域、機能領域、または設計判断領域を表す。

Epic は、複数の Issue を束ねる意味的まとまりである。

Epic には、以下を含める。

背景  
目的  
対象ユーザー  
対象機能  
対象外機能  
関連仕様  
関連 ADR  
含める Issue  
含めない Issue  
受け入れ条件  
T-RDE 観点  
完了条件

Epic は、Milestone の完了に必要な意味的まとまりを表す。

Epic が大きくなりすぎた場合は、さらに複数の Epic に分割する。

Epic は、単なる作業グループではない。  
問題、仮説、設計、実装、検証を束ねる単位である。

## 9. Issue

Issue は、実装、調査、仕様化、テスト、監査、ドキュメント化の最小作業単位である。

Issue は、原則として 1 Branch、1 Pull Request に対応する。

Issue には、以下を含める。

Problem Statement  
関連 Roadmap  
関連 Milestone  
関連 Phase  
関連 Epic  
背景  
目的  
対象範囲  
非対象範囲  
受け入れ条件  
テスト計画  
T-RDE チェック項目  
依存関係  
リスク  
完了定義

Issue は、単なる作業依頼ではない。  
Manifest または Design から Evolve へ移行するための実行単位である。

Issue が複数の目的、複数の受け入れ条件、複数の PR を必要とする場合は、Issue を分割する。

## 10. Branch

main ブランチへの直接編集は禁止する。

すべての変更は Issue 単位の Branch で行う。

Branch は、変更の作業単位である。  
Pull Request は、変更の統合審査単位である。

ブランチ命名は以下を標準とする。

feature/issue-123-short-name  
fix/issue-123-short-name  
docs/issue-123-short-name  
refactor/issue-123-short-name  
test/issue-123-short-name  
ci/issue-123-short-name  
prototype/issue-123-short-name  
audit/issue-123-short-name  
hotfix/issue-123-short-name

prototype Branch は探索用であり、そのまま main に統合してはならない。

Prototype の成果を本実装に反映する場合は、別途 feature、fix、refactor などの Branch を作成する。

## 11. Label

Label は、Milestone、Phase、Epic、Issue の状態を横断的に検索・可視化するための補助メタデータである。

Label は、管理階層そのものではない。  
Label は、状態、種別、優先度、影響範囲、KPI、ドメイン、リスク、監査条件、リリース条件を表す分類情報である。

前提として、管理階層は以下である。

Project / Product  
→ Roadmap  
→ Milestone  
→ Phase  
→ Epic  
→ Issue  
→ Branch  
→ Pull Request

この階層のうち、Label が担うのは分類と可視化である。  
Milestone、Phase、Epic、Issue の代替として Label を使ってはならない。

特に、phase:manifest、phase:design、phase:evolve、phase:sustain は、Issue や Epic が MDES のどの Phase に属するかを示す補助情報である。  
Phase そのものを Label だけで管理してはならない。

### 11.1 標準 Label

Label は、Milestone、Phase、Epic、Issue を横断して検索・集計・可視化するための補助メタデータである。

Label は管理階層そのものではない。  
Milestone、Phase、Epic、Issue の構造を Label で代替してはならない。

標準 Label は以下とする。

|カテゴリ|プレフィックス|値例|用途|
|---|---|---|---|
|MDES Phase|`phase:`|`manifest`, `design`, `evolve`, `sustain`|Issue または Epic が MDES のどの進行相に属するかを示す|
|作業種別|`type:`|`feature`, `bug`, `doc`, `task`, `research`, `prototype`, `audit`, `adr`, `test`, `ci`|Issue / PR の作業内容または成果物種別を分類する|
|状態|`status:`|`triage`, `ready`, `in-progress`, `blocked`, `review`, `done`, `deferred`|Issue / Epic / PR の現在状態を示す|
|優先度|`priority:`|`p0`, `p1`, `p2`, `p3`|対応順序と緊急度を示す|
|影響度|`impact:`|`high`, `medium`, `low`|事業・利用者・技術基盤への影響範囲を示す|
|難易度|`difficulty:`|`xs`, `s`, `m`, `l`, `xl`|実装・調査・検証の見積もり粒度を示す|
|KPI|`kpi:`|`mttr`, `nps`, `roi`, `pass-rate`, `latency`, `reliability`, `security`|成果測定または改善対象となる指標を示す|
|ドメイン|`domain:`|`kazane`, `sayane`, `ai-banto`, `chronicle-stack`, `luxcore`, `luxaide`, `mdes-orbit`|対象プロダクト、サブシステム、事業領域を示す|
|リスク|`risk:`|`security`, `privacy`, `migration`, `performance`, `compatibility`, `data-loss`|注意すべきリスク領域を示す|
|監査|`audit:`|`t-rde-required`, `t-rde-light`, `t-rde-full`, `security-review`, `adr-required`|必要な監査・レビュー条件を示す|
|リリース|`release:`|`breaking-change`, `migration-required`, `release-blocker`, `docs-required`|リリース判断に関わる条件を示す|

#### 11.1.1 Label 値の例

実際の Label は、以下のような形式になる。

`phase:manifest`  
`phase:design`  
`phase:evolve`  
`phase:sustain`

`type:feature`  
`type:bug`  
`type:prototype`  
`type:audit`

`status:triage`  
`status:in-progress`  
`status:blocked`  
`status:review`

`priority:p0`  
`priority:p1`

`impact:high`  
`difficulty:m`

`kpi:latency`  
`kpi:security`

`domain:kazane`  
`domain:sayane`

`risk:privacy`  
`risk:migration`

`audit:t-rde-full`  
`audit:adr-required`

`release:breaking-change`  
`release:docs-required`

#### 11.1.2 Label 使用例

以下の Label が付いた Issue があるとする。

`phase:evolve`  
`type:feature`  
`status:in-progress`  
`priority:p1`  
`impact:high`  
`difficulty:m`  
`domain:kazane`  
`audit:t-rde-light`

この Issue は、Kazane に関する Evolve フェーズの機能開発であり、進行中、優先度 P1、影響度高、難易度 M、軽量 T-RDE が必要であることを示す。

別の例として、以下の Label が付いた Issue があるとする。

`phase:design`  
`type:adr`  
`status:review`  
`priority:p1`  
`domain:chronicle-stack`  
`risk:compatibility`  
`audit:adr-required`

この Issue は、Chronicle Stack に関する Design フェーズの ADR 作成または審査であり、互換性リスクを伴い、ADR 記録が必須であることを示す。

### 11.2 Label 命名規約

Label は小文字ケバブケースを原則とする。

値は短く、検索可能で、GitHub Projects や GitHub Actions と連動しやすい名前にする。

新規 domain Label を追加する場合は、Pull Request で追加理由を明記する。

新規 Label カテゴリを追加する場合は、既存カテゴリで表現できない理由を明記する。

phase Label と status Label は、自動化可能な場合、GitHub Projects または GitHub Actions と連動させる。

### 11.3 Label の使用原則

Label は検索、集計、可視化、自動化のために使用する。

Label によって、Milestone、Phase、Epic、Issue の構造を代替してはならない。

Milestone は到達点である。  
Phase は進行相である。  
Epic は意味的まとまりである。  
Issue は作業単位である。  
Branch は変更単位である。  
Pull Request は統合審査単位である。  
Label は分類・検索・可視化のためのメタデータである。

この区別を崩すと、MDES が単なるラベル運用に矮小化されるため、禁止する。

### 11.4 禁止される Label 運用

Label を Milestone の代わりに使ってはならない。

Label を Epic の代わりに使ってはならない。

`phase:` だけで MDES の進行管理を完結させてはならない。

`status:` と `phase:` を混同してはならない。

`type:prototype` を付けた Issue の成果物を、そのまま Production Code として main に統合してはならない。

`audit:t-rde-full` が付いた Issue または PR は、完全 T-RDE を完了するまで main に統合してはならない。

`release:breaking-change` が付いた PR は、移行手順、Release Note、互換性影響の記録を必須とする。

## 12. 分解ルール

開発対象は、規模に応じて以下のように分解する。

小規模変更では、Issue のみで管理してよい。

中規模変更では、Milestone を作成し、複数の Issue を束ねる。

複数の設計判断、複数の実装領域、複数のリリース判断を含む場合は、Milestone を Phase に分解する。

Phase 内に複数の意味的まとまりがある場合は、Epic を作成する。

Epic が大きくなりすぎた場合は、複数の Epic に分割する。

Issue が複数の目的、複数の受け入れ条件、複数の PR を必要とする場合は、Issue を分割する。

原則は以下である。

Milestone は到達点である。  
Phase は進行相である。  
Epic は意味的まとまりである。  
Issue は作業単位である。  
Branch は変更単位である。  
Pull Request は統合審査単位である。

## 13. Prototype First

未知性が高い機能、外部依存が大きい機能、UI/UX の妥当性が不明な機能、性能上の不確実性が高い機能では、Prototype First を原則とする。

Prototype の目的は、完成コードを書くことではない。  
不確実性を下げ、Design を更新することである。

Prototype では、以下を明記する。

検証仮説  
最小動作  
検証結果  
本実装へ持ち込む要素  
本実装へ持ち込まない要素  
発見された制約  
更新すべき仕様  
次の Issue

Prototype は Evolve の前段であり、Production Code ではない。

Prototype Branch をそのまま main に統合してはならない。

Prototype の成果を本実装へ移す場合は、新たに本実装用 Issue と Branch を作成する。

## 14. Test First / TDD

本実装では Test First を原則とする。

TDD は以下のサイクルで行う。

Red  
失敗するテストを書く。

Green  
最小実装でテストを通す。

Refactor  
設計を整える。

Review  
仕様意図との一致を確認する。

T-RDE  
意味差分を監査する。

テストは仕様の実行可能な表現である。

テストが存在しない仕様は、実装上の保証を持たない。

テストには、以下を含める。

Unit Test  
Integration Test  
Contract Test  
Regression Test  
Permission Test  
Security Test  
Error Handling Test  
Migration Test  
CLI Smoke Test  
API Smoke Test  
T-RDE 用の意味差分確認テスト

TDD は、設計を硬直させるための手順ではない。  
仕様仮説を実行可能にし、リファクタリングを安全にするための手順である。

## 15. CI

CI は原則として local act によりローカルで再現可能にする。

GitHub Actions を使う場合でも、可能な限り act で同等の検証ができる構成にする。

CI は以下を含む。

format check  
lint  
type check  
unit test  
integration test  
contract test  
security check  
dependency check  
build  
smoke test  
artifact validation

Pull Request 作成前に local act を通すことを原則とする。

CI は fast CI と full CI に分離してよい。

fast CI は日常開発用である。  
full CI は PR 前、release 前、重要変更時に実行する。

CI が重すぎる場合でも、最低限の fast CI は必ず通す。

CI は開発速度を落とすための装置ではない。  
変更の再現性を保証し、main を壊さないための安全機構である。

## 16. T-RDE

T-RDE は Test-with-Resonant Deviation Evaluator とする。

T-RDE は、コード変更が元の Manifest、Design、Issue、ADR、Test Spec からどのように意味変化したかを監査する。

T-RDE は品質採点ではない。  
意味差分監査である。

T-RDE では以下を確認する。

保存された要素  
変換された要素  
補完された要素  
未解決の要素  
逸脱リスク  
次回更新方針

特に以下を重点確認する。

元仕様より強い主張になっていないか。  
未検証の挙動を保証済みに見せていないか。  
Prototype 由来の暫定実装が混入していないか。  
実装上の便宜が設計思想を歪めていないか。  
権限モデルが弱体化していないか。  
ログ、監査、復旧可能性が失われていないか。  
テストが仕様ではなく実装都合だけを固定していないか。  
Sustain に必要な運用知識が残されているか。

T-RDE は、軽量 T-RDE と完全 T-RDE に分けてよい。

通常 Issue では軽量 T-RDE を行う。  
重要 Issue、Architecture Change、Release、Security Change では完全 T-RDE を行う。

### 16.1 軽量 T-RDE

軽量 T-RDE は、通常 Issue または小規模 PR に対して行う。

軽量 T-RDE では、最低限以下を確認する。

元 Issue の目的は保存されているか。  
実装が Issue の範囲を超えていないか。  
テストで受け入れ条件が確認されているか。  
未解決事項が Follow-up Issue に分離されているか。  
main に統合してよい既知リスクか。

### 16.2 完全 T-RDE

完全 T-RDE は、重要 Issue、Architecture Change、Security Change、Breaking Change、Release 前に行う。

完全 T-RDE では、以下を記録する。

対象 Issue / PR / Milestone  
元 Manifest の意図  
元 Design の意図  
保存された要素  
変換された要素  
補完された要素  
未解決の要素  
逸脱リスク  
テストとの対応  
CI 結果  
Sustain への影響  
次回更新方針  
判定

判定は以下のいずれかとする。

Accept  
Accept with Follow-up Issue  
Request Changes  
Reject

## 17. Pull Request

Pull Request は、Issue に対応して作成する。

Pull Request には、以下を含める。

Related Issue  
Related Milestone  
Related Phase  
Related Epic  
Change Summary  
Design Difference  
Test Result  
local act Result  
T-RDE Result  
Known Limitations  
Follow-up Issues  
Review Focus

Pull Request は、Issue で定義された範囲を超えてはならない。

範囲を超える発見があった場合は、新しい Issue を作成する。

Pull Request は、単なるコード統合依頼ではない。  
Issue で定義された問題、仕様、検証、意味差分を main に統合してよいかを審査する単位である。

## 18. Review

Review は、コードの正しさだけでなく、仕様意図、テスト妥当性、将来保守性、T-RDE 差分を確認する。

Review では以下を確認する。

仕様に合っているか。  
Issue の範囲を超えていないか。  
テストが十分か。  
エラー処理が適切か。  
権限・セキュリティが保たれているか。  
ログ・監査可能性があるか。  
過剰抽象化していないか。  
将来拡張を妨げていないか。  
T-RDE 上の逸脱が許容範囲か。  
Sustain に必要な記録が残っているか。

Review は、実装者を止めるための手続きではない。  
main の意味的一貫性を守るための手続きである。

## 19. main 統合条件

main に統合できる条件は以下とする。

Issue に対応している。  
Issue 単位の Branch で作業されている。  
Pull Request が作成されている。  
必要なテストが通っている。  
local act による CI が通っている。  
T-RDE が実施されている。  
Review 指摘が解消されている。  
未解決事項が明示されている。  
main への直接編集でない。  
破壊的変更の場合は移行方針がある。  
必要なドキュメントが更新されている。

main は常に動作可能であることを原則とする。

main が壊れた場合は、最優先で修復する。

## 20. ADR

設計判断は ADR として記録する。

ADR には以下を含める。

Context  
Decision  
Alternatives  
Consequences  
Rejected Options  
T-RDE Notes  
Related Issues  
Related PRs

ADR は Design フェーズの成果物であり、Sustain フェーズで運用知識として再評価される。

ADR は、設計判断の勝者だけを記録するものではない。  
なぜ他の案を採用しなかったかも記録する。

ADR は、後から「なぜこうなっているのか」を理解するための来歴保存である。

## 21. Documentation

コード変更には、必要に応じてドキュメント変更を伴わせる。

仕様、README、設計文書、ADR、運用手順、テスト方針のいずれかに影響する変更は、対応する文書を更新する。

ドキュメントは、実装の説明だけではない。  
判断の来歴を保存するために書く。

Issue は短期作業管理である。  
ADR は設計判断の保存である。  
T-RDE は意味差分の監査記録である。  
Release Note は外部化された変更履歴である。  
Obsidian などの Knowledge Base は、長期文脈管理である。

## 22. Obsidian / Knowledge Base 連携

Issue、ADR、T-RDE、Release Note は、必要に応じて Obsidian などの知識基盤にミラーリングする。

目的は、GitHub 上の作業履歴を、長期的な文脈知識として再利用可能にすることである。

GitHub は実行管理に強い。  
Obsidian は意味連結と長期記憶に強い。

両者は競合しない。  
GitHub は作業の現在を扱い、Obsidian は思考と来歴の持続を扱う。

Knowledge Base には、単なる完了結果だけでなく、判断の理由、却下された案、未解決の問い、次に検証すべき仮説も保存する。

## 23. MDES-Orbit への拡張

将来的には、GitHub Issue を補完する MDES-Orbit を導入する。

MDES-Orbit は、問題、仮説、反証、KPI、ADR、T-RDE、PR、Release をグラフとして管理する。

その目的は、以下を実現することである。

Problem as Graph  
Dialectic Threads  
Spiral Analytics  
LLM Assist  
Semantic Search  
Obsidian Sync  
KPI Hooks  
Dialectic Diff View

初期段階では、GitHub Issue、GitHub Projects、ADR、T-RDE、Obsidian ミラーリングで運用する。

必要に応じて、MDES-Orbit に移行する。

MDES-Orbit は、GitHub を置き換えるためのものではない。  
MDES の意味論的追跡能力を補完・拡張するための基盤である。

## 24. Release

Release は、単なるタグ付けではない。  
仕様状態の確定である。

Release 前には、以下を確認する。

対象 Milestone の完了  
対象 Phase の完了状態  
対象 Epic の完了状態  
変更履歴  
破壊的変更  
移行手順  
既知の制約  
セキュリティ影響  
ドキュメント更新  
サンプル更新  
CI 結果  
T-RDE Release 監査  
次 Milestone への接続

Release Note には、利用者に見える変更だけでなく、運用上重要な制約と既知リスクを記録する。

Release 後には、Sustain Review を行い、次の Manifest に接続する。

## 25. Definition of Done

Issue の完了には以下を必要とする。

実装が完了している。  
テストが存在する。  
テストが通っている。  
local act が通っている。  
T-RDE が記録されている。  
必要なドキュメントが更新されている。  
Pull Request がレビューされている。  
main へ直接編集していない。  
未解決事項が Follow-up Issue に分離されている。

Milestone の完了には以下を必要とする。

含まれる Issue が完了している。  
主要 KPI が確認されている。  
必要な T-RDE が完了している。  
Release 可否判断が記録されている。  
次 Milestone または次 Manifest への接続が定義されている。

Release の完了には以下を必要とする。

Release Note が作成されている。  
移行手順が明示されている。  
既知制約が記録されている。  
必要なタグが作成されている。  
Sustain Review が実施されている。  
次の Manifest または Follow-up Issue が作成されている。

## 26. 禁止事項

main への直接編集は禁止する。

Issue なしの実装は禁止する。

テストなしの本実装は禁止する。

Prototype の無審査統合は禁止する。

CI 未実行の Pull Request は原則禁止する。

T-RDE なしの重要変更は禁止する。

仕様変更をコードだけで行うことは禁止する。

未検証の主張を README や仕様に書くことは禁止する。

一時対応を恒久仕様に見せることは禁止する。

Label によって Milestone、Phase、Epic、Issue の管理階層を代替することは禁止する。

main を壊れた状態で放置することは禁止する。

Security、Privacy、Migration、Breaking Change に関わる変更を、通常 Issue と同じ軽さで扱うことは禁止する。

## 27. 例外

緊急修正では hotfix Branch を認める。

ただし、hotfix でも main への直接編集は禁止する。

hotfix は最小変更、最小テスト、最小 T-RDE を行う。

統合後、通常 Issue として再監査する。

例外は記録されなければならない。

例外を標準運用にしてはならない。

## 28. 結語

MDES は、問題から始まる。  
Roadmap は、検証順序を定める。  
Milestone は、到達点を定める。  
Phase は、進行相を示す。  
Epic は、意味的まとまりを束ねる。  
Issue は、作業を実行可能にする。  
Branch は、変更を隔離する。  
Pull Request は、統合を審査する。  
Test は、仕様を実行可能にする。  
CI は、再現性を守る。  
T-RDE は、意味の逸脱を監査する。  
Sustain は、成果を次の Manifest へ接続する。

ZYX の開発は、実装速度と意味保存を対立させない。  
探索し、検証し、監査し、統合し、次の問題へ進む。