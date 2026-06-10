# Artifact Model 仕様書

## 1. 文書情報

文書名：Artifact Model 仕様書
版：v0.1-draft
親文書：[Chronicle Stack v0.1 — Chronicle Core 基本仕様書](chronicle-stack-basic-spec-v0.1.md) §11–12
実装：`src/chronicle/models/artifact.py`, `src/chronicle/services/artifact_service.py`, `src/chronicle/store/artifact_store.py`
作成者：Tomoyuki Kano

## 2. 目的と位置づけ

Artifact は、人間とAIの共同作業によって生成・更新される成果物の識別子と状態を表す。Artifact Model の責務は成果物の**内容**を持つことではなく、内容ファイルへのパス、更新履歴（Version）、状態（status）を時系列で追跡可能にすることである。

設計上の中心的な選択は次の二つである。

第一に、**内容はファイル、履歴はEvent**という分離。成果物本文は `artifacts/<artifact_id>/` 以下に人間可読な Markdown として置かれ、Artifact / Version のメタデータは Event の payload として JSONL に記録される。インデックス（artifact_index.json）は Event 列から再生成可能な派生データに過ぎない。

第二に、**差分ではなくスナップショット**。各 Version は全文コピーを `versions/<version_id>.md` に保存する。復元性と実装容易性を優先し、ストレージ効率は v0.1 では犠牲にする。

## 3. Artifact フィールド仕様

| フィールド | 型 | 説明 |
|-----------|------|------|
| artifact_id | str | `art_` + UUID hex |
| chronicle_id | str | 所属 Chronicle |
| title | str | 表示名 |
| artifact_type | ArtifactType | §3.1 |
| current_version_id | str | 最新 Version のID |
| created_at / updated_at | datetime | ISO 8601、タイムゾーン付き |
| status | ArtifactStatus | §3.2。既定は draft |
| path | str | `artifacts/<artifact_id>/current.md`（Chronicle ルート相対） |
| tags | list[str] | 任意タグ |

### 3.1 artifact_type

```text
document / specification / roadmap / essay / summary / translation /
code / prompt / review / report / configuration / other
```

### 3.2 status

```text
draft / reviewing / accepted / rejected / superseded / archived / unknown
```

v0.1 ではワークフロー制御を行わず、状態の記録のみを提供する。**Decision の記録は Artifact.status を変更しない**。これは設計上の意図的な分離であり、「判断の記録」と「状態の遷移」を連動させるか否かは v0.5 Human Review Decision Model の設計判断として保留する（基本仕様書 §27.4 および Roadmap Linkage Document 参照）。

## 4. ArtifactVersion フィールド仕様

| フィールド | 型 | 説明 |
|-----------|------|------|
| version_id | str | `ver_` + UUID hex |
| artifact_id | str | 親 Artifact |
| created_at | datetime | 作成時刻 |
| created_by | str | Actor 値の文字列（user / assistant 等） |
| source_event_id | str | この Version を生成した Event のID |
| parent_version_id | str \| None | 直前の Version。初版は None |
| path | str | `artifacts/<artifact_id>/versions/<version_id>.md` |
| change_summary | str | 変更要約。create 時は "created"、update 時は指定値または "updated" |
| rde_record_id | str \| None | この更新に対応する RDE Diff Record |

`parent_version_id` の連鎖により Version は単線の履歴を構成する。v0.1 では分岐（同一 parent からの複数 Version）を禁止しないが、サポートもしない。`history` は created_at 順の平坦なリストを返す。

## 5. ライフサイクル

### 5.1 作成（ArtifactService.create）

1. `artifact_id` と `version_id` を生成する。
2. Artifact（status=draft）と初版 Version（parent_version_id=None, change_summary="created"）を構築する。
3. `ArtifactStore.create_artifact_files` が `current.md` と `versions/<version_id>.md` の両方に本文を書き込む。本文は `--file` 指定ファイル、`content` 引数、または空文字列。
4. `artifact_created` Event を記録する。payload には artifact と version のスナップショットを含む。
5. インデックスを再構築する。

### 5.2 更新（ArtifactService.update）

1. インデックスから既存 Artifact を取得する。存在しなければ `ArtifactNotFoundError`。
2. 新 `version_id` を生成し、`parent_version_id` に現行 `current_version_id` を設定する。
3. Artifact の `current_version_id` と `updated_at` を更新したコピーを作る。
4. `current.md` を上書きし、新スナップショットを `versions/` に保存する。
5. `artifact_versioned` Event を記録し、インデックスを再構築する。

### 5.3 参照

`history` / `list_artifacts` / `get` はインデックス経由で読む。本文の読み出しは `ArtifactStore.read_current` / `read_version` による。

## 6. 不変条件（normative）

1. `current.md` の内容は、`current_version_id` が指す Version スナップショットと常に一致する。
2. すべての Version はちょうど一つの Event（artifact_created または artifact_versioned）から生成され、`source_event_id` でその Event を逆参照できる。
3. Version スナップショットファイルは作成後に変更されない。
4. インデックスを削除しても、JSONL から全 Artifact / Version メタデータを再構成できる（本文ファイルは artifacts/ に残存しているため、両者の結合で完全復元が成立する）。

## 7. 既知の課題（v0.1-draft 時点）

不変条件2の逆参照は現行実装で破綻している。`source_event_id` が空文字のまま payload に永続化される（Event Model 仕様書 §6 と同一のP0問題）。

また、`ArtifactVersion.rde_record_id` はモデル上存在するが、これを設定する経路が実装されていない。RDE Diff Record の記録（RdeService.record）は Version 側を更新しないため、Version→RDE のリンクは常に None である。RDE→Version 方向のリンク（from_version_id / to_version_id）のみが機能している。v0.1 内で `rde_diff_recorded` Event のインデックス処理とあわせて対応する（P1）。

## 8. 将来互換

v0.2 Context Sovereignty Layer では Artifact に `visibility_hint` を追加可能とする（基本仕様書 §22）。v0.3 RDE Integration では Version 更新時に RDE 評価を自動起票する接続点として `rde_record_id` を使用する。v0.4 CSG-RAG は artifact_id を検索結果の出所表示の単位として用いる。
