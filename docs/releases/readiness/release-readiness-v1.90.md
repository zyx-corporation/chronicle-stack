# Release Readiness v1.90

## Checklist

- [x] federation package create can emit unsigned or local-dev signed manifests without mutating Chronicle primary records
- [x] federation package verify distinguishes `unsigned`, `signed`, `mismatch`, `expired`, and `revoked`
- [x] signed verification remains local-first and reviewable rather than implying trust certification
- [x] CLI and service tests cover signed success, tampering, expiration, and revocation
- [x] federation package growth stays preview-only and does not introduce auto-apply or transport behavior
