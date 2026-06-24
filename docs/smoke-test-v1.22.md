# Chronicle Stack v1.22.0 Smoke Test

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

Expected `v1.22.0` contract additions:

- `/api/ai-index-status` exposes `message_key`
- `/api/ai-index-status` exposes `boundary_note_key`
- `/api/ai-index-status` vector payload exposes `counts_summary_key`
- `/api/ai-index-status` graph payload exposes `counts_summary_key`
