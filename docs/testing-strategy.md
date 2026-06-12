# Testing Strategy

Chronicle Core v0.1 のテスト方針。

## 方針

- TDD を前提とし、CLI ユースケース単位でテストを記述
- 一時ディレクトリ（`tmp_path`）上で Chronicle を操作
- 一次記録（JSONL）の読み書きを中心に検証

## テスト構成（42 件）

### Service Tests

| テスト | ファイル | 件数 |
|--------|---------|------|
| Chronicle 初期化 | test_init.py | 2 |
| Event 追記 | test_event_recording.py | 2 |
| Artifact 作成・更新・履歴 | test_artifact.py | 10 |
| Decision 記録 | test_decision.py | 5 |
| RDE Diff Record 作成 | test_rde.py | 5 |
| 検索・Index 再生成・Export | test_search.py | 4 |

### CLI Integration Tests

| テスト | ファイル | 件数 |
|--------|---------|------|
| CLI 統合テスト | test_cli.py | 14 |

### 主要な回帰テスト

| テスト | 目的 |
|--------|------|
| `test_create_artifact_source_event_id_is_persisted` | `ArtifactVersion.source_event_id` が JSONL と rebuild 後も保持されることを確認 |
| `test_update_artifact_source_event_id_is_persisted` | 更新時も `source_event_id` が正しく永続化されることを確認 |
| `test_decision_event_id_is_persisted` | `Decision.event_id` が JSONL と rebuild 後も保持されることを確認 |
| `test_update_artifact_requires_content` | `--file` なしの更新が `ARTIFACT_CONTENT_MISSING` エラーになることを確認 |
| `test_update_artifact_missing_file_returns_chronicle_error` | 存在しないファイル指定が `SOURCE_FILE_NOT_FOUND` になることを確認 |
| `test_rde_record_links_to_target_version` | RDE → ArtifactVersion の派生リンクが rebuild 後に付与されることを確認 |
| `test_rde_record_is_searchable` | RDE レコードが検索可能であることを確認 |
| `test_rde_empty_sections_show_none` | 空の RDE セクションが `(none)` と表示されることを確認 |

## 実行

```bash
pip install -e ".[dev]"
pytest
ruff check src/ tests/
```

## CI

GitHub Actions (`.github/workflows/ci.yml`) で push / pull_request 時に以下を実行:

- `ruff check src/ tests/`
- `pytest -v`
