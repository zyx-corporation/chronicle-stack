# Chronicle Doctor

`chronicle doctor` は、Chronicle project のローカル整合性を確認するread-only診断コマンドです。

## Usage

```bash
chronicle doctor
chronicle doctor --json
```

## Scope

Doctor は次を確認します。

- `.chronicle/` の存在
- `.chronicle/chronicle.jsonl` の存在
- `metadata.yaml` の存在とparse可否
- JSONL各行のparse可否
- known EventType
- derived indexes の存在
- Artifact file の存在
- recorded InjectionPlan が参照する Context の存在
- graph-json export生成可否
- HTML dashboard export生成可否

## Read-only contract

Doctor は読み取り専用です。

- JSONLを変更しません。
- Indexを自動rebuildしません。
- Artifact fileを自動作成しません。
- 修復は行いません。

## Status and exit code

| status | meaning | exit code |
|---|---|---|
| `ok` | 問題なし | 0 |
| `warning` | 注意点あり。再構築などで解消可能な場合を含む | 0 |
| `error` | Chronicleとして致命的な問題あり | non-zero |

## JSON output

`chronicle doctor --json` は次の形を返します。

```json
{
  "status": "warning",
  "chronicle_id": "chr_...",
  "checks": [
    {
      "check_id": "indexes_present",
      "severity": "warning",
      "summary": "one or more derived indexes are missing",
      "detail": "artifact_index.json",
      "recommendation": "run `chronicle index rebuild`"
    }
  ]
}
```

## Non-goals

Doctor は次を行いません。

- 自動修復
- `--fix`
- index rebuildの自動実行
- artifact recovery
- semantic correctness validation
- remote validation
- cloud sync
- security scanning
- access control

## Related

- [CLI Reference](cli-reference.md)
- [Interface Contracts](interface-contracts.md)
- [v0.4 Roadmap](roadmap-v0.4.md)
