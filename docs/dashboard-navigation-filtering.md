# Dashboard Navigation and Filtering

Chronicle Stack の HTML dashboard は、単一ファイルの静的・読み取り専用reportです。

v0.4では、大きめのChronicleでも確認しやすいように、ローカルアンカーnavigationと軽量な行filterを追加します。

## Scope

追加される機能:

- section navigation
- stable local anchors
- local row filtering
- single-file HTML output
- no external assets

## Sections

Dashboardは次のsection anchorを持ちます。

- `#manifest`
- `#summary`
- `#events`
- `#contexts`
- `#artifacts`
- `#decisions`
- `#rde-records`
- `#boundary-rules`
- `#injection-plans`
- `#notes`

## Local filtering

HTML内のfilter inputで、表示中のtable rowsをローカルに絞り込めます。

対象:

- Recent Events
- Contexts
- Artifacts
- Decisions
- RDE Diff Records
- Boundary Rules
- Recorded Injection Plans

Filterは表示補助です。Chronicle records、JSONL、indexes、export内容そのものを変更しません。

## Non-goals

この機能は次を提供しません。

- live dashboard server
- editing UI
- authentication
- cloud sync
- frontend framework
- graph visualization engine
- access control
- redaction

## Contract

- Dashboard remains static.
- Dashboard remains read-only.
- HTML is a human-facing derived view.
- HTML layout is not a machine-processing stable contract.
- JSONL remains primary.
- No external JavaScript or CSS dependency is introduced.

## Related

- [CLI Reference](cli-reference.md)
- [Storage Format](storage-format.md)
- [Export Manifest](export-manifest.md)
- [Redaction-aware Export](redaction-aware-export.md)
- [v0.4 Roadmap](roadmap-v0.4.md)
