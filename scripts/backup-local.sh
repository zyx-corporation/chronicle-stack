#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$PWD}"
OUTPUT_DIR="${2:-$ROOT_DIR/.chronicle-backups}"
TIMESTAMP="${CHRONICLE_BACKUP_TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
DRY_RUN="${DRY_RUN:-0}"

log() {
  printf '[chronicle-backup] %s\n' "$*"
}

run() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '[chronicle-backup] dry-run: %q' "$1"
    shift || true
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return 0
  fi
  "$@"
}

usage() {
  cat <<'EOF'
Usage:
  scripts/backup-local.sh [ROOT_DIR] [OUTPUT_DIR]

Behavior:
  - archives the local .chronicle directory into OUTPUT_DIR
  - stores a UTC timestamp in the archive name
  - does not mutate Chronicle records

Environment:
  DRY_RUN=1                     Print commands without executing
  CHRONICLE_BACKUP_TIMESTAMP    Override the UTC timestamp suffix
EOF
}

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

if [ ! -d "$ROOT_DIR/.chronicle" ]; then
  printf '[chronicle-backup] error: .chronicle directory not found under %s\n' "$ROOT_DIR" >&2
  exit 1
fi

run mkdir -p "$OUTPUT_DIR"

CHRONICLE_ID="unknown"
if [ -f "$ROOT_DIR/.chronicle/metadata.yaml" ]; then
  CHRONICLE_ID="$(
    awk -F': ' '/^chronicle_id: / {print $2; exit}' "$ROOT_DIR/.chronicle/metadata.yaml" \
      | tr -d '"' \
      | tr -d '\r'
  )"
  CHRONICLE_ID="${CHRONICLE_ID:-unknown}"
fi

ARCHIVE_BASENAME="chronicle-backup-${CHRONICLE_ID}-${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="$OUTPUT_DIR/$ARCHIVE_BASENAME"

log "Root dir: $ROOT_DIR"
log "Output dir: $OUTPUT_DIR"
log "Archive: $ARCHIVE_PATH"

run tar -C "$ROOT_DIR" -czf "$ARCHIVE_PATH" .chronicle

if [ "$DRY_RUN" != "1" ]; then
  log "Backup complete"
  printf '%s\n' "$ARCHIVE_PATH"
fi
