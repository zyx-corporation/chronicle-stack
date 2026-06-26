# Chronicle Stack v0.5 Roadmap

Status: Initial security-first planning draft  
Theme: Security-aware Composition and Integration Layer

## Theme

**Security-aware Composition and Integration Layer**

v0.4で整えたOperational Readiness Layerの上に、Chronicle recordsを安全に組み合わせ、外部ツールや将来のCSG-RAG / Sayane / Kotomi連携へ接続できる基盤を整える。

v0.5は、連携機能を増やす版ではない。連携しても文脈主権を壊さないための版である。

## Background

v0.4では以下を実装しました。

- `chronicle doctor`
- Export Manifest
- Redaction-aware export
- Dashboard navigation/filtering
- Graph export inspection

一方で、Chronicle Stack は単なる文書管理やRAG用文書ストアではありません。

Chronicle Stack は、問いの発端、判断過程、反論、保留、意味変化、失敗、未公開仮説、組織内の学習履歴を保存します。

したがって v0.5 では、CSG-RAG / Sayane / review package / export integration へ進む前に、以下の安全境界を整備します。

- classification metadata
- allowed operation model
- LLM injection policy
- prompt-injection sanitizer boundary
- export / inject / reinterpret auditability
- redact / seal / tombstone lifecycle
- integrity metadata preparation

## Guiding ADR

v0.5以降の設計は、次のADRを基準にします。

- [ADR-0001: Treat Chronicle Records as Context Assets](adr/0001-context-assets-security.md)

このADRにより、Chronicle Stack records は単なるinformation assetsではなくcontext assetsとして扱います。

## Candidate Scope

### 1. Security-aware Roadmap and Scope

v0.5のscopeをsecurity-firstに凍結する。

候補:

- roadmap改訂
- ADR整備
- security policy draftのrepo収録
- v0.5 planning issuesの作成

非目的:

- 実装着手
- runtime enforcement
- full access control

### 2. Classification Metadata Schema

Chronicle recordsにLayer 0〜4とLLM policyを持たせる。

候補:

```yaml
classification:
  layer: 0 | 1 | 2 | 3 | 4
  sensitivity: public | shareable | internal | sensitive | restricted
  owner: string
allowed_operations:
  - view
  - summarize
  - reinterpret
  - export
  - inject
  - publish
llm_policy:
  local_allowed: boolean
  external_allowed: boolean
  masking_required: boolean
retention:
  mode: keep | review | expire | seal
integrity:
  hash: string
  previous_hash: string
  signature: string
```

非目的:

- full enforcement
- cryptographic signing
- tenant isolation

### 3. Operation Permission Model

`read` と `inject` と `publish` を分離する。

候補operation:

```text
view
create
edit
append
redact
seal
export
inject
reinterpret
publish
```

非目的:

- authentication implementation
- complete RBAC / ABAC runtime
- cloud IAM integration

### 4. LLM Injection Policy and Dry-run Gateway

LLM投入前に、目的、対象Layer、外部/ローカルLLM、masking requirement、output classificationを確認できるdry-run gatewayを追加する。

候補:

```bash
chronicle inject check --target external-llm --purpose "draft public summary"
chronicle inject check --json
```

非目的:

- actual LLM API calls
- automatic injection
- cloud model runtime

### 5. Prompt Injection Sanitizer Boundary

保存されたChronicle recordsをLLMに読ませる場合、保存内容を命令ではなくデータとして扱う境界を定義する。

候補:

- sanitizer policy document
- prompt-injection marker detection
- export warning
- doctor security warning

非目的:

- perfect prompt-injection prevention
- model-level safety guarantee

### 6. Audit Log for Export / Inject / Reinterpret

export、inject、reinterpret はreadより高リスクの操作としてaudit対象にする。

候補:

```text
audit event:
  operation: export | inject | reinterpret
  actor
  purpose
  target_layer
  output_classification
  referenced_records
  created_at
```

非目的:

- immutable external audit service
- cryptographic notarization

### 7. Redact / Seal / Tombstone Lifecycle

Chronicle Stackは保存だけでなく忘却も設計する。

候補:

```bash
chronicle record redact --target ...
chronicle record seal --target ...
chronicle record tombstone --target ...
```

非目的:

- irreversible deletion as default
- storing deleted content inside audit logs

### 8. Integrity Metadata and Hash Chain Preparation

改ざん検知の基盤として、record hash、previous hash、snapshot metadataを準備する。

候補:

- schema design
- optional hash metadata
- doctor integrity warning

非目的:

- full signed snapshot implementation
- remote attestation

### 9. Doctor Security Checks

`chronicle doctor` にsecurity-oriented checksを追加する。

候補:

- unclassified records warning
- Layer 4 body-storage warning
- external LLM allowed without masking warning
- missing retention policy warning
- missing audit metadata warning

非目的:

- automatic repair
- destructive mutation

### 10. Security-aware Export Profiles

v0.4のredaction-aware exportをclassification metadataに接続する。

候補:

```bash
chronicle export --format yaml --profile public-review
chronicle export --format html --profile internal-review
```

非目的:

- access control
- complete leak prevention

### 11. Controlled CSG-RAG / Sayane Integration Contracts

CSG-RAG / Sayane連携は、classification、inject policy、audit logが整ってから進める。

候補:

- context package contract
- review package contract
- referenced-records manifest
- reinterpretation log contract

非目的:

- GraphRAG engine
- vector DB runtime
- external LLM runtime
- automatic review judgment

## Recommended Implementation Sequence

```text
1. Security roadmap + ADRs
2. Classification metadata schema
3. Operation permission model
4. LLM injection policy / dry-run gateway
5. Prompt injection sanitizer boundary
6. Audit log for export / inject / reinterpret
7. Redact / seal / tombstone lifecycle
8. Integrity metadata / hash chain preparation
9. Doctor security checks
10. Security-aware export profiles
11. Controlled CSG-RAG / Sayane integration contracts
```

## Candidate v0.5 Issues

```text
#60 v0.5: Security-aware Roadmap and ADRs
#61 v0.5: Add Classification Metadata Schema
#62 v0.5: Add Operation Permission Model
#63 v0.5: Add LLM Injection Policy and Dry-run Gateway
#64 v0.5: Define Prompt Injection Sanitizer Boundary
#65 v0.5: Add Audit Log for Export / Inject / Reinterpret
#66 v0.5: Add Redact / Seal / Tombstone Lifecycle Model
#67 v0.5: Add Integrity Metadata and Hash Chain Preparation
#68 v0.5: Extend Doctor with Security Checks
#69 v0.5: Add Security-aware Export Profiles
#70 v0.5: Prepare Controlled CSG-RAG / Sayane Integration Contracts
```

Issue numbers are placeholders until GitHub issues are created.

## Deferred from the earlier draft

The earlier v0.5 draft included these candidates:

- nested graph CLI
- export sidecar manifest
- redaction policy profiles
- validate / dry-run workflows
- CSG-RAG integration prep
- Sayane review package export

They are not discarded. They are reordered behind the security foundation.

## Non-goals

v0.5 planning should avoid scope creep into:

- GraphRAG engine
- embeddings
- vector database runtime
- graph database runtime
- external LLM API calls
- automatic LLM injection
- automatic semantic judgment
- full authentication system
- full tenant isolation
- cryptographic signing as enforcement
- commercial license template unless #26 is explicitly reopened

## RDE Review

### Preserved

- JSONL remains primary.
- Derived exports remain derived.
- Redaction is not access control.
- Export Manifest is not cryptographic proof.
- Graph inspection is not GraphRAG.
- v0.4 interface contracts remain in force.

### Transformed

- v0.5 changes from integration-first to security-aware integration.
- Chronicle records are treated as context assets.
- CSG-RAG / Sayane integration becomes gated by classification, injection policy, and auditability.

### Added

- Security-aware v0.5 planning frame.
- ADR dependency.
- Classification and LLM injection control as first-class roadmap items.
- Audit / lifecycle / integrity items.

### Unresolved

- GitHub issue numbers are not assigned yet.
- Exact metadata schema is not committed yet.
- Existing record migration strategy is not committed yet.
- Enforcement vs advisory boundary remains to be designed.

### Deviation Risks

- Do not implement external integration before injection policy exists.
- Do not treat classification metadata as enforcement by itself.
- Do not treat redaction-aware export as access control.
- Do not preserve all context without supporting redact / seal / delete workflows.
- Do not allow security planning to become a blocker for all incremental implementation.
