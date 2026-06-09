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

## Artifact / Version

成果物とそのスナップショット履歴。`artifacts/<id>/current.md` が最新、`versions/` に履歴。

## Decision

採用・棄却・保留などの判断記録。`decision_recorded` イベントに格納。

## RDE Diff Record

成果物更新における意味変化の簡易監査。6 固定項目:

- preserved / transformed / supplemented
- unresolved / deviation_risks / next_update_policy

## ID プレフィックス

`chr_` `evt_` `ctx_` `art_` `ver_` `dec_` `rde_` `src_`
