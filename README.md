# Chronicle Stack

Chronicle Stack は、AIとの共同作業で生まれる文脈、判断、生成物、差分、出所、境界ルールを、後から再構成できる形で記録する local-first な基盤です。

## 概要

Chronicle Stack が重視する中心価値は **再構成可能性** です。最終成果物だけでなく、そこに至る文脈、判断、意味変化、出所を後から辿れるようにします。

主な特徴:

- `chronicle.jsonl` を一次記録とする local-first 設計
- Context / Artifact / Decision / RDE / Audit / Lifecycle の記録
- read-only local web UI と静的 export による inspect-first 運用
- federation package / trust / runtime を preview-first で扱う境界重視の設計

Chronicle Stack は、クラウド型AIメモリ、ホステッド実行基盤、完成済み GraphRAG runtime、default-on GUI mutation ではありません。詳細な境界と現状は [Product Overview](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/product-overview.md) を参照してください。

## 利用方法

### インストール

開発用:

```bash
pip install -e ".[dev]"
```

ローカル配備用:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh -o /tmp/chronicle-install-local.sh
less /tmp/chronicle-install-local.sh
bash /tmp/chronicle-install-local.sh
```

詳細は [Local Deployment Guide](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/local-deployment-curl.md) を参照してください。

### クイックスタート

```bash
chronicle --version
chronicle init --title "My Project"
chronicle doctor
chronicle record --type user_input --actor user --summary "仕様書を作成する"
chronicle add-context --title "Task Context" --summary "このタスクだけで使う文脈" --scope task --visibility private
chronicle artifact create --title "Basic Spec" --type specification --file docs/spec.md --visibility private
chronicle decision record --artifact <ARTIFACT_ID> --type accepted --reason "採用理由"
chronicle export --format yaml
chronicle ui-smoke --json
chronicle ui
```

日常利用でよく使う導線:

- 記録開始: `chronicle init`, `chronicle record`, `chronicle add-context`
- 成果物管理: `chronicle artifact`, `chronicle decision`, `chronicle rde`
- 状態確認: `chronicle doctor`, `chronicle show`, `chronicle ui`, `chronicle ui-smoke`
- 共有前確認: `chronicle boundary`, `chronicle audit`, `chronicle lifecycle`, `chronicle federation package`

より広い CLI 例、UI endpoint、運用境界、extended quickstart は [Usage Reference](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/usage-reference.md) を参照してください。

## 運用方法

ローカル運用の入口:

- [Local Operator Runbook](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/releases/operations/local-operator-runbook.md)
- [Local Backup And Restore](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/releases/operations/local-backup-and-restore.md)
- [Local UI Validation Checklist](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/ui-local-validation-checklist.ja.md)
- [Release Operations](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/releases/operations/README.md)

確認の基本コマンド:

```bash
chronicle doctor
chronicle ui-smoke --json
ruff check src/ tests/
pytest
```

現在の release lane とリリース文書:

- [Releases Index](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/releases/README.md)
- [Release Notes v2.0.0](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/releases/notes/release-notes-v2.0.0.md)
- [Release Readiness v2.0](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/releases/readiness/release-readiness-v2.0.md)

## 関連文書

- [Architecture](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/architecture.md)
- [Interface Contracts](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/interface-contracts.md)
- [CLI Reference](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/cli-reference.md)
- [Product Overview](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/product-overview.md)
- [Usage Reference](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/usage-reference.md)
- [Overall Roadmap](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/roadmaps/overall-roadmap.md)

## ライセンス

AGPL-3.0-or-later. 詳細は [LICENSE](/Users/tomyuk/Projects/Chronicle/chronicle-stack/LICENSE) を参照してください。

商用利用、クローズドソース製品への組み込み、SaaS/ホステッドサービスでの利用については、別途商用ライセンスを検討します。詳細は [Commercial-SaaS-License.md](/Users/tomyuk/Projects/Chronicle/chronicle-stack/Commercial-SaaS-License.md) と [Contributor License Policy](/Users/tomyuk/Projects/Chronicle/chronicle-stack/docs/contributor-license-policy.md) を参照してください。
