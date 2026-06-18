# Chronicle Stack Interface Contracts

Related: [ADR-0001](adr/0001-context-assets-security.md), [ADR-0018](adr/0018-local-ui-read-only-navigation-boundary.md)

この文書は、Chronicle Stack のコード上のインターフェース契約を定義します。

Chronicle Stack は local-first な記録基盤であり、中心にある契約は `.chronicle/chronicle.jsonl` です。v0.x 系では実装が進化しますが、どの形式が安定契約で、どの形式が派生・表示・内部実装なのかを明確にします。

## 契約レベル

| 契約レベル | 意味 | 例 |
|---|---|---|
| Primary Stable | 強い互換性を維持する一次契約 | `.chronicle/chronicle.jsonl` |
| Public Stable-ish | v0.x中も互換性を重視する公開契約 | `chronicle.models.*`, CLI `--json` |
| Semi-public | 外部利用は可能だが変更余地がある | YAML export, selected service APIs |
| Human-facing | 人間向け表示。機械処理契約ではない | 通常CLI出力, Markdown export |
| Derived/Internal | 再構築可能・内部実装。互換性を保証しない | `.chronicle/indexes/*`, store internals |

## 1. JSONL Event Contract

`.chronicle/chronicle.jsonl` はChronicle Stackの一次記録です。

派生Index、検索結果、export、history表示は、原則としてJSONLから再構築可能でなければなりません。

### ChronicleEventの基本フィールド

Chronicle Eventは、少なくとも次の概念を持ちます。

| フィールド | 契約 |
|---|---|
| `event_id` | Eventの一意ID |
| `chronicle_id` | Chronicleの一意ID |
| `timestamp` | Event発生時刻。ISO 8601 JSON表現 |
| `event_type` | EventType文字列 |
| `actor` | Actor文字列 |
| `summary` | 人間向け要約 |
| `payload` | EventTypeごとの構造化payload |
| `parent_event_id` | 任意。親Event |
| `artifact_id` | 任意。関連Artifact |
| `context_ids` | 任意。関連Context ID一覧 |
| `decision_id` | 任意。関連Decision |
| `rde_record_id` | 任意。関連RDE record |
| `source` | 任意。SourceProvenance |
| `confidence` | 任意。confidence hint |
| `review_status` | 任意。review status |
| `tags` | 任意。tag一覧 |

### EventType-to-payload contract

EventTypeごとのpayloadは、次の形を標準契約とします。

| EventType | payload contract |
|---|---|
| `chronicle_created` | Chronicle作成情報 |
| `context_added` | `{ "context": Context }` |
| `user_input` | 任意の入力記録。ただしsummaryを主表示に使う |
| `assistant_output` | 任意の出力記録。ただしsummaryを主表示に使う |
| `artifact_created` | `{ "artifact": Artifact, "version": ArtifactVersion? }` |
| `artifact_updated` | `{ "artifact": Artifact, "version": ArtifactVersion? }` |
| `artifact_versioned` | `{ "artifact_id": str, "version": ArtifactVersion }` |
| `decision_recorded` | `{ "decision": Decision }` |
| `rde_diff_recorded` | `{ "rde": RdeDiffRecord }` |
| `boundary_rule_added` | `{ "boundary_rule": BoundaryRule }` |
| `note_added` | 任意のnote payload |
| `tag_updated` | tag変更payload |
| `metadata_updated` | metadata変更payload |

v0.3以降でInjectionPlanを記録する場合は、次を追加する方針です。

```json
{
  "event_type": "injection_plan_recorded",
  "payload": {
    "injection_plan": "InjectionPlan"
  }
}
```

### payload互換性

- 新しいEventTypeを追加しても、既存EventTypeのpayload意味を破壊してはなりません。
- 既存payloadに任意フィールドを追加することは可能です。
- 既存payloadの必須フィールドを削除、改名、意味変更する場合はbreaking changeです。
- `payload` は自由dictではなく、EventTypeに対応する構造化領域として扱います。

## 2. Model Serialization Contract

Chronicle StackのPydantic modelは、JSONL、CLI JSON、exportで利用されます。

### 共通方針

- enumは文字列値として保存します。
- datetimeはJSONシリアライズ可能なISO 8601形式として扱います。
- 旧データを読むための互換validatorは、v1.0までは原則維持します。
- unknown値は、欠損や未分類を表す後方互換値として維持します。
- `model_dump(mode="json")` 相当の出力を永続化・JSON出力の基準とします。

### Context

`Context.scope` は正式フィールドです。

`scope_hint` はv0.1互換用のdeprecated fieldです。v1.0までは読み取り互換を維持します。

互換方針:

- `scope` があり `scope_hint` がない場合、`scope` を使用します。
- `scope` がなく `scope_hint` がある場合、`scope_hint` から `scope` を補完します。
- どちらもない場合、`scope = unknown` とします。
- `visibility_hint` がない旧データは `unknown` とします。
- `source` がない旧データは `None` とします。
- `source_type` / `source_ref` は互換用として当面維持します。

### SourceProvenance

SourceProvenanceは「出所記録」であり、真実性や完全性の暗号学的証明ではありません。

互換方針:

- 欠損sourceは許容します。
- source系Boundary Ruleはsource欠損Contextに対しても例外を投げてはなりません。
- 新しいsource metadata fieldの追加は非破壊変更です。

### VisibilityHint

VisibilityHintは分類・警告のためのhintであり、redactionやaccess controlではありません。

- `public`, `private`, `sensitive`, `unknown` を文字列値として扱います。
- exportやCLI JSONは、visibility_hintを隠蔽しません。
- 将来redactionを導入する場合は、明示的な別オプションとして追加します。

## 3. Boundary Rule Evaluation Contract

Boundary Rulesは助言的な分類であり、access controlや強制的な保護機構ではありません。

### Rule types

| rule_type | 意味 |
|---|---|
| `include` | 選択理由を補強する |
| `warn` | 注意喚起を付ける |
| `exclude` | plan候補から除外する |

### Evaluation priority

Injection Plan生成時の優先順位は次の通りです。

```text
exclude > warn > include > default candidate
```

契約:

- `exclude` にmatchしたContextは `selected` に入れてはなりません。
- `warn` にmatchしたContextは `selected` と `warned` の両方に入ることがあります。
- `include` にmatchしたContextは `selected` に入り、reasonにrule情報を反映します。
- どのruleにもmatchしないContextはdefault candidateとして扱うことがあります。
- `enabled=false` のBoundaryRuleは評価しません。

### Fields and operators

| field | 対象 |
|---|---|
| `scope` | `Context.scope` |
| `visibility` | `Context.visibility_hint` |
| `source_type` | `Context.source.source_type` または互換source_type |
| `source_tool` | `Context.source.source_tool` |
| `source_session` | `Context.source.source_session` |
| `source_model` | `Context.source.source_model` |
| `tag` | `Context.tags` |

| operator | 意味 |
|---|---|
| `equals` | 対象値がvalueと等しい |
| `not_equals` | 対象値がvalueと等しくない |
| `in` | 対象値がvalue一覧に含まれる |
| `contains` | 対象collectionまたは文字列がvalueを含む |

sourceが存在しないContextにsource系ruleを評価しても、例外を投げてはなりません。

## 4. Injection Plan Contract

InjectionPlanは、LLMへ自動注入する仕組みではありません。人間が確認可能な文脈選択案です。

### Default behavior

- `chronicle injection plan` はデフォルトで非永続です。
- plan生成は `chronicle.jsonl` を変更しません。
- plan生成はContextを変更しません。
- plan生成はBoundaryRuleを変更しません。

### Plan sections

| section | 契約 |
|---|---|
| `selected` | 候補として選ばれたContext |
| `warned` | 注意が必要なContext。selectedと重複可能 |
| `excluded` | 除外されたContext。selectedに入ってはならない |
| `notes` | 人間向け注記。機械処理契約ではない |

### Ordering and duplication

- 同一section内でcontext_idは重複させません。
- `excluded` と `selected` は重複してはなりません。
- `warned` と `selected` は重複可能です。
- 可能な限り安定順序を維持します。

### Future persistence

v0.3以降で `--record` を導入する場合、明示的なオプションが指定された場合だけJSONLへ記録します。

デフォルト非永続の契約は維持します。

## 5. CLI Contract

CLIは公開インターフェースです。ただし、人間向け出力と機械向けJSON出力は分けて扱います。

| CLI出力 | 契約レベル |
|---|---|
| 通常のテキスト出力 | Human-facing。表現変更可能 |
| Markdown風表示 | Human-facing。表現変更可能 |
| `--json` 出力 | Public Stable-ish。互換性を重視 |
| exit code | Public Stable-ish |
| error message本文 | Human-facing |
| structured error JSONを導入した場合 | Public Stable-ish |

### CLI互換方針

- 既存command名はv1.0まで可能な限り維持します。
- enum値はmodelのenum値と一致させます。
- invalid enumは非zero exitにします。
- `--json` 出力に新しいフィールドを追加することは可能です。
- `--json` 出力の既存フィールド削除・改名・意味変更はbreaking changeです。

## 6. Export Contract

Exportは外部連携に使われる可能性があります。

| Export形式 | 契約レベル |
|---|---|
| YAML export | Semi-public。機械可読性を重視 |
| Markdown export | Human-facing。表示用 |
| future JSON export | Public Stable-ish候補 |
| future HTML dashboard export | Human-facing / static report |

### Export方針

- Exportは原則としてJSONLと派生Indexから再構成されるsnapshotです。
- YAML exportは、可能な限り安定したキー構造を維持します。
- Markdown exportは人間可読reportであり、機械処理契約ではありません。
- visibility_hintはredactionではないため、デフォルトでは隠蔽しません。
- 将来sensitive情報を除外する場合は、`--exclude-sensitive` などの明示オプションとして追加します。

## 6.1 Local Placeholder AI Index Contract

`ai-index` は local file-backed placeholder vector / graph surface です。

これは一次記録ではありません。`.chronicle/chronicle.jsonl` が引き続き正本です。

契約レベル:

| Surface | 契約レベル |
|---|---|
| `chronicle ai-index ... --json` | Public Stable-ish |
| `.chronicle/ai_indexes/*.json` | Derived/Internal |
| placeholder scoring implementation | Internal |

方針:

- placeholder AI index は local derived surface です。
- index 内容は削除・再生成・再投入されうる補助データです。
- `vector search` の結果順は、実装改善により変わる可能性があります。
- `embedding_provider=disabled`, `embedding_model=none`, `external_call_made=false` は境界の一部です。
- record ID と record type の意味を破壊する変更は避けます。
- `.chronicle/ai_indexes/*.json` のフォーマット自体は安定契約ではありません。

## 6.2 Local UI Read-only Endpoint Contract

`chronicle ui` が提供する `/api/*` endpoint は read-only derived view です。

契約レベル:

| Surface | 契約レベル |
|---|---|
| `/api/*` JSON payload | Public Stable-ish |
| browser shell HTML | Human-facing |

追加された endpoint:

- `/api/ai-index-status`
- `/api/ai-index-vector`
- `/api/ai-index-graph-nodes`
- `/api/ai-index-graph-edges`

方針:

- endpoint は local file 由来の派生 view です。
- endpoint は Chronicle 記録を書き換えてはなりません。
- endpoint は daemon / hosted runtime / GraphRAG runtime / vector DB / graph DB を含意してはなりません。
- detail endpoint の not found は失敗として扱われず、read-only inspection failure として扱います。

## 7. Python API Stability Policy

Python moduleはimport可能ですが、すべてを同じ安定度で扱うわけではありません。

| Module領域 | 契約レベル |
|---|---|
| `chronicle.models.*` | Public Stable-ish |
| `chronicle.services.*` | Semi-public / evolving |
| `chronicle.cli` | CLI実装。CLI契約を優先 |
| `chronicle.exporters.*` | Semi-public |
| `chronicle.store.*` | Internal |
| `chronicle.indexes.*` が存在する場合 | Internal / derived |
| `.chronicle/indexes/*` | Derived/Internal |

### 方針

- 外部利用者は、可能な限りCLIまたはJSONL/exportを利用してください。
- Python modelは外部ツールが参照する可能性があるため、互換性を重視します。
- store/index実装は内部詳細であり、breaking changeの対象になりえます。

## 8. Breaking Change Policy

v0.xでは破壊的変更の可能性があります。ただし、Chronicle Stackは再構成可能性を中核価値とするため、記録済みJSONLの読み取り互換を最優先します。

### Breaking changeに該当するもの

- 既存JSONL EventTypeの意味変更
- 既存payload必須フィールドの削除・改名
- 既存enum値の削除・意味変更
- `--json` 出力の既存フィールド削除・改名
- 既存Chronicleをrebuildできなくする変更

### 非breakingまたは軽微変更

- 新しいEventTypeの追加
- 新しい任意フィールドの追加
- 新しいCLIオプションの追加
- human-facing出力の文言変更
- derived index形式の変更。ただしrebuild可能であること

## 9. RDE Review for Interface Changes

インターフェース変更PRでは、可能な限り次を記録します。

- Preserved: 維持される契約
- Transformed: 変更される契約
- Added: 追加される契約
- Deprecated: 非推奨になる契約
- Breaking Risk: 既存JSONL、CLI JSON、export、Python APIへの影響

## 10. v0.3への適用

v0.3の各Issueは、この文書を参照します。

特に次の機能は、この契約に従って設計します。

- persisted Injection Plans
- GraphRAG integration boundary
- static dashboard export
- CLI UX and project metadata
- export format additions

## 関連Issue

- #32 v0.3: Define Interface Stability and Serialization Contracts
