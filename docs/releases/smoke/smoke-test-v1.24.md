# Chronicle Stack v1.24.0 Smoke Test

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

Expected `v1.24.0` contract additions:

- `/api/package-review` exposes `message_key`
- `/api/package-review` exposes `counts_summary_key`
- `/api/package-review` exposes `boundary_note_key`
