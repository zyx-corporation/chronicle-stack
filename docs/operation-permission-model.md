# Chronicle Stack Operation Permission Model

Status: v0.5 advisory model  
Related: #62, [ADR-0001](adr/0001-context-assets-security.md), [Security Policy v0.1](security-policy-v0.1.md)

## Purpose

The Operation Permission Model defines what kind of operation a human, tool, agent, or future integration intends to perform with a Chronicle record.

It exists because Chronicle Stack records are context assets, not merely documents.

The central rule is:

```text
Being allowed to view a record does not imply being allowed to export it, inject it into model context, reinterpret it, or publish it.
```

## Advisory Boundary

In v0.5 this model is advisory metadata.

It does not implement:

- access control
- authentication
- authorization
- encryption
- tenant isolation
- policy-engine enforcement

It provides a stable vocabulary for later checks, doctor warnings, export profiles, and model-context use dry-runs.

## Operations

| Operation | Meaning |
|---|---|
| `view` | Read or display the record for a human or local tool. |
| `create` | Create a new record. |
| `edit` | Modify an existing record. |
| `append` | Add a new event, version, note, or continuation without silently rewriting the past. |
| `summarize` | Produce a lower-detail summary from the record. |
| `reinterpret` | Produce a later interpretation, critique, or RDE review from the record. |
| `redact` | Remove or mask sensitive portions while preserving a safer derived record. |
| `seal` | Remove a record from ordinary access while preserving a tombstone or governance trace. |
| `export` | Write the record or derived data to an external file or package. |
| `inject` | Use the record as model context. |
| `publish` | Make the record or derived content externally public. |

## Operation Categories

### Read-like

```text
view
summarize
```

Read-like operations do not necessarily leave the local Chronicle boundary, but they may still reveal context to a human or tool.

### Mutation-like

```text
create
edit
append
redact
seal
```

Mutation-like operations alter Chronicle state or lifecycle. They require careful provenance handling.

### Derived meaning

```text
reinterpret
```

Reinterpretation creates later meaning. It must not be confused with the original intent of the record.

### Disclosure-like

```text
export
inject
publish
```

Disclosure-like operations are higher risk.

They may move context outside the original Chronicle boundary or into another processing surface.

## View vs Export vs Inject vs Publish

These operations must remain distinct.

```text
view:
  A record can be read.

export:
  A record or derived form can be written outside the Chronicle store.

inject:
  A record can be used as model context.

publish:
  A record or derived form can be made public.
```

A record may be viewable but not exportable.  
A record may be exportable for internal review but not publishable.  
A record may be summarizable but not usable as external model context.

## Default Classification Behavior

`ClassificationMetadata.allowed_operations` defaults to:

```text
view
summarize
reinterpret
```

For Layer 4 / Restricted Secret records, the model narrows default operations to:

```text
view
```

and marks model-context use as not allowed by default.

This remains advisory and does not replace secret management.

## Relationship to VisibilityHint

`VisibilityHint` remains a broad hint such as `public`, `private`, `sensitive`, or `unknown`.

The Operation Permission Model is more specific. It describes permitted operation categories, not merely visibility.

Neither one is access control by itself.

## Relationship to Future Work

This model prepares later work:

- #63 Model Context Use Policy and Dry-run Check
- #65 Audit Log for Export / Context Use / Reinterpretation
- #68 Doctor Security Checks
- #69 Security-aware Export Profiles
- #70 Controlled CSG-RAG / Sayane Integration Contracts

## RDE Review

### Preserved

- JSONL remains primary.
- Classification metadata remains optional.
- VisibilityHint remains backward-compatible.
- No runtime access control is introduced.

### Transformed

- Chronicle records now have a vocabulary for action-level risk separation.

### Added

- Full v0.5 operation vocabulary.
- Read-like / mutation-like / derived-meaning / disclosure-like categories.
- Explicit distinction between view, export, inject, and publish.

### Unresolved

- Enforcement policy.
- CLI behavior when an operation is disallowed.
- Warning vs blocking classification.
- Actor identity model.

### Deviation Risks

- Treating allowed operations as actual permission enforcement.
- Conflating export with publish.
- Conflating view with model-context use.
- Creating operation metadata that is too complex for users to maintain.
