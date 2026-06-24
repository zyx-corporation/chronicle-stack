# Chronicle Stack v1.23.0 Smoke Test

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

Expected `v1.23.0` contract additions:

- `/api/ai-index-vector/<id>` exposes `message_key`
- `/api/ai-index-vector/<id>` exposes `counts_summary_key`
- `/api/ai-index-vector/<id>` exposes `boundary_note_key`
- `/api/ai-index-graph-nodes/<id>` exposes `message_key`
- `/api/ai-index-graph-nodes/<id>` exposes `counts_summary_key`
- `/api/ai-index-graph-nodes/<id>` exposes `boundary_note_key`
