# Chronicle Stack v1.61.0 Release Readiness

Related: `../../adr/0080-local-ui-mutation-session-token-boundary.md`, `../status/release-status-v1.61.0.md`, `../smoke/smoke-test-v1.61.md`

Expected current version baseline:

```text
chronicle 1.61.0
```

This release is ready when browser-triggered review write routes require a per-session mutation token, the route-contract metadata exposes that requirement, and the standard local verification sequence passes.
