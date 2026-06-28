# Smoke Test Procedure — Chronicle Core v0.2

Chronicle Core v0.2 Context Sovereignty Layer の動作確認手順。

## 前提

```bash
pip install -e ".[dev]"
```

## 手順

### 1. 初期化

```bash
chronicle init --title "v0.2 Smoke"
```

### 2. Context 作成（Scope + Visibility + Source Provenance）

```bash
chronicle add-context \
  --title "Project Context" \
  --summary "Useful project context" \
  --scope project \
  --visibility private \
  --source-type conversation \
  --source-tool chatgpt \
  --source-session smoke_001 \
  --json

chronicle add-context \
  --title "Sensitive Context" \
  --summary "Sensitive task note" \
  --scope task \
  --visibility sensitive \
  --source-type conversation \
  --source-tool chatgpt \
  --source-session smoke_001 \
  --json

chronicle add-context \
  --title "Temporary Context" \
  --summary "Temporary scratch note" \
  --scope temporary \
  --visibility private \
  --source-type conversation \
  --source-tool local-cli \
  --json
```

確認: 各 Context の JSON に `scope`, `visibility_hint`, `source` が含まれる。

### 3. Boundary Rule 追加

```bash
chronicle boundary add \
  --type warn \
  --field visibility \
  --operator equals \
  --value sensitive \
  --reason "Sensitive context should be reviewed before injection" \
  --json

chronicle boundary add \
  --type exclude \
  --field scope \
  --operator equals \
  --value temporary \
  --reason "Temporary context should not be injected by default" \
  --json
```

確認: 各 Rule の JSON に `rule_id` (`br_` prefix) が含まれる。

### 4. Boundary Rule 一覧・評価

```bash
chronicle boundary list --json
chronicle boundary check --context <ctx_sensitive_id> --json
```

確認: 一覧に2件の Rule が表示される。`check` で warn Rule が matched になる。

### 5. Context Injection Plan

```bash
chronicle injection plan --task "Draft v0.2 release notes" --json
chronicle injection plan --task "Draft v0.2 release notes"
```

確認:
- Project Context は `selected` に入る
- Sensitive Context は `selected` かつ `warned` に入る
- Temporary Context は `excluded` に入る
- Markdown 風出力に3分類が表示される
- `chronicle.jsonl` のイベント数は Plan 生成だけでは増えない

### 6. 検索

```bash
chronicle search "smoke_001" --json
```

確認: Source Provenance (`source_session`) で検索できる。

### 7. Export

```bash
chronicle export --format yaml
chronicle export --format markdown
```

確認: Context / Boundary Rule / Source の情報が含まれる。

### 8. Index Rebuild

```bash
chronicle index rebuild
chronicle show
```

確認: rebuild 後も全データが保持される。

## 合格基準

- Context に scope / visibility / source が正しく保存される
- Boundary Rule が追加・一覧・評価できる
- Injection Plan が selected / warned / excluded に正しく分類する
- Plan 生成は Context や Boundary Rule を変更しない
- 検索が Source Provenance を含む
- Export に全データが含まれる
- Index rebuild が正常に完了する
