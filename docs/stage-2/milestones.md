# Chronicle Stack Stage 2 マイルストーン

Status: Draft  
Author: Tomoyuki Kano  
Specification: `docs/stage-2/basic-specification.md`  
Roadmap: `docs/stage-2/roadmap.md`

## 1. マイルストーン運用

Stage 2のマイルストーンは、暦上の期日ではなく、依存関係と退出条件によって管理する。

各マイルストーンは次を持つ。

- Goal: 到達すべき能力
- In scope: 実装対象
- Out of scope: 混入させない対象
- Required artifacts: 文書、ADR、code、test、runbook
- Acceptance criteria: 完了判定
- Failure gates: 完了を拒否する条件
- Rights gate: 外部コード・依存・AI支援実装の権利確認
- RDE checkpoint: 元設計からの意味変化監査

GitHub上のMilestoneを作成する場合、次のtitleを推奨する。

```text
Stage 2.0 — Rights and Architecture Baseline
Stage 2.1 — Runtime Backend Separation
Stage 2.2 — Runtime Event and Recording Boundary
Stage 2.3 — Static Capability Registry
Stage 2.4 — Scoped Capability Runtime
Stage 2.5 — Operation Plan and Proposal Integration
Stage 2.6 — Proposal Surface Protocol
Stage 2.7 — Transport Boundary Skeleton
Stage 2.8 — Operational Hardening and Exit Audit
```

## 2. 全体サマリー

| ID | Milestone | 主成果 | 依存 |
|---|---|---|---|
| M2.0 | Rights and Architecture Baseline | 仕様、ADR、出所・権利管理 | 既存Core / Boundary |
| M2.1 | Runtime Backend Separation | Backend Port、Orchestrator、Fake Backend | M2.0 |
| M2.2 | Runtime Event and Recording Boundary | Event分類、Recording Service | M2.1 |
| M2.3 | Static Capability Registry | Manifest、Registry、doctor | M2.2 |
| M2.4 | Scoped Capability Runtime | 最小権限Port、Proposal Writer | M2.3 |
| M2.5 | Operation Plan and Proposal Integration | Plan DSL、Preview、Review、Apply | M2.4 |
| M2.6 | Proposal Surface Protocol | GUI Review契約、CLI parity | M2.5 |
| M2.7 | Transport Boundary Skeleton | Envelope、Mock Transport、昇格経路 | M2.4 |
| M2.8 | Operational Hardening and Exit Audit | 診断、回帰、Runbook、RDE | M2.6 / M2.7 |

## 3. M2.0 — Rights and Architecture Baseline

### Goal

Stage 2の意味、境界、実装順序、著作権・ライセンス処理を、コード変更より先に固定する。

### In scope

- Stage 2基本仕様
- Stage 2ロードマップ
- Stage 2マイルストーン
- Runtime Backend Port ADR
- Capability Registry ADR
- Operation Plan ADR
- Proposal Surface ADR
- Upstream study記録
- Adoption Ledger
- Third-party Notice運用
- PR rights classification

### Out of scope

- Runtime codeの実装
- MulmoClaudeコードの直接移植
- 動的Plugin loader
- 外部Transport実装

### Required artifacts

```text
docs/stage-2/basic-specification.md
docs/stage-2/roadmap.md
docs/stage-2/milestones.md
docs/provenance/upstream-study-mulmoclaude.md
docs/provenance/upstream-adoption-ledger.yaml
THIRD_PARTY_NOTICES.md
```

### Acceptance criteria

- Stage 2が既存Overall Roadmapとの関係を説明している。
- `.chronicle/chronicle.jsonl`の一次記録性が不変条件として明記されている。
- 外部能力はAdapterであり正本ではないと定義されている。
- `conceptual_reimplementation`が既定採用方式である。
- 直接ソース利用時のMIT notice保持方針がある。
- AGPL公開版への利用と商用版への利用権が区別されている。
- 主要ADRのissueまたはdraftが準備されている。

### Failure gates

- 参照元repository、commit、licenseが欠落している。
- 外部文書の表現を大量に転記している。
- 上流著作権をZYX単独著作権として扱っている。
- Stage 2がAI万能ホスト化を目的としている。

### Rights gate

- MulmoClaude参照箇所をAdoption Ledgerへ記録する。
- copied sourceの有無を明記する。
- direct reuseは個別承認まで禁止する。

### RDE checkpoint

- Chronicleの正本・Review・Boundaryが保存されているか。
- MulmoClaudeの製品思想をChronicleの思想へ無批判に移植していないか。

## 4. M2.1 — Runtime Backend Separation

### Goal

Provider固有実行をBackend Adapterへ閉じ込め、ChronicleのOrchestratorをProvider非依存にする。

### In scope

- RuntimeBackend Protocol
- RuntimeRequest
- BackendCapabilities
- Runtime共通Error
- Disabled Backend
- Fake Backend
- Runtime Orchestrator
- cancellation / timeout / cleanup
- Compatibility Facade

### Out of scope

- Capability Registry
- Operation Plan
- GUI Surface
- Tool marketplace

### Required artifacts

- Runtime Backend ADR
- Runtime contract models
- Fake Backend test fixture
- Orchestrator unit tests
- Local / HTTP migration note
- compatibility test matrix

### Acceptance criteria

- Orchestratorが具体Provider classをimportしない。
- Fake Backendだけで正常、失敗、取消、timeoutをテストできる。
- Disabled Backendが既定である。
- 少なくとも一つの既存Runtime経路がAdapterへ移行している。
- 旧CLI経路の主要出力・exit codeが維持される。
- 実行後に一時file、process、connectionが残らない。

### Failure gates

- BackendがArtifactServiceまたはJsonlStoreへ直接書く。
- Provider固有responseが公開Service contractへ漏れる。
- runtime config変更でin-flight requestのBackendが差し替わる。
- cleanup失敗が元のfailureを上書きする。

### Rights gate

- Backend interfaceを外部コードからコピーしていないことを確認する。
- 外部SDKを追加する場合はlicenseとnoticeを確認する。

### RDE checkpoint

- RuntimeService分解によって既存のexplicit executionが弱まっていないか。
- Backend抽象化がChronicle provenanceを削っていないか。

## 5. M2.2 — Runtime Event and Recording Boundary

### Goal

一時的な実行streamと、Chronicleへ残す意味的記録を分離する。

### In scope

- RuntimeEvent model
- Event classification
- Runtime Recording Service
- Record Policy
- SourceProvenance mapping
- failure / cancellation recording
- secret exclusion

### Out of scope

- 全token保存
- distributed tracing platform
- remote telemetry backend

### Required artifacts

- Runtime Event ADR
- event classification table
- recording policy
- retention note
- negative tests for secrets
- record=false regression tests

### Acceptance criteria

- token deltaが既定でChronicleへ保存されない。
- final result、provider、model、source refs、review statusを記録できる。
- record=falseで一次記録を変更しない。
- failed、cancelled、timeoutが成功と区別される。
- raw token、credential、secret headerが保存されない。

### Failure gates

- Runtime TraceがChronicle Eventを代替する。
- Operational Logだけが最終結果の唯一の出所になる。
- failure途中の部分出力が確定Artifactになる。

### Rights gate

- 外部SDK event名を安定したChronicle契約としてそのまま公開しない。
- Provider固有型を保存schemaへ固定しない。

### RDE checkpoint

- 記録量の増加が再構成可能性を高めず、ノイズだけを増やしていないか。
- 「観測されたこと」と「正しいこと」を混同していないか。

## 6. M2.3 — Static Capability Registry

### Goal

実行能力をManifest付きの静的Registryへ集約し、未宣言能力の実行を防ぐ。

### In scope

- CapabilityManifest
- Static Registry
- capability ID policy
- schema version
- duplicate / unknown / disabled diagnostics
- capability list / show CLI
- doctor integration

### Out of scope

- package auto-discovery
- third-party runtime installation
- remote capability catalog
- marketplace

### Required artifacts

- Capability Registry ADR
- Manifest schema
- naming convention
- initial capability list
- collision tests
- doctor checks

### Acceptance criteria

- Stage 2能力がRegistry経由で解決される。
- duplicate IDはstartupまたはexecution前に拒否される。
- unknown / disabled能力はfail closedとなる。
- capability list / showが外部通信なしで利用できる。
- Registryは派生面であり再生成可能である。

### Failure gates

- first-write-winsでcollisionを黙認する。
- Manifestなしのlegacy pathが永続的に残る。
- Provider名をCapability IDとして使う。
- Registryを一次記録へ格上げする。

### Rights gate

- 上流Plugin Manifestのschemaを直接コピーしていないことを確認する。
- capability名称に第三者商標を不要に含めない。

### RDE checkpoint

- 拡張性のために安全境界を弱めていないか。
- RegistryがProviderロックインを強めていないか。

## 7. M2.4 — Scoped Capability Runtime

### Goal

Capabilityが必要最小限のContext、Proposal、Artifact、Networkだけへアクセスできる構造を作る。

### In scope

- Scoped Context Reader
- Proposal Writer
- Scoped Artifact Access
- Policy-bound Network Client
- Audit Emitter
- capability execution context factory
- negative permission tests

### Out of scope

- 完全なOS Sandbox
- multi-tenant IAM
- arbitrary code execution
- dynamic third-party adapter

### Required artifacts

- Scoped Runtime ADR
- Port interfaces
- access matrix
- deny-by-default tests
- network policy tests
- audit failure tests

### Acceptance criteria

- Capabilityへroot pathまたはraw Storeを渡さない。
- selected Context以外を取得できない。
- mutation capabilityはProposal Writerのみを利用する。
- network destinationとoperationをpolicyで限定できる。
- Audit失敗時にMutation成功とならない。

### Failure gates

- CapabilityがService locatorから任意Serviceを取得できる。
- ID推測で非選択Contextへアクセスできる。
- network clientが任意URLを許可する。
- CapabilityがDecisionなしに確定状態を変更する。

### Rights gate

- scoped runtime実装が上流factory codeの翻案コピーになっていないか確認する。
- direct source reuseの場合はfile単位noticeを追加する。

### RDE checkpoint

- 最小権限が単なるAPI上の慣習でなく構造的に強制されているか。
- 実装上の便宜が権限拡大の理論的正当化に変わっていないか。

## 8. M2.5 — Operation Plan and Proposal Integration

### Goal

AIまたはToolの提案を、検証可能なOperation PlanとしてPreviewし、Review後に既存Proposal / Apply経路へ接続する。

### In scope

- OperationPlan model
- schema version
- validator
- assumptions / constraints / source refs
- preview CLI
- plan-to-proposal conversion
- stale target protection
- duplicate apply protection
- RDE requirement

### Out of scope

- 無制限multi-agent planning
- autonomous long-running workflow
- background task scheduler
- automatic approval

### Required artifacts

- Operation Plan ADR
- Plan schema
- validator tests
- preview examples
- plan-to-proposal integration tests
- stale / duplicate / partial failure tests

### Acceptance criteria

- plan generationとexecutionが分離されている。
- source refs、target refs、assumptionsが検査可能である。
- Previewが既定である。
- Reviewなしにapplyできない。
- stale targetとduplicate applyを拒否する。
- Apply後のDecision、Audit、Event、RDEを再構成できる。

### Failure gates

- Plan生成時にMutationする。
- AI補完値がassumptionではなくfactとして扱われる。
- partial applyを成功扱いする。
- plan schemaを変更してもversionが変わらない。

### Rights gate

- DSL文法が外部プロジェクトの固有schemaを複製していないか確認する。
- example文書の転用を避ける。

### RDE checkpoint

- Planによって元要求より強い主張・操作へ変換されていないか。
- 未検証内容が確定済みに見える表現になっていないか。

## 9. M2.6 — Proposal Surface Protocol

### Goal

local UIが任意Plugin codeを実行せず、ProposalのReviewに必要なread modelと許可操作を共通契約で扱えるようにする。

### In scope

- ProposalSurface JSON contract
- surface versioning
- read-only renderers
- allowed actions
- mutation session continuity
- CLI parity
- apply integration

### Out of scope

- arbitrary HTML / JavaScript execution
- remote GUI plugin installation
- public web hosting
- live collaborative editing

### Required artifacts

- Proposal Surface ADR
- JSON schema
- CLI parity matrix
- read-only UI renderer
- mutation integration tests
- CSRF / duplicate / stale tests

### Acceptance criteria

- Artifact ProposalをSurface経由でReviewできる。
- UIはStoreへ直接書かない。
- allowed actions外のoperationを拒否する。
- PreviewとApplyでproposal identityが連続する。
- CLIとUIが同じCommand Layerを利用する。
- DecisionとAuditの両方が成功した場合だけApply成功となる。

### Failure gates

- Surface payloadに実行可能scriptを含める。
- UIだけが強い権限を持つ。
- renderer実装がstable contractになる。
- mutation tokenとproposal IDの関係が検証されない。

### Rights gate

- `gui-chat-protocol`等の外部protocol codeを直接利用する場合は別途採用審査する。
- 概念参照のみの場合もAdoption Ledgerへ記録する。

### RDE checkpoint

- GUI導入によりinspect-firstがmutation-firstへ反転していないか。
- UI上の分かりやすさが不確実性の隠蔽になっていないか。

## 10. M2.7 — Transport Boundary Skeleton

### Goal

メッセージアプリ等の外部入力を、即時命令ではなく検証可能なEnvelopeとして受け入れる境界を定義する。

### In scope

- ExternalInteractionEnvelope
- transport identity evidence
- attachment refs
- user_input / Context candidate recording
- explicit command promotion
- Mock Transport
- Core外配置方針

### Out of scope

- Telegram / Slack / LINE全実装
- hosted relay
- offline queue
- public webhook service
- autonomous remote agent

### Required artifacts

- Transport Boundary ADR
- Envelope schema
- identity mapping note
- Mock Transport
- attachment boundary tests
- command promotion tests

### Acceptance criteria

- 外部messageをuser_inputまたはContext candidateとして記録できる。
- message受信とcommand実行が分離されている。
- transport identityをChronicle actorと自動同一視しない。
- attachment bytesをEvent payloadへ無制限に保存しない。
- transport固有APIがCoreへ入らない。

### Failure gates

- 外部messageだけでCapabilityが自動実行される。
- platform tokenがChronicleへ保存される。
- webhook署名未検証でも受理する。
- Transport runtimeが一次記録を直接変更する。

### Rights gate

- MulmoBridge等のコードを直接採用する場合はpackage単位のMIT noticeと商用版権利確認を行う。
- 原則はprotocol patternの独自実装とする。

### RDE checkpoint

- 遠隔利便性がoperator consentと文脈主権を上回っていないか。
- 外部チャネルの短いmessageが過大なcommandへ解釈されていないか。

## 11. M2.8 — Operational Hardening and Exit Audit

### Goal

Stage 2を運用可能な品質へ引き上げ、既存Chronicle契約を壊していないことを確認する。

### In scope

- doctor checks
- runtime / capability status
- cleanup diagnostics
- adoption ledger validation
- migration / rebuild tests
- security negative tests
- performance baseline
- operator runbook
- release readiness
- Stage Exit RDE

### Out of scope

- Stage 3機能
- dynamic ecosystem
- hosted runtime
- network federation completion

### Required artifacts

- Stage 2 operator runbook
- Stage 2 release readiness
- security review
- rights review
- migration report
- performance baseline
- Stage Exit RDE report

### Acceptance criteria

- ruffとpytestが通る。
- CLI、UI smoke、JSONL rebuild、migrationが通る。
- Stage 2無効時に既存動作が変わらない。
- external runtimeは既定無効である。
- dangerous configurationをdoctorが検出する。
- cleanup漏れがない。
- direct source reuseにnoticeとrights recordがある。
- 重大なRDE逸脱が解消または明示的に延期されている。

### Failure gates

- 派生Registry、cache、runtime stateが正本化する。
- Stage 2無効でもnetwork callが起きる。
- Reviewを経ないMutation pathが残る。
- rights origin不明のコードが残る。
- documentationと実装の境界が一致しない。

### Rights gate

- SBOMまたは依存一覧を確認する。
- THIRD_PARTY_NOTICESを更新する。
- 商用版へ含める部分の権利分類を再確認する。
- AI支援実装の出所・類似性レビューを完了する。

### RDE checkpoint

Stage 2基本仕様に対して次を監査する。

1. Preserved: Chronicle正本、local-first、Review、Boundary
2. Transformed: RuntimeService、UI、外部入力の構造
3. Supplemented: Capability、Plan、Surface、Rights ledger
4. Unresolved: Stage 3へ延期する事項
5. Deviation risks: AI host化、dynamic plugin化、記録過多、権利混同
6. Next update policy: Stage 3開始条件

## 12. Issue作成テンプレート

各Milestone配下のIssueは次の形式を推奨する。

```markdown
## Goal

## Stage 2 milestone

M2.x

## Problem

## Proposed change

## Affected contracts

- [ ] Primary Stable
- [ ] Public Stable-ish
- [ ] Semi-public
- [ ] Derived/Internal only

## Failure conditions

## Security / boundary impact

## Rights and provenance

- External reference:
- Adoption mode:
- Copied source: yes / no
- License review:
- Commercial-edition rights review:

## Tests

## RDE delta

### Preserved
### Transformed
### Supplemented
### Unresolved
### Deviation risks
### Next update policy
```

## 13. Milestone完了ルール

Milestoneをcloseする前に、次を確認する。

- 必須artifactがmainへmerge済みである。
- CIが成功している。
- failure-path testsが存在する。
- interface contractへの影響が記録されている。
- security / boundary reviewが済んでいる。
- rights / provenance記録が更新されている。
- RDE checkpointがPRまたはrelease文書に残っている。
- 次Milestoneへ持ち越す事項がIssue化されている。

単にコードが動作することはMilestone完了を意味しない。契約、失敗条件、監査、権利、運用の再構成可能性が揃って初めて完了とする。
