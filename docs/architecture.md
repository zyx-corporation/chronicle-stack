# Chronicle Stack アーキテクチャ

この文書は、Chronicle Stack の構造とデータの流れを説明します。

## 設計目標

Chronicle Stack は、AIとの共同作業で発生する文脈、判断、成果物、差分、出所を後から辿れるようにする local-first な基盤です。

主な目標は次の通りです。

- `chronicle.jsonl` を一次記録とする
- 派生Indexを再構築可能にする
- Artifactの履歴を保存する
- Decisionを成果物と結びつける
- RDEで意味変化を構造化して記録する
- Contextのscope、visibility、source、boundaryを扱う

## 全体構造

```mermaid
flowchart TD
    U[利用者] --> CLI[Chronicle CLI]
    CLI --> S[Chronicle Services]
    S --> E[Chronicle Events]
    S --> C[Contexts]
    S --> A[Artifacts]
    S --> D[Decisions]
    S --> R[RDE Diff Records]
    S --> B[Boundary Rules]
    E --> J[(chronicle.jsonl 一次記録)]
    J --> IDX[(派生Index)]
    IDX --> Search[Search]
    IDX --> Export[Export]
    IDX --> History[Artifact History]
    IDX --> Check[Boundary Check]
    Check --> Plan[次段階: Context Injection Plan]
```

`chronicle.jsonl` が一次記録です。Indexは検索や表示のための派生データであり、再構築できます。

## レイヤ構造

```mermaid
flowchart TB
    subgraph Interface[インターフェース]
        CLI[Chronicle CLI]
        OUT[Markdown / YAML Export]
    end

    subgraph Services[サービス層]
        CHRON[ChronicleService]
        CONTEXT[ContextService]
        ARTIFACT[ArtifactService]
        DECISION[DecisionService]
        RDES[RdeService]
        BOUNDARY[BoundaryService]
        SEARCH[SearchService]
    end

    subgraph Models[モデル層]
        EVENT[ChronicleEvent]
        CTXM[Context]
        ARTM[Artifact / ArtifactVersion]
        DECM[Decision]
        RDEM[RdeDiffRecord]
        SRC[SourceProvenance]
        VIS[VisibilityHint]
        BRM[BoundaryRule]
    end

    subgraph Storage[保存層]
        JSONL[(chronicle.jsonl)]
        FILES[(artifact files)]
        REPORTS[(RDE reports)]
        INDEXES[(derived indexes)]
    end

    CLI --> Services
    Services --> Models
    Services --> Storage
    JSONL --> INDEXES
```

## ArtifactとRDEの流れ

```mermaid
sequenceDiagram
    participant User as 利用者
    participant CLI as Chronicle CLI
    participant Service as Chronicle Services
    participant JSONL as chronicle.jsonl
    participant Store as Artifact Store
    participant Index as Derived Index

    User->>CLI: chronicle artifact create
    CLI->>Service: Artifact と Version を作成
    Service->>Store: current.md と version snapshot を保存
    Service->>JSONL: artifact_created event を追記
    Service->>Index: Indexを再構築

    User->>CLI: chronicle rde record
    CLI->>Service: RDE Diff Record を作成
    Service->>JSONL: rde_diff_recorded event を追記
    Service->>Index: 対象Versionへ rde_record_id を派生リンク
```

## Context Sovereignty 層

v0.2では、Contextを単なるメモではなく、選択可能で確認可能な文脈単位として扱います。

構成要素は次の通りです。

- Context Scope: 文脈の有効範囲
- Visibility Hint: 可視性に関する軽量ヒント
- Source Provenance: 出所記録
- Boundary Rule: include / exclude / warn の判断材料

これらは、次段階の Context Injection Plan に接続されます。

## 今後の拡張

Chronicle Stack は、まず local-first な記録と再構成可能性を優先します。

GraphRAG、Dashboard、外部連携、より高度な文脈選択は将来の拡張対象です。
