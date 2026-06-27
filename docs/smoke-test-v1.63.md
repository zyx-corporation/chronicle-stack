# Chronicle Stack v1.63 Smoke Test

## Proposal-first flows

- record artifact proposal with `chronicle artifact propose-update`
- record context proposal with `chronicle context propose-update`
- confirm `/api/proposals` returns both proposal records
- confirm `/api/contexts/<id>` and `/api/artifacts/<id>` expose `proposal_summary`
