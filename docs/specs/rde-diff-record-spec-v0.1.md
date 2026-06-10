# RDE Diff Record 仕様書

## 1. 文書情報

文書名：RDE Diff Record 仕様書
版：v0.1-draft
親文書：[Chronicle Stack v0.1 — Chronicle Core 基本仕様書](chronicle-stack-basic-spec-v0.1.md) §14
実装：`src/chronicle/models/rde.py`, `src/chronicle/services/rde_service.py`
作成者：Tomoyuki Kano

## 2. 目的と位置づけ

RDE Diff Record は、ある成果物更新において、元の意図・価値・設計思想がどのように保存、変換、補完、逸脱したかを記録する簡易的な意味変化監査である。

textual diff（difflib 等が示す字面の差分）が「何が変わったか」を示すのに対し、RDE Diff Record は「**意味として何が保たれ、何が変質したか**」を示す。両者は補完関係にあり、置換関係にない。改稿・要約・翻訳・仕様変更のように字面が大きく変わる操作でこそ、意味の保存性を字面と独立に監査する価値が生じる。

v0.1 では RDE エンジン（自動評価）を実装しない。評価項目を6つに固定し、人間または AI が手動・半自動で記入する形式のみを提供する。これは意図的な抑制である。評価の自動化を先行させると、評価の信頼性よりも見かけの完成度が先行する（基本仕様書 §28 逸脱リスク）。

## 3. フィールド仕様

| フィールド | 型 | 説明 |
|-----------|------|------|
| rde_record_id | str | `rde_` + UUID hex |
| artifact_id | str | 対象 Artifact |
| from_version_id / to_version_id | str | 比較区間。両端とも存在する Version でなければならない |
| created_at | datetime | 作成時刻 |
| created_by | str | 評価主体。Actor 値に一致すれば Event の actor に反映、しなければ assistant にフォールバック |
| summary | str | 一行要約 |
| preserved | list[str] | 保存された要素 |
| transformed | list[str] | 変換された要素 |
| supplemented | list[str] | 補完された要素 |
| unresolved | list[str] | 未解決の要素 |
| deviation_risks | list[str] | 逸脱リスク |
| next_update_policy | list[str] | 次回更新方針 |

### 3.1 六項目の記入規約

六項目は v0.1 で固定であり、追加・削除しない。各項目は自然文の短い記述のリストとし、空リストを許容する。ただし六項目すべてが空の Record は監査として意味を持たないため、最低一項目の記入を推奨する。

各項目の判定基準を以下に定める。

**preserved**：from 版に存在した意図・方針・制約のうち、to 版でも明示的に維持されているもの。「言及されていないが矛盾もしていない」ものは preserved ではなく unresolved の候補である。

**transformed**：意図は引き継がれたが表現形式・抽象度・適用範囲が変わったもの。構想→仕様、仕様→実装、原文→翻訳など。

**supplemented**：from 版に存在せず to 版で新規に追加されたもの。

**unresolved**：from 版で開かれた論点のうち、to 版でも未決着のもの。先送りの明示化が目的であり、否定的評価ではない。

**deviation_risks**：今回の変換が将来引き起こしうる、元の意図からの逸脱の可能性。現に逸脱した事実ではなく、リスクの予告である。

**next_update_policy**：次の更新で守るべき方針。次回の RDE 評価における preserved 判定の基準線となる。

この最後の点が六項目構造の要である。next_update_policy → 次回の preserved という連鎖により、RDE Record 列は単発の評価の集積ではなく、**意図の継承を世代間で検証可能にする鎖**を構成する。

## 4. 記録手順（RdeService.record）

1. 対象 Artifact の存在を検証する。存在しなければ `ArtifactNotFoundError`。
2. from / to 両 Version のスナップショットファイルの存在を `ArtifactStore.version_exists` で検証する。存在しなければ `RdeVersionNotFoundError`。
3. RdeDiffRecord を構築する。
4. 人間可読レポートを `reports/rde/<rde_record_id>.md` に書き出す。レポートは Summary と六項目を見出しとする Markdown であり、空の項目は "(none)" と明示する。
5. `rde_diff_recorded` Event を記録する。payload に Record スナップショットを含める。

## 5. 不変条件（normative）

1. from_version_id と to_version_id は、記録時点で同一 Artifact 配下に実在する Version を指す。
2. すべての RDE Record はちょうど一つの `rde_diff_recorded` Event に対応する。
3. reports/ 以下のレポートは JSONL の payload から再生成可能である（一次記録は Event 側）。

## 6. 既知の課題（v0.1-draft 時点）

第一に、CLI（`chronicle rde record`)は summary しか受け取れず、六項目を入力する経路がサービス層 API（Python）に限られる。「手動または半自動で記録できる形式」という §14 の要件を CLI が満たしていない。修正方針は `--input rde.yaml` によるファイル入力の追加（P1）。六項目×複数値をコマンドラインオプションで渡す設計は非実用的なため採らない。

第二に、`rebuild_indexes` が `rde_diff_recorded` Event を処理しないため、RDE Record はどのインデックスにも載らない。検索は Event の payload 文字列照合経由でのみ可能である。また Artifact Model 仕様書 §7 の通り、`ArtifactVersion.rde_record_id` を設定する経路がなく、Version→RDE 方向のリンクが機能していない。rde_index.json の追加と Version リンクの設定を v0.1 内で対応する（P1）。

第三に、from/to の存在検証がスナップショットファイルの存在に依存している。ファイルが手動削除された場合、インデックス上は存在する Version への RDE 記録が拒否される。v0.1 では許容するが、検証の一次根拠をインデックス（＝Event 由来）に移すことを v0.3 で検討する。

## 7. 将来互換

v0.3 RDE Integration は本モデルを基礎に、Version 更新時の自動起票、ΔM 五成分・RDE 六軸（T-RDE v1.1+ で統合予定の体系）との対応付け、評価主体の位置性開示（created_by の拡張）を扱う。六項目の固定リスト構造は、軸別スコアリングへの移行時にも「自然文による根拠記述」として保持し、数値化が記述を置換しないことを設計原則とする。
