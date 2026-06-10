# Roadmap Linkage Document

## 1. 文書情報

文書名：Roadmap Linkage Document
版：v0.1-draft
親文書：[Chronicle Stack v0.1 — Chronicle Core 基本仕様書](chronicle-stack-basic-spec-v0.1.md) §23
作成者：Tomoyuki Kano

## 2. 目的

本文書は、Chronicle Core v0.1 のデータ構造・実装上の各要素が、v0.2 以降のどの段階のどの機能に接続するかを明示する。目的は二つある。第一に、v0.1 の設計判断（特に「いま実装しないが構造だけ残す」判断）の根拠を後から追跡可能にすること。第二に、後続段階の実装時に、v0.1 のどの接続点を使うべきか・使ってはならないかを迷わず判断できるようにすることである。

## 3. 段階別接続表

### v0.2 Context Sovereignty Layer

| v0.1 の接続点 | 接続内容 |
|--------------|---------|
| Context.scope_hint | 正式なスコープ制御への昇格。hint（助言）から enforcement（強制）への移行が論点 |
| Context.confidence | 文脈の信頼度に基づく利用制御 |
| Context.source_type / source_ref | 文脈の来歴追跡の基礎 |
| ChronicleEvent.context_ids | どの Event がどの文脈に依拠したかの参照経路 |
| visibility_hint（§22、未実装） | private / project / public_candidate / public / sensitive の追加 |

**v0.1 が意図的に残した空白**：scope_hint の enforcement、Context のスコープ変更履歴、変更の認可主体の記録。特に三つ目は「文脈の主権者は誰か」「スコープ変更を誰が認可し、その認可を誰が監査するか」という認可遡及の問いに直結し、v0.2 仕様の中心論点である。基本仕様書 §3 第五の問題（文脈が人間の問いを支えるのではなく、AI側の応答最適化に吸収される）への対抗を、データモデルとして表現する段階となる。

### v0.3 RDE Integration

| v0.1 の接続点 | 接続内容 |
|--------------|---------|
| RdeDiffRecord 六項目 | 自動・半自動評価の出力スキーマとして維持 |
| ArtifactVersion.rde_record_id | Version 更新→RDE 起票の自動連結（v0.1 では未配線、P1で配線） |
| RdeDiffRecord.created_by | 評価主体の位置性開示への拡張点 |
| next_update_policy → preserved 連鎖 | 世代間の意図継承検証の基礎構造 |

**前提条件**：P1（rde index 化、Version リンク、CLI からの六項目入力）が v0.1 内で完了していること。これらが未了のまま v0.3 に入ると、自動評価の出力先が存在しない状態で評価器だけが先行する。

### v0.4 CSG-RAG Prototype

| v0.1 の接続点 | 接続内容 |
|--------------|---------|
| prefix 付き ID 体系 | Graph ノードの型判別。chr_/evt_/ctx_/art_/ver_/dec_/rde_ がそのままノード種別になる |
| Event の参照フィールド群 | Graph エッジの導出元（parent_event_id, artifact_id, context_ids, decision_id, rde_record_id） |
| JSONL 一次記録 | Graph は派生データ。indexes/ と同格の「再生成可能物」として扱い、一次記録に昇格させない |

**設計上の防衛線**（§28 逸脱リスク）：GraphRAG の早期導入は、記録基盤を検索基盤として歪める。v0.4 においても、Graph 構築は `chronicle index rebuild` と同型の「JSONL からの再生成」として実装し、Graph 側への書き込みを一次記録化しない。

### v0.5 Human Review Decision Model

| v0.1 の接続点 | 接続内容 |
|--------------|---------|
| Decision Model 全体 | 直接の拡張元 |
| DecisionType.needs_review / deferred | レビューワークフローの遷移起点 |
| ChronicleEvent.review_status / Actor.reviewer | v0.1 では予約状態。ここで実用化 |
| Decision.decided_by（自由文字列） | 判断主体の認可記録、PoP-UID 等の人格証明体系への接続点 |

**v0.1 から持ち越す設計判断**：Decision と Artifact.status の連動規則。v0.1 は意図的に非連動とした（Decision Model 仕様書 §2）。連動させる場合は「判断の記録が状態を変える」、させない場合は「状態変更そのものを独立の Event として記録し続ける」。どちらが監査可能性に資するかを v0.5 仕様の冒頭で Decision として記録すること。

### v0.6 Sayane Integration

| v0.1 の接続点 | 接続内容 |
|--------------|---------|
| local-first 原則と明示 Export | クロス LLM コンテキスト移植の出口。Chronicle は移植元の一次根拠となる |
| Event.source（SourceRef） | 移植されてきた文脈の来歴記録。importer Actor とともに使用 |
| schema_version | Sayane 側スキーマ正規化との互換性宣言 |

**規約**：AI 固有のニックネーム等は PII として扱い、Export 時の取り扱いを Sayane 側の `promptExport: never` 原則と整合させる。

### v0.7 Dashboard / v0.8 Research Observatory

| v0.1 の接続点 | 接続内容 |
|--------------|---------|
| `--json` 全コマンド対応 | Dashboard のデータ取得 API の前身。CLI の JSON 出力スキーマを安定化させること |
| indexes/ | 表示用クエリの一次対象（JSONL 全走査の回避） |
| Event.source / SourceRef | v0.8 で外部知識（論文・Web・GitHub）の観測記録に拡張 |

## 4. 横断的な防衛線

ロードマップ全体を通じて維持する原則を再掲する。

1. **JSONL が唯一の一次記録**である。Graph、Index、Dashboard キャッシュ、Export 産物はすべて再生成可能な派生データであり、これらへの書き込みを真実の更新と見なさない。
2. **Event を経由しない状態変更を作らない**。後続段階で新しいオブジェクト種別を導入する場合、必ず対応する event_type と payload 規約を定義する。
3. **ID prefix 体系を破壊しない**。新種別は新 prefix を追加する（既存 prefix の意味変更を行わない）。
4. **ユーザーの明示操作なしに外部送信しない**。v0.6 以降で外部連携が増えても、Export の明示性を維持する。

## 5. v0.1 残作業とロードマップの依存関係

| 残作業 | 優先度 | ブロックする後続段階 |
|--------|--------|---------------------|
| source_event_id / event_id の事前生成（整合性修正） | P0 | すべて（一次記録の汚染が進行中のため） |
| rde record の六項目ファイル入力 | P1 | v0.3 |
| RDE の index 化と Version リンク | P1 | v0.3, v0.4 |
| decision record CLI の alternatives / notes 対応 | P1 | v0.5 |
| CLI 統合テスト・E2E デモテスト | P2 | （品質基盤として全段階） |
| Context テストの追加 | P2 | v0.2 |
