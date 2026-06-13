# Redaction-aware Export

Redaction-aware export は、`visibility_hint=sensitive` の Context / Artifact を、明示的なexport optionでredactまたはexcludeする仕組みです。

これは派生exportの開示制御であり、access control、認証、暗号化、完全な情報保護ではありません。

## Usage

```bash
chronicle export --format yaml --redact-sensitive
chronicle export --format yaml --exclude-sensitive
chronicle export --format html --redact-sensitive
chronicle export --format html --exclude-sensitive
```

`--redact-sensitive` と `--exclude-sensitive` は同時指定できません。

## Supported formats

v0.4 Phase 4では、次の形式に対応します。

| format | support |
|---|---|
| `yaml` | supported |
| `html` | supported |
| `markdown` | not supported |
| `graph-json` | not supported |

`graph-json` はGraphRAG接続準備用の派生構造であり、redaction semanticsを慎重に扱う必要があるため、このPhaseでは対象外です。

## Behavior

### `--redact-sensitive`

`sensitive` な Context / Artifact のtitle、summary、source、path、tagsなどを `[REDACTED:sensitive]` に置き換えます。

YAML exportでは、sensitive Context / Artifact を含むevent payloadもredactされます。

### `--exclude-sensitive`

`sensitive` な Context / Artifact をexportから除外します。

YAML exportでは、sensitive Context / Artifact を含むeventも除外します。

## Export Manifest

Redaction-aware exportを使った場合、Export Manifest の `export_options` に次の情報が記録されます。

```json
{
  "redact_sensitive": true,
  "exclude_sensitive": false
}
```

## Non-goals

Redaction-aware export は次を提供しません。

- access control
- authentication
- encryption
- automatic sensitive classification
- complete leakage prevention
- cryptographic proof
- legal compliance guarantee

## Contract

- JSONLを変更しません。
- Indexを変更しません。
- default export behaviorは変えません。
- redaction/exclusionは明示option指定時のみ有効です。
- `private` はこのPhaseでは対象外です。
- `sensitive` の判定は `visibility_hint=sensitive` に基づきます。

## Related

- [CLI Reference](cli-reference.md)
- [Export Manifest](export-manifest.md)
- [Storage Format](storage-format.md)
- [v0.4 Roadmap](roadmap-v0.4.md)
