# Decision Model 仕様書

## 1. 文書情報

文書名：Decision Model 仕様書
版：v0.1-draft
親文書：[Chronicle Stack v0.1 — Chronicle Core 基本仕様書](chronicle-stack-basic-spec-v0.1.md) §13
実装：`src/chronicle/models/decision.py`, `src/chronicle/services/decision_service.py`
作成者：Tomoyuki Kano

## 2. 目的と位置づけ

Decision は、人間またはシステムが生成物・方針に対して行った判断の記録である。Chronicle Stack において Decision は周辺機能ではなく中核である。AI生成物の履歴だけでは「なぜこの成果物が採用されたのか」を再構成できない。採用された案だけでなく、棄却された案、保留された論点、再検討条件を記録対象とすることで、成果物を「結果」ではなく「判断の系譜」として扱えるようにする。

設計原則として、v0.1 の Decision は**宣言的記録**である。Decision を記録しても、対象 Artifact の status は変化せず、いかなる副作用も生じない。判断と状態遷移の連動（あるいは意図的な非連動）は v0.5 の設計判断として明示的に保留する。この保留自体が、Chronicle 上に Decision として記録されるべき種類の判断である。

## 3. フィールド仕様

| フィールド | 型 | 説明 |
|-----------|------|------|
| decision_id | str | `dec_` + UUID hex |
| chronicle_id | str | 所属 Chronicle |
| artifact_id | str \| None | 判断対象の Artifact。方針判断など対象なしも許容 |
| event_id | str \| None | この Decision を記録した Event |
| decision_type | DecisionType | §3.1 |
| decided_by | str | 判断主体。既定は "user" |
| decided_at | datetime | 判断時刻 |
| reason | str | 判断理由。空文字を許容するが、推奨しない |
| alternatives | list[str] | 検討された代替案 |
| notes | str | 補足。再検討条件などを記す |

### 3.1 decision_type

| 値 | 意味 |
|----|------|
| accepted | 採用 |
| rejected | 棄却 |
| revised | 修正のうえ採用 |
| deferred | 保留（再検討条件を notes に記すこと） |
| superseded | 後続案による置換 |
| merged | 他案との統合 |
| split | 分割 |
| needs_review | 要レビュー |

### 3.2 「責任仮固定」との対応

deferred と needs_review は、判断を最終確定ではなく**再開可能条件付きの仮固定**として扱うための型である。deferred には再開条件を、needs_review にはレビュー主体の期待を notes に残すことを規約とする。これにより Decision 列は「閉じた決定のログ」ではなく「開かれた問いの台帳」としても機能する。

## 4. 記録手順（DecisionService.record）

1. `artifact_id` が指定された場合、対象 Artifact の存在を検証する。存在しなければ `DecisionTargetNotFoundError`（`ArtifactNotFoundError` を原因例外として連鎖）。
2. Decision を構築する。
3. `decision_recorded` Event を記録する。Event には `decision_id` と `artifact_id` を設定し、payload に Decision スナップショットを含める。
4. インデックスを再構築する。decision_index.json は Event payload から導出される。

## 5. 不変条件（normative）

1. `artifact_id` を持つ Decision は、記録時点で存在する Artifact のみを参照する。
2. すべての Decision はちょうど一つの `decision_recorded` Event に対応し、`event_id` でその Event を逆参照できる。
3. Decision は記録後に変更されない。判断の変更は新しい Decision（superseded / revised 等）の追記によって表現する。

## 6. 既知の課題（v0.1-draft 時点）

不変条件2が現行実装で破綻している。`event_id` は Event 記録後に `model_copy` で補完されるため、JSONL 上の payload では未設定のまま永続化される。インデックス再構築後の Decision は `event_id=None` となる（Event Model 仕様書 §6 のP0問題と同根）。修正は event_id の事前生成による。

また、CLI（`chronicle decision record`）は `alternatives` / `notes` / `decided_by` を受け取れない。棄却案と再検討条件の記録という Decision Model の本来の目的に対し、CLI が reason のみに制限されているのは機能不足であり、v0.1 内での `--alternative`（複数指定可）/ `--notes` / `--decided-by` の追加を推奨する（P1相当）。

## 7. 将来互換

v0.5 Human Review Decision Model は本モデルの直接の拡張先である。想定される拡張は、レビューワークフロー（needs_review→reviewed の遷移）、複数レビュアーの合議、Decision と Artifact.status の連動規則、判断主体の認可記録（誰がその判断者を判断者として認めたか）である。v0.1 では `decided_by` を自由文字列に留めることで、PoP-UID 等の人格証明体系への将来接続を妨げない。
