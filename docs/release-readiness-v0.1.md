# Release Readiness — Chronicle Core v0.1

## 目的

Chronicle Core v0.1 を正式な初期リリース候補として凍結できるかを評価する。

## 対象範囲

- Chronicle Event による JSONL 一次記録
- Artifact の作成・更新・バージョン履歴
- Decision（採用・棄却・保留など）の記録
- RDE Diff Record による簡易意味変化監査
- CLI による操作
- YAML / Markdown エクスポート
- Local act CI

## 非目的（v0.1 スコープ外）

- GraphRAG
- Dashboard
- 外部 LLM API 連携
- Sayane 連携
- SQLite / DB 移行
- 複数ユーザー権限管理
- クラウド同期
- RDE 自動評価
- Context Scope / Boundary Rule

## 実装済み機能一覧

| 機能 | 状態 |
|------|------|
| `chronicle init` | ✅ |
| `chronicle record` | ✅ |
| `chronicle add-context` | ✅ |
| `chronicle artifact create` | ✅ |
| `chronicle artifact update` | ✅ |
| `chronicle artifact history` | ✅ |
| `chronicle artifact list` | ✅ |
| `chronicle decision record` | ✅ |
| `chronicle rde record` (6 フィールド) | ✅ |
| `chronicle search` | ✅ |
| `chronicle show` | ✅ |
| `chronicle export --format yaml` | ✅ |
| `chronicle export --format markdown` | ✅ |
| `chronicle index rebuild` | ✅ |
| `ArtifactVersion.source_event_id` 永続化 | ✅ |
| `Decision.event_id` 永続化 | ✅ |
| `RDE → ArtifactVersion` 派生リンク | ✅ |
| Artifact 空更新ガード | ✅ |
| CLI 統合テスト | ✅ |
| Local act CI | ✅ |

## CLI 確認結果

CLI スモークテストを実施し、以下を確認済み:

- `chronicle init` 〜 `chronicle show` までの全主要コマンドが正常動作
- `artifact history --json` で `source_event_id` が正しく永続化
- `index rebuild` 後に `rde_record_id` が ArtifactVersion へ派生付与
- RDE レポートに 6 項目が出力
- 検索が全カテゴリ（event, artifact, decision, rde）で動作
- エクスポート（YAML / Markdown）が正常完了
- `--file` なしの `artifact update` がエラーになることを確認

詳細: [docs/smoke-test-v0.1.md](smoke-test-v0.1.md)

## テスト結果

```
42 passed
ruff: All checks passed
```

## CI 設定

Hosted GitHub Actions は使用しない。CI相当の検証は、ローカル環境の `act` で明示的に実行する。

```bash
scripts/act-ci.sh
```

Local act CI の workflow は `.act/workflows/ci.yml` に置く。`.github/workflows/` 配下には置かないため、GitHub hosted Actions の push / pull_request trigger としては実行されない。

Local act CI の詳細は [Local act CI](local-act-ci.md) を参照する。

## 既知の制約

- GraphRAG は未実装
- Dashboard は未実装
- RDE は自動評価ではなく、構造化された差分記録である
- JSONL は一次記録だが、暗号化や権限管理は未実装
- 同一 Version への複数 RDE は、v0.1 では JSONL 上で最後に現れた RDE が派生 Index 上で優先される
- 外部 LLM 連携は未実装
- `chronicle.jsonl` の schema versioning / migration は未実装
- Local act CI は明示的なローカル実行であり、PR上のhosted checkを自動作成しない

## v0.2 へ送る課題

| 課題 | 優先度 |
|------|--------|
| Context Scope Model の正式化 | High |
| Context Boundary Rule の導入 | High |
| visibility_hint の追加 | Medium |
| Source Provenance Metadata の強化 | Medium |
| Context Injection Plan の生成 | Medium |
| RDE index / search の強化 | Low |
| JSONL schema_version と migration 方針 | Low |
| artifact content source validation 強化 | Low |
| export filtering | Low |
| public/private/sensitive context labels | Low |

詳細: [docs/backlog-v0.2.md](backlog-v0.2.md)

## RDE 差異検証

### 保存された要素
- v0.1 を local-first な記録基盤として扱う方針
- GraphRAG / Dashboard を後続に分離する方針
- README と基本仕様書にその方針を明記

### 変換された要素
- 仕様上の抽象モデルを Python 実装へ変換
- Typer CLI、Pydantic モデル、JSONL Store、IndexStore、ArtifactStore として実装
- CIの実行主体を hosted GitHub Actions から local act へ移行

### 補完された要素
- `artifact list` や `index rebuild` など、基本仕様に対して実用上便利な CLI を追加
- Local act CI workflow と実行scriptを追加

### 未解決の要素
- Context Scope / Boundary Rule の未実装
- JSONL schema migration 方針の未定義
- local act 実行結果のPRテンプレート記録欄

### 逸脱リスク
- 現状のまま機能追加を優先すると、一次記録内の参照整合性が後回しになるリスク → v0.1 で修正済み
- hosted CI廃止により、ローカル実行を忘れると品質ゲートが弱くなるリスク

### 次回更新方針
- v0.1 は機能追加より先に、Event・Version・Decision・RDE の参照整合性を固める → 達成
- local act CI の実行結果を release readiness / PR body に残す運用を検討する

## リリース判定

v0.1.0 としての初期リリースは **可能** と判断する。

条件:
1. この PR が main にマージされること
2. Local act CI が pass すること
3. v0.1.0 tag を作成すること
