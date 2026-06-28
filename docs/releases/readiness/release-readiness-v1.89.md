# Release Readiness v1.89

## Checklist

- [x] federation package create writes a local bundle directory without mutating Chronicle primary records
- [x] federation package inspect returns manifest and redaction-report details read-only
- [x] federation package verify recomputes payload file hashes and fails on tampering
- [x] target-node trust preview can be carried into package metadata as advisory context
- [x] unsigned placeholder signatures remain explicit warnings rather than silent assumptions
