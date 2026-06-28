# Smoke Test v1.101

Related: `../readiness/release-readiness-v1.101.md`, `../status/release-status-v1.101.0.md`, `../notes/release-notes-v1.101.0.md`, `../remaining/v1.101-release-remaining-issues.md`

## Commands

- `python -m chronicle.cli federation package import-preview --package-dir <package_dir> --json`

## Expected

- overview Federation panel shows the manual import-preview CLI template as read-only guidance
- no UI affordance executes package import or persists import results automatically
