# Chronicle Stack v1.25.0 Smoke Test

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

Expected `v1.25.0` contract additions:

- `/api/runtime-records/<id>` embedded package-review exposes `message_key`
- `/api/runtime-records/<id>` embedded package-review exposes `counts_summary_key`
- `/api/runtime-records/<id>` embedded package-review exposes `boundary_note_key`
- `/api/review-queue/<id>` embedded package-review exposes `message_key`
- `/api/review-queue/<id>` embedded package-review exposes `counts_summary_key`
- `/api/review-queue/<id>` embedded package-review exposes `boundary_note_key`
