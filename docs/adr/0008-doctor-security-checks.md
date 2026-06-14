# ADR-0008: Doctor Security Checks

Status: Accepted  
Date: 2026-06-14  
Scope: Chronicle Stack v0.5 and later  
Related: ADR-0001, ADR-0002, ADR-0004, ADR-0005, ADR-0006, ADR-0007, `docs/doctor-security-checks.md`

## Context

Chronicle Stack v0.5 introduced classification metadata, operation permissions, model-context dry-runs, prompt-injection boundaries, audit logs, lifecycle logs, encrypted store contracts, and integrity metadata preparation.

These surfaces are useful only if they can be observed.

`chronicle doctor` is the primary read-only project health surface. It should therefore expose security-readiness checks without mutating records.

## Decision

Chronicle Stack will extend `chronicle doctor` with v0.5 security checks.

These checks are advisory warnings unless the underlying primary JSONL or required files are structurally broken.

## Security Checks

v0.5 doctor checks include:

```text
security_context_classification_present
security_layer4_body_storage
security_sensitive_context_use_policy
security_prompt_injection_markers
security_integrity_metadata_present
security_audit_log_parseable
security_lifecycle_log_parseable
```

## Severity Boundary

Security checks should prefer warning over error unless the Chronicle is structurally unreadable.

```text
error:
  required primary files are missing or chronicle.jsonl is corrupted

warning:
  security-readiness issue, missing classification, suspicious marker, missing side surface, parseable side-surface issue

ok:
  no detected issue for that check
```

## Non-goals

This ADR does not implement:

- automatic repair
- mutation of records
- policy enforcement
- complete prompt-injection protection
- proof of security
- release certification

## Consequences

### Positive

- Security posture becomes observable.
- v0.5 metadata and surfaces become operationally meaningful.
- CI and issue closure can cite doctor output more consistently.

### Negative / Cost

- Initialized projects may report warning until security metadata is added.
- Some warnings are advisory and require human interpretation.
- False positives are possible for prompt-injection markers.

## RDE Review

### Preserved

- Doctor remains read-only.
- Primary JSONL remains authoritative.
- Doctor pass/warning is not security certification.

### Transformed

- Doctor becomes the primary security-readiness observation surface.

### Added

- Classification metadata checks.
- Layer 4 body-storage warning.
- Sensitive context-use policy warning.
- Prompt-injection marker warning.
- Integrity metadata presence warning.
- Audit/lifecycle side-log parseability checks.

### Unresolved

- Automatic repair.
- Doctor JSON schema versioning.
- Release gate thresholds.
- Observation E2E integration.

### Deviation Risks

- Treating doctor warnings as proof of safety.
- Treating all warnings as blockers.
- Ignoring warnings because they are advisory.
