# Release Operations

このディレクトリは、Chronicle Stack の release / operator 実務で使う運用文書をまとめる領域です。

## Current Entry Points

- release operator guide: `release-operator-guide.md`
- local web UI operator validation: `local-web-ui-operator-validation-v1.0.md`
- local web UI validation report template: `local-web-ui-operator-validation-report-template.md`
- local web UI validation evidence example: `local-web-ui-operator-validation-evidence-2026-06-30.md`
- local web UI manual walkthrough evidence example: `local-web-ui-operator-validation-evidence-2026-06-30-manual-walkthrough.md`
- local web UI detail-entry follow-up evidence example: `local-web-ui-operator-validation-evidence-2026-06-30-detail-entry-followup.md`
- release tag policy: `release-tag-policy.md`

## Quick Start

1. release 実行手順を見るなら `release-operator-guide.md`
2. local web UI を手動検証するなら `local-web-ui-operator-validation-v1.0.md`
3. 検証結果を残すなら `local-web-ui-operator-validation-report-template.md`
4. preflight/startup evidence の実例を見るなら `local-web-ui-operator-validation-evidence-2026-06-30.md`
5. manual walkthrough の実例を見るなら `local-web-ui-operator-validation-evidence-2026-06-30-manual-walkthrough.md`
6. detail-entry fix 後の follow-up を見るなら `local-web-ui-operator-validation-evidence-2026-06-30-detail-entry-followup.md`

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
