# Chronicle Event Origin Contract v1

Status: Stable design contract; implementation pending  
Contract version: `chronicle-event-origin/v1`  
Governing decision:
[ADR-0105](../adr/0105-chronicle-event-origin-attribution-contract.md)  
Extends: [Chronicle Event Model v0.1](chronicle-event-model-spec-v0.1.md),
[Interface Contracts](../interface-contracts.md), [Storage Format](../storage-format.md)  
Related: [Agent Runtime Contract](../api/agent-runtime-contract.md),
[Export Manifest](../export-manifest.md), [Stack Handoff Contracts](../yard/handoff-contracts.md)

## 1. Purpose and status boundary

This contract defines how a Chronicle Event attributes a claim or generation act, how existing
Chronicles adopt that field without rewriting history, and how review and derived surfaces must
preserve the distinction.

The contract is stable at the design layer. The current source model does not yet implement it.
Normative words such as MUST and MUST NOT apply to the implementation and to any Chronicle after
its cutover declaration; they are not a claim that current binaries already enforce the rules.

## 2. Four separate attribution axes

| Axis | Question answered | Current or future surface |
|---|---|---|
| recorder | Which Chronicle-side role wrote the Event? | `ChronicleEvent.actor` |
| Event origin | Whose claim or generation is represented? | future `ChronicleEvent.origin` |
| request origin | Who or what initiated an API request? | `ApiOriginMetadata` |
| source provenance | Where was the content captured, generated, or imported from? | `SourceProvenance` |

Transport identity evidence is a fifth, evidence-only surface. Authentication, authorization,
capability grants, and reviewer-session proof are security surfaces rather than attribution axes.

Implementations MUST NOT:

- treat `actor` as Event origin;
- treat API request origin as identity proof or automatic Event origin;
- derive Event origin from `source` without an explicit mapping decision;
- promote an unverified transport display name to `actor_id`;
- treat `actor_id` or `identity_evidence_ref` as an authorization grant.

## 3. JSONL schema

`ChronicleEvent` gains an optional top-level field named `origin`:

```json
{
  "origin": {
    "actor_type": "ai",
    "actor_id": "agent:example",
    "assertion_mode": "ai_proposal",
    "identity_evidence_ref": "msg_example"
  }
}
```

The origin object has exactly these v1 semantic fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `actor_type` | enum | yes | Kind of attributed human, AI, tool, or system |
| `actor_id` | string | no | Attribution identifier when known; not identity proof |
| `assertion_mode` | enum | yes | How the represented content entered the Chronicle |
| `identity_evidence_ref` | string | no | Opaque reference to separately retained identity evidence |

`actor_id` and `identity_evidence_ref`, when present, MUST be non-empty and MUST NOT contain a
password, bearer token, cookie, signing secret, or equivalent credential. The Event MUST retain
the core origin snapshot even when the evidence reference is unresolved or omitted.

The `origin` field is optional in the physical model so legacy Events remain readable. Its
write-time requirement is determined by the per-Chronicle cutover in section 6.

### 3.1 `actor_type`

| Value | Meaning |
|---|---|
| `human` | A human is attributed as the source of the assertion or generation act |
| `ai` | An AI model or agent-generated output is attributed |
| `tool` | A tool or business-system observation is attributed |
| `system` | A Chronicle or other deterministic system process is attributed |
| `unknown` | The actor kind cannot be established |

`unknown` is valid after cutover. It is safer than inferring a human or AI identity from weak
evidence.

### 3.2 `assertion_mode`

| Value | Meaning |
|---|---|
| `human_assertion` | A human states, decides, or explicitly adopts the represented content |
| `ai_proposal` | AI-generated content is proposed for possible later review or adoption |
| `tool_observation` | A tool or business system reports an observation |
| `rule_derived` | A deterministic rule or defined transformation derives the result |
| `not_applicable` | The Event was assessed and has no applicable claim/generation mode |
| `unknown` | The mode cannot be established |

`not_applicable` and `unknown` are different. The former is an affirmative classification; the
latter records uncertainty. `AssertionKind` in the API describes whether an assertion object is a
claim, evidence, caveat, unknown, or verification status and MUST NOT be substituted for this
origin mode.

Known actor/mode combinations SHOULD be semantically coherent. A consumer MAY warn about an
apparent contradiction, but MUST NOT silently rewrite it into another attribution.

## 4. Examples

### 4.1 AI proposal recorded by a tool

```json
{
  "actor": "tool",
  "event_type": "assistant_output",
  "origin": {
    "actor_type": "ai",
    "actor_id": "agent:writer",
    "assertion_mode": "ai_proposal"
  }
}
```

The recorder is the tool; the generated content is attributed to the AI.

### 4.2 Unverified external message import

```json
{
  "actor": "importer",
  "event_type": "user_input",
  "origin": {
    "actor_type": "unknown",
    "assertion_mode": "unknown",
    "identity_evidence_ref": "msg_external_123"
  }
}
```

The transport identity remains evidence. The importer does not convert it into a verified human
attribution.

### 4.3 Structural Event with no assertion mode

```json
{
  "actor": "system",
  "event_type": "metadata_updated",
  "origin": {
    "actor_type": "system",
    "actor_id": "chronicle:migration",
    "assertion_mode": "not_applicable"
  }
}
```

## 5. Event invariants

For every Event after cutover:

1. `origin` MUST be present and non-null.
2. `actor_type` and `assertion_mode` MUST be recognized v1 values.
3. Unknown attribution MUST be represented explicitly with enum values, not field omission.
4. Origin MUST remain independent of recorder, request, source, and authority metadata.
5. A later review, correction, or verification MUST NOT mutate the origin of the target Event.

A post-cutover Event missing origin remains part of the primary history. It is a semantic contract
violation, not automatically a corrupt JSONL line. Consumers MUST surface the violation and MAY
decline committed downstream use; they MUST NOT silently reinterpret it as a legacy Event.

## 6. Per-Chronicle cutover

### 6.1 Declaration Event

The migration MUST append one existing `metadata_updated` Event. Its payload is:

```json
{
  "event_origin_contract": {
    "contract_version": "chronicle-event-origin/v1",
    "scope_chronicle_id": "chr_example",
    "boundary_basis": "authoritative_jsonl_append_order",
    "effective_after_event_id": "evt_origin_cutover",
    "pre_cutover_missing_origin": "legacy_unknown",
    "post_cutover_missing_origin": "contract_violation"
  }
}
```

The complete Event uses the same ID in the outer record:

```json
{
  "event_id": "evt_origin_cutover",
  "chronicle_id": "chr_example",
  "event_type": "metadata_updated",
  "actor": "system",
  "summary": "Declare Chronicle Event origin contract v1",
  "payload": {
    "event_origin_contract": {
      "contract_version": "chronicle-event-origin/v1",
      "scope_chronicle_id": "chr_example",
      "boundary_basis": "authoritative_jsonl_append_order",
      "effective_after_event_id": "evt_origin_cutover",
      "pre_cutover_missing_origin": "legacy_unknown",
      "post_cutover_missing_origin": "contract_violation"
    }
  },
  "origin": {
    "actor_type": "system",
    "actor_id": "chronicle:event-origin-migration",
    "assertion_mode": "rule_derived"
  }
}
```

The declaration Event itself is outside the origin-required region because the rule is effective
after its row. It SHOULD nevertheless carry origin when written by an upgraded implementation.

The following cross-field checks are mandatory:

- payload `scope_chronicle_id` equals outer `chronicle_id`;
- payload `effective_after_event_id` equals outer `event_id`;
- `boundary_basis` has the exact v1 value;
- `parent_event_id` does not refer to the declaration itself;
- no prior valid cutover declaration exists for the same Chronicle.

### 6.2 Boundary resolution

The Event ID identifies the declaration. It does not encode order. A reader resolves the boundary
by locating that Event in the authoritative JSONL and using physical append order for Events with
the same `chronicle_id`.

```text
before declaration row  -> absent/null origin = legacy_unknown
declaration row         -> absent/null origin = legacy_unknown
after declaration row   -> absent/null origin = contract_violation
after declaration row   -> explicit unknown values = valid
```

Readers MUST NOT use:

- lexical or numeric Event ID order;
- Event timestamps;
- timeline sorting;
- GraphRAG `(timestamp, event_id)` order;
- graph-export incremental ordering;
- file modification time.

Backdated and imported Events are classified by when their Event row was appended to this
Chronicle, not by the time described in `timestamp`.

### 6.3 Migration sequencing

Before cutover, an implementation MUST:

1. deploy origin-aware readers without requiring origin on legacy Events;
2. upgrade every Core, CLI, daemon, future MCP, API, import, and maintenance writer;
3. upgrade model-based exports and derived projections or mark their loss explicitly;
4. quiesce writers or acquire an exclusive Chronicle migration guard;
5. append and validate the declaration Event;
6. activate origin-required validation before writers resume.

An implementation MUST refuse cutover if it cannot prevent an old or concurrent writer from
appending origin-less Events afterward. Replaying the migration MUST be idempotent and MUST NOT
append a second cutover declaration.

## 7. Compatibility behavior

### 7.1 Existing Events

Legacy JSONL lines are never rewritten to add inferred origin. A derived reader MAY display
`legacy_unknown`, but that label is an interpretation under this contract, not a field inserted
into the original Event.

### 7.2 Current old reader

The current `ChronicleEvent` model ignores unknown top-level fields. An executable probe against
the current implementation established:

```text
unknown origin accepted during parse: yes
origin retained on parsed model: no
origin retained after model reserialization: no
raw JSONL changed by read: no
metadata_updated migration payload retained: yes
unknown declaration-specific EventType accepted: no
```

Consequences:

- raw, byte-preserving reads and backups retain future origin data;
- an old model must not be used for read-modify-write migration;
- old model-based YAML and other projections are not Event-origin faithful;
- the cutover uses `metadata_updated`, not a new EventType.

### 7.3 Old writers

Old writers are not post-cutover compatible. Request-origin metadata, recorder actor, or source
metadata does not make an origin-less write conformant. Such a write is retained and reported as
`contract_violation`.

## 8. Request, agent, and transport mapping

### 8.1 API

The draft API field `ApiWriteRequest.origin` remains request-origin metadata. It MUST NOT be
copied blindly into `ChronicleEvent.origin`. An Event write contract needs a distinct Event-origin
input or an explicit, validated mapping rule.

For example, an AI agent may initiate a request that records a human assertion. The API caller is
the agent; the Event origin is the human. Conversely, a human-triggered request may record an AI
proposal.

### 8.2 Agent runtime

`AgentRecordOriginKind` is an existing draft vocabulary, not the canonical EventOrigin schema.
An adapter MUST preserve its meaning explicitly and MUST reject or request review for ambiguous
mappings. It must not collapse every non-human kind into one Event origin.

### 8.3 External transport

Under ADR-0035, transport identity is evidence rather than a Chronicle actor. An unverified
external interaction normally uses explicit unknown Event origin and may refer to its envelope or
evidence through `identity_evidence_ref`.

### 8.4 Coordination identifiers

This v1 contract adds no `correlation_id` or `causation_id`. `message_id`, API `request_id`, and
Event `parent_event_id` retain their existing meanings. A later shared coordination-envelope
contract may add correlation/causation fields, but it must not hide Event origin outside the
primary Event.

## 9. Confirmation and verification

Confirmation is an append-only relation:

```text
review Event --target_event_id / parent_event_id--> target Event
```

A review Event MUST include `target_event_id` in its payload and SHOULD set `parent_event_id` to
that target. It MUST NOT mutate the target Event, its origin, or a `confirmed_by` field.

Example lineage:

```text
AI proposal Event
  origin = ai / ai_proposal
        ^
        |
human review Event
  target_event_id = proposal Event
  disposition = approve
  origin = human / human_assertion
```

Approval records a review disposition. It is not truth proof. A supported, contested, disproven,
or otherwise verified epistemic status belongs in a separate assertion/verification record.

Compatibility readers MUST continue to recognize the current review shape:

```json
{
  "event_type": "note_added",
  "actor": "reviewer",
  "parent_event_id": "evt_target",
  "payload": {
    "review_decision": true,
    "target_event_id": "evt_target",
    "disposition": "approve"
  }
}
```

The reserved `review_decision_recorded` EventType does not invalidate historical `note_added`
review Events.

## 10. Export and subset contract

### 10.1 Full primary copy

A byte-preserving copy of the complete `.chronicle/chronicle.jsonl` plus its matching metadata
preserves the boundary. A normal full `.chronicle/` backup therefore retains the contract so long
as files are not parsed and reserialized by an old model.

### 10.2 Event-bearing derived exports

A YAML, JSON, package, or other derived surface that claims Event-origin fidelity MUST include:

- source `chronicle_id`;
- `chronicle-event-origin/v1`;
- cutover declaration Event ID;
- `authoritative_jsonl_append_order` as the boundary basis;
- whether original append order was preserved;
- warnings for filtered, redacted, invalid, or unprojected origin data.

For a reordered or partial selection, the export MUST do at least one of:

1. preserve source append order and include the declaration Event; or
2. materialize a per-record boundary state such as `legacy_unknown`, `declared_origin`,
   `contract_violation`, or `redacted`.

Including the declaration without preserving or materializing order is insufficient because an
Event ID is not sortable.

### 10.3 Human and graph projections

Markdown, HTML, graph, GraphRAG, and context-only packages may intentionally omit Event origin.
When they do, they MUST be described as non-origin-faithful and MUST NOT infer human authorship
from omission. If a graph or query surface begins answering attribution questions, it MUST project
origin and its loss warnings explicitly.

### 10.4 Redaction and dangling references

An export profile may omit `actor_id` and `identity_evidence_ref`. It SHOULD retain `actor_type`
and `assertion_mode` and MUST distinguish a redacted value from a missing-origin violation.

When a subset includes a review Event but excludes its target, it MUST preserve
`target_event_id` as an unresolved reference. It must not rewrite the review as a direct property
of another Event.

## 11. Rotation and import contract

### 11.1 Rotation

There is no current primary JSONL rotation implementation. A future rotation is permitted only as
physical segmentation of one logical append-only stream. Segment metadata MUST preserve:

- `chronicle_id`;
- deterministic segment order independent of timestamps and UUIDs;
- continuity with the preceding segment;
- the cutover declaration reference or inherited origin-contract state.

The migration declaration remains one semantic Event. It MUST NOT be duplicated into every
segment. Concatenating authoritative segments in their declared order must reconstruct the same
boundary and Event history.

Compaction, reordering, or deletion is not rotation and cannot be applied to the same
authoritative Chronicle under this contract.

### 11.2 Import and clone

- A full clone or restore that preserves the same `chronicle_id` and byte order preserves the
  original cutover.
- A subset, federation package, or derived export is not automatically an authoritative clone.
- Import into a different `chronicle_id` MUST append a new local declaration after compatible
  writers are active.
- Imported claim/generation attribution SHOULD be preserved when available and linked through
  `SourceProvenance`.
- When imported attribution is unavailable after local cutover, the new Event MUST carry explicit
  unknown values rather than omit origin.
- An imported source cutover Event MUST NOT be treated as the local cutover merely because its
  payload was copied.

## 12. Conformance checks

An implementation claiming this contract must test at least:

- reading pre-cutover Events without origin;
- retaining explicit unknown values after cutover;
- detecting absent and null post-cutover origin without dropping the Event;
- rejecting a declaration whose self ID or Chronicle scope does not match;
- idempotent one-declaration migration;
- cutover behavior for backdated Events;
- old/concurrent writer exclusion;
- byte-preserving backup and restore;
- model-based export preservation or explicit loss warning;
- filtered and reordered subset classification;
- redacted attribution versus missing attribution;
- physical segment reconstruction when rotation is implemented;
- new-Chronicle import behavior;
- separate target-referencing confirmation history.

Passing schema tests is not identity proof, truth proof, authorization proof, or evidence
verification.

## 13. Current implementation gaps

As of 2026-08-28, the accepted contract still requires implementation work:

- add the EventOrigin model and optional `ChronicleEvent.origin` field;
- add Core write validation and a semantic read validator;
- add migration serialization/idempotency support;
- add separate API request-origin and Event-origin mapping;
- preserve origin in exports, GraphRAG text, graph metadata where claimed, and manifests;
- add diagnostics for post-cutover violations;
- add the conformance tests in section 12.

No Chronicle should append the cutover declaration until these prerequisites and every active
writer are ready.
