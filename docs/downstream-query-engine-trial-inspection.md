# Downstream Query-Engine Trial Inspection

Use these read-only commands to inspect recorded downstream trial outcomes.

## List recorded trials

```bash
chronicle package query-engine-trial-list
chronicle package query-engine-trial-list --json
```

## Show one recorded trial

```bash
chronicle package query-engine-trial-show --event evt_xxx
chronicle package query-engine-trial-show --event evt_xxx --json
```

## Boundary

- read-only inspection only
- no downstream import execution
- no hosted query execution
- no mutation of Chronicle primary records beyond the separately explicit trial-record command
