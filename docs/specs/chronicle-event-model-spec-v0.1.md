# Chronicle Event Model 仕様書

## 1. 文書情報

文書名：Chronicle Event Model 仕様書
版：v0.1-draft
親文書：[Chronicle Stack v0.1 — Chronicle Core 基本仕様書](chronicle-stack-basic-spec-v0.1.md) §9
実装：`src/chronicle/models/event.py`, `src/chronicle/store/jsonl_store.py`
作成者：Tomoyuki Kano

## 2. 目的と位置づけ

Chronicle Event は Chronicle Stack における最小記録単位である。ユーザー入力、AI出力、成果物の生成・更新、判断、意味変化監査、メタ情報更新は、すべて Chronicle Event として `chronicle.jsonl` に追記される。

Event Model の設計原則は次の三つである。

第一に、**追記専用（append-only）**であること。Event は記録後に書き換えられない。訂正が必要な場合は、訂正を表す新しい Event を追記する。

第二に、**自己完結**であること。各 Event は payload に当該時点のオブジェクト全体（Artifact、Version、Decision 等）のスナップショットを含み、Event 列のみからすべての派生インデックスを再構成できる。

第三に、**型判別可能な参照**であること。他オブジェクトへの参照はすべて prefix 付きID（`evt_` `art_` `ctx_` `dec_` `rde_`）で行い、参照先の種類をIDだけで判別できる。

## 3. フィールド仕様

### 3.1 必須フィールド

| フィールド | 型 | 説明 |
|-----------|------|------|
| event_id | str | `evt_` + UUID hex。生成は `ids.generate_id("event")` |
| chronicle_id | str | 所属 Chronicle のID。metadata.yaml と一致しなければならない |
| timestamp | datetime | ISO 8601。タイムゾーン付き（実装は `datetime.now(timezone.utc).astimezone()`） |
| event_type | EventType | §3.3 の列挙値 |
| actor | Actor | §3.4 の列挙値。記録主体を必ず残す |
| summary | str | 人間可読の一行要約 |
| payload | dict | 種別固有データ。省略時は空辞書 |

### 3.2 任意フィールド

| フィールド | 型 | 説明 |
|-----------|------|------|
| parent_event_id | str \| None | 因果関係上の親 Event |
| artifact_id | str \| None | 関連 Artifact |
| context_ids | list[str] | 関連 Context（複数可） |
| decision_id | str \| None | 関連 Decision |
| rde_record_id | str \| None | 関連 RDE Diff Record |
| source | SourceRef \| None | `source_type` と `source_ref` の組 |
| confidence | Confidence \| None | high / medium / low / unknown |
| review_status | ReviewStatus \| None | unreviewed / reviewed / needs_review |
| tags | list[str] | 任意タグ |

シリアライズ時、`None` のフィールドは出力しない（`to_jsonl()` は `exclude_none=True`）。これにより JSONL の行サイズを抑え、将来フィールドを追加しても旧記録との互換を保つ。

### 3.3 event_type と payload の対応

v0.1 で定義する event_type と、その payload に含めるべきオブジェクトを以下に固定する。

| event_type | payload の規約 | 発行元 |
|-----------|---------------|--------|
| chronicle_created | `{"title": str}` | ChronicleService.init |
| context_added | `{"context": Context}` | ContextService.add_context |
| user_input | 自由形式 | CLI record |
| assistant_output | 自由形式 | CLI record |
| artifact_created | `{"artifact": Artifact, "version": ArtifactVersion}` | ArtifactService.create |
| artifact_updated | `{"artifact": Artifact, "version": ArtifactVersion}` | （予約。v0.1の実装は artifact_versioned を使用） |
| artifact_versioned | `{"artifact": Artifact, "version": ArtifactVersion}` | ArtifactService.update |
| decision_recorded | `{"decision": Decision}` | DecisionService.record |
| rde_diff_recorded | `{"rde": RdeDiffRecord}` | RdeService.record |
| note_added | 自由形式 | CLI record |
| tag_updated | 自由形式 | （予約） |
| metadata_updated | 自由形式 | （予約） |

payload に格納されたスナップショットが、インデックス再構成（`chronicle index rebuild`）の唯一の情報源である。したがって payload 規約の変更はスキーマ変更として扱い、`schema_version` を更新する。

### 3.4 actor

```text
user / assistant / system / tool / reviewer / importer
```

v0.1 では権限管理を行わないが、「誰が記録したか」を必ず残す。これは将来の監査（誰が監査者を認可するか、という認可遡及の問いを含む）に備えた最低限の足場である。

## 4. 永続化と読み出し

Event は `JsonlStore.append` により1行1イベントで追記される。読み出し（`read_all`）は既定で `skip_corrupt=True` とし、破損行を読み飛ばして残りを返す。`skip_corrupt=False` の場合は `JsonlParseError`（行番号付き）を送出する。破損行の数は `count_corrupt_lines` で計数でき、`chronicle show` が警告として表示する。

この耐性設計の含意は、**部分的な破損が全体の喪失に波及しない**ことである。一次記録の一部が壊れても、残る Event からインデックスと成果物履歴を再構成できる。

## 5. 不変条件（normative）

以下を v0.1 の不変条件として規定する。

1. `event_id` は Chronicle 内で一意である。
2. `chronicle_id` は metadata.yaml の値と一致する。
3. Event は追記のみされ、既存行は変更・削除されない。
4. オブジェクト生成系の Event（artifact_created / artifact_versioned / decision_recorded / rde_diff_recorded）の payload は、**そのEventのevent_idを含む完全なスナップショット**を格納する。すなわち `ArtifactVersion.source_event_id` および `Decision.event_id` は、payload 書き込み時点で当該 Event の event_id を保持していなければならない。

## 6. 既知の課題（v0.1-draft 時点）

不変条件4は、現行実装で**満たされていない**。`ArtifactService.create/update` および `DecisionService.record` は、Event 記録後に `model_copy` で逆参照IDを補完するため、JSONL 上の payload には空の `source_event_id` / 未設定の `event_id` が永続化される（E2E検証で確認済み）。

修正方針：`record_event` に event_id を渡せるようにするか、service 側で `generate_id("event")` を事前生成し、スナップショット作成と Event 記録の双方に同一IDを供給する。本修正は v0.1 完了条件に含める（P0）。

## 7. 将来互換

v0.2 Context Sovereignty Layer は `context_ids` と `source` を、v0.3 RDE Integration は `rde_record_id` を、v0.5 Human Review Decision Model は `review_status` と `actor=reviewer` を接続点とする。これらのフィールドは v0.1 では未使用または最小限の使用に留まるが、削除・改名しない。
