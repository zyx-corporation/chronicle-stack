# ADR-0105: Chronicle Event Origin Attribution and Cutover Contract

Status: Accepted  
Date: 2026-08-28  
Scope: Chronicle Event attribution, backward-compatible migration, review lineage, and handoff
surfaces  
Related: ADR-0035, ADR-0084, ADR-0099, ADR-0100, ADR-0101, ADR-0102, ADR-0103,
ADR-0104, `docs/specs/chronicle-event-origin-contract-v1.md`

## Context

`ChronicleEvent.actor` records which Chronicle-side role wrote an Event. It does not reliably
answer whose assertion, proposal, observation, or derived result the Event contains. The current
API also has `ApiOriginMetadata`, but that object identifies the initiator of an API request and
is explicitly neither identity proof nor an authorization grant. `SourceProvenance` records where
content came from, while transport identity remains evidence under ADR-0035.

These are different questions. Reusing any one of them for all attribution would make a recorded
AI proposal indistinguishable from a human assertion, or turn untrusted transport evidence into a
Chronicle actor. In an append-only record, failing to preserve this distinction at write time is
not repairable by later in-place editing.

Existing Chronicles also contain Events with no claim/generation attribution. A migration must
preserve those bytes, distinguish legacy absence from a new write defect, and remain readable by
the current EventType enum. It must not use timestamps, UUID ordering, or a derived GraphRAG order
as a substitute for authoritative append order.

## Decision

### Event origin is a separate semantic axis

Chronicle will define `ChronicleEvent.origin` as claim/generation attribution. It answers:

```text
Whose assertion, proposal, observation, or rule-derived result does this Event represent?
```

It is separate from:

- `ChronicleEvent.actor`: the Chronicle-side recorder role;
- `ApiOriginMetadata`: the initiator and request provenance at the API boundary;
- `SourceProvenance`: where content was captured, generated, or imported from;
- transport identity evidence: an untrusted or separately verified evidence record;
- authentication, authorization, capability grants, and reviewer-session proof.

Adapters must map these axes explicitly. They must not infer Event origin from an API caller,
transport display name, capability id, or `source` field merely because those values are present.

### Event origin schema

The stable `chronicle-event-origin/v1` object contains:

```text
actor_type
actor_id                optional
assertion_mode
identity_evidence_ref   optional
```

`actor_type` values are:

```text
human / ai / tool / system / unknown
```

`assertion_mode` values are:

```text
human_assertion / ai_proposal / tool_observation / rule_derived /
not_applicable / unknown
```

`unknown` is a deliberate value for an attribution or classification that cannot be established.
`not_applicable` means the Event has been assessed and does not express a claim/generation mode;
it is not a synonym for missing data.

`actor_id` is an attribution identifier, not proof of identity. `identity_evidence_ref` points to
separately retained evidence and must not embed credentials or secret-bearing transport metadata.
The origin object is an Event-local snapshot even when its evidence reference cannot be resolved.

The model field remains optional for backward reading. After the cutover described below, new
writes must supply a non-null origin object; an explicit `unknown` value is valid, but an absent or
null object is not.

### Append-only cutover

Each Chronicle adopts the contract with exactly one `metadata_updated` Event. The payload uses the
Event's own pre-generated `event_id` as the boundary anchor:

```json
{
  "event_origin_contract": {
    "contract_version": "chronicle-event-origin/v1",
    "scope_chronicle_id": "chr_...",
    "boundary_basis": "authoritative_jsonl_append_order",
    "effective_after_event_id": "evt_<this-event>",
    "pre_cutover_missing_origin": "legacy_unknown",
    "post_cutover_missing_origin": "contract_violation"
  }
}
```

The declaration Event belongs to the outer Event's `chronicle_id`; the payload value must match
it, and `effective_after_event_id` must equal the outer Event's `event_id`. `parent_event_id` must
not point to the declaration itself.

The anchor is resolved by physical order in the authoritative JSONL stream for that Chronicle:

- missing origin before or on the declaration Event is `legacy_unknown`;
- missing or null origin after the declaration Event is `contract_violation`;
- an explicit post-cutover origin using `unknown` remains valid.

Neither a timestamp comparison nor lexical/numeric comparison of Event IDs may determine the
boundary. A GraphRAG, timeline, index, or export ordering is derived and may differ from JSONL
append order.

The migration does not rewrite legacy Events. Cutover must quiesce or serialize every active
writer, append the declaration, activate origin-required validation, and resume only compatible
writers. An old writer that can still append after cutover is incompatible. A post-cutover
violation remains readable evidence; it must not be silently reclassified as legacy or skipped as
corrupt solely because origin is missing.

### Compatibility choice

The declaration uses the existing `metadata_updated` EventType. A new declaration-specific
EventType is rejected because current readers validate EventType as a closed enum and may skip an
unknown value as a corrupt line.

The current Pydantic Event reader accepts but discards an unknown top-level `origin` field. A raw
read leaves JSONL bytes unchanged, but model reserialization and current model-based exports lose
that field. Therefore reader compatibility is forward-tolerant, not round-trip compatible. The
implementation must update Core readers, writers, validators, exporters, indexes, and adapters
before any Chronicle is cut over.

### Confirmation remains a separate Event

Human confirmation, rejection, or request for changes must append a review Event that identifies
the target with `target_event_id`; it should also use `parent_event_id` for the target Event. It
must not add or mutate `confirmed_by` on the target Event, and it does not replace the target's
origin.

Thus an AI proposal remains attributed as an AI proposal after a human approves it. The human
review Event separately records who made the disposition. Review approval is a workflow judgment,
not proof that the target statement is true. Epistemic verification, where needed, remains a
separate assertion or verification record.

Existing `note_added` Events with `payload.review_decision=true` and `target_event_id` remain
readable. Any future migration to the reserved `review_decision_recorded` EventType must preserve
that legacy review history.

### Envelope and coordination vocabulary

Event origin is embedded in the primary Event and may be reused as a shared attribution vocabulary
by API, agent-runtime, transport, or federation envelopes. Envelope metadata is not a substitute
for the Event-local snapshot.

This decision does not introduce `correlation_id` or `causation_id`. Current `message_id`,
`request_id`, and `parent_event_id` have distinct meanings and must not be renamed or treated as
synonyms without a separate coordination-envelope contract.

### Export, subset, rotation, and import

- A byte-preserving full JSONL copy or backup retains origin, declaration, and append order.
- A model-based export that claims Event-origin fidelity must retain `origin` and carry the
  contract version, source `chronicle_id`, cutover Event ID, boundary basis, and any omission or
  redaction warning in its manifest.
- A filtered, reordered, or partial Event subset must preserve original append order and the
  declaration, or materialize enough per-record boundary state to distinguish `legacy_unknown`
  from `contract_violation`.
- A derived surface that does not project Event origin must say so. It must not imply that absent
  origin means a human assertion.
- Redaction may omit `actor_id` or `identity_evidence_ref`, but must preserve the distinction
  between redacted origin and missing origin.
- A future physical JSONL rotation must preserve one ordered logical stream per `chronicle_id`.
  It must not duplicate the semantic cutover Event in each segment.
- A full restore that retains `chronicle_id` and byte order retains the original boundary. Import
  into a different Chronicle requires a new local cutover declaration; the imported source
  declaration does not become authority for the new `chronicle_id`.
- Missing attribution imported after a local cutover must be represented explicitly with
  `actor_type=unknown` and `assertion_mode=unknown`, not by omitting origin.

The normative details are fixed in
`docs/specs/chronicle-event-origin-contract-v1.md`.

## Alternatives

### Reuse `ChronicleEvent.actor`

Rejected. It would collapse recorder role and claim/generation attribution and cannot represent
an importer recording a human assertion or a tool recording an AI proposal.

### Persist only API or agent-runtime origin

Rejected. CLI, import, transport, and future MCP writes must produce the same Core semantics, and
the primary Event must remain self-contained when envelope data is unavailable.

### Rewrite legacy Events with inferred origin

Rejected. It violates append-only history and would turn guesses based on old actor/source values
into apparently original facts.

### Use a timestamp or Event ID comparison as the cutover

Rejected. UUID4 Event IDs are not ordered, and imported/backdated timestamps need not be monotonic
with append order.

### Add a new migration EventType immediately

Rejected. Current readers reject unknown enum values, while `metadata_updated` already provides a
compatible structured payload carrier.

### Mutate the target when it is confirmed

Rejected. It would erase the distinction between original attribution and later review and would
violate append-only reconstruction.

## Consequences

### Positive

- Human assertions, AI proposals, tool observations, and rule-derived output become explicitly
  distinguishable.
- Legacy absence and post-cutover defects have different, reconstructable meanings.
- HTTP, future MCP, CLI, import, and agent-runtime paths can converge on one Core attribution
  contract without sharing transport authentication logic.
- Human review preserves rather than overwrites AI attribution.

### Negative / Cost

- Every active writer and model-based projection must be upgraded before cutover.
- Export and subset manifests require additional fidelity metadata.
- Actor identifiers and evidence references add disclosure and redaction considerations.
- A safe migration needs writer serialization that the current JSONL store does not provide.

## Implementation Status and Verification Contract

This ADR accepts the design contract; it does not claim runtime implementation. At acceptance:

- `ChronicleEvent` has no `origin` field;
- API request origin is not persisted as Event claim/generation origin;
- current model-based exports do not preserve an unknown top-level origin field;
- there is no cutover command, write lock, semantic validator, or JSONL rotation implementation;
- review decisions are already appended as separate target-referencing Events.

Future implementation tests must cover legacy reading, self-ID declaration validation,
same-Chronicle append-order classification, backdated Events, old-writer rejection, explicit
unknown values, export/subset fidelity, redaction, import, and separate confirmation history.

## Full T-RDE

### Preserved

- JSONL authority, Event self-containment, append-only correction, and reconstructability.
- Existing recorder actor, API request provenance, SourceProvenance, transport evidence, and
  review history as distinct surfaces.
- Derived exports and GraphRAG ordering remain non-authoritative.

### Transformed

- "Who recorded this" is no longer treated as sufficient attribution for "whose claim this is."
- Missing origin changes from one undifferentiated absence into legacy unknown before cutover and
  a contract violation after cutover.
- Review acceptance is explicitly modeled as a later Event rather than target mutation.

### Supplemented

- Stable Event origin vocabulary.
- Append-order migration declaration and old-reader compatibility rule.
- Export, subset, rotation, import, and redaction requirements.
- An explicit implementation-readiness boundary.

### Unresolved

- Concrete Pydantic models, service validation, writer locking, migration command, and diagnostics.
- API request/event-origin mapping and AgentRecordOriginKind compatibility adapters.
- Export manifest schema and shared future coordination-envelope vocabulary.
- Correction payload for a post-cutover attribution violation.

### Deviation Risks

- Treating `actor_id` or identity evidence as authentication or authority.
- Inferring legacy origin from `actor`, API caller, source tool, or transport identity.
- Activating the declaration before all writers and projections are compatible.
- Using timestamp-sorted GraphRAG state to interpret the cutover.
- Dropping origin in a derived export without an explicit loss warning.

### Judgment

`Accept with implementation follow-up`. The attribution and migration semantics are stable; no
Chronicle should be cut over until the implementation and verification contract is satisfied.
