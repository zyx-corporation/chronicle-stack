# Upstream Study: receptron/mulmoclaude

Status: Reference study / no direct source reuse approved  
Author: Tomoyuki Kano  
Related: `docs/stage-2/basic-specification.md`

## 1. 参照情報

- Project: MulmoClaude
- Repository: `https://github.com/receptron/mulmoclaude`
- Reviewed commit: `6fcf15f3d976ebb499d6946b791a95290dafbf1a`
- Repository license observed: MIT License
- Copyright notice observed: Copyright (c) 2026 Satoshi Nakajima and the members of Receptron
- Review purpose: Chronicle Stack Stage 2のRuntime / Capability構造検討

この記録は法的助言ではない。実際にソース、package、asset、文書を利用する場合は、対象pathと配布物ごとのlicenseを再確認する。

## 2. 参照した設計領域

### 2.1 BackendとOrchestrationの分離

Provider固有のLLM実行を共通Backend interfaceの後ろへ置き、上位の実行準備、prompt構築、tool設定、session、cleanupと分離する構造を確認した。

Chronicle Stackへの採用判断:

- 採用方式: `conceptual_reimplementation`
- 採用内容: Provider固有実行をRuntime Backend Portへ隔離する設計原理
- 非採用: TypeScript interface、型名、コメント、実装コードのコピー
- Chronicle側補正: BackendはChronicle Storeへ書かず、Recording ServiceがProvenanceとReview状態を記録する

### 2.2 Feature integrationとHost Coreの分離

個別サービス連携をplugin側へ置き、host側へ汎用dispatch、asset、runtime infrastructureだけを置く構造を確認した。

Chronicle Stackへの採用判断:

- 採用方式: `conceptual_reimplementation`
- 採用内容: feature-specific integrationをCoreから分離する依存方向
- 非採用: npm runtime plugin形式、Vue component構造、host aggregator実装
- Chronicle側補正: PluginではなくCapability Adapterとし、Boundary、Review、Audit、RDEをManifestへ結びつける

### 2.3 Scoped Runtime

Integration codeへglobal file systemやglobal event busを渡さず、packageまたはplugin単位にscopeされたruntimeを渡す構造を確認した。

Chronicle Stackへの採用判断:

- 採用方式: `conceptual_reimplementation`
- 採用内容: 最小権限Portを構造的に注入する原理
- 非採用: factory実装、API名、file namespace実装のコピー
- Chronicle側補正: selected Context、Proposal Writer、policy-bound Network、Audit Emitterに限定する

### 2.4 Runtime Registry

静的能力とruntime能力の登録、name collision、load order、dynamic asset解決などの課題を確認した。

Chronicle Stackへの採用判断:

- 採用方式: `conceptual_reimplementation`
- 採用内容: 能力IDの一意性、未登録能力の拒否、Registry診断
- 非採用: first-loaded precedence、任意packageの動的ロード
- Chronicle側補正: Stage 2では静的Registryとし、collisionはfail closedとする

### 2.5 Messaging Bridge分離

Platform固有のmessage受信を小さなAdapterへ閉じ込め、共通protocol/client/serviceから分離する構造を確認した。

Chronicle Stackへの採用判断:

- 採用方式: `conceptual_reimplementation`
- 採用内容: Transport固有APIをCore外へ置く構造
- 非採用: MulmoBridge wire protocol、package、Bridge codeのコピー
- Chronicle側補正: 外部messageを即時commandにせず、Envelope、Identity、Consent、Boundary、Command Promotionを経由する

### 2.6 Natural Languageから構造化定義への変換

LLMを業務ロジック実行主体にせず、自然言語をschemaまたはDSLへ変換し、通常のengineが検証・実行するパターンを確認した。

Chronicle Stackへの採用判断:

- 採用方式: `conceptual_reimplementation`
- 採用内容: AI出力を検証可能な中間表現へ固定する設計原理
- 非採用: 上流DSL、Collections schema、engine codeのコピー
- Chronicle側補正: Operation Plan、Proposal、Boundary、Review、Apply、RDEへ接続する

### 2.7 ChatとGUIの連携

Agentが内容に応じたGUI surfaceを呼び出し、構造化入力を受け取る構造を確認した。

Chronicle Stackへの採用判断:

- 採用方式: `conceptual_reimplementation`
- 採用内容: text以外のReview surfaceをprotocol化する発想
- 非採用: `gui-chat-protocol` code、Vue runtime、任意GUI plugin実行
- Chronicle側補正: Proposal SurfaceをJSON read modelと許可操作へ限定する

## 3. 明示的に採用しない要素

Stage 2では次を採用しない。

- LLMをChronicle全体の万能Controllerとする構造
- 任意packageの自動検出と動的code loading
- first-loadedまたはpreset優先によるcollision解決
- GUI pluginが任意の実行surfaceを提供する構造
- external messageからagent commandへの直接経路
- session stateまたはworkspace fileをChronicle正本の代替とする構造
- Provider固有eventをChronicleの安定Event契約として保存する構造

## 4. 著作権・ライセンス判断

Repository rootで確認したMIT Licenseは、利用、変更、統合、配布等を許諾する一方、Softwareのcopyまたはsubstantial portionsにCopyright NoticeとPermission Noticeを含めることを条件とする。

Stage 2初期方針:

1. 上流コードを直接コピーしない。
2. 上流の型名、関数名、コメント、schema、testを翻訳コピーしない。
3. Chronicle Stackの要求とfailure conditionsから独自設計する。
4. 直接reuseが必要になった場合は、対象commit、path、license、notice、変更内容を個別記録する。
5. AGPL公開版へ含められることと、ZYXの別商用ライセンス版へ再利用できる権利を分けて確認する。
6. 上流由来部分をZYX単独著作物として表示しない。
7. package dependencyとして利用する場合も、package配布物のlicenseを再確認する。

## 5. AI支援実装の注意

AIへ上流repositoryを参照させて実装を生成する場合でも、次を確認する。

- 上流codeとの長い一致または特徴的な一致がないか
- 上流固有のコメント、変数名、test caseが混入していないか
- 生成物の設計根拠がChronicle側仕様から説明できるか
- copied sourceの有無を正しくAdoption Ledgerへ記録したか
- commercial-edition rights reviewが必要か

大規模生成差分は、動作だけでなくprovenanceとreviewabilityを確認する。

## 6. Current adoption records

現時点では、MulmoClaude由来のソースコード、schema、test、assetはChronicle Stackへ直接取り込んでいない。

Adoption modeはすべて`conceptual_reimplementation`である。将来変更する場合は、`docs/provenance/upstream-adoption-ledger.yaml`と`THIRD_PARTY_NOTICES.md`を同じPRで更新する。

## 7. RDE review

### Preserved

- Chronicle Stack固有の正本、境界、Review、RDE、local-first

### Transformed

- Application plugin architectureをCapability Adapter architectureへ読み替えた
- Chat GUIをProposal Review Surfaceへ限定した
- Messaging bridgeをInput EnvelopeとCommand Promotionへ変換した

### Supplemented

- Rights Review
- Adoption Ledger
- 商用ライセンス版への利用権分離
- AI支援実装の類似性確認

### Unresolved

- 将来、外部packageをdependencyとして直接利用する必要性
- direct source reuse時のfile-level notice形式
- 法務専門家による商用版rights review

### Deviation risks

- MITであることを理由に出所管理を省略すること
- 設計参照とコード翻案の境界を曖昧にすること
- 上流の製品思想までChronicleの設計目標へ持ち込むこと

### Next update policy

- 参照commitを更新して再調査した場合は、新しいreview recordを追記する。
- direct source reuseまたはexternal dependency採用時にRights Reviewを再実施する。
