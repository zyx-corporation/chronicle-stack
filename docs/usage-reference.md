# Chronicle Stack Usage Reference

## 拡張クイックスタート

```bash
chronicle --version
chronicle init --title "My Project"
chronicle doctor
chronicle record --type user_input --actor user --summary "仕様書を作成する"
chronicle add-context --title "Task Context" --summary "このタスクだけで使う文脈" --scope task --visibility private
chronicle context classification missing
chronicle context classification set --context <CONTEXT_ID> --layer internal --sensitivity internal
chronicle audit record --operation export --purpose "internal review" --target local
chronicle lifecycle record --target <CONTEXT_ID> --target-kind context --action seal
chronicle package review --purpose "Sayane review" --target local --context <CONTEXT_ID>
chronicle artifact create --title "Basic Spec" --type specification --file docs/spec.md --visibility private
chronicle boundary add --type warn --field visibility --operator equals --value sensitive --reason "Review sensitive context"
chronicle injection plan --task "Draft release notes" --record
chronicle export --format yaml
chronicle export profile --format yaml --profile public-review
chronicle package context --purpose "Sayane review" --target local
chronicle package query-engine-adapter --query "What context should a downstream query engine inspect?"
chronicle package query-engine-bundle --query "What context should a downstream query engine inspect?" --output-dir handoff-bundle
chronicle export --format graph-json -o graph.json
chronicle export --format html -o chronicle-review-console.html
chronicle ai-index status
chronicle ai-index vector add --record <EVENT_ID> --text "placeholder local search text" --type event
chronicle ai-index vector search --query "local search"
chronicle ai-index graph add-node --id <EVENT_ID> --label event
chronicle ai-index graph neighbors --id <EVENT_ID>
chronicle runtime status
chronicle runtime summarize --text "Long source text to summarize locally" --record
chronicle runtime retrieve-plan --query "What context should I use?"
chronicle runtime retrieve-plan --query "What context should I use?" --record
chronicle object record --type question --summary "Why does this policy exist?" --created-by user
chronicle object list
chronicle object show --id <OBJECT_ID>
chronicle federation message create --type request_context --source-node node:local:alpha --target-node node:local:beta --purpose "project review"
chronicle federation inbox inspect
chronicle federation outbox inspect
chronicle federation package create --purpose "project review" --target-node node:partner:beta --visibility federated --output-dir federation-package
chronicle federation package inspect --package-dir federation-package
chronicle federation package verify --package-dir federation-package
chronicle federation package preview --package-dir federation-package
chronicle federation package import-preview --package-dir federation-package
chronicle federation boundary check --purpose "project review" --target-node node:partner:beta --context <CONTEXT_ID> --visibility federated
chronicle trust node add --node-id node:partner:beta --subject-id subject:beta
chronicle trust assert --target-node node:partner:beta --domain technical_review --purpose "project review" --level trusted --capability review
chronicle trust list
chronicle review queue
chronicle review approve --event <EVENT_ID> --reviewer <NAME>
chronicle review reject --event <EVENT_ID> --reviewer <NAME>
chronicle review request-changes --event <EVENT_ID> --reviewer <NAME>
chronicle artifact apply-proposal --event <PROPOSAL_EVENT_ID>
chronicle context apply-proposal --event <PROPOSAL_EVENT_ID>
chronicle ui-smoke
chronicle ui-smoke --json
chronicle ui
chronicle graph summary
chronicle context check --target local --purpose "internal review"
chronicle show
```

## UI と運用境界

- `chronicle ui` は明示起動型の foreground local web UI です
- デフォルトでは `127.0.0.1:8765` に bind し、read-only で現在の Chronicle root を表示します
- auth/authz 未実装のため loopback host (`127.0.0.1`, `localhost`, `::1`) のみ許可します
- `chronicle ui-smoke` はサーバーを起動せず、ブラウザも使わず、ローカル UI の read-only データ面を検証します

## 重要な動作仕様

- `.chronicle/chronicle.jsonl` が一次記録です
- `indexes/` は再構築可能な派生データです
- RDE は意味変化の構造化記録であり、正しさの判定ではありません
- Boundary Rules は助言的な分類であり、強制的な保護機構ではありません
- Classification metadata / Audit / Lifecycle は advisory metadata であり、アクセス制御ではありません
- `graph-json` は GraphRAG 接続準備用の派生 export です
- `chronicle federation package` と `preview` / `import-preview` は inspect-first の advisory workflow であり、自動送信や auto-apply は行いません
- `chronicle trust` は local trust registry であり、グローバル trust certification ではありません

## よく参照する文書

- [CLI Reference](./cli-reference.md)
- [Architecture](./architecture.md)
- [Interface Contracts](./interface-contracts.md)
- [GraphRAG Boundary](./graphrag-boundary.md)
- [Local Deployment Guide](./local-deployment-curl.md)
- [Doctor Security Checks](./doctor-security-checks.md)
- [Local UI Validation Checklist](./ui-local-validation-checklist.ja.md)
- [Releases Index](./releases/README.md)
