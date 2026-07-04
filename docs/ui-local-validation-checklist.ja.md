# Chronicle Stack Local UI Validation Checklist

Status: Active  
Date: 2026-07-04  
Scope: `chronicle ui` の現行 local web UI を、ローカル運用前に短時間で確認するための実施チェック

## 1. Goal

このチェックリストは、現在の local UI が次の 5 点を満たしているかを確認するためのものです。

- 明色で可読な shell が崩れていない
- settings / locale / font scale が使える
- overview の first viewport で現状把握できる
- artifact / audit / boundary / trust / review / runtime / federation が読める
- read-only boundary と manual CLI parity が崩れていない

## 2. Fast Validation

最短確認は次の 3 コマンドです。

```bash
./.venv/bin/ruff check src/ tests/
./.venv/bin/pytest -q
chronicle ui-smoke
```

## 3. Manual Walkthrough

`chronicle ui` を起動し、`127.0.0.1:8765` を開いて次を確認します。

### Shell

- 右上に `表示言語`、`表示フォント`、`設定` が見える
- font scale `100 / 120 / 140 / 160 / 180 / 200%` を切り替えて shell が崩れない
- settings を開くと locale / font scale / appearance の要約が見える
- 現在地の nav が active 表示される

### Overview

- first viewport に hero summary が出る
- `Current questions`、`Pending proposals`、`Needs attention` の関係が一目で分かる
- `Review Queue`、`Runtime Records`、`Summary Jobs` へ即移動できる

### Artifact Workbench

- artifact detail に `Artifact Workbench` notice が出る
- `Detail / Provenance / Next Steps` の 3 セクションで読める
- linked context / decision / RDE / source event / audit へ飛べる

### Audit / Boundary / Trust

- audit route で governance summary が cards と counts で読める
- boundary / lifecycle route で rules / markers の件数が cards で読める
- trust route で node / relation / delegated actor / ai proxy relation が cards で読める

### Review / Runtime / Federation

- review queue summary で `Needs attention / Ready now / Advisory only / Package ready` が cards で読める
- runtime records summary で provider / trial / escalation が cards で読める
- summary jobs summary で provider / source refs / provider kinds が cards で読める
- federation inbox / outbox summary で preview-only / audited 状態が cards で読める

## 4. Boundary Checks

- warning banner が read-only local UI であることを維持している
- `chronicle ui` が write authority を暗示していない
- federation / runtime / review 導線が manual CLI parity を壊していない
- trust / boundary / audit 表示が advisory / derived / local inspection であることを保っている

## 5. Exit Criteria

次を満たせば、現行 UI はローカル運用前提の validation を通過したとみなしてよいです。

- automated validation が通る
- settings / locale / font scale が動く
- overview / artifact / review / runtime / federation の主要導線が読める
- read-only / advisory / local inspection boundary が崩れていない
