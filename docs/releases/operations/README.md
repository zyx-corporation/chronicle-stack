# Release Operations

このディレクトリは、Chronicle Stack の release / operator 実務で使う運用文書をまとめる領域です。

## Current Entry Points

- release operator guide: `release-operator-guide.md`
- local web UI operator validation: `local-web-ui-operator-validation-v1.0.md`
- local web UI validation report template: `local-web-ui-operator-validation-report-template.md`
- release tag policy: `release-tag-policy.md`

## Historical / Versioned Operations Docs

- release execution: `release-execution-v0.9.0.md`, `release-execution-v1.0.0.md`
- deployment notes: `release-deployment-v0.6.md`, `release-deployment-v0.9.md`
- release artifacts / lock / operator notes:
  - `release-artifacts-v0.9.0.md`
  - `release-lock-v0.9.0.md`
  - `release-operator-note-v0.9.0.md`

## Guidance

- 新しい operator-facing validation 文書を追加する場合は、まず current entry point か historical/versioned doc かを判断する
- 現在も参照される実務導線は versionless guide に寄せる
- 過去 release 固有の手順や証跡は versioned file として残す
