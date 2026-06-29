# Chronicle Stack 最終 UI 実装差分仕様書

Status: Draft  
Related:

- `docs/final-ui-design-spec.ja.md`
- `docs/final-ui-design-workspace-addendum.ja.md`
- `Chronicle Stack.html` design prototype

## 1. 目的

この文書は、作成済み UI デザインを Chronicle Stack の実装バックログへ変換するための差分仕様書です。

扱う問いは次の 3 つです。

- 現行 `chronicle ui` と既存 read model で、どこまで実装できるか
- どこに追加 read model / API / renderer が必要か
- どの順序で実装すれば boundary を壊さずに前進できるか

この文書は visual design の評価書ではなく、実装計画書です。

## 2. 現在地

現行 `chronicle ui` には、すでに次が存在します。

- `/api/overview`
- `/api/events`
- `/api/contexts`
- `/api/chronicle-objects`
- `/api/federation-inbox`
- `/api/federation-outbox`
- `/api/trust-nodes`
- `/api/trust-relations`
- `/api/artifacts`
- `/api/decisions`
- `/api/rde`
- `/api/boundary`
- `/api/audit`
- `/api/lifecycle`
- `/api/runtime-records`
- `/api/review-queue`
- `/api/ui-boundary`
- `/api/package-review`
- `/api/federation-package-preview`
- `/api/graph-summary`
- `/api/ai-index-status`
- `/api/ai-index-vector`
- `/api/ai-index-graph-nodes`
- `/api/ai-index-graph-edges`
- `/api/summary-jobs`
- `/api/proposals`

また detail endpoint として、少なくとも次が存在します。

- events
- contexts
- artifacts
- decisions
- rde
- boundary
- audit
- lifecycle
- runtime-records
- review-queue
- summary-jobs

設計上の大前提:

- UI は derived surface
- `chronicle.jsonl` が authority
- local-first
- review / federation / runtime は preview-first / inspect-first

## 3. 判定カテゴリ

実装差分は次の 3 段階で判定します。

### A. そのまま実装可能

既存 read model と renderer の再構成で到達できるもの。

### B. 軽微な read model 追加で実装可能

既存 service 群を使い、overview 集約や detail payload の追加で到達できるもの。

### C. 新規 surface 設計が必要

新しい endpoint、payload contract、または UI 専用の再構成 read model が必要なもの。

## 4. 画面別差分

## 4.1 Home / Overview

判定:

- A と B の混在

既にあるもの:

- counts
- runtime summary
- review / auth / identity / mutation readiness
- federation preflight / overlap / grouped CLI guidance
- trust summary
- triage shortcut
- warning surface

不足しているもの:

- current question 中心の landing 優先順位
- active artifact / unresolved objection / current proposal 候補の同居
- right-rail 的 evidence / trust / boundary priority 配置

必要差分:

- B: overview payload に question-centric summary を追加
- B: overview payload に active proposal summary を追加
- B: objections / hypotheses / current artifact candidate を top-level aggregate として追加
- A: renderer を dashboard 的 equal-card 構成から operator-priority 構成へ再編

## 4.2 Chronicle Objects

判定:

- A と B の混在

既にあるもの:

- `/api/chronicle-objects`
- object record / derived object view

不足しているもの:

- question-centric navigation の優先表示
- object 間の semantic path の強調
- objections / hypotheses / decay の関係把握

必要差分:

- B: `/api/chronicle-objects` に relationship summary を追加
- A: list/detail renderer を object-first の導線へ再設計

## 4.3 Context & Artifact Workbench

判定:

- B が中心、一部 C

既にあるもの:

- `/api/artifacts`
- `/api/artifacts/<id>`
- `/api/contexts`
- `/api/contexts/<id>`
- `/api/decisions`
- `/api/rde`
- proposal summary の一部 payload

既存 payload で足りるもの:

- artifact list
- artifact detail
- version metadata
- linked context / linked decision / linked RDE のベース情報
- proposal count / pending proposal count

不足しているもの:

- workbench 向け 3 カラム統合 view
- artifact ごとの semantic change summary 集約
- right rail 向け provenance / boundary / audit / linked decision のまとめ
- artifact 中心の unified navigation state

必要差分:

- B: `/api/artifacts/<id>` に workbench 用 `linked_contexts`, `linked_decisions`, `linked_rde_records`, `source_event_summary`, `boundary_summary`, `audit_summary`, `proposal_summary` を整形追加
- B: semantic diff / RDE summary を artifact detail でより直接使える形に再構成
- C: 必要なら `/api/artifact-workbench/<artifact_id>` のような UI 専用統合 endpoint を追加

推奨:

- まずは新 endpoint を増やさず、artifact detail payload 拡張で進める

## 4.4 Review Workspace

判定:

- A と B の混在

既にあるもの:

- `/api/review-queue`
- review detail
- reviewer identity / session / enforcement / validation gate
- action preview
- CLI parity
- blocked-route preview

不足しているもの:

- design prototype で強く表現されている step-based review progression
- proposal review と apply 候補の結合表示
- review outcome matrix の整理された presentation

必要差分:

- A: renderer の再構成で多くを吸収可能
- B: review detail payload に `review_step_summary`, `apply_prerequisites`, `outcome_matrix`, `identity_sufficiency_summary` を追加すると実装しやすい

## 4.5 Audit / Boundary / Lifecycle Workspace

判定:

- B が中心

既にあるもの:

- `/api/audit`
- `/api/lifecycle`
- `/api/boundary`
- overview の federation preflight summary
- detail endpoint 群

不足しているもの:

- governance console としての統合された reading flow
- selected audit row に対する related boundary / lifecycle / impacted target implication
- top summary rail

必要差分:

- B: audit row に `related_boundary_rule_ids`, `related_lifecycle_ids`, `impacted_target_summary`, `operational_implication` を追加
- B: `/api/audit` に governance summary aggregate を追加
- A: renderer で `summary rail + stream + implication rail` の 3 部構成へ再設計

新規 endpoint の必要性:

- 当面は不要

## 4.6 Federation Workspace

判定:

- A と B の混在

既にあるもの:

- inbox / outbox
- package preview
- overview federation panel
- boundary-check / inspect / verify / preview / import-preview guidance
- consent overlap
- trust summary

不足しているもの:

- package screen を shipping inspection desk として見せる統合 presentation
- package purpose / trust / consent / redaction / import implication の一画面統合

必要差分:

- B: `/api/federation-package-preview` に `package_route_summary`, `trust_reference_summary`, `consent_summary`, `import_implication_summary` を整理して追加
- A: overview federation panel と package preview detail renderer の再構成

## 4.7 Trust Workspace

判定:

- B が中心

既にあるもの:

- `/api/trust-nodes`
- `/api/trust-relations`
- overview trust summary

不足しているもの:

- node / subject / relation の関係を一続きで読むための統合 view
- trust relation の domain / purpose / capability matrix 的理解
- assertion / withdrawal history
- federation implication の近接表示

必要差分:

- B: trust relation payload に `history_summary`, `active_state`, `federation_implication`, `subject_summary` を追加
- B: trust node payload に relation count 以外の `latest_activity_summary`, `domain_coverage_summary` を追加
- C: 必要なら `/api/trust-workspace/<node_id>` のような統合 endpoint

推奨:

- まずは trust node / relation 既存 payload 拡張で進める

## 4.8 Runtime / Retrieval Workspace

判定:

- A と B の混在

既にあるもの:

- `/api/runtime-records`
- `/api/summary-jobs`
- query-engine trial / escalation cue
- handoff / bundle / reviewed files / import-readiness
- AI index / graph summary

不足しているもの:

- runtime posture summary の統合 presentation
- runtime records / summary jobs / trials / handoff / escalation の一画面整理
- "Chronicle core と external runtime の境界" の視覚表現強化

必要差分:

- B: runtime record payload に `posture_role`, `downstream_boundary_note`, `trial_sufficiency_summary`, `handoff_summary` の整理追加
- B: summary jobs payload に `package_readiness_summary`, `auth_advisory_summary`, `identity_assurance_summary` の簡潔化
- A: renderer の組み替えでかなり前進可能

## 5. 実装優先順位

## Phase 1: Renderer-first refactor

目的:

- 現行 endpoint を活かしながら、最終 UI 案の layout grammar に寄せる

対象:

- Overview
- Review Workspace
- Federation Workspace
- Runtime / Retrieval Workspace の presentation 再編

理由:

- 既存 payload が比較的豊富
- local-first / read-only boundary を壊しにくい

## Phase 2: Read model enrichment

目的:

- Context & Artifact Workbench
- Audit / Boundary / Lifecycle
- Trust Workspace

の情報密度を最終 UI 案に耐える形へ上げる

対象:

- artifact detail payload 拡張
- audit aggregate / implication field 追加
- trust relation / node summary 拡張
- runtime posture 整理

## Phase 3: UI-only integrated endpoints

目的:

- 複数 endpoint をフロントで無理に束ねず、operator-oriented integrated view を安定提供する

候補:

- `/api/artifact-workbench/<id>`
- `/api/trust-workspace/<id>`
- UI 統合向け governance summary endpoint

条件:

- 既存 detail payload 拡張だけでは renderer が過度に複雑になる場合に限る

## 6. 実装しないこと

この UI デザインの実装過程でも、次はしないこと:

- hosted SaaS 的 multi-user semantics の導入
- hidden auto-sync
- hidden auto-import
- review を飛ばした direct mutation default
- Chronicle core を external query runtime の実行面にすること
- trust relation を permission grant に見せること

## 7. 推奨タスク分解

### Task 1

- Overview を final UI 案に沿って情報優先順位で再編する

### Task 2

- Review Workspace を step / blocker / outcome 明示型に再構成する

### Task 3

- Federation Workspace を package inspection desk 型に再構成する

### Task 4

- Runtime / Retrieval Workspace を posture + handoff + escalation 型に再構成する

### Task 5

- artifact detail payload を workbench 向けに拡張する

### Task 6

- audit payload を governance console 向けに拡張する

### Task 7

- trust payload を relation semantics inspector 向けに拡張する

## 8. Summary

今回の UI デザインは、現行 Chronicle Stack と断絶した夢案ではありません。
かなりの部分は既存 read model の再編で到達可能です。

実装上の本質は:

- 新機能追加よりも、derived information を operator-centered に再配置すること
- どうしても必要なところだけ read model を厚くすること
- local-first / proposal-first / preview-first の boundary を崩さないこと

特に次の 4 つは、既存資産を活かしつつ前進しやすい重点領域です。

- Review Workspace
- Federation Workspace
- Runtime / Retrieval Workspace
- Context & Artifact Workbench
