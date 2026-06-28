# Chronicle Stack v1.26.0 Smoke Test

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

Expected `v1.26.0` contract additions:

- `/api/review-queue` package readiness summary exposes `label_key`
- `/api/review-queue` package readiness summary exposes `message_key`
- `/api/review-queue` package readiness summary exposes `message_template_key`
