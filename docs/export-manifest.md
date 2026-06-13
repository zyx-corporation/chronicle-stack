# Export Manifest

Export Manifest は、Chronicle Stack が生成する派生exportに付与される来歴メタデータです。

これは、出力がどのChronicle状態から、どの形式で、どのツールversionにより生成されたかを追跡するための情報です。

## 目的

- export成果物の生成元を確認できるようにする
- `chronicle_id` と出力形式を明示する
- tool version と event count を残す
- 将来の redaction option などの export option を記録できるようにする

## 非目的

Export Manifest は次を提供しません。

- 暗号署名
- tamper-proof guarantee
- remote attestation
- 法的証明
- 内容の正しさの保証

## 対応形式

v0.4 Phase 3では、次の形式にmanifestを含めます。

| format | manifest location |
|---|---|
| `yaml` | top-level `export_manifest` |
| `graph-json` | top-level `export_manifest` |
| `html` | `Export Manifest` section |

Markdown exportは人間向けreportであり、このPhaseではmanifest埋め込み対象外です。将来、sidecar manifestを検討します。

## Manifest fields

```json
{
  "schema_version": "0.4",
  "export_format": "yaml",
  "generated_at": "...",
  "chronicle_id": "chr_...",
  "chronicle_title": "...",
  "tool_name": "chronicle-stack",
  "tool_version": "0.4.0.dev0",
  "event_count": 1,
  "export_options": {},
  "notes": []
}
```

## Contract

- Export Manifest は派生メタデータです。
- JSONLを変更しません。
- `chronicle.jsonl` が一次記録であることは変わりません。
- `generated_at` は生成時刻なので、完全deterministicではありません。
- Manifestはprovenance metadataであり、cryptographic proofではありません。

## Related

- [CLI Reference](cli-reference.md)
- [Interface Contracts](interface-contracts.md)
- [Storage Format](storage-format.md)
- [v0.4 Roadmap](roadmap-v0.4.md)
