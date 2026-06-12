# Smoke Test Procedure — Chronicle Core v0.1

Chronicle Core v0.1 のリリース前動作確認手順。

## 前提

```bash
pip install -e ".[dev]"
```

## 手順

### 1. 初期化

```bash
chronicle init --title "Smoke Test"
```

確認: `.chronicle/` が作成され、`chronicle.jsonl` と `metadata.yaml` が存在する。

### 2. イベント記録

```bash
chronicle record --type user_input --actor user --summary "Create initial spec"
```

確認: `evt_` で始まる event_id が出力される。

### 3. Artifact 作成

```bash
echo "# Spec v1" > spec-v1.md
chronicle artifact create --title "Smoke Spec" --type specification --file spec-v1.md
chronicle artifact list
```

確認: `art_` で始まる artifact_id と `ver_` で始まる version_id が出力される。

### 4. Artifact 更新

```bash
echo "# Spec v2" > spec-v2.md
chronicle artifact update --artifact <art_id> --file spec-v2.md --summary "Update spec"
chronicle artifact history --artifact <art_id>
```

確認: 2 つのバージョンが表示され、新しいバージョンに `parent_version_id` が設定されている。

### 5. Artifact 履歴（JSON）

```bash
chronicle artifact history --artifact <art_id> --json
```

確認: 各バージョンに `source_event_id` が `evt_` で始まる値で格納されている。

### 6. Decision 記録

```bash
chronicle decision record --artifact <art_id> --type accepted --reason "Accepted for smoke test"
```

確認: `dec_` で始まる decision_id が出力される。

### 7. RDE Diff Record 記録

```bash
chronicle rde record \
  --artifact <art_id> \
  --from <ver_1> \
  --to <ver_2> \
  --summary "Smoke RDE" \
  --preserved "Original purpose" \
  --transformed "Expanded content" \
  --supplemented "Added smoke test" \
  --unresolved "No unresolved item" \
  --deviation-risk "Scope creep risk" \
  --next-update-policy "Keep v0.1 minimal"
```

確認:
- `rde_` で始まる rde_record_id が出力される
- `.chronicle/reports/rde/<rde_id>.md` が作成され、6 項目が Markdown 形式で出力されている

### 8. Index 再構築と RDE → Version リンク確認

```bash
chronicle index rebuild
chronicle artifact history --artifact <art_id> --json
```

確認: 更新後のバージョン (`to_version_id` に指定したバージョン) の `rde_record_id` に、手順 7 で作成した `rde_` ID が設定されている。

### 9. 検索

```bash
chronicle search "Smoke"
```

確認: イベント、Artifact、Decision、RDE の各カテゴリから "Smoke" を含む結果が返る。

### 10. エクスポート

```bash
chronicle export --format yaml
chronicle export --format markdown
```

確認: いずれもエラーなく出力される。

### 11. 概要表示

```bash
chronicle show
```

確認: Chronicle タイトル、イベント数、Artifact 数、Decision 数が表示される。

## 合格基準

- 全コマンドがエラーなく実行できる
- `source_event_id` が `chronicle.jsonl` と再構築後のインデックスの両方で保持される
- `decision.event_id` が永続化される
- `rde_record_id` が index rebuild 後に ArtifactVersion へ派生付与される
- RDE レポートに 6 項目（Preserved / Transformed / Supplemented / Unresolved / Deviation Risks / Next Update Policy）が出力される
- 検索が全カテゴリにわたって動作する
- エクスポートが正常に完了する
