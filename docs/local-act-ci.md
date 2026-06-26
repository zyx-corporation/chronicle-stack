# Local act CI

Chronicle Stack は、hosted GitHub Actions をCIの実行基盤として使わず、ローカル環境の `act` でCI相当の検証を実行します。

## 目的

この方針の目的は、CIの実行権限をGitHub hosted runnerから切り離し、開発者が明示的にローカルで検証できるようにすることです。

CIは引き続き、lint、test、UI smoke を確認する品質ゲートです。ただし、その実行場所はGitHub Actionsではなく、開発者のローカル `act` 環境です。

## 実行方法

事前に `act` と Docker 互換ランタイムを用意してください。

```bash
bash scripts/act-ci.sh
```

追加の `act` 引数を渡す場合は、そのまま script の後ろに指定します。

```bash
bash scripts/act-ci.sh --verbose
```

## Workflow location

ローカルCI用のworkflowは、次に置きます。

```text
.act/workflows/ci.yml
```

このファイルは `.github/workflows/` 配下ではないため、GitHub hosted Actions の push / pull_request trigger として実行されません。

## 検証内容

ローカル act CI は、次を実行します。

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
ruff check src/ tests/
pytest -v
chronicle ui-smoke --root "$ROOT"
chronicle ui-smoke --root "$ROOT" --json
```

UI smoke は、isolated temporary root を作成して実行します。通常の Chronicle root は変更しません。

## 非目的

この仕組みは、次を目的としません。

- GitHub hosted Actions の代替ホスティング。
- hosted CI provider の追加。
- GitHub branch protection の自動満足。
- CIの完全な強制。
- 外部サービス上での自動実行。

## 運用上の注意

`act` は GitHub Actions workflow syntax をローカルで実行するためのツールです。ただし、GitHub hosted runner と完全に同一の環境ではありません。ローカルDockerイメージ、CPU architecture、mount、network、cache の違いにより、差異が出る可能性があります。

このため、失敗時には次を確認してください。

- Docker または互換ランタイムが起動しているか。
- `act` がインストールされているか。
- Python 3.11 setup が workflow 内で成功しているか。
- Apple Silicon 環境では `--container-architecture linux/amd64` が必要か。

`scripts/act-ci.sh` は、既定で `--container-architecture linux/amd64` を指定します。

## RDE review

### Preserved

- lint、test、UI smoke をCI相当の品質ゲートとして維持する。
- UI smoke は read-only / no browser / no external runtime の前提を維持する。

### Transformed

- CI実行権限を GitHub hosted Actions からローカル act 実行へ移す。

### Added

- `.act/workflows/ci.yml`
- `scripts/act-ci.sh`
- local act CI documentation

### Deviation risks

- hosted CIを廃止することで、PR上の自動チェックが表示されなくなる。
- local act の環境差異により、GitHub hosted runner と完全一致しない可能性がある。
- ローカル実行を忘れると品質ゲートが弱くなる。

### Next update policy

必要に応じて、PRテンプレートまたはrelease readiness文書に `bash scripts/act-ci.sh` 実行結果の記録欄を追加する。
