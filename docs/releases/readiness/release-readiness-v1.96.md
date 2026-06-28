# Release Readiness v1.96

## Checklist

- [x] `review_queue` rows expose `matching_federation_consent_summary` only when consent audit references overlap
- [x] `runtime_records` rows and detail payloads expose the same overlap contract
- [x] overlap summaries stay derived, read-only, and non-authoritative over Chronicle JSONL
- [x] tests cover overlap detection on both review and runtime read models
