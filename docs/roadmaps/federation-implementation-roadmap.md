# Chronicle Stack 分散連合拡張 実装ロードマップ

Status: Draft  
Scope: Chronicle Stack federation extension implementation plan  
Related: `docs/federation-requirements.md`  
Author: Tomoyuki Kano

## 1. 目的

この文書は、`docs/federation-requirements.md` で定義した Chronicle Stack 分散連合拡張を、実装可能な段階へ分解するためのロードマップである。

分散連合拡張の目的は、Chronicle Stack を「投稿を流通させるSNS」ではなく、「問い、判断、生成物、差分、反論、監査、撤回を、来歴付きで連合する文脈SNS」へ拡張することである。

ただし、最初から完全な分散連合を実装してはならない。Chronicle Stack の中心価値は local-first な文脈正本と再構成可能性にある。したがって実装は、ローカル正本を壊さない範囲で、段階的に外部共有、署名、検証、連合、信頼、SNS的操作へ拡張する。

## 2. 実装方針

### 2.1 v0.1 相当の最小中核を肥大化させない

分散連合拡張は、既存の local-first 中核を置き換えない。`.chronicle/chronicle.jsonl` を一次記録とし、派生Index、export、UI、AI index、runtime surface は再構築可能な派生面として扱う設計を維持する。

分散連合は、まず export/import、manifest、署名、検証、手動共有の拡張として扱い、常時接続型の連合サーバーや複雑なプロトコル実装は後段に送る。

### 2.2 実装順序は「正本、境界、証跡、共有、連合」

実装順序は、次の原則に従う。

1. ローカル正本を安定させる。
2. 文脈境界と共有範囲を明示する。
3. 署名、Manifest、監査ログで証跡を固める。
4. 手動共有パッケージを安全に作る。
5. ノード間共有へ進む。
6. 連合プロトコルへ進む。
7. 文脈SNS UIへ進む。

### 2.3 AI連携は従属ではなく境界制御として実装する

AI連携は、外部AIへ大量の文脈を送る機能ではない。外部AIへ何を渡し、何を渡さず、戻ってきた出力が元文脈をどう変形したかを確認する境界制御として実装する。

Sayane 連携は、外部AI接続の利便性ではなく、文脈の持ち出し、要約、再構成、過剰断定、AI解釈の固定化を抑制するための制御層として扱う。

## 3. フェーズ構成

分散連合拡張は、次のフェーズに分けて実装する。

| Phase | 主題 | 目的 |
|---|---|---|
| Phase 0 | Baseline Alignment | 既存実装と要求仕様の接続点を整理する |
| Phase 1 | Local Federation Package | 手動共有可能な連合パッケージを作る |
| Phase 2 | Signed Manifest and Verification | 署名付きManifestと検証を導入する |
| Phase 3 | Context Boundary Enforcement | 共有境界、redaction、同意ログを強化する |
| Phase 4 | Chronicle Object Expansion | 問い、反論、仮説、減衰などの型を拡張する |
| Phase 5 | Federation Message MVP | Publish/Request/Grant/Revoke などの連合メッセージを定義する |
| Phase 6 | Node Trust Model | Node ID、鍵、文脈別信頼、委譲を扱う |
| Phase 7 | Sayane / AI Adapter Integration | AI送信境界とRDE監査を連携する |
| Phase 8 | Context SNS Surface | 問いフォロー、反論、再審、購読UIを追加する |
| Phase 9 | Networked Federation | ノード間の実通信と同期を導入する |

## 4. Phase 0: Baseline Alignment

### 4.1 目的

既存 Chronicle Stack の実装と分散連合拡張要求を対応付ける。現行の一次記録、Context、Artifact、Decision、RDE Diff Record、Boundary Rule、Audit、Lifecycle、Package Review、read-only UI、runtime surface を、将来の連合拡張にどう接続するかを整理する。

### 4.2 実装タスク

- 既存モデルと Chronicle オブジェクト要求の対応表を作る。
- 既存 `visibility`、`scope`、classification、audit、lifecycle と連合共有範囲の対応を整理する。
- `docs/federation-requirements.md` から v0.1 に入れない項目を明示する。
- 既存 export/profile/package review の境界を確認する。
- README または architecture から federation roadmap への参照を追加するか検討する。

### 4.3 受け入れ条件

- 既存モデルと将来モデルの対応が文書化されている。
- 分散連合拡張が既存 local-first 原則を壊さないことが確認されている。
- 連合拡張の最初の実装対象が export/import package であることが明確になっている。

### 4.4 非対象

- 実通信プロトコルの実装。
- DID、PoP、ZKP の実装。
- 常駐サーバー型の連合ノード。
- 書き込み可能なGUI。

## 5. Phase 1: Local Federation Package

### 5.1 目的

Chronicle Stack のローカル正本から、他ノードへ安全に渡せる手動共有パッケージを作成する。ここではネットワーク連合を実装せず、ファイルとして export し、受信側で検証、preview、import 判断できる形を目指す。

### 5.2 実装タスク

- `chronicle federation package create` のCLI案を定義する。
- 共有目的、共有範囲、対象Chronicle、対象フィールド、保存期間、再共有可否を指定できる package metadata を定義する。
- package 内に本文、metadata、audit、lifecycle、RDE summary、redaction summary を含める。
- package review で、送信前に機密情報、PII、AI解釈、未検証仮説、撤回対象を警告する。
- package は zip または directory bundle として扱い、Manifest を含める。

### 5.3 CLI候補

```bash
chronicle federation package create \
  --purpose "project review" \
  --target-node "partner-a" \
  --visibility federated \
  --context <CONTEXT_ID> \
  --include-rde \
  --redaction-profile public-review \
  -o chronicle-federation-package.zip

chronicle federation package inspect chronicle-federation-package.zip
chronicle federation package verify chronicle-federation-package.zip
```

### 5.4 データ構成案

```text
chronicle-federation-package/
  manifest.json
  records.jsonl
  contexts/
  artifacts/
  rde/
  audit/
  lifecycle/
  redaction-report.json
  README.md
```

### 5.5 受け入れ条件

- ローカル正本を変更せずに共有パッケージを作成できる。
- package inspect で共有範囲、目的、含有データ、警告を確認できる。
- package verify でManifest整合性を確認できる。
- 受信側が import 前に preview できる。

### 5.5.1 実装メモ

- `chronicle federation package create` が `manifest.json`, `records.jsonl`, `redaction-report.json`, `README.md` を持つ local bundle directory を生成する。
- package create は既存の context package boundary と warning classification を再利用しつつ、target node 向け trust preview を metadata に残す。
- `chronicle federation package inspect` は manifest と redaction report を read-only に確認するだけで、import や transport は行わない。
- `chronicle federation package verify` は file hash を再計算する構造確認に留まり、署名 placeholder を明示する。

### 5.6 非対象

- 自動送信。
- ノード間常時同期。
- 双方向連合。
- 撤回伝播。

## 6. Phase 2: Signed Manifest and Verification

### 6.1 目的

共有パッケージと Chronicle export に、改ざん検知と由来確認のための署名付きManifestを導入する。

### 6.2 実装タスク

- Manifest schema を定義する。
- package 内の各ファイルの hash を記録する。
- Node ID、作成日時、作成目的、共有範囲、保存期限、source root、tool version を記録する。
- 初期実装ではローカル鍵または開発用鍵による署名 surface を用意する。
- 署名なしManifestも扱えるが、warning classification で区別する。
- `chronicle manifest verify` を追加する。

### 6.3 Manifest schema 案

```json
{
  "schema_version": "federation-manifest/v0.1",
  "package_id": "pkg_...",
  "created_at": "2026-06-26T00:00:00Z",
  "created_by_node": "node:local:...",
  "purpose": "project review",
  "visibility": "federated",
  "retention_policy": {
    "expires_at": null,
    "revocable": true
  },
  "files": [
    {
      "path": "records.jsonl",
      "sha256": "..."
    }
  ],
  "signature": {
    "algorithm": "placeholder",
    "key_id": "local-dev-key",
    "value": "..."
  }
}
```

### 6.4 受け入れ条件

- Manifest の hash 検証ができる。
- 署名あり、署名なし、署名不一致を区別できる。
- package review または import preview で検証結果を表示できる。
- 署名方式は将来 DID/PoP/ZKP に差し替え可能な抽象層になっている。

### 6.4.1 実装メモ

- 現段階の manifest verify は `signature.status=unsigned` を warning として明示しつつ、bundle payload file の hash 検証を先に固定する。
- manifest 自身は存在必須だが、自己参照 hash を避けるため payload file list からは分離する。
- `chronicle federation package create --signature-mode local_dev` により、reviewable な local dev signed-manifest surface を生成できる。
- `chronicle federation package verify` は `unsigned`, `signed`, `mismatch`, `expired`, `revoked` を区別するが、どれも trust certification や remote identity proof には昇格させない。

### 6.5 非対象

- 本格DID実装。
- ブロックチェーン連携。
- PoP本人性証明。
- 鍵管理UI。

## 7. Phase 3: Context Boundary Enforcement

### 7.1 目的

分散連合に入る前に、共有してよい文脈と共有してはいけない文脈の境界を強化する。

### 7.2 実装タスク

- 共有範囲を `Private`、`Trusted`、`Project`、`Organization`、`Community`、`Federated`、`Public`、`Expired`、`Revoked`、`Tombstone` に対応させる。
- 既存 visibility/classification と federation visibility の変換表を作る。
- フィールド単位 redaction policy を定義する。
- AI解釈、心理推測、性格推定、思想推定、能力推定を恒久属性として export しない warning を追加する。
- package create 時に共有目的の指定を必須化する。
- consent log と third-party sharing restriction を audit event として記録する。

### 7.3 CLI候補

```bash
chronicle federation boundary check \
  --purpose "external review" \
  --target-node "partner-a" \
  --context <CONTEXT_ID>

chronicle federation consent record \
  --target-node "partner-a" \
  --purpose "project review" \
  --scope federated \
  --retention "90d"
```

### 7.4 受け入れ条件

- 共有目的なしの federation package 作成を警告または拒否できる。
- PII、秘密情報、AI解釈、未検証仮説、撤回対象を区別して warning できる。
- consent log が append-only event として記録される。
- redaction report が package に含まれる。

### 7.5 非対象

- 完全自動匿名化の保証。
- 法的同意管理の完成版。
- 強制的DRM。

## 8. Phase 4: Chronicle Object Expansion

### 8.1 目的

分散連合で流通させる意味単位として、Question、Conversation、Decision、Artifact、Delta、Objection、Hypothesis、Decay を扱えるようにする。

### 8.2 実装タスク

- 既存 event/model と新 Chronicle object type の対応を定義する。
- Question Chronicle を追加する。既存 event の `summary` や context title だけに依存しない。
- Objection Chronicle を追加する。反論、異議、留保、再審要求を表現する。
- Hypothesis Chronicle を追加する。未検証仮説を事実と区別する。
- Decay Chronicle を追加する。期限切れ、撤回、Tombstone、非公開化、減衰を表現する。
- Delta Chronicle を RDE Diff Record と接続する。

### 8.3 データモデル案

```json
{
  "id": "chr_...",
  "type": "question",
  "created_at": "2026-06-26T00:00:00Z",
  "created_by": "node:local:...",
  "origin_question_id": null,
  "summary": "Why should this policy exist?",
  "evidence": [],
  "visibility": "private",
  "ai_involvement": {
    "involved": false,
    "models": []
  },
  "rde": null,
  "lifecycle": {
    "state": "active",
    "retention": null
  }
}
```

### 8.4 受け入れ条件

- 新 object type がJSONL eventまたは派生Indexとして表現できる。
- 既存 export が壊れない。
- read-only UI で object type ごとの一覧またはdetailを表示できる。
- RDE Diff Record と Delta Chronicle の関係が明示される。

### 8.4.1 実装メモ

- `chronicle object record` / `list` / `show` が explicit Question / Objection / Hypothesis / Decay record を append-only event として扱う。
- `/api/chronicle-objects` が explicit object records に加えて Conversation / Artifact / Decision / Delta の derived object view を read-only に表示する。
- Delta Chronicle は linked `RDE Diff Record` を detail 上で明示し、Chronicle core 側で hosted runtime や書き込み GUI を追加しない。

### 8.5 非対象

- 完全なGraphRAG query engine。
- 書き込み可能なGUI。
- 複雑な ontology 管理。

## 9. Phase 5: Federation Message MVP

### 9.1 目的

分散連合で交換する意味メッセージを定義し、まずはファイルベースまたはlocal queueベースで扱えるようにする。

### 9.2 対象メッセージ

MVPでは次を対象とする。

- Publish Chronicle
- Request Context
- Grant Context
- Deny Context
- Revoke Context
- Update Chronicle
- Fork Chronicle
- Reference Chronicle
- Object Chronicle
- Audit Chronicle
- Decay Notice

Trust Assertion と Trust Withdrawal は Phase 6 に送る。

### 9.3 実装タスク

- federation message envelope を定義する。
- message type、source node、target node、object refs、purpose、created_at、expires_at、signature status を持たせる。
- `chronicle federation message create` を追加する。
- `chronicle federation inbox inspect` を追加する。
- 受信メッセージは import 前に preview-only とする。
- `Revoke Context` と `Decay Notice` はローカル正本を即時削除せず、review queue に入れる。

### 9.4 Envelope 案

```json
{
  "schema_version": "federation-message/v0.1",
  "message_id": "msg_...",
  "type": "request_context",
  "source_node": "node:...",
  "target_node": "node:...",
  "created_at": "2026-06-26T00:00:00Z",
  "purpose": "project review",
  "object_refs": ["chr_..."],
  "policy": {
    "retention": "90d",
    "reshare": false
  },
  "signature_ref": "manifest.signature"
}
```

### 9.5 受け入れ条件

- federation message を作成、保存、inspect できる。
- message はJSONとして安定出力できる。
- 受信メッセージは自動適用されず、preview/review 経由になる。
- revoke/decay は監査ログに残る。

### 9.5.1 実装メモ

- `chronicle federation message create` が preview-only の message envelope を local inbox/outbox queue に保存する。
- `chronicle federation inbox inspect` / `outbox inspect` と `/api/federation-inbox` / `/api/federation-outbox` が read-only inspect surface を提供する。
- `revoke_context` と `decay_notice` を inbox に保存した場合は、local primary record を触らず audit event だけを追記する。

### 9.6 非対象

- HTTP配送。
- ActivityPub互換。
- リアルタイム同期。

## 10. Phase 6: Node Trust Model

### 10.1 目的

ノード間の信頼関係、署名、鍵ローテーション、権限委譲、代理投稿、AI代理生成を扱う。

### 10.2 実装タスク

- Node profile schema を定義する。
- Node ID と Subject ID を分ける。
- trust relation を文脈別に表現する。
- trust level を単一スコアではなく、domain、purpose、capability ごとに持たせる。
- Trust Assertion と Trust Withdrawal message を定義する。
- 代理投稿、代理判断、AI代理生成を明示する metadata を追加する。

### 10.3 Trust relation 案

```json
{
  "source_node": "node:local:...",
  "target_node": "node:partner:...",
  "domain": "technical_review",
  "level": "trusted",
  "capabilities": ["review", "reference", "request_context"],
  "expires_at": null,
  "created_from": "manual_assertion"
}
```

### 10.4 受け入れ条件

- 信頼関係を追加、撤回、一覧表示できる。
- federation package/message 作成時に trust relation を参照できる。
- 信頼が文脈別であり、単一スコアではないことがUI/API上で明示される。
- 代理行為とAI代理生成が監査可能に記録される。

### 10.4.1 実装メモ

- `chronicle trust node add`, `chronicle trust assert`, `chronicle trust withdraw`, `chronicle trust list` が local trust registry を扱う。
- `/api/trust-nodes` と `/api/trust-relations` が Node ID / Subject ID / trust level / domain / capability を read-only に表示する。
- federation message envelope と context package metadata は target node 向け trust summary を advisory metadata として参照する。

### 10.5 非対象

- グローバルID基盤。
- ブロックチェーンベースの信頼証明。
- 自動信用スコアリング。

## 11. Phase 7: Sayane / AI Adapter Integration

### 11.1 目的

外部AI利用時の文脈送信境界、AI応答の保存、AI解釈の分類、RDE監査を、Sayane またはAI Adapter経由で統合する。

### 11.2 実装タスク

- AI送信前 package preview を作る。
- 外部AIへ送る文脈の最小化 report を出す。
- prompt、response、model id、処理系、timestamp を保存可否設定付きで扱う。
- AI要約と原文を分離する。
- AI推測とユーザー発言を分離する。
- AI解釈を hypothesis または ai_interpretation として decay 対象にする。
- RDE diff memo を作成し、Delta Chronicle と接続する。
- Sayane 連携用 export/import surface を定義する。

### 11.3 CLI候補

```bash
chronicle ai-boundary preview \
  --task "summarize for external model" \
  --context <CONTEXT_ID> \
  --model "external:placeholder"

chronicle rde draft \
  --source <CHRONICLE_ID> \
  --derived <ARTIFACT_ID> \
  --mode ai-assisted
```

### 11.4 受け入れ条件

- AIへ送る前に共有境界とredactionを確認できる。
- AI応答がユーザー発言や事実記録と混ざらない。
- AI解釈が恒久属性化されない。
- RDE diff memo が Delta Chronicle として再構成できる。

### 11.5 非対象

- 特定AI事業者への固定接続。
- 外部AIの正しさ保証。
- 自動人格推定。

## 12. Phase 8: Context SNS Surface

### 12.1 目的

Chronicle Stack を投稿中心ではなく、問い、判断、反論、再審、共同編集を中心にした文脈SNSとして見せる。

### 12.2 実装タスク

- 問いフォロー機能を設計する。
- Chronicle購読機能を設計する。
- Objection Chronicle をUIに表示する。
- 「理解した」「保留する」「根拠不足」「再審したい」「別文脈では異なる」「自ノードに取り込む」「参照する」「反論する」「共同編集を提案する」などの反応型を定義する。
- Lineage View と Delta View を優先実装する。
- Trust View、Context Boundary View、Decay View を read-only UI に追加する。

### 12.3 UI優先順位

1. Lineage View
2. Delta View
3. Context Boundary View
4. Objection View
5. Decay View
6. Trust View
7. AI Involvement View
8. Timeline View

Timeline View は補助であり、中心UIではない。

### 12.4 受け入れ条件

- ひとつの方針や成果物について、由来となる問い、関連会話、判断、差分、反論、RDEをたどれる。
- 反応が単なる「いいね」ではなく、意味ある関係として記録される。
- UI mutation は段階的に導入し、初期は read-only / preview-first を維持する。

### 12.5 非対象

- 注意経済型フィード。
- 広告配信。
- ランキング最適化。
- エンゲージメント最大化。

## 13. Phase 9: Networked Federation

### 13.1 目的

ファイルベース、手動共有、message queue を経た後に、ノード間の実通信を導入する。

### 13.2 実装選択肢

実通信の方式は未確定であり、次の三案を比較する。

- Export/Import Sync: 最も安全。手動または半自動。v0.1からの連続性が高い。
- Chronicle-native Protocol: 意味関係を最も正確に扱える。実装負荷は高い。
- ActivityPub Bridge: 分散SNSとの接続性が高い。ただし投稿中心モデルへ引き寄せられるリスクがある。

### 13.3 実装タスク

- federation endpoint の threat model を作る。
- Node discovery を設計する。
- inbox/outbox queue を設計する。
- signed message verification を導入する。
- Revoke Context と Decay Notice の扱いを実通信上で検証する。
- ActivityPub Bridge を採用する場合、Chronicle object と ActivityPub activity の対応表を作る。

### 13.4 受け入れ条件

- ノード間で Publish、Request、Grant、Deny、Revoke、Audit の最小交換ができる。
- 受信メッセージは自動適用されず、review gate を通る。
- 撤回、期限切れ、Tombstone が監査ログ付きで扱える。
- 中央サーバーが文脈正本を保持しない。

### 13.5 非対象

- 完全なグローバルSNS運用。
- 中央タイムライン。
- 未承認ノードからの自動取り込み。

## 14. 横断的なセキュリティ要求

すべてのPhaseで、次を守る。

- local-first 正本を壊さない。
- export/import は preview-first とする。
- 外部AI送信は明示操作とする。
- AI解釈を事実として保存しない。
- 共有目的を必須または強警告とする。
- PII、秘密情報、未検証仮説、撤回対象を warning する。
- 受信データは自動適用しない。
- 署名不一致、Manifest不一致、期限切れ、Revoked は危険扱いにする。
- 管理者権限と文脈所有者権限を混同しない。

## 15. 推奨Issue分割

実装時には、次のようにIssue化する。

### Epic A: Federation package foundation

- Define federation package directory layout.
- Add package manifest schema.
- Add package create/inspect CLI.
- Add package verify CLI.
- Add redaction report to federation package.

### Epic B: Context boundary and consent

- Map existing visibility/classification to federation visibility.
- Add federation purpose metadata.
- Add consent audit event.
- Add third-party sharing restriction metadata.
- Add AI interpretation export warning.

### Epic C: Chronicle object expansion

- Add Question Chronicle draft model.
- Add Objection Chronicle draft model.
- Add Hypothesis Chronicle draft model.
- Add Decay Chronicle draft model.
- Connect Delta Chronicle to RDE Diff Record.

### Epic D: Federation message MVP

- Define federation message envelope.
- Add message create CLI.
- Add inbox inspect CLI.
- Add revoke/decay review gate.
- Add audit message export.

### Epic E: Trust model

- Define node profile schema.
- Add trust relation model.
- Add trust assertion/withdrawal events.
- Add delegated actor metadata.
- Add AI proxy generation metadata.

### Epic F: Sayane / AI adapter boundary

- Add AI boundary preview.
- Add external AI context minimization report.
- Separate AI response from user statement.
- Mark AI interpretation as decay target.
- Add RDE draft helper for AI-derived artifacts.

### Epic G: Context SNS read-only surface

- Add Lineage View.
- Add Delta View.
- Add Objection View.
- Add Context Boundary View.
- Add Decay View.
- Add Trust View.

## 16. 実装優先順位

最優先は Phase 1 から Phase 3 である。理由は、分散連合を始める前に、共有パッケージ、Manifest、redaction、consent、boundary が必要だからである。

Phase 1, Phase 2, Phase 6, Phase 7, Phase 8 の最小 slice が揃ったため、次は Phase 3 を進める。context boundary enforcement がなければ federation package を安全に外へ持ち出せない。

Phase 6 と Phase 7 は、実用化段階で重要になる。信頼とAI境界がなければ、Chronicle Stack は文脈主権を守れない。

Phase 8 と Phase 9 は、文脈SNSとしての可視化と実通信である。ここは魅力的だが、早く作りすぎると、既存SNSの模倣や中央化へ逸脱する危険がある。

## 17. RDE差異検証

保存された要素は、Chronicle Stack の中心が local-first、文脈主権、来歴保存、RDE監査、AI非依存であるという思想である。

変換された要素は、分散連合拡張要求を実装Phase、CLI候補、データ構成、受け入れ条件、非対象へ分解した点である。

補完された要素は、Phase 0 から Phase 9 までの実装順序、federation package、signed Manifest、context boundary enforcement、federation message envelope、trust relation、Sayane / AI Adapter、Context SNS surface、Networked Federation の段階化である。

未解決の要素は、実通信方式として export/import sync、Chronicle-native protocol、ActivityPub bridge のどれを採用するかである。また、DID、PoP、ZKP、鍵管理UI、法的同意管理は後続検討とする。

逸脱リスクは、文脈SNS UIや実通信を急ぎすぎて、ローカル正本と境界制御の実装が薄くなることである。もう一つのリスクは、ActivityPub互換を急ぐことで、Chronicle Stack が投稿中心モデルへ引き寄せられることである。

次回更新方針は、Phase 1 を最初の実装Issue群へ分解し、`federation package create/inspect/verify` のCLI仕様、Manifest schema、package review warning classification を具体化することである。

## 18. 結論

Chronicle Stack 分散連合拡張は、ネットワーク機能から始めてはならない。まず、ローカル正本を守ったまま共有できる package を作り、次に署名と検証、文脈境界、Chronicle object、federation message、trust、AI boundary、文脈SNS UI、実通信へ進むべきである。

実装順序は、次の一文に集約される。

> 正本を守り、境界を定め、証跡を固め、最小共有し、最後に連合する。

この順序を守る限り、Chronicle Stack は単なる分散SNSではなく、AI時代に社会が自分の記憶を失わないための文脈主権型基盤として成長できる。
