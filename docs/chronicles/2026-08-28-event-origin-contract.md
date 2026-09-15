# 2026-08-28 - Chronicle Event Origin Contract

Status: Design contract accepted; implementation and cutover pending

## Chronicle Entry

- Date: 2026-08-28
- Task: Define durable claim/generation attribution for Chronicle Events and a safe append-only
  migration boundary.
- Branch: `codex/hotfix-daemon-request-boundary`
- Baseline: `ChronicleEvent.actor` represented the recorder category, API origin represented the
  request initiator, SourceProvenance represented content source, and transport identity remained
  evidence. No Core Event field distinguished human assertion, AI proposal, tool observation, or
  rule-derived output.
- Changed: Added ADR-0105 and the stable `chronicle-event-origin/v1` design contract. The contract
  defines Event origin, a self-ID `metadata_updated` cutover in authoritative JSONL append order,
  legacy/post-cutover interpretation, separate confirmation Events, and fidelity rules for
  exports, subsets, rotation, and import. Corrected the interface compatibility policy so a new
  EventType or optional field is not called round-trip compatible when an old model rejects or
  silently drops it.
- Preserved: JSONL authority, append-only history, legacy bytes, recorder actor, request
  provenance, SourceProvenance, transport evidence, and current target-referencing review history.
- Why: In an append-only Chronicle, absent claim/generation attribution becomes permanent. The
  migration must add future precision without fabricating origin for existing Events.
- Next: Implement the model, Core validator, migration serialization, API mapping, exporter and
  GraphRAG projection behavior, diagnostics, and conformance tests before any Chronicle cutover.
- Re-evaluate when: A writer, MCP transport, agent-runtime adapter, export format, JSONL segment
  rotation, or cross-Chronicle import is implemented against the contract.

## Evidence Reviewed

- `src/chronicle/models/event.py` and `src/chronicle/store/jsonl_store.py`.
- `docs/interface-contracts.md` and `docs/specs/chronicle-event-model-spec-v0.1.md`.
- `src/chronicle/api/contracts.py` and `src/chronicle/api/agent_runtime.py`.
- `src/chronicle/models/source.py`, `src/chronicle/models/transport.py`, and
  `src/chronicle/models/federation_message.py`.
- `src/chronicle/models/review.py` and `src/chronicle/services/review_service.py`.
- Existing Event, interface, storage, export-manifest, package, graph, transport, daemon/API, and
  documentation-governance contracts.

## Compatibility Probe

An executable, temporary-file probe against the current reader established:

```text
parsed_count 2
unknown_origin_present_on_model False
unknown_origin_present_after_reserialize False
raw_store_unchanged_by_read True
known_metadata_updated_parsed metadata_updated
migration_payload_preserved True
new_event_type_rejected ValidationError
```

An actual YAML export probe established:

```text
yaml_has_top_level_origin False
yaml_preserves_migration_payload True
manifest_has_origin_contract False
```

These results support use of the existing `metadata_updated` EventType and prohibit cutover before
old model-based projections are upgraded or marked as lossy.

## Full T-RDE

### Original intent

Make "whose claim is this" durable without allowing origin metadata to become authentication,
authority, truth proof, or a rewrite of old history.

### Preserved

- Current source-of-truth and append-only invariants.
- Existing meanings of recorder actor, API request origin, SourceProvenance, and transport
  identity evidence.
- Current separate review Event lineage.

### Transformed

- Missing origin becomes `legacy_unknown` only before the per-Chronicle declaration and a
  `contract_violation` after it.
- Event ID is a boundary anchor resolved in JSONL append order, not an ordering value.
- Human confirmation preserves AI proposal attribution instead of replacing it.

### Supplemented

- `actor_type`, optional `actor_id`, `assertion_mode`, and optional
  `identity_evidence_ref`.
- Explicit unknown and not-applicable values.
- Export/subset/rotation/import requirements and old-reader limits.
- A verification contract for future implementation.

### Unresolved

- Runtime model and service implementation.
- Writer locking and migration command.
- API and agent-runtime compatibility adapters.
- Export manifest extension and future coordination identifiers.
- Post-cutover origin-correction payload beyond recording a later corrective Event.

### Deviation Risks

- Treating request origin or transport identity as Event attribution without validation.
- Treating `actor_id` as authenticated identity or a capability grant.
- Activating cutover while an old writer or lossy exporter remains active.
- Using timestamp or GraphRAG ordering as the migration boundary.
- Claiming a subset is attribution-complete without boundary state.

### Validation

- Required canon and related ADR/spec documents were read before editing.
- Documentation links and terminology are checked as part of this task.
- No source code, primary Chronicle data, or existing Chronicle entry was rewritten.

### Judgment

`Accept with implementation follow-up`. The design is stable, while runtime conformance and any
actual Chronicle cutover remain explicitly pending.
