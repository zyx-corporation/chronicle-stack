# Chronicle Stack v1.20.0 Smoke Test

Run from the repository root:

```bash
chronicle ui-smoke
chronicle ui-smoke --json
```

Expected boundary:

- read-only
- no server
- no browser
- no external runtime

Expected `v1.20.0` contract additions:

- runtime-record detail retrieval-handoff payloads expose `message_key`
- runtime-record detail retrieval-handoff payloads expose `hit_counts_summary_key`
- runtime-record detail invocation-plan payloads expose `message_key`
- runtime-record detail invocation-plan payloads expose `provider_summary_key`
