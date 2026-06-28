# Smoke Test v1.103

Related: `../readiness/release-readiness-v1.103.md`, `../status/release-status-v1.103.0.md`, `../notes/release-notes-v1.103.0.md`, `../remaining/v1.103-release-remaining-issues.md`

## Commands

- `python -m chronicle.cli federation package verify --package-dir <package_dir> --json`

## Expected

- overview Federation panel shows the manual package-verify CLI template as read-only guidance
- no UI affordance executes package verification or persists package-derived changes automatically
