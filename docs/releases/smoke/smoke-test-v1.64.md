# Chronicle Stack v1.64 Smoke Test

## Proposal apply flows

- record and approve an artifact proposal, then apply it with `chronicle artifact apply-proposal`
- record and approve a context proposal, then apply it with `chronicle context apply-proposal`
- confirm `/api/proposals` shows `apply_ready` before apply and `applied` after apply
