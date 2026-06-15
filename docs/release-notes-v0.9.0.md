# Chronicle Stack v0.9.0

Chronicle Stack v0.9.0 is the Release Candidate Hardening and Version Finalization release.

## Highlights

- v0.7 operational workflows:
  - Context classification workflow
  - Audit event workflow
  - Lifecycle marker workflow
  - Doctor remediation guidance
- v0.8 verified package / export review workflow:
  - `chronicle package review`
  - pass / warning / blocked review reports
  - selected Context review
  - persisted package review
- v0.9 release candidate hardening:
  - project version finalized as `0.9.0`
  - v0.9 release readiness documentation
  - v0.9 smoke profile
  - v0.9 deployment procedure

## Verification

Local verification result:

```text
283 passed
```

Expected version:

```text
chronicle 0.9.0
```

## Boundary

This release remains local-first and diagnostic.

It does not introduce:

- server runtime
- daemon runtime
- model API calls
- GraphRAG execution
- vector database dependency
- graph database dependency

## Legal / governance status

- Commercial SaaS License draft exists: `Commercial-SaaS-License.md`
- Contributor license policy draft exists: `docs/contributor-license-policy.md`
- Both are treated as draft completed / counsel review pending.

## Documentation

- `docs/release-readiness-v0.9.md`
- `docs/smoke-test-v0.9.md`
- `docs/release-deployment-v0.9.md`
- `docs/v0.8-package-review-workflow.md`
- `docs/v0.7-operational-hardening-plan.md`
