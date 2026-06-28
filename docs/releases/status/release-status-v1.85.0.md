# Release Status v1.85.0

- lane: federation phase 5 federation message mvp
- status: implemented
- scope: add preview-only federation message envelope storage plus local inbox/outbox inspection surfaces
- boundary: messages remain local queue files, preview-only, and non-authoritative over Chronicle JSONL; no auto-import, HTTP delivery, or realtime sync is introduced
