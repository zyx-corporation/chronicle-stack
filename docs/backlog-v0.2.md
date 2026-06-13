# Backlog — v0.2 Candidates

Chronicle Core v0.2 の候補課題。Issue 化しやすい粒度で記述。

## 1. Context Scope Model の正式化（ → 実装中 #10）

**目的**: Context に明示的な Scope と Boundary を持たせ、注入計画を生成可能にする。

**概要**: 現在の `ScopeHint` を正式な Scope Model に拡張し、Context がどの範囲（Task / Project / Session / Global）で有効かを厳密に定義する。

**受け入れ条件**:
- `Context.scope` が境界条件を持つ
- 境界を越えた Context の使用を検出できる
- CLI で scope 指定が必須になる

## 2. Context Boundary Rule の導入

**目的**: Context の有効範囲を制御し、関係ない Context が注入されないようにする。

**概要**: Context 間に boundary rule（包含、排他、順序）を定義し、注入時に違反を検出する。

**受け入れ条件**:
- Boundary rule のデータモデルが定義されている
- 注入時に boundary check が実行される
- 違反時に警告が出力される

## 3. visibility_hint の追加

**目的**: Context や Artifact の可視性を制御する。

**概要**: `public` / `private` / `sensitive` の visibility hint を追加し、エクスポートや注入時に参照する。

**受け入れ条件**:
- Context と Artifact に `visibility_hint` フィールドが追加される
- エクスポート時に visibility でフィルタリング可能
- 注入時に sensitive Context が警告付きで扱われる

## 4. Source Provenance Metadata の強化

**目的**: 各イベントや Artifact の出所をより詳細に追跡可能にする。

**概要**: `source_ref` に加えて、source tool / source session / source model などのメタデータを追加する。

**受け入れ条件**:
- `SourceRef` モデルが拡張される
- CLI で source metadata が指定可能
- 検索で source によるフィルタリングが可能

## 5. Context Injection Plan の生成

**目的**: 与えられたタスクに対して、どの Context を注入すべきかの計画を生成する。

**概要**: Scope / Boundary / visibility をもとに、タスクに関連する Context の注入計画を自動生成する。LLM に依存しないルールベースの初期実装。

**受け入れ条件**:
- タスク記述に対して関連 Context を選択できる
- 注入計画が Markdown または JSON で出力される
- 境界違反があれば警告が含まれる

## 6. RDE index / search の強化

**目的**: RDE レコードの一覧・検索・フィルタリングを改善する。

**概要**: `chronicle rde list` コマンドの追加、RDE レコードの検索精度向上、Artifact 履歴表示での RDE リンク表示。

**受け入れ条件**:
- `chronicle rde list` が実装されている
- Artifact 履歴に RDE リンクが表示される
- RDE レコードの検索がフィールド別に可能

## 7. JSONL schema_version と migration 方針

**目的**: 将来のスキーマ変更に備え、migration 方針を確立する。

**概要**: `chronicle.jsonl` の schema_version を管理し、バージョン間の migration ルールを定義する。

**受け入れ条件**:
- `chronicle.jsonl` の先頭またはメタデータに schema_version が記録される
- 異なる schema_version の読み取り時に警告が出力される
- 基本的な migration スクリプトが提供される

## 8. artifact content source validation 強化

**目的**: Artifact 作成・更新時の入力バリデーションを強化する。

**概要**: ファイルサイズ制限、エンコーディング検出、空ファイルの拒否などを追加する。

**受け入れ条件**:
- ファイルサイズ上限を設定可能
- エンコーディング自動検出
- 空ファイルは明示的なエラーになる

## 9. export filtering

**目的**: エクスポート時に Artifact タイプや日付範囲でフィルタリング可能にする。

**概要**: `chronicle export` に `--type` / `--since` / `--until` オプションを追加する。

**受け入れ条件**:
- artifact type でフィルタリング可能
- 日付範囲でフィルタリング可能
- 複数フィルタの組み合わせが可能

## 10. public/private/sensitive context labels

**目的**: 機密性に応じた Context の取り扱いを可能にする。

**概要**: visibility_hint と連動し、sensitive ラベルの Context はエクスポート時や注入時に特別な扱いを受ける。

**受け入れ条件**:
- Context に visibility label が設定可能
- エクスポート時に label によるフィルタが可能
- sensitive Context の検索結果に警告マークが付く
