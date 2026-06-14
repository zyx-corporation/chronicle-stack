# Chronicle Stack Doctor Security Checks

Status: v0.5 doctor contract  
Related: #68, [ADR-0008](adr/0008-doctor-security-checks.md)

## Purpose

`chronicle doctor` is the read-only project health surface for Chronicle Stack.

In v0.5, doctor also reports security-readiness warnings for classification, model-context use, prompt-injection markers, integrity metadata, audit logs, and lifecycle logs.

Doctor remains an observation tool. It does not repair, mutate, redact, seal, delete, or certify anything.

## Checks

v0.5 security checks include:

| Check ID | Meaning |
|---|---|
| `security_context_classification_present` | Context records should have ClassificationMetadata. |
| `security_layer4_body_storage` | Layer 4 Context body storage is risky. |
| `security_sensitive_context_use_policy` | Sensitive contexts marked for model-context or external use need review. |
| `security_prompt_injection_markers` | Context text contains known instruction-like markers. |
| `security_integrity_metadata_present` | Classified contexts lack integrity hashes. |
| `security_audit_log_parseable` | audit.jsonl is parseable if present. |
| `security_lifecycle_log_parseable` | lifecycle.jsonl is parseable if present. |

## Severity

Doctor uses:

```text
ok
warning
error
```

v0.5 security checks generally produce `warning`, not `error`.

`error` remains reserved for core structural failures such as missing primary files or corrupt primary JSONL.

## Initialized Project Status

A newly initialized Chronicle can report `warning` because v0.5 security metadata and side surfaces may not exist yet.

This does not mean the project is unreadable. It means security readiness is incomplete.

## Boundary

Important:

```text
doctor warning != proof of compromise
doctor ok != security certification
doctor does not mutate records
doctor does not repair records
```

## RDE Review

### Preserved

- Doctor remains read-only.
- Primary JSONL remains authoritative.
- Doctor does not certify correctness or security.

### Transformed

- Doctor becomes the security-readiness observation surface.

### Added

- Classification warnings.
- Layer 4 body-storage warning.
- Context-use policy warnings.
- Prompt-injection marker warnings.
- Integrity metadata warnings.
- Audit/lifecycle side-log parseability checks.

### Unresolved

- Automatic repair.
- Doctor JSON schema versioning.
- Observation E2E integration.
- Release gate thresholds.

### Deviation Risks

- Treating doctor warnings as proof of danger.
- Treating doctor ok as proof of safety.
- Ignoring advisory warnings.
