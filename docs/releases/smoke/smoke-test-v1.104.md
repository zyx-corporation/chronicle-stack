# Smoke Test v1.104

Related: `../readiness/release-readiness-v1.104.md`, `../status/release-status-v1.104.0.md`, `../notes/release-notes-v1.104.0.md`, `../remaining/v1.104-release-remaining-issues.md`

## Commands

- `python -m chronicle.cli federation package inspect --package-dir <package_dir> --json`
- `python -m chronicle.cli federation package verify --package-dir <package_dir> --json`
- `python -m chronicle.cli federation package preview --package-dir <package_dir> --json`
- `python -m chronicle.cli federation package import-preview --package-dir <package_dir> --json`

## Expected

- overview Federation panel groups package review CLI guidance into a compact read-only line
- no UI affordance executes package commands or persists package-derived changes automatically
