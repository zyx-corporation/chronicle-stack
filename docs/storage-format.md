# Storage Format

Chronicle Core v0.1 の永続化形式。

## 一次記録: chronicle.jsonl

- 形式: JSONL（1 行 1 JSON オブジェクト）
- 全 Chronicle Event を追記
- Git 差分管理に適する
- 破損行があっても他行は読み取り可能（`skip_corrupt=True`）

**重要**: `chronicle.jsonl` が唯一の一次記録です。`indexes/` 以下のファイルはすべて派生データであり、`chronicle index rebuild` で再生成可能です。

## メタデータ: metadata.yaml

```yaml
chronicle_id: chr_...
title: Project Title
created_at: "2026-06-09T12:00:00+09:00"
version: "0.1"
schema_version: "chronicle-core-0.1"
default_timezone: "Asia/Tokyo"
```

## 派生データ: indexes/

| ファイル | 内容 |
|---------|------|
| artifact_index.json | Artifact と Version（RDE リンク付与済み） |
| context_index.json | Context |
| decision_index.json | Decision |
| rde_index.json | RDE Diff Record |
| boundary_rule_index.json | Boundary Rule |

`chronicle index rebuild` で `chronicle.jsonl` から再生成可能。

### RDE → Version リンクの派生付与

`chronicle.jsonl` の RDE_DIFF_RECORDED event は変更しません。
index rebuild 時に、RDE payload の `to_version_id` と一致する `ArtifactVersion` に `rde_record_id` を派生付与します。

複数の RDE が同一 Version を指す場合、v0.1 では JSONL 上で **後に現れた RDE が優先** されます。

## Artifact ファイル

```
artifacts/<artifact_id>/
  current.md              # 最新版
  versions/<version_id>.md  # スナップショット
```

## RDE レポート

```
reports/rde/<rde_record_id>.md
```

Markdown 形式の人間可読レポート。6 つの RDE フィールド（Preserved / Transformed / Supplemented / Unresolved / Deviation Risks / Next Update Policy）を含む。

## v0.1 → v0.2 Context 互換性

v0.1 の Context は `scope_hint` フィールドのみを持ちます。
v0.2 では正式な `ContextScope` （`scope` フィールド）を追加し、`scope_hint` は互換用に残されています。

- v0.1 形式（`scope_hint` のみ）のデータは v0.2 でそのまま読み込めます。`scope` が補完されます。
- v0.2 で作成された Context は `scope` と `scope_hint` の両方を持ちます。
- 将来のバージョンで `scope_hint` を削除する可能性があります。

## InjectionPlan の永続化

v0.2 の Context Injection Plan はデフォルトでは永続化しません。Plan は boundary rule 評価に基づいて都度生成される文脈選択案であり、Context や Boundary Rule のレコードを変更しません。
