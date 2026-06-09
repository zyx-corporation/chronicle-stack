# Chronicle Stack v0.1 — Chronicle Core 基本仕様書

## 1. 文書情報

文書名：Chronicle Stack v0.1 — Chronicle Core 基本仕様書  
版：v0.1-draft  
対象範囲：Chronicle Stack Core Layer  
位置づけ：初期実装仕様  
想定読者：開発者、設計者、研究者、AI共同執筆・AI共同開発の運用者  
作成者：Tomoyuki Kano

## 2. 概要

Chronicle Stack は、人間とAIの共同思考において発生する文脈、入力、生成物、判断、修正、差分、意味変化を記録し、後から再構成・監査・再利用できるようにするための基盤である。

v0.1 — Chronicle Core は、その最小中核である。

v0.1では、GraphRAG、Dashboard、高度なRDE評価、外部AI連携、Sayane連携は本格実装しない。まず、すべての上位機能が依存する共通記録形式を定義し、ローカル環境でChronicleを作成・保存・検索・追跡・差分確認できる状態を目指す。

Chronicle Core の目的は、AIとのやり取りを単なる会話ログとして保存することではない。むしろ、ある成果物がどの文脈から生じ、どの指示によって変化し、どの判断によって採用・棄却・保留されたかを、時間軸に沿って追跡可能にすることである。

## 3. 背景と問題意識

AIとの共同作業では、成果物だけが残り、その生成過程、判断理由、採用されなかった案、修正指示、文脈の変化が失われやすい。

このとき、次の問題が発生する。

第一に、なぜその成果物になったのかを後から説明できない。  
第二に、過去の判断や棄却理由が再利用されない。  
第三に、AIが出力した内容と人間が採用した内容の境界が曖昧になる。  
第四に、改稿・要約・翻訳・仕様変更によって、元の意図がどのように保存または変質したかを検証しにくい。  
第五に、文脈が蓄積されても、それが人間の問いを支えるのではなく、AI側の応答最適化に吸収されやすい。

Chronicle Core は、これらの問題に対して、まず「記録可能性」と「再構成可能性」を提供する。

## 4. v0.1 の目的

v0.1 の目的は、Chronicle Stack の最小記録基盤を実装することである。

具体的には、以下を実現する。

会話、指示、生成物、判断、修正、差分を Chronicle Event として記録する。  
生成物を Artifact として識別し、その更新履歴を追跡する。  
人間の採用・棄却・保留・修正判断を Decision として記録する。  
生成物の更新に対して、簡易的なRDE Diff Recordを保存する。  
JSONLまたはYAMLによるローカル永続化を提供する。  
CLIから記録、一覧、検索、履歴表示、差分表示を実行できる。  
後続のContext Sovereignty Layer、RDE Integration、CSG-RAGに接続可能なデータ構造を定義する。

## 5. v0.1 の非目的

v0.1 では以下を目的としない。

高度なGraphRAGの実装。  
ベクトル検索基盤の本格導入。  
外部LLM APIとの密結合。  
リアルタイムDashboard。  
複数ユーザーの権限管理。  
クラウド同期。  
自動RDE評価の完全実装。  
AIエージェントの実行制御。  
Sayaneとの完全連携。  
企業向け監査ワークフロー。  
論文・Web・GitHub等の外部知識観測。

これらは v0.2 以降で扱う。

v0.1 は、すべての上位機能の下敷きとなる「記録の骨格」を作る段階である。

## 6. 基本概念

### 6.1 Chronicle

Chronicle は、特定のプロジェクト、対話、研究、文書、開発作業に関する時系列記録である。

Chronicle は単なるログではなく、文脈、入力、出力、判断、成果物、差分を関連づける構造化記録である。

### 6.2 Chronicle Event

Chronicle Event は、Chronicle Stack における最小記録単位である。

ユーザー入力、AI出力、文書生成、判断、修正、差分評価、メタ情報更新などはすべて Chronicle Event として記録される。

### 6.3 Context

Context は、生成物や判断の背景となった情報である。

v0.1では、Context は高度なスコープ制御を持たない。ただし、将来のContext Sovereignty Layerに接続できるよう、context_id、source、scope_hint、confidence を保持する。

### 6.4 Artifact

Artifact は、AIまたは人間との共同作業によって生成・更新される成果物である。

例として、仕様書、エッセイ、要約、翻訳、コード、設計メモ、レビュー結果、ロードマップ、プロンプト、設定ファイルなどがある。

### 6.5 Decision

Decision は、人間またはシステムが行った判断記録である。

例として、採用、棄却、修正、保留、置換、統合、公開可否判断、再検討判断などがある。

### 6.6 RDE Diff Record

RDE Diff Record は、ある生成物更新において、元の意図・価値・設計思想がどのように保存、変換、補完、逸脱したかを記録するための簡易評価である。

v0.1では完全なRDEエンジンは実装しない。評価項目を固定し、手動または半自動で記録できる形式を提供する。

## 7. 全体アーキテクチャ

v0.1 の構成は以下とする。

Chronicle CLI  
Chronicle Store  
Chronicle Event Model  
Artifact Model  
Decision Model  
RDE Diff Record Model  
Local Persistence Layer  
Basic Query Layer  
Basic Diff Layer

外部LLM、Graph DB、Dashboard、クラウドサービスには依存しない。

基本構成は local-first とし、ユーザーがローカルファイルとして Chronicle を保持できることを優先する。

## 8. データ保存方針

v0.1 の標準保存形式は JSONL とする。

理由は以下である。

追記型ログとして扱いやすい。  
Gitで差分管理しやすい。  
CLI処理が容易である。  
壊れた場合でも一部復旧しやすい。  
将来的にSQLiteやGraph DBへ移行しやすい。

補助形式として YAML Export を提供してもよい。

標準ファイル構成は以下とする。

```text
.chronicle/
  chronicle.jsonl
  artifacts/
    <artifact_id>/
      current.md
      versions/
        <version_id>.md
  indexes/
    artifact_index.json
    context_index.json
    decision_index.json
  reports/
    rde/
      <rde_record_id>.md
  metadata.yaml
```

v0.1では、`chronicle.jsonl` を真の一次記録とする。  
`indexes/` 以下は再生成可能な派生データとする。  
`artifacts/` 以下の成果物ファイルは人間が読める形式を優先する。

## 9. Chronicle Event Model

### 9.1 必須フィールド

Chronicle Event は以下の必須フィールドを持つ。

```json
{
  "event_id": "evt_...",
  "chronicle_id": "chr_...",
  "timestamp": "2026-06-09T12:00:00+09:00",
  "event_type": "user_input",
  "actor": "user",
  "summary": "Chronicle Coreの基本仕様書を作成する指示",
  "payload": {}
}
```

### 9.2 推奨フィールド

```json
{
  "parent_event_id": "evt_...",
  "artifact_id": "art_...",
  "context_ids": ["ctx_..."],
  "decision_id": "dec_...",
  "rde_record_id": "rde_...",
  "source": {
    "source_type": "conversation",
    "source_ref": "chat_session_..."
  },
  "confidence": "medium",
  "review_status": "unreviewed",
  "tags": ["spec", "chronicle-core"]
}
```

### 9.3 event_type

v0.1で扱う event_type は以下とする。

```text
chronicle_created
context_added
user_input
assistant_output
artifact_created
artifact_updated
artifact_versioned
decision_recorded
rde_diff_recorded
note_added
tag_updated
metadata_updated
```

各 event_type は、payload の構造を限定してよい。

### 9.4 actor

actor は以下を基本とする。

```text
user
assistant
system
tool
reviewer
importer
```

v0.1では詳細な権限管理は行わない。ただし、将来の監査に備え、誰が記録したかを必ず残す。

## 10. Context Object Model

v0.1 の Context は軽量モデルとする。

```json
{
  "context_id": "ctx_...",
  "title": "Chronicle Stack ロードマップ",
  "summary": "v0.1からv1.0までの開発方針",
  "source_type": "conversation",
  "source_ref": "chat_session_...",
  "scope_hint": "project",
  "confidence": "medium",
  "created_at": "2026-06-09T12:00:00+09:00",
  "tags": ["roadmap", "chronicle-stack"]
}
```

### 10.1 scope_hint

v0.1では正式なContext Scope制御は行わないが、将来互換のために scope_hint を持つ。

候補は以下とする。

```text
global
project
session
task
artifact
temporary
unknown
```

### 10.2 confidence

confidence は以下とする。

```text
high
medium
low
unknown
```

この値は事実の正確性を保証するものではない。あくまで、その文脈をどの程度信頼して扱うべきかのヒントである。

## 11. Artifact Object Model

Artifact は成果物を表す。

```json
{
  "artifact_id": "art_...",
  "chronicle_id": "chr_...",
  "title": "Chronicle Core 基本仕様書",
  "artifact_type": "specification",
  "current_version_id": "ver_...",
  "created_at": "2026-06-09T12:00:00+09:00",
  "updated_at": "2026-06-09T12:30:00+09:00",
  "status": "draft",
  "path": "artifacts/art_.../current.md",
  "tags": ["spec", "core"]
}
```

### 11.1 artifact_type

v0.1で想定する artifact_type は以下とする。

```text
document
specification
roadmap
essay
summary
translation
code
prompt
review
report
configuration
other
```

### 11.2 status

Artifact の status は以下とする。

```text
draft
reviewing
accepted
rejected
superseded
archived
unknown
```

v0.1ではワークフロー制御までは行わない。状態記録のみを提供する。

## 12. Artifact Version Model

Artifact の更新履歴は Version として記録する。

```json
{
  "version_id": "ver_...",
  "artifact_id": "art_...",
  "created_at": "2026-06-09T12:30:00+09:00",
  "created_by": "assistant",
  "source_event_id": "evt_...",
  "parent_version_id": "ver_...",
  "path": "artifacts/art_.../versions/ver_....md",
  "change_summary": "v0.1の基本仕様を追加",
  "rde_record_id": "rde_..."
}
```

current.md は常に最新状態を指す。  
versions/ 以下には各バージョンのスナップショットを保存する。

v0.1では差分保存ではなく、スナップショット保存を標準とする。理由は、復元性と実装容易性を優先するためである。

## 13. Decision Model

Decision は、生成物や方針に対する判断を記録する。

```json
{
  "decision_id": "dec_...",
  "chronicle_id": "chr_...",
  "artifact_id": "art_...",
  "event_id": "evt_...",
  "decision_type": "accepted",
  "decided_by": "user",
  "decided_at": "2026-06-09T12:40:00+09:00",
  "reason": "v0.1の範囲として妥当なため採用",
  "alternatives": [],
  "notes": "GraphRAGはv0.4以降に分離する"
}
```

### 13.1 decision_type

v0.1で扱う decision_type は以下とする。

```text
accepted
rejected
revised
deferred
superseded
merged
split
needs_review
```

### 13.2 判断記録の意義

Decision は単なる状態ではない。  
Chronicle Stack において Decision は、後から「なぜこの成果物になったのか」を再構成するための中核記録である。

採用された案だけでなく、棄却された案、保留された論点、再検討条件も記録対象とする。

## 14. RDE Diff Record Model

v0.1 の RDE Diff Record は、簡易的な意味変化監査である。

```json
{
  "rde_record_id": "rde_...",
  "artifact_id": "art_...",
  "from_version_id": "ver_...",
  "to_version_id": "ver_...",
  "created_at": "2026-06-09T12:45:00+09:00",
  "created_by": "assistant",
  "summary": "ロードマップのv0.1部分を基本仕様書へ変換",
  "preserved": [
    "Chronicle Coreを最小記録基盤とする方針",
    "GraphRAGやDashboardを後続に分離する方針"
  ],
  "transformed": [
    "ロードマップ上の項目を実装仕様へ変換"
  ],
  "supplemented": [
    "Event Model、Artifact Model、Decision Modelの詳細を追加"
  ],
  "unresolved": [
    "SQLite導入時期",
    "RDE自動評価の範囲"
  ],
  "deviation_risks": [
    "v0.1に機能を入れすぎるとCoreの実装が重くなる"
  ],
  "next_update_policy": [
    "v0.1ではJSONLとCLIを優先し、Graph構造はv0.4以降に分離する"
  ]
}
```

### 14.1 RDE評価項目

v0.1では以下の6項目を固定する。

保存された要素  
変換された要素  
補完された要素  
未解決の要素  
逸脱リスク  
次回更新方針

この6項目により、成果物を単なる品質評価ではなく、元の意図からの意味変化として扱う。

## 15. CLI 基本仕様

v0.1では CLI を主要インターフェースとする。

コマンド名は仮に `chronicle` とする。

### 15.1 chronicle init

新しい Chronicle を作成する。

```bash
chronicle init --title "Chronicle Stack Development"
```

生成物：

```text
.chronicle/
  chronicle.jsonl
  metadata.yaml
```

### 15.2 chronicle add-context

Context を追加する。

```bash
chronicle add-context \
  --title "Chronicle Stack Roadmap" \
  --source-type conversation \
  --scope project \
  --summary "v0.1からv1.0までの開発ロードマップ"
```

### 15.3 chronicle record

任意のイベントを記録する。

```bash
chronicle record \
  --type user_input \
  --actor user \
  --summary "Chronicle Coreの基本仕様書を作成"
```

### 15.4 chronicle artifact create

Artifact を作成する。

```bash
chronicle artifact create \
  --title "Chronicle Core Basic Specification" \
  --type specification \
  --file docs/chronicle-core-spec.md
```

### 15.5 chronicle artifact update

Artifact を更新し、新しい Version を作成する。

```bash
chronicle artifact update \
  --artifact art_123 \
  --file docs/chronicle-core-spec.md \
  --summary "Event ModelとDecision Modelを追加"
```

### 15.6 chronicle artifact history

Artifact の履歴を表示する。

```bash
chronicle artifact history --artifact art_123
```

出力例：

```text
Artifact: Chronicle Core Basic Specification

ver_001  2026-06-09 12:00  created
ver_002  2026-06-09 12:30  Event Model added
ver_003  2026-06-09 12:45  RDE Diff Record added
```

### 15.7 chronicle decision record

Decision を記録する。

```bash
chronicle decision record \
  --artifact art_123 \
  --type accepted \
  --reason "v0.1の基本仕様として採用"
```

### 15.8 chronicle rde record

RDE Diff Record を作成する。

```bash
chronicle rde record \
  --artifact art_123 \
  --from ver_001 \
  --to ver_002 \
  --summary "基本仕様の詳細化"
```

### 15.9 chronicle show

Chronicle の概要を表示する。

```bash
chronicle show
```

### 15.10 chronicle search

Chronicle Event を検索する。

```bash
chronicle search "Decision Model"
```

v0.1では全文検索または単純なキーワード検索でよい。

### 15.11 chronicle export

Chronicle をYAMLまたはMarkdownへエクスポートする。

```bash
chronicle export --format yaml
chronicle export --format markdown
```

## 16. 永続化仕様

### 16.1 chronicle.jsonl

すべての Chronicle Event は `chronicle.jsonl` に追記される。

1行1イベントとする。

例：

```json
{"event_id":"evt_001","chronicle_id":"chr_001","timestamp":"2026-06-09T12:00:00+09:00","event_type":"chronicle_created","actor":"user","summary":"Chronicle Stack Development created","payload":{"title":"Chronicle Stack Development"}}
{"event_id":"evt_002","chronicle_id":"chr_001","timestamp":"2026-06-09T12:10:00+09:00","event_type":"artifact_created","actor":"assistant","summary":"Chronicle Core specification created","artifact_id":"art_001","payload":{"title":"Chronicle Core Basic Specification"}}
```

### 16.2 metadata.yaml

Chronicle 全体のメタデータを保存する。

```yaml
chronicle_id: chr_001
title: Chronicle Stack Development
created_at: "2026-06-09T12:00:00+09:00"
version: "0.1"
schema_version: "chronicle-core-0.1"
default_timezone: "Asia/Tokyo"
```

### 16.3 Index Files

indexes/ 以下のファイルは、chronicle.jsonl から再生成可能な派生データとする。

v0.1では、破損時に index rebuild ができることを目標とする。

```bash
chronicle index rebuild
```

## 17. ID仕様

IDは可読性と衝突回避を両立するため、prefix + ULID または UUID を用いる。

推奨prefix：

```text
chr_  Chronicle
evt_  Event
ctx_  Context
art_  Artifact
ver_  Version
dec_  Decision
rde_  RDE Diff Record
src_  Source
```

例：

```text
chr_01JY...
evt_01JY...
art_01JY...
```

v0.1ではID生成方式を固定しすぎない。ただし、prefixによって型を判別できることを必須とする。

## 18. エラー処理方針

v0.1では、次のエラーを明示的に扱う。

Chronicle が初期化されていない。  
chronicle.jsonl が存在しない。  
JSONLの一部行が壊れている。  
指定された artifact_id が存在しない。  
指定された version_id が存在しない。  
Artifactファイルが存在しない。  
Decision の対象が存在しない。  
RDE Diff の from_version / to_version が存在しない。  
Index が古い、または破損している。

エラーは標準エラー出力に人間が読める形式で出力する。  
機械処理用に `--json` オプションを提供してもよい。

例：

```json
{
  "error": {
    "code": "ARTIFACT_NOT_FOUND",
    "message": "Artifact not found: art_123",
    "hint": "Run `chronicle artifact list` to see available artifacts."
  }
}
```

## 19. テスト方針

v0.1では以下のテストを必須とする。

Chronicle初期化テスト。  
Event追記テスト。  
壊れたJSONL行への耐性テスト。  
Artifact作成テスト。  
Artifact更新とVersion作成テスト。  
Decision記録テスト。  
RDE Diff Record作成テスト。  
Artifact履歴取得テスト。  
検索テスト。  
Index再生成テスト。  
Exportテスト。

テストはTDDを前提とし、最初にCLIユースケース単位のテストを書く。

## 20. 実装言語方針

初期実装は Python を推奨する。

理由は、データモデル、CLI、JSONL処理、Markdown出力、テストの実装速度が高いためである。

ただし、将来的に配布性、堅牢性、単一バイナリ化を重視する場合は Rust 実装へ移行または併存できる設計とする。

Python 実装の場合の候補：

CLI：Typer または Click  
データ検証：Pydantic  
テスト：pytest  
保存：JSONL、YAML  
差分：difflib  
ID生成：uuid または ulid-py

v0.1では外部依存を増やしすぎないことを優先する。

## 21. ディレクトリ構成案

```text
chronicle-stack/
  pyproject.toml
  README.md
  docs/
    chronicle-core-basic-spec.md
    data-model.md
    cli-reference.md
  src/
    chronicle/
      __init__.py
      cli.py
      models/
        event.py
        context.py
        artifact.py
        decision.py
        rde.py
      store/
        jsonl_store.py
        artifact_store.py
        index_store.py
      services/
        chronicle_service.py
        artifact_service.py
        decision_service.py
        rde_service.py
        search_service.py
      exporters/
        yaml_exporter.py
        markdown_exporter.py
      errors.py
      ids.py
  tests/
    test_init.py
    test_event_recording.py
    test_artifact.py
    test_decision.py
    test_rde.py
    test_search.py
```

## 22. セキュリティとプライバシー

v0.1では高度な暗号化やアクセス制御は実装しない。

ただし、以下の方針は仕様として明記する。

Chronicle は原則として local-first とする。  
ユーザーの明示操作なしに外部送信しない。  
Exportは明示コマンドによってのみ実行する。  
個人情報・秘匿情報を含む可能性があるため、公開前確認を前提とする。  
将来のために、ContextおよびArtifactに visibility_hint を追加可能な設計とする。

将来候補の visibility_hint：

```text
private
project
public_candidate
public
sensitive
unknown
```

v0.1では必須項目にはしないが、拡張余地を残す。

## 23. 互換性と拡張方針

Chronicle Core v0.1 のデータモデルは、以下の後続機能に接続できる必要がある。

v0.2 Context Sovereignty Layer  
v0.3 RDE Integration  
v0.4 CSG-RAG Prototype  
v0.5 Human Review Decision Model  
v0.6 Sayane Integration  
v0.7 Dashboard  
v0.8 Research Observatory

そのため、v0.1の設計では以下を重視する。

Event中心設計にする。  
すべての成果物をartifact_idで追跡する。  
すべての判断をdecision_idで追跡する。  
すべての文脈をcontext_idで参照可能にする。  
RDE評価を後付けではなく、Version更新に接続できるようにする。  
JSONLを一次記録とし、GraphやIndexは派生データとして扱う。

## 24. v0.1 完了条件

v0.1 は以下を満たした時点で完了とする。

`chronicle init` で新規Chronicleを作成できる。  
`chronicle record` で任意のEventを記録できる。  
`chronicle artifact create` でArtifactを作成できる。  
`chronicle artifact update` でVersionを追加できる。  
`chronicle artifact history` で履歴を表示できる。  
`chronicle decision record` で判断を記録できる。  
`chronicle rde record` で簡易RDE Diff Recordを作成できる。  
`chronicle search` でイベント・成果物・判断を検索できる。  
`chronicle export` でMarkdownまたはYAMLに出力できる。  
chronicle.jsonl を一次記録として再読み込みできる。  
Indexが壊れても rebuild できる。  
基本仕様書、データモデル仕様、CLI仕様、テストが揃っている。

## 25. v0.1 で作成すべきドキュメント

v0.1 では以下の文書を作成する。

Chronicle Core 基本仕様書  
Chronicle Event Model 仕様書  
Artifact Model 仕様書  
Decision Model 仕様書  
RDE Diff Record 仕様書  
CLI Reference  
Storage Format 仕様書  
Testing Strategy  
Roadmap Linkage Document

これらは docs/ 以下に配置する。

## 26. v0.1 の最小デモシナリオ

v0.1 のデモは、以下の流れで行う。

新しいChronicleを作成する。  
ユーザーが「Chronicle Coreの仕様書を作成する」という入力を記録する。  
AI出力として仕様書ドラフトをArtifactに保存する。  
ユーザーが一部修正を指示する。  
更新版を新しいVersionとして保存する。  
変更に対してRDE Diff Recordを作成する。  
ユーザーが「採用」と判断する。  
Decision Recordを作成する。  
最後にArtifact履歴とRDEレポートを表示する。

このデモにより、Chronicle Stack が「生成物」ではなく「生成物に至る文脈と判断」を扱う基盤であることを示す。

## 27. 設計上の重要判断

### 27.1 JSONLを一次記録とする

v0.1では複雑なDB設計よりも、追記可能で検証しやすいJSONLを優先する。

### 27.2 Graph構造は後続に分離する

GraphRAGはChronicle Stackの重要機能だが、v0.1では導入しない。  
v0.1では、Graph化可能なID参照構造を整えることに集中する。

### 27.3 RDEは簡易記録から始める

v0.1ではRDEを完全自動化しない。  
まず、意味変化を記録するための固定フォーマットを導入する。

### 27.4 Decisionを中核要素として扱う

AI生成物の履歴だけでは、なぜその成果物が採用されたのかは分からない。  
そのため、v0.1からDecision Modelを導入する。

### 27.5 Artifactはファイルとして読める形を保つ

成果物は人間が読めるMarkdown等で保存する。  
Chronicle Stack は記録基盤であると同時に、人間の再読可能性を重視する。

## 28. RDE差異検証

Chronicle Stack v0.1 は、前段のロードマップに対して以下の意味変化を持つ。

### 保存された要素

Chronicle Coreを最小記録基盤として扱う方針。  
Event、Artifact、Decision、RDE Diff Recordを中核に置く方針。  
GraphRAG、Dashboard、Sayane連携を後続段階へ分離する方針。  
local-first、監査可能性、再構成可能性を重視する方針。

### 変換された要素

ロードマップ上の抽象項目を、実装可能な基本仕様へ変換した。  
「Chronicleを作る」という構想を、JSONL、CLI、ID、ディレクトリ構成、テスト方針へ具体化した。  
RDEを思想的原理から、v0.1で扱える簡易データモデルへ変換した。

### 補完された要素

Chronicle Event Model の具体フィールドを追加した。  
Artifact Version Model を追加した。  
CLIコマンド仕様を追加した。  
保存ディレクトリ構成を追加した。  
エラー処理方針とテスト方針を追加した。  
最小デモシナリオを追加した。

### 未解決の要素

SQLite導入時期。  
Graph DB採用有無。  
RDE自動評価の実装範囲。  
外部LLM連携の境界。  
Dashboardとの責務分離。  
個人文脈とプロジェクト文脈の厳密な分離。  
暗号化とアクセス制御の実装時期。

### 逸脱リスク

v0.1に機能を入れすぎると、Chronicle Coreの実装が過度に複雑化する。  
RDEを早期に自動化しすぎると、評価の信頼性よりも見かけの完成度が先行する。  
GraphRAGを早期導入すると、記録基盤ではなく検索基盤として設計が歪む可能性がある。  
Decision Modelを軽視すると、単なるログ保存ツールに近づいてしまう。

### 次回更新方針

次回更新では、Chronicle Event Model、Artifact Model、Decision Model、RDE Diff Record Modelを個別仕様書として分離する。  
その後、CLI Reference と Storage Format 仕様を確定する。  
実装は `chronicle init`、`chronicle record`、`chronicle artifact create` から開始する。  
GraphRAG、Dashboard、Sayane連携はv0.1完了後に扱う。

## 29. 一文定義

Chronicle Core v0.1 は、AIとの共同思考における文脈・生成物・判断・差分を、後から再構成できる形で記録するための、Chronicle Stackの最小中核である。