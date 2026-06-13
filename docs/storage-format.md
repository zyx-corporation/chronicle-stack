# Chronicle Stack Storage Format

Chronicle Stack v0.4 の永続化形式と派生データ形式を説明します。

## 一次記録: chronicle.jsonl

`.chronicle/chronicle.jsonl` が唯一の一次記録です。

- 形式: JSONL（1行1 JSON object）
- 内容: Chronicle Eventを追記
- Git差分管理に適する
- 派生Index、export、dashboard、graph-jsonは原則としてJSONLから再構成可能

重要:

`indexes/` 以下のファイル、export結果、HTML dashboard、graph-jsonは一次記録ではありません。

## ChronicleEvent JSONL

各行はChronicleEventです。

基本形:

```json
{
  "event_id": "evt_...",
  "chronicle_id": "chr_...",
  "timestamp": "2026-06-13T00:00:00+09:00",
  "event_type": "context_added",
  "actor": "user",
  "summary": "Add context",
  "payload": {}
}
```

EventTypeごとのpayload contractは [インターフェース契約](interface-contracts.md) と [データモデル](data-model.md) を参照してください。

## メタデータ: metadata.yaml

```yaml
chronicle_id: chr_...
title: Project Title
created_at: "2026-06-13T12:00:00+09:00"
version: "0.3"
schema_version: "chronicle-stack-0.3"
default_timezone: "Asia/Tokyo"
```

既存データとの互換性のため、過去のschema_versionを持つmetadataも読み取り対象です。

## 派生データ: indexes/

| ファイル | 内容 | 一次記録か |
|---|---|---|
| `artifact_index.json` | ArtifactとVersion | いいえ |
| `context_index.json` | Context | いいえ |
| `decision_index.json` | Decision | いいえ |
| `rde_index.json` | RDE Diff Record | いいえ |
| `boundary_rule_index.json` | Boundary Rule | いいえ |

`chronicle index rebuild` で `chronicle.jsonl` から再生成可能です。

将来InjectionPlan専用indexを追加する場合も、一次記録ではなく派生Indexとして扱います。

## Artifact files

```text
artifacts/<artifact_id>/
  current.md
  versions/<version_id>.md
```

Artifact本文はファイルとして保存されます。Artifact metadataとVersion metadataはEvent payloadおよび派生Indexから再構成されます。

## RDE reports

```text
reports/rde/<rde_record_id>.md
```

Markdown形式の人間可読reportです。一次記録ではありません。

## InjectionPlan persistence

Context Injection Planはデフォルトでは永続化されません。

```bash
chronicle injection plan --task "Draft"
```

上記はJSONLを変更しません。

明示的に `--record` を指定した場合のみ、`injection_plan_recorded` EventとしてJSONLへ記録されます。

```bash
chronicle injection plan --task "Draft" --record
```

payload形状:

```json
{
  "injection_plan": {
    "plan_id": "ip_...",
    "task": "Draft",
    "created_at": "...",
    "selected": [],
    "warned": [],
    "excluded": [],
    "notes": []
  }
}
```

## Export outputs

Exportは派生ビューです。JSONLを変更しません。

| format | 出力 | 契約レベル |
|---|---|---|
| `yaml` | YAML snapshot with `export_manifest` | Semi-public |
| `markdown` | Markdown report | Human-facing |
| `graph-json` | node/edge graph-ready JSON with `export_manifest` | Semi-public / derived |
| `html` | static read-only dashboard with manifest section | Human-facing |

## Export Manifest

Export Manifestは、export成果物に付与される来歴メタデータです。

対応形式:

- `yaml`: top-level `export_manifest`
- `graph-json`: top-level `export_manifest`
- `html`: `Export Manifest` section

Markdown exportは人間向けreportであり、この段階ではmanifest埋め込み対象外です。

Export Manifestは暗号署名やtamper-proof保証ではありません。JSONLを変更せず、出力がどのChronicle状態から生成されたかを追跡しやすくするための派生メタデータです。

### graph-json

```bash
chronicle export --format graph-json -o graph.json
```

`graph-json` はGraphRAG接続準備用の派生exportです。GraphRAGエンジン、graph DB、vector DB、embedding、LLM APIは含みません。

### html

```bash
chronicle export --format html -o chronicle-dashboard.html
```

HTML dashboardは静的・読み取り専用の人間向けreportです。HTML layoutは機械処理の安定契約ではありません。

## Visibility and redaction

`visibility_hint` はredactionではありません。

- `public`
- `private`
- `sensitive`
- `unknown`

exportやHTML dashboardでは、visibility hintは表示上の注意喚起として扱われます。デフォルトでは機密情報を自動除外しません。

将来redactionを導入する場合は、`--exclude-sensitive` などの明示オプションとして追加します。

## v0.1 → v0.2 → v0.3 compatibility

### Context scope compatibility

v0.1のContextは `scope_hint` のみを持つ場合があります。

v0.2以降では正式な `scope` フィールドを使います。`scope_hint` は互換用に残され、読み込み時に `scope` へ補完されます。

### Visibility compatibility

`visibility_hint` が欠損している旧データは `unknown` として扱います。

### Source compatibility

`source` が欠損している旧データは `None` として扱います。Source系Boundary Ruleはsource欠損Contextでも例外を投げません。

### InjectionPlan compatibility

v0.2のInjectionPlanは非永続のみでした。

v0.3では、明示的な `--record` 指定時のみ `injection_plan_recorded` Eventとして永続化できます。

## Rebuild contract

`chronicle index rebuild` はJSONLを一次記録として、派生Indexを再生成します。

rebuildはJSONLを変更してはなりません。

RDE → ArtifactVersion などの派生リンクはIndex上で付与されます。一次Event payloadは書き換えません。
