# Testing Strategy

Chronicle Core v0.1 のテスト方針。

## 方針

- TDD を前提とし、CLI ユースケース単位でテストを記述
- 一時ディレクトリ（`tmp_path`）上で Chronicle を操作
- 一次記録（JSONL）の読み書きを中心に検証

## 必須テスト（v0.1）

| テスト | ファイル |
|--------|---------|
| Chronicle 初期化 | test_init.py |
| Event 追記 | test_event_recording.py |
| 壊れた JSONL 行への耐性 | test_event_recording.py |
| Artifact 作成・更新・履歴 | test_artifact.py |
| Decision 記録 | test_decision.py |
| RDE Diff Record 作成 | test_rde.py |
| 検索 | test_search.py |
| Index 再生成 | test_search.py |
| Export | test_search.py |
| CLI 統合テスト | test_cli.py |

## 実行

```bash
pip install -e ".[dev]"
pytest
```

## 今後

- 最小デモシナリオの E2E テスト
