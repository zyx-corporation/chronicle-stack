# Chronicle Stack Security Policy v0.1

Author: Tomoyuki Kano  
Status: Draft  
Scope: Chronicle Stack / Sayane / AI番頭 / CS知識気象台 / 組織内知識気象台  
Classification: Internal Security Policy Draft

## 1. Basic Recognition

Chronicle Stack is not merely a document storage foundation.

It stores not only finished artifacts, but also originating questions, decision processes, objections, unresolved items, meaning changes, failures, unpublished hypotheses, and organizational learning traces.

Therefore, Chronicle Stack requires a higher security standard than ordinary knowledge bases, FAQs, meeting-note systems, or RAG document stores.

```text
Ordinary document management:
  stores what was decided

Chronicle Stack:
  stores why it was thought
  which alternatives were rejected
  what was deferred
  which question started the work
  which meaning changes occurred
```

Chronicle Stack is therefore both a knowledge management foundation and a provenance protection foundation for thought, judgment, strategy, and organizational learning.

## 2. Core Policy

The security policy is summarized as follows:

```text
To preserve provenance is to preserve the time axis of personhood, organization, and judgment.
Therefore Chronicle Stack protects context assets, not merely information assets.
```

Context assets include not only documents or data, but also the questions, situations, uncertainties, judgments, values, and relationships from which they arose.

Protected targets include:

```text
content
origin
judgment process
intent
objections
deferrals
unpublished weaknesses
chronology
relationships
reinterpretation history
meaning change ΔM
```

Chronicle Stack must therefore protect provenance, reinterpretability, and context sovereignty in addition to confidentiality, integrity, and availability.

## 3. Security Principles

### 3.1 Local-first

The original Chronicle source should be local-first by default.

Cloud services may be used for synchronization, sharing, backup, and collaboration, but cloud state must not become the sole source of truth.

```text
Principle:
  keep the original record locally or in a self-managed domain
  treat cloud services as replication / sync / sharing layers
  do not make cloud state the only canonical record
```

When Chronicle Stack content is sent to a cloud AI system, the scope, purpose, model, storage policy, and reuse policy must be explicit.

### 3.2 Least Disclosure

Chronicle Stack must provide only the necessary context to the necessary party.

Being able to read a file does not imply permission to inject it into an LLM.

```text
Forbidden conflation:
  file is readable
  =
  file may be sent to an external LLM
```

Permissions should distinguish at least:

```text
read
summarize
reinterpret
export
inject
publish
```

In particular, `inject` and `publish` must be separate from `read`.

### 3.3 Layer Separation

Chronicle Stack records should be classified by sensitivity and nature.

```text
Layer 0: Public
  published artifacts, public articles, public materials

Layer 1: Shareable
  externally shareable summaries, sales materials, public explanations

Layer 2: Internal
  internal discussion, judgment process, objections, deferrals, meeting records

Layer 3: Sensitive Context
  personal context, thought formation, emotional triggers, unpublished hypotheses, strategy

Layer 4: Restricted Secret
  contracts, personal data, credentials, secret keys, legal / financial / HR high-confidential data
```

Most Chronicle Stack value exists in Layer 2 and Layer 3. These layers require protection equal to or stronger than Sayane.

Layer 4 should not be stored directly in Chronicle body text. When needed, use references and keep the actual secret in a dedicated secret manager, contract management system, or credential manager.

### 3.4 Append-only and Correctability

Chronicle Stack has an append-only nature because it preserves provenance.

However, correction, sealing, redaction, and deletion must be possible for typo correction, personal data, legal deletion requests, confidentiality leaks, and safety reasons.

Preferred structure:

```text
original record
redacted record
tombstone
audit event
```

Some deletion workflows must record only that deletion occurred, not the deleted content.

### 3.5 Reinterpretation Logs

Reinterpretation is a core Chronicle Stack use case.

Reinterpretation must be logged.

```text
log:
  which records were referenced
  which model or agent read them
  for what purpose
  what output was generated
  which parts are inference
  what meaning change ΔM occurred
```

Reinterpretation results must not be confused with original records.

```text
Original:
  record from that time

Interpretation:
  later interpretation

RDE Audit:
  evaluation of meaning change and deviation risk
```

Confusing these is a serious semantic integrity violation.

## 4. Threat Model

Chronicle Stack must consider at least:

- confidentiality leakage
- context extraction
- semantic tampering
- prompt injection
- privilege crossing
- chronology contamination
- vendor lock-in and external dependency capture

Prompt injection must be handled because stored documents may contain instructions aimed at later LLM processing.

## 5. Access Control Policy

User-level access control is insufficient.

Actors include:

```text
Human User
Owner
Collaborator
Reviewer
AI Agent
External LLM
Local LLM
Connector
```

Operations include:

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

AI Agents should be least-privilege by default.

```text
AI Agent defaults:
  Layer 0/1 only by default
  Layer 2 only for purpose-limited use
  Layer 3 requires explicit permission
  Layer 4 is prohibited by default
```

## 6. LLM Injection Policy

When Chronicle Stack content is injected into an LLM, the following must be explicit:

```text
1. purpose
2. target layers
3. external vs local LLM
4. storage / learning / logging policy
5. output classification
6. prompt injection mitigation
7. reinterpretation log
```

Layer policy:

```text
Layer 0: generally allowed
Layer 1: purpose-limited
Layer 2: internal or explicitly approved external models
Layer 3: local or high-trust environment by default
Layer 4: prohibited
```

## 7. Data Classification Metadata

Records should carry at least:

```yaml
classification:
  layer: 0 | 1 | 2 | 3 | 4
  sensitivity: public | shareable | internal | sensitive | restricted
  owner: string
  created_at: datetime
  source_type: conversation | document | email | issue | meeting | decision | audit
  source_refs: list
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
    review_at: datetime
  integrity:
    hash: string
    previous_hash: string
    signature: string
```

This metadata should be usable across Markdown, Obsidian, RDBMS, Git-backed vaults, and graph/RAG pipelines.

## 8. Record Structure

Chronicle records should separate:

- origin
- background
- observations
- interpretation
- judgment
- objections and alternatives
- deferrals
- reflected artifacts
- next review
- RDE difference validation

Facts, interpretations, and judgments must not be confused.

## 9. Tamper Detection

Chronicle Stack should adopt:

```text
record hash
hash chain
signed snapshot
append log
audit log
```

Git-backed vaults can use commits, signed tags, and diffs, but Git alone is insufficient. LLM injection, export, reinterpretation, anonymization, and sealing also require audit coverage.

## 10. Redaction, Sealing, and Deletion

Chronicle Stack must design forgetting, not only preservation.

Modes:

```text
redact
seal
expire
tombstone
hard delete
```

Deletion and sealing are the conflict point between provenance and safety.

## 11. CS Knowledge Weather Observatory Connection

CS Knowledge Weather Observatory observes inquiry flow, FAQs, templates, and support history. Chronicle Stack stores the provenance of decisions arising from that observation.

```text
CS Knowledge Weather Observatory:
  observes knowledge bottlenecks

Chronicle Stack:
  stores the provenance of decisions arising from observations
```

Raw CS data must not be stored without limit.

Avoid storing:

- customer personal data
- unnecessary full inquiries
- granularity usable for staff evaluation
- emotion scores
- individual rankings

## 12. Prohibited Uses

Chronicle Stack must not be used for:

- personal ideology scoring
- employee ranking
- automatic HR evaluation
- adverse customer classification
- continuous surveillance profiling
- opaque evaluation models
- unauthorized use of non-public context
- using Layer 3 information for sales or persuasion optimization

The goal is to observe knowledge flow, not to score individuals.

## 13. Operational Rules

Minimum operational rules:

```text
1. assign classification at record creation
2. review Layer 2+ before external sharing
3. prohibit or individually approve external LLM use for Layer 3+
4. do not store Layer 4 in Chronicle body
5. use only public-context records for public document generation
6. separate reinterpretations from original records
7. attach RDE difference validation to important decisions
8. periodically review / seal / redact unnecessary records
```

## 14. Minimum Implementation Requirements

MVP-level requirements:

```text
record classification
metadata header
local storage
export control
LLM injection control
audit log
redaction
RDE block
```

Classification and LLM injection control are required early; otherwise existing records become dangerous unclassified data.

## 15. Recommended Architecture

Practical initial architecture:

```text
Storage:
  local filesystem
  Git-backed vault
  SQLite / PostgreSQL
  Obsidian-compatible Markdown

Metadata:
  YAML front matter
  JSON schema
  hash chain

Search:
  local index
  vector index
  GraphRAG index

LLM:
  local LLM preferred for Layer 3
  external LLM only for Layer 0/1 or masked Layer 2

Audit:
  append-only audit log
  signed snapshots

Secrets:
  separated into an external secret manager
```

Self-hosted PostgreSQL must not be exposed directly to the Internet. Use LAN, VPN, WireGuard, Tailscale, ZeroTier, or SSH tunnel.

## 16. Security Classification Summary

```text
Sayane:
  S3
  protects active context sovereignty

Chronicle Stack:
  S4
  protects time-axis context sovereignty

CS Knowledge Weather Observatory:
  W3
  observes organizational support and FAQ flow

Organization Knowledge Weather Observatory:
  W3
  observes organizational knowledge flow

Weather Observatory connected to personal evaluation / ideology inference:
  W4
  prohibited or subject to special review
```

Chronicle Stack protects time-axis context sovereignty and therefore requires protection equal to or greater than Sayane.

## 17. Initial Checklist

```text
[ ] original storage location is clear
[ ] layer classification exists
[ ] Layer 3+ handling is defined
[ ] external LLM injection permission is recorded
[ ] customer personal data is separated from body text
[ ] credentials and secret keys are not stored
[ ] reinterpretation logs exist
[ ] public document generation is context-limited
[ ] redact / seal / delete operation exists
[ ] RDE difference validation exists
[ ] Git / hash / snapshot tamper detection exists
```

## 18. Future Work

- concrete permission model
- YAML / JSON metadata schema
- LLM injection gateway
- prompt injection sanitizer
- RDE audit automation
- Git signatures and hash chain
- local-first sync
- customer tenant separation
- CS Knowledge Weather Observatory connection specification
- privacy law / GDPR review
- external LLM usage policy
- deletion / sealing / audit-log conflict handling

## 19. RDE Review

### Preserved

- Chronicle Stack requires security considerations equal to or greater than Sayane.
- Chronicle Stack protects time-axis context sovereignty.

### Transformed

- Chronicle Stack is defined as a context-asset protection system, not only a knowledge storage system.

### Added

- Layer 0-4 classification.
- LLM injection policy.
- Reinterpretation logs.
- Append-only and deletion-right compatibility.
- CS Knowledge Weather Observatory connection policy.
- Prohibited uses.

### Unresolved

- concrete metadata schema
- key management
- signature method
- external LLM gateway
- customer tenant separation
- legal review

### Deviation Risks

Chronicle Stack must not become a system that preserves everything without respecting the right to forget, seal, and redact.
