# Chronicle Stack v0.3 Smoke Test

この文書は、Chronicle Stack v0.3 の手動スモークテスト手順です。

## 前提

```bash
pip install -e ".[dev]"
ruff check src/ tests/
pytest -v
```

期待:

```text
ruff: pass
pytest: 155 passed 以上
```

## 1. 初期化

```bash
rm -rf /tmp/chronicle-v03-smoke
mkdir -p /tmp/chronicle-v03-smoke
cd /tmp/chronicle-v03-smoke
chronicle --version
chronicle init --title "v0.3 Smoke"
chronicle show
```

確認:

- `chronicle --version` が成功する
- `.chronicle/chronicle.jsonl` が作成される
- `chronicle show` が成功する

## 2. Context / Visibility / Source

```bash
chronicle add-context \
  --title "Project Context" \
  --summary "General project context" \
  --scope project \
  --visibility private \
  --source-type conversation \
  --source-tool chatgpt

chronicle add-context \
  --title "Sensitive Context" \
  --summary "Sensitive review context" \
  --scope task \
  --visibility sensitive \
  --source-type document \
  --source-tool manual

chronicle add-context \
  --title "Temporary Context" \
  --summary "Temporary scratch context" \
  --scope temporary \
  --visibility unknown
```

確認:

- Contextが3件作成される
- `scope` と `visibility_hint` が保存される
- sensitive/privateはredactionされない

## 3. Artifact / Decision / RDE

```bash
mkdir -p docs
cat > docs/spec.md <<'EOF'
# Smoke Spec

Initial content.
EOF

chronicle artifact create --title "Smoke Spec" --type specification --file docs/spec.md --visibility private

cat > docs/spec.md <<'EOF'
# Smoke Spec

Updated content.
EOF

# art_... and ver_... values should be taken from command output / history.
chronicle artifact list
chronicle artifact history --artifact art_xxx

chronicle decision record --artifact art_xxx --type accepted --reason "Smoke decision"

chronicle rde record --artifact art_xxx --from ver_aaa --to ver_bbb --summary "Smoke RDE" \
  --preserved "Title" \
  --transformed "Body updated" \
  --supplemented "Smoke detail" \
  --unresolved "None" \
  --deviation-risk "Low" \
  --next-update-policy "Review on next release"
```

確認:

- Artifactが作成される
- Artifact historyが表示される
- Decisionが記録される
- RDE Diff Recordが記録される

## 4. Boundary Rules

```bash
chronicle boundary add \
  --type warn \
  --field visibility \
  --operator equals \
  --value sensitive \
  --reason "Sensitive context should be reviewed"

chronicle boundary add \
  --type exclude \
  --field scope \
  --operator equals \
  --value temporary \
  --reason "Temporary context should not be used by default"

chronicle boundary list
chronicle boundary list --json
```

確認:

- warn ruleとexclude ruleが作成される
- `boundary_rule_index.json` が再構築可能
- Boundary Rulesは助言的分類であり、access controlではない

## 5. Injection Plan 非永続 / 永続

```bash
before=$(wc -l < .chronicle/chronicle.jsonl)
chronicle injection plan --task "Draft release notes"
after=$(wc -l < .chronicle/chronicle.jsonl)
test "$before" = "$after"

chronicle injection plan --task "Draft release notes" --json

chronicle injection plan --task "Draft release notes" --record
chronicle injection plan --task "Draft release notes" --record --json
```

確認:

- `--record` なしではJSONL行数が変わらない
- `--record` 指定時のみ `injection_plan_recorded` Eventが追加される
- JSON出力に `plan`, `recorded`, `event_id` が含まれる
- selected / warned / excluded が保存される
- LLMへの自動注入は行われない

## 6. Search / Rebuild

```bash
chronicle search "Smoke"
chronicle search "Smoke" --json

rm -rf .chronicle/indexes
chronicle index rebuild
chronicle show
```

確認:

- 検索が成功する
- JSON出力がparse可能
- indexes削除後もrebuildできる
- JSONLは一次記録として維持される

## 7. Export

```bash
chronicle export --format yaml -o chronicle.yaml
chronicle export --format markdown -o chronicle.md
chronicle export --format graph-json -o graph.json
chronicle export --format html -o chronicle-dashboard.html
```

確認:

- YAML exportが生成される
- Markdown exportが生成される
- graph-json exportが生成され、`nodes` と `edges` を含む
- HTML dashboardが生成される
- exportはJSONLを変更しない
- visibility hintは表示されるがredactionされない

## 8. Graph-ready export

```bash
python -m json.tool graph.json >/tmp/graph.pretty.json
```

確認:

- `schema_version` がある
- `chronicle_id` がある
- `nodes` がある
- `edges` がある
- Context / Artifact / Decision / BoundaryRule / InjectionPlan nodeが含まれる
- graph DB / vector DB / embedding / LLM 依存がない
- GraphRAG engineではない

## 9. HTML Dashboard

```bash
grep -i "Chronicle Stack Dashboard" chronicle-dashboard.html
grep -i "Boundary Rules" chronicle-dashboard.html
grep -i "Recorded Injection Plans" chronicle-dashboard.html
grep -i "Graph" chronicle-dashboard.html
grep -i "sensitive" chronicle-dashboard.html
```

確認:

- Dashboard titleがある
- Summary cardsがある
- Recent Eventsがある
- Context / Artifact / Decision / RDE / Boundary Rule / Injection Planが表示される
- Graph overviewが表示される
- sensitive/private visibilityが表示される
- HTMLは読み取り専用の派生ビューである

## 10. Final verification

```bash
ruff check src/ tests/
pytest -v
```

期待:

```text
ruff: pass
pytest: 155 passed 以上
```

## Release readiness判断

次を満たせば v0.3.0 release candidate として扱える。

- ruff pass
- pytest pass
- smoke test pass
- JSONL primary contract維持
- `--record` なしInjectionPlan非永続維持
- graph-json exportはderived view
- HTML dashboardはstatic read-only derived view
- README / CHANGELOG / CLI reference / data model / storage format / interface contracts が整合している
