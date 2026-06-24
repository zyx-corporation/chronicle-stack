# Chronicle Stack v1.21.0 Smoke Test

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

Expected `v1.21.0` contract additions:

- `/api/graph-summary` exposes `message_key`
- `/api/graph-summary` exposes `counts_summary_key`
- `/api/graph-summary` exposes `boundary_note_key`
- overview graph-summary payload preserves the same structured contract fields
