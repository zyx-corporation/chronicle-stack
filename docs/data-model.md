# Chronicle Data Model

Chronicle Core v0.1 のデータモデル概要。詳細は [基本仕様書](specs/chronicle-stack-basic-spec-v0.1.md) を参照。

## Chronicle Event

最小記録単位。`chronicle.jsonl` に 1 行 1 イベントで追記される。

| フィールド | 必須 | 説明 |
|-----------|------|------|
| event_id | ✓ | `evt_` プレフィックス |
| chronicle_id | ✓ | 所属 Chronicle |
| timestamp | ✓ | ISO 8601 |
| event_type | ✓ | イベント種別 |
| actor | ✓ | 記録主体 |
| summary | ✓ | 人間可読要約 |
| payload | ✓ | 種別固有データ |

## Context

生成物・判断の背景情報。`context_added` イベントの payload に格納。

| フィールド | 必須 | 説明 |
|-----------|------|------|
| context_id | ✓ | `ctx_` プレフィックス |
| title | ✓ | 人間可読タイトル |
| summary | | 要約 |
| scope | ✓ | 正式な有効範囲（v0.2 で導入） |
| scope_hint | | 非推奨（v0.1互換用） |
| visibility_hint | | 可視性ヒント（public / private / sensitive / unknown）。権限管理ではない。 |
| source_type | | conversation / document / ... |
| confidence | | high / medium / low / unknown |

### ContextScope（v0.2）

| 値 | 意味 |
|----|------|
| `global` | プロジェクトをまたぐ長期文脈 |
| `project` | 現在のChronicleまたはプロジェクト単位 |
| `session` | 特定セッション内 |
| `task` | 特定タスク内 |
| `artifact` | 特定Artifactに紐づく |
| `temporary` | 一時的文脈 |
| `unknown` | 未分類または移行互換 |

`scope_hint` は v0.1 互換用に残されており、新規コードでは `scope` を使用する。
v0.1 形式（`scope_hint` のみ）のデータも読み込み時に `scope` として補完される。

## Artifact

成果物とそのスナップショット履歴。`artifacts/<id>/current.md` が最新、`versions/` に履歴。

`ArtifactVersion` は成果物の各スナップショットを表す。

| フィールド | 必須 | 説明 |
|-----------|------|------|
| artifact_id | ✓ | `art_` プレフィックス |
| title | ✓ | 人間可読タイトル |
| artifact_type | ✓ | document / specification / ... |
| status | | draft / reviewing / accepted / ... |
| visibility_hint | | 可視性ヒント（public / private / sensitive / unknown）。権限管理ではない。 |

### VisibilityHint（v0.2）

| 値 | 意味 |
|----|------|
| `public` | 公開候補。将来のexportや共有時に警告は低い |
| `private` | 個人・プロジェクト内部向け |
| `sensitive` | 機微情報を含む可能性。将来のexport/injection時に警告対象 |
| `unknown` | 未分類または移行互換 |

## Decision

採用・棄却・保留などの判断記録。`decision_recorded` イベントに格納。

## RDE Diff Record

成果物更新における意味変化の簡易監査。6 固定項目:

- preserved / transformed / supplemented
- unresolved / deviation_risks / next_update_policy

## Chronicle Metadata

Chronicle 全体のメタ情報。`metadata.yaml` として永続化。

## モデル間の参照関係

### Event → Version

```
ArtifactVersion.source_event_id → ChronicleEvent.event_id
```

`source_event_id` はバージョンが作成されたイベントを直接参照する。この値は `chronicle.jsonl` に永続化され、index rebuild 後も保持される。

### Event → Decision

```
Decision.event_id → ChronicleEvent.event_id
```

各 Decision は、それを記録したイベントの `event_id` を保持する。`chronicle.jsonl` に永続化される。

### RDE → Artifact / Version

```
RdeDiffRecord.artifact_id → Artifact.artifact_id
RdeDiffRecord.from_version_id → ArtifactVersion.version_id
RdeDiffRecord.to_version_id → ArtifactVersion.version_id
```

RDE Diff Record は、特定の Artifact の 2 つのバージョン間の差分を記録する。

### Version → RDE（派生リンク）

```
ArtifactVersion.rde_record_id → RdeDiffRecord.rde_record_id
```

このリンクは **一次 Event payload を直接書き換えるものではなく**、`chronicle index rebuild` 時に派生的に付与される。

- RDE event (RDE_DIFF_RECORDED) の `to_version_id` と一致する `ArtifactVersion.version_id` に対して、`rde_record_id` が設定される。
- 複数の RDE が同一 Version を指す場合、v0.1 では JSONL 上で **後に現れた RDE が優先** される。

## ID プレフィックス

`chr_` `evt_` `ctx_` `art_` `ver_` `dec_` `rde_` `src_`
