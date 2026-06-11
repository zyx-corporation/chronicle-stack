# Storage Format

Chronicle Core v0.1 の永続化形式。

## 一次記録: chronicle.jsonl

- 形式: JSONL（1 行 1 JSON オブジェクト）
- 全 Chronicle Event を追記
- Git 差分管理に適する
- 破損行があっても他行は読み取り可能（`skip_corrupt=True`）

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
| artifact_index.json | Artifact と Version |
| context_index.json | Context |
| decision_index.json | Decision |
| rde_index.json | RDE Diff Record |

`chronicle index rebuild` で `chronicle.jsonl` から再生成可能。

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

Markdown 形式の人間可読レポート。
