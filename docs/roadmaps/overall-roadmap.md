# Chronicle Stack 全体ロードマップ

Status: Draft  
Scope: Integrated roadmap across existing `docs/` roadmap documents  
Author: Tomoyuki Kano  
Related:

- `docs/specs/roadmap-linkage-v0.1.md`
- `docs/roadmaps/roadmap-v0.4.md`
- `docs/roadmaps/roadmap-v0.5.md`
- `docs/federation/requirements.md`
- `docs/roadmaps/federation-implementation-roadmap.md`
- `docs/future/README.md`

## 1. 目的

この文書は、Chronicle Stack の `docs/` 配下に分散している個別ロードマップを精査し、全体ロードマップとして統合するための文書である。

既存文書には、v0.1 基本仕様から後続段階への接続を示す `roadmap-linkage-v0.1`、v0.4 の Operational Readiness Layer、v0.5 の Security-aware Composition and Integration Layer、将来構想を隔離する `docs/future/`、および分散連合拡張ロードマップが存在する。これらはそれぞれ有用だが、時期、粒度、対象レイヤーが異なるため、単一の実装順序として読むには整理が必要である。

本ロードマップは、これらを次の原則で統合する。

1. `chronicle.jsonl` を一次記録とする local-first 原則を維持する。
2. 派生Index、Graph、Dashboard、UI、AI index、export package は再生成可能な派生面として扱う。
3. 外部AI送信、公開、連合、再解釈、撤回は高リスク操作として境界と監査を先に整える。
4. 分散連合はネットワーク機能から始めず、export/import package、Manifest、検証、redaction、consent から始める。
5. future concept は製品可能性として保持するが、安定インターフェースやリリース約束とは分ける。

## 2. 精査対象文書と読み替え

### 2.1 `docs/specs/roadmap-linkage-v0.1.md`

この文書は、v0.1 の設計要素が v0.2 以降のどの段階へ接続するかを示す初期ロードマップである。重要なのは、v0.1 の空白を「未実装」ではなく「後続段階への接続点」として扱っている点である。

保持すべき要素は、JSONL一次記録、Event 経由の状態変更、ID prefix 体系、外部送信の明示性である。これらは現在の全体ロードマップでも横断的防衛線として維持する。

読み替えが必要な点は、当初の v0.3 / v0.4 / v0.5 / v0.6 の名称と、現在の実装済みリリース番号が一致しないことである。したがって、この文書は「リリース番号の確定表」ではなく、「設計接続表」として扱う。

### 2.2 `docs/roadmaps/roadmap-v0.4.md`

この文書は、Operational Readiness Layer のロードマップである。対象は `chronicle doctor`、Export Manifest、Redaction-aware Export、Dashboard navigation/filtering、Graph export inspection である。

保持すべき要素は、運用診断、export provenance、redaction-aware export、static read-only dashboard、Graph inspection である。

特に重要な防衛線は、redaction-aware export は access control ではない、export manifest は cryptographic proof ではない、graph inspection は GraphRAG engine ではない、dashboard filtering は live dashboard ではない、という区別である。

このロードマップは、全体ロードマップでは「Operational Readiness Baseline」として位置づける。

### 2.3 `docs/roadmaps/roadmap-v0.5.md`

この文書は、Security-aware Composition and Integration Layer のロードマップである。v0.5 は連携機能を増やす版ではなく、連携しても文脈主権を壊さないための版として定義されている。

保持すべき要素は、classification metadata、operation permission model、LLM injection policy、prompt-injection sanitizer boundary、export / inject / reinterpret auditability、redact / seal / tombstone lifecycle、integrity metadata、security-aware export profiles である。

このロードマップは、全体ロードマップでは「Security and Boundary Baseline」として位置づける。分散連合やAI連携へ進む前に、必ずここを通過する。

### 2.4 `docs/federation/requirements.md`

この文書は、Chronicle Stack を AI時代の文脈SNSとして成立させるための要求仕様である。中心要求は、各主体が文脈正本をローカルに保持し、共有可能な意味だけを、来歴、権限、撤回可能性、監査証跡付きで連合できることである。

保持すべき要素は、ローカル正本、最小共有、来歴必須、可逆・撤回・減衰、AI非依存、RDE監査、分散連合、Node モデル、Chronicle オブジェクト、共有範囲、信頼モデル、AI連携、文脈SNS UI である。

この文書は、全体ロードマップでは「長期要求の上位仕様」として扱う。実装順序を直接決める文書ではなく、各実装フェーズが逸脱していないかを検査する基準である。

### 2.5 `docs/roadmaps/federation-implementation-roadmap.md`

この文書は、分散連合拡張を Phase 0 から Phase 9 へ分解した実装計画である。

保持すべき要素は、Baseline Alignment、Local Federation Package、Signed Manifest and Verification、Context Boundary Enforcement、Chronicle Object Expansion、Federation Message MVP、Node Trust Model、Sayane / AI Adapter Integration、Context SNS Surface、Networked Federation である。

この文書は、全体ロードマップでは「Federation Track」として扱う。ただし、Federation Track は Operational Readiness と Security / Boundary の上に載るものであり、単独で先行させない。

### 2.6 `docs/future/README.md`

この文書は、将来構想を安定仕様やリリース約束から分離するための領域を定義している。

保持すべき要素は、future concept は speculative であり、current stable interface contract ではなく、release commitment でもないという境界である。

この文書は、全体ロードマップでは「Future Concept Parking Lot」として扱う。

## 3. 統合判断

個別ロードマップを統合すると、Chronicle Stack の発展は次の四つの主系列に整理できる。

第一に、Core / Local-first Track である。これは JSONL一次記録、Context、Artifact、Decision、RDE、Boundary、Audit、Lifecycle、Review、Export、UI を安定させる主系列である。

第二に、Security / Boundary Track である。これは classification、allowed operations、redaction、seal、tombstone、LLM injection policy、audit、integrity metadata を扱う。

第三に、AI / Retrieval Track である。これは local runtime summarize、retrieval dry-run、placeholder AI index、将来の GraphRAG query engine、Sayane / AI Adapter 連携を扱う。ただし外部AI接続は、文脈境界が整うまで拡大しない。

第四に、Federation / Context SNS Track である。これは federation package、signed manifest、context boundary enforcement、Chronicle object expansion、federation message、trust model、Context SNS surface、networked federation を扱う。

この四系列は並列ではなく、依存関係を持つ。Federation / Context SNS Track は、Security / Boundary Track と Core / Local-first Track の上に載る。AI / Retrieval Track は、Security / Boundary Track と RDE の上に載る。

## 4. 全体ロードマップ

### Stage A: Core Baseline Preservation

主題は、local-first な一次記録と再構成可能性を壊さないことである。

対象は、JSONL一次記録、Event 経由の状態変更、ID prefix 体系、Context、Artifact、Decision、RDE Diff Record、Source Provenance、Boundary Rule、Audit、Lifecycle、Review Queue、read-only UI、export である。

完了条件は、既存実装の安定性を維持し、派生IndexやUIが一次記録に昇格しないこと、状態変更が Event と audit によって追跡可能であること、既存 interface contract を破壊しないことである。

非対象は、GraphRAG engine、外部AI自動接続、クラウド同期、連合プロトコル、書き込み可能GUIである。

### Stage B: Operational Readiness Baseline

主題は、継続運用できるローカル基盤にすることである。

対象は、doctor、Export Manifest、Redaction-aware Export、Dashboard navigation/filtering、Graph export inspection、release readiness、smoke test、read-only local UI smoke である。

完了条件は、Chronicle root の健全性を診断でき、export の生成元とオプションを追跡でき、redaction-aware export を明示的 opt-in として扱え、Graph / Dashboard / UI が派生ビューであることを維持できることである。

非対象は、自動修復、暗号署名、access control、live dashboard、GraphRAG engine である。

### Stage C: Security and Boundary Baseline

主題は、連携しても文脈主権を壊さないための安全境界を整えることである。

対象は、classification metadata、allowed operation model、LLM injection policy、prompt-injection sanitizer boundary、export / inject / reinterpret audit、redact / seal / tombstone lifecycle、integrity metadata、doctor security checks、security-aware export profiles である。

完了条件は、read / export / inject / reinterpret / publish が区別され、外部AI投入前に dry-run または check ができ、機密分類、retention、masking requirement、audit metadata が記録可能であることである。

非対象は、完全なRBAC / ABAC、tenant isolation、クラウドIAM連携、完全なprompt-injection防止、remote attestation である。

### Stage D: AI / Retrieval Boundary Expansion

主題は、AI利用と検索拡張を、文脈境界とRDE監査の下で拡張することである。

対象は、placeholder AI index、local runtime summarize、retrieval dry-run plan、AI boundary preview、AI response と user statement の分離、AI interpretation の decay 対象化、RDE draft helper、将来の GraphRAG query engine の準備である。

完了条件は、外部AIへ送る文脈が明示的に確認され、AI応答がユーザー発言や事実記録と混ざらず、AI推測が恒久属性化されず、RDE Diff Record または Delta Chronicle として意味変化が再構成可能であることである。

非対象は、特定AI事業者への固定接続、AIの正しさ保証、自動人格推定、無制限の文脈投入である。

### Stage E: Federation Package Foundation

主題は、ネットワーク連合の前に、手動共有できる安全な federation package を作ることである。

対象は、federation package create / inspect / verify、package Manifest、records bundle、contexts、artifacts、rde、audit、lifecycle、redaction report、README、import preview である。

完了条件は、ローカル正本を変更せずに共有パッケージを作成でき、共有目的、共有範囲、保存期間、再共有可否、含有データ、警告を inspect でき、Manifest 整合性を verify でき、受信側が import 前に preview できることである。

非対象は、自動送信、ノード間常時同期、双方向連合、撤回伝播である。

### Stage F: Signed Manifest and Integrity

主題は、改ざん検知と由来確認を、将来のDID/PoP/ZKPへ拡張可能な形で導入することである。

対象は、Manifest schema、file hash、package id、created_by_node、purpose、visibility、retention policy、tool version、signature placeholder、manifest verify、warning classification である。

完了条件は、署名あり、署名なし、署名不一致、hash不一致、期限切れ、Revoked を区別でき、package review または import preview で検証結果を表示できることである。

非対象は、本格DID、ブロックチェーン、PoP本人性証明、鍵管理UIである。

### Stage G: Chronicle Object Expansion

主題は、投稿ではなく、問い、判断、反論、仮説、差分、減衰を第一級の意味単位として扱うことである。

対象は、Question Chronicle、Conversation Chronicle、Decision Chronicle、Artifact Chronicle、Delta Chronicle、Objection Chronicle、Hypothesis Chronicle、Decay Chronicle である。

完了条件は、新 object type が JSONL event または派生Indexとして表現でき、既存 export が壊れず、read-only UI で一覧または detail を確認でき、RDE Diff Record と Delta Chronicle の関係が明示されることである。

非対象は、完全な ontology 管理、GraphRAG query engine、書き込み可能GUIである。

### Stage H: Federation Message MVP

主題は、連合で交換する意味メッセージを、まずファイルベースまたは local queue ベースで扱うことである。

対象は、Publish Chronicle、Request Context、Grant Context、Deny Context、Revoke Context、Update Chronicle、Fork Chronicle、Reference Chronicle、Object Chronicle、Audit Chronicle、Decay Notice である。

完了条件は、federation message envelope を作成、保存、inspect でき、受信メッセージが自動適用されず、preview / review 経由となり、revoke / decay が監査ログに残ることである。

非対象は、HTTP配送、ActivityPub互換、リアルタイム同期である。

### Stage I: Node Trust Model

主題は、ノード間の信頼関係、署名、鍵、委譲、代理行為を文脈別に扱うことである。

対象は、Node profile schema、Node ID、Subject ID、trust relation、Trust Assertion、Trust Withdrawal、delegated actor metadata、AI proxy generation metadata である。

完了条件は、信頼関係を追加、撤回、一覧表示でき、federation package / message 作成時に trust relation を参照でき、信頼が単一スコアではなく domain / purpose / capability ごとに扱われることである。

非対象は、グローバルID基盤、ブロックチェーン信用証明、自動信用スコアリングである。

### Stage J: Context SNS Surface

主題は、Chronicle Stack を注意経済型タイムラインではなく、問い、判断、反論、再審、共同編集を中心にした文脈SNSとして見せることである。

対象は、Lineage View、Delta View、Context Boundary View、Objection View、Decay View、Trust View、AI Involvement View、問いフォロー、Chronicle購読、意味ある反応型である。

完了条件は、ひとつの方針や成果物について、由来となる問い、関連会話、判断、差分、反論、RDEをたどれ、反応が単なる「いいね」ではなく意味関係として記録されることである。

非対象は、広告配信、ランキング最適化、エンゲージメント最大化、中央タイムラインである。

### Stage K: Networked Federation

主題は、package、Manifest、境界、message、trust が整った後に、ノード間の実通信を導入することである。

対象は、Node discovery、inbox/outbox queue、signed message verification、Publish / Request / Grant / Deny / Revoke / Audit の最小交換、ActivityPub bridge 検討、Chronicle-native protocol 検討である。

完了条件は、中央サーバーが文脈正本を保持せず、受信メッセージが自動適用されず、撤回、期限切れ、Tombstone が監査ログ付きで扱え、ネットワーク機能が local-first 原則を壊さないことである。

非対象は、完全なグローバルSNS運用、未承認ノードからの自動取り込み、中央管理DB化である。

### Stage L: Future Concept Graduation

主題は、`docs/future/` の構想を、研究ノート、製品仕様、実装Issue、または保留に分類することである。

対象は、music context sovereignty などの future concept、外部プロダクト展開、研究開発候補、応用領域である。

完了条件は、future concept が安定仕様や release commitment と混同されず、実装対象に昇格する場合は、要求仕様、非目的、受け入れ条件、RDE差異検証を持つことである。

非対象は、future concept の即時実装、安定インターフェースへの無審査追加である。

## 5. 依存関係

全体の依存関係は次の通りである。

```text
Stage A Core Baseline Preservation
  -> Stage B Operational Readiness Baseline
  -> Stage C Security and Boundary Baseline
      -> Stage D AI / Retrieval Boundary Expansion
      -> Stage E Federation Package Foundation
          -> Stage F Signed Manifest and Integrity
          -> Stage G Chronicle Object Expansion
          -> Stage H Federation Message MVP
              -> Stage I Node Trust Model
              -> Stage J Context SNS Surface
              -> Stage K Networked Federation

Stage L Future Concept Graduation は全段階から独立した保留・昇格レーンとして扱う。
```

注意すべき点は、AI / Retrieval Track と Federation Track が Stage C 以降で分岐することである。どちらも便利さを急ぐと文脈主権を壊すため、Stage C の security / boundary baseline を通過条件とする。

## 6. 優先順位

短期優先は、Stage C までの整合確認と、Stage E / F の package + Manifest foundation である。

理由は、Chronicle Stack はすでに local-first の記録基盤、export、UI、runtime surface を持っているため、次に必要なのは「外へ出す前の安全な境界」である。GraphRAG query engine や networked federation を急ぐより、package、Manifest、redaction、consent、verify、preview を先に固める方が、文脈主権に忠実である。

中期優先は、Stage G / H / I である。Chronicle object と federation message と trust model がなければ、連合は単なるファイル共有または投稿配送に堕する。

長期優先は、Stage J / K である。文脈SNS UI と networked federation は魅力的だが、早すぎると既存SNSの模倣、中央化、注意経済化へ逸脱する。

## 7. 推奨Issue化

### Epic 1: Overall roadmap alignment

- Add integrated overall roadmap.
- Add source roadmap mapping table.
- Add dependency graph between Core, Security, AI/Retrieval, Federation, Future.
- Add README or architecture reference to overall roadmap.

### Epic 2: Security / boundary consolidation

- Reconcile v0.5 classification metadata with existing context classification implementation.
- Define operation permission model for export / inject / reinterpret / publish.
- Add or update security-aware export profile documentation.
- Define AI interpretation warning classification.

### Epic 3: Federation package foundation

- Define federation package layout.
- Define package Manifest schema.
- Implement package create / inspect / verify as preview-first commands.
- Add redaction report to package.
- Add import preview surface.

### Epic 4: Integrity and signed Manifest

- Add file hash verification.
- Add package hash verification.
- Add signature placeholder abstraction.
- Add warning classification for unsigned / mismatch / expired / revoked packages.

### Epic 5: Chronicle object expansion

- Define Question Chronicle.
- Define Objection Chronicle.
- Define Hypothesis Chronicle.
- Define Decay Chronicle.
- Connect Delta Chronicle to RDE Diff Record.

### Epic 6: Federation message MVP

- Define federation message envelope.
- Add local message create / inspect.
- Add inbox preview queue.
- Add revoke / decay review gate.
- Add audit message export.

### Epic 7: Trust model

- Define node profile schema.
- Define trust relation model.
- Add trust assertion / withdrawal records.
- Add delegated actor metadata.
- Add AI proxy generation metadata.

### Epic 8: Context SNS read-only surface

- Add Lineage View.
- Add Delta View.
- Add Objection View.
- Add Context Boundary View.
- Add Decay View.
- Add Trust View.

### Epic 9: Networked federation research spike

- Compare export/import sync, Chronicle-native protocol, and ActivityPub bridge.
- Define threat model for federation endpoints.
- Define inbox/outbox queue requirements.
- Define centralization risk checklist.

## 8. 横断的防衛線

全段階を通じて、次の防衛線を維持する。

1. JSONL が一次記録である。
2. 派生Index、Graph、Dashboard、UI、AI index、export package は再生成可能な派生面である。
3. Event を経由しない状態変更を作らない。
4. 外部送信はユーザーの明示操作を必要とする。
5. AI解釈を事実または恒久属性として保存しない。
6. Redaction-aware export を access control と見なさない。
7. Export Manifest を cryptographic proof と見なさない。
8. Graph inspection を GraphRAG engine と見なさない。
9. Read-only UI を authority surface と見なさない。
10. Federation package を network federation と見なさない。
11. ActivityPub bridge を採用しても、Chronicle Stack を投稿中心モデルへ矮小化しない。
12. Future concept を release commitment と見なさない。

## 9. RDE差異検証

保存された要素は、Chronicle Stack が local-first、再構成可能性、文脈主権、来歴保存、RDE監査、AI非依存を中心とする基盤であるという思想である。

変換された要素は、個別ロードマップに分散していた v0.1接続表、v0.4運用基盤、v0.5安全境界、分散連合拡張、future concept 境界を、Core、Security、AI/Retrieval、Federation、Future の全体構造へ再編成した点である。

補完された要素は、Stage A から Stage L までの統合ロードマップ、各Stageの主題、対象、完了条件、非対象、依存関係、推奨Issue化、横断的防衛線である。

未解決の要素は、networked federation の実通信方式、ActivityPub bridge の採否、Chronicle-native protocol の範囲、DID / PoP / ZKP の導入時期、GraphRAG query engine の具体的境界である。

逸脱リスクは、全体ロードマップが大きく見えることで実装対象が肥大化することである。特に、Stage J / K の文脈SNS UI と networked federation を急ぐと、ローカル正本、境界制御、検証、撤回可能性が薄くなる。もう一つのリスクは、future concept を安定仕様と誤読することである。

次回更新方針は、この文書を基準に、短期実装として Stage C / E / F を Issue 化し、`federation package create/inspect/verify`、Manifest schema、redaction report、AI interpretation warning classification を具体化することである。

## 10. 結論

Chronicle Stack の全体ロードマップは、便利な機能を横に足す計画ではない。正本、境界、証跡、監査、共有、信頼、連合の順に、文脈主権を壊さないよう積み上げる計画である。

統合後の実装順序は、次の一文に集約される。

> JSONL正本を守り、運用診断を固め、安全境界を定め、AIと連合を最小共有から始め、最後に文脈SNSへ拡張する。

この順序を維持する限り、Chronicle Stack は単なるRAG、単なる文書管理、単なる分散SNSではなく、AI時代に社会が自分の記憶と判断の来歴を失わないための基盤として成長できる。
