# Chronicle Stack Data Model

Chronicle Stack v0.3 のデータモデル概要です。詳細な安定性方針は [インターフェース契約](interface-contracts.md) を参照してください。

## 基本原則

Chronicle Stack の一次記録は `.chronicle/chronicle.jsonl` です。

すべての派生Index、検索結果、export、HTML dashboard、graph-json exportは、原則としてJSONLから再構成可能な派生ビューです。

## Chronicle Event

最小記録単位です。`chronicle.jsonl` に 1 行 1 Event として追記されます。

| フィールド | 必須 | 説明 |
|---|---|---|
| `event_id` | ✓ | `evt_` prefix |
| `chronicle_id` | ✓ | 所属Chronicle |
| `timestamp` | ✓ | ISO 8601 |
| `event_type` | ✓ | Event種別 |
| `actor` | ✓ | 記録主体 |
| `summary` | ✓ | 人間可読要約 |
| `payload` | ✓ | EventType固有payload |
| `parent_event_id` | | 親Event |
| `artifact_id` | | 関連Artifact |
| `context_ids` | | 関連Context ID一覧 |
| `decision_id` | | 関連Decision |
| `rde_record_id` | | 関連RDE record |
| `source` | | SourceProvenance |
| `confidence` | | confidence hint |
| `review_status` | | review status |
| `tags` | | tag一覧 |

## EventType payload contract

| EventType | payload |
|---|---|
| `chronicle_created` | Chronicle作成情報 |
| `context_added` | `{ "context": Context }` |
| `user_input` | 任意の入力記録 |
| `assistant_output` | 任意の出力記録 |
| `artifact_created` | `{ "artifact": Artifact, "version": ArtifactVersion? }` |
| `artifact_updated` | `{ "artifact": Artifact, "version": ArtifactVersion? }` |
| `artifact_versioned` | `{ "artifact_id": str, "version": ArtifactVersion }` |
| `decision_recorded` | `{ "decision": Decision }` |
| `rde_diff_recorded` | `{ "rde": RdeDiffRecord }` |
| `boundary_rule_added` | `{ "boundary_rule": BoundaryRule }` |
| `injection_plan_recorded` | `{ "injection_plan": InjectionPlan }` |
| `note_added` | note payload |
| `tag_updated` | tag変更payload |
| `metadata_updated` | metadata変更payload |

## Context

生成物・判断の背景情報です。`context_added` Eventのpayloadに格納されます。

| フィールド | 必須 | 説明 |
|---|---|---|
| `context_id` | ✓ | `ctx_` prefix |
| `title` | ✓ | 人間可読タイトル |
| `summary` | | 要約 |
| `source_type` | | v0.1互換source分類 |
| `source_ref` | | v0.1互換source参照 |
| `scope` | ✓ | 正式な有効範囲 |
| `scope_hint` | | 非推奨。v0.1互換用 |
| `visibility_hint` | | public / private / sensitive / unknown |
| `source` | | SourceProvenance |
| `confidence` | | high / medium / low / unknown |
| `created_at` | ✓ | 作成時刻 |
| `tags` | | tag一覧 |

### ContextScope

| 値 | 意味 |
|---|---|
| `global` | プロジェクトをまたぐ長期文脈 |
| `project` | 現在のChronicleまたはプロジェクト単位 |
| `session` | 特定セッション内 |
| `task` | 特定タスク内 |
| `artifact` | 特定Artifactに紐づく |
| `temporary` | 一時的文脈 |
| `unknown` | 未分類または移行互換 |

`scope_hint` はv0.1互換用に残されています。新規コードでは `scope` を使用します。v1.0までは読み取り互換を維持する方針です。

## SourceProvenance

SourceProvenanceは出所記録です。真実性や完全性の暗号学的証明ではありません。

主なフィールド:

| フィールド | 説明 |
|---|---|
| `source_type` | source分類 |
| `source_ref` | source参照 |
| `source_tool` | 取得・生成に使ったtool |
| `source_session` | session識別子 |
| `source_model` | model識別子 |
| `source_file` | file参照 |
| `source_url` | URL参照 |
| `captured_at` | 取得時刻 |
| `imported_at` | import時刻 |

## VisibilityHint

VisibilityHintは分類・注意喚起のhintです。アクセス制御やredactionではありません。

| 値 | 意味 |
|---|---|
| `public` | 公開候補 |
| `private` | 個人・プロジェクト内部向け |
| `sensitive` | 機微情報を含む可能性 |
| `unknown` | 未分類または移行互換 |

## Artifact / ArtifactVersion

Artifactは成果物です。ArtifactVersionは成果物の各スナップショットを表します。

| フィールド | 必須 | 説明 |
|---|---|---|
| `artifact_id` | ✓ | `art_` prefix |
| `title` | ✓ | 人間可読タイトル |
| `artifact_type` | ✓ | document / specification / ... |
| `status` | | draft / reviewing / accepted / ... |
| `visibility_hint` | | public / private / sensitive / unknown |

ArtifactVersionは `source_event_id` により、それを作成したEventへ接続されます。

## Decision

採用・棄却・保留などの判断記録です。`decision_recorded` Eventに格納されます。

Decisionは `event_id` により、それを記録したEventへ接続されます。

## RDE Diff Record

成果物更新における意味変化の簡易監査です。

固定項目:

- preserved
- transformed
- supplemented
- unresolved
- deviation_risks
- next_update_policy

RDEは正しさを証明するものではありません。意味変化を構造化して記録するための枠組みです。

## Boundary Rule

Boundary Rule は文脈使用に関する助言的なルールです。

| rule_type | 意味 |
|---|---|
| `include` | 選択理由を補強する |
| `exclude` | plan候補から除外する |
| `warn` | 注意喚起する |

評価優先順位:

```text
exclude > warn > include > default candidate
```

Boundary Ruleは `boundary_rule_added` Eventとして記録され、`boundary_rule_index.json` として派生Index化されます。アクセス制御や強制削除の仕組みではありません。

## Context Injection Plan

Context Injection Plan は、Boundary Rule評価に基づいてContextを `selected` / `warned` / `excluded` に分類する文脈選択案です。

| section | 意味 |
|---|---|
| `selected` | 利用候補として提案されるContext |
| `warned` | 注意が必要なContext。selectedと重複可能 |
| `excluded` | 候補から除外されたContext。selectedとは重複しない |
| `notes` | 人間向け注記 |

重要:

- LLMへの自動注入は行いません。
- デフォルトでは永続化しません。
- `chronicle injection plan --record` を指定した場合のみ `injection_plan_recorded` EventとしてJSONLに記録します。
- ContextやBoundary Ruleのレコードを変更しません。

## Graph Export Model

v0.3ではGraphRAG接続準備として、Chronicle記録をnode/edgeへ写像する派生exportを追加しました。

| Model | 説明 |
|---|---|
| `GraphNode` | graph node候補 |
| `GraphEdge` | graph edge候補 |
| `GraphExport` | graph-json export snapshot |

Graph exportは `chronicle export --format graph-json` で生成します。

重要:

- GraphRAGエンジンではありません。
- graph DB / vector DB / embedding / LLM 依存はありません。
- JSONLからdeterministicに再構成される派生ビューです。

## HTML Dashboard Export

v0.3では静的・読み取り専用HTML dashboard exportを追加しました。

```bash
chronicle export --format html -o chronicle-dashboard.html
```

HTML dashboardは人間向けの派生reportです。機械処理の安定契約ではありません。

## モデル間の参照関係

### Event → Version

```text
ArtifactVersion.source_event_id → ChronicleEvent.event_id
```

### Event → Decision

```text
Decision.event_id → ChronicleEvent.event_id
```

### RDE → Artifact / Version

```text
RdeDiffRecord.artifact_id → Artifact.artifact_id
RdeDiffRecord.from_version_id → ArtifactVersion.version_id
RdeDiffRecord.to_version_id → ArtifactVersion.version_id
```

### Version → RDE（派生リンク）

```text
ArtifactVersion.rde_record_id → RdeDiffRecord.rde_record_id
```

このリンクは一次Event payloadを直接書き換えるものではなく、`chronicle index rebuild` 時に派生的に付与されます。

### InjectionPlan → Context

```text
InjectionPlan.selected[].context_id → Context.context_id
InjectionPlan.warned[].context_id → Context.context_id
InjectionPlan.excluded[].context_id → Context.context_id
```

## ID prefixes

```text
chr_ evt_ ctx_ art_ ver_ dec_ rde_ src_ br_ ip_
```

Graph exportのnode/edge IDは派生IDであり、JSONL上の一次IDではありません。
