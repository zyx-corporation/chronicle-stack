#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_PATH="${1:-}"
ROOT_DIR="${2:-$PWD}"
PRESERVE_EXISTING="${PRESERVE_EXISTING:-1}"
TIMESTAMP="${CHRONICLE_RESTORE_TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
DRY_RUN="${DRY_RUN:-0}"

log() {
  printf '[chronicle-restore] %s\n' "$*"
}

run() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '[chronicle-restore] dry-run: %q' "$1"
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
  scripts/restore-local.sh ARCHIVE_PATH [ROOT_DIR]

Behavior:
  - restores a .chronicle backup archive into ROOT_DIR
  - preserves the current .chronicle directory by default
  - does not attempt semantic merge or conflict resolution

Environment:
  DRY_RUN=1                     Print commands without executing
  PRESERVE_EXISTING=0           Replace .chronicle without renaming the current one first
  CHRONICLE_RESTORE_TIMESTAMP   Override the UTC suffix used for preserved directories
EOF
}

if [ "$ARCHIVE_PATH" = "--help" ] || [ "$ARCHIVE_PATH" = "-h" ]; then
  usage
  exit 0
fi

if [ -z "$ARCHIVE_PATH" ]; then
  usage >&2
  exit 1
fi

if [ ! -f "$ARCHIVE_PATH" ]; then
  printf '[chronicle-restore] error: archive not found: %s\n' "$ARCHIVE_PATH" >&2
  exit 1
fi

if [ -d "$ROOT_DIR/.chronicle" ] && [ "$PRESERVE_EXISTING" = "1" ]; then
  PRESERVED_PATH="$ROOT_DIR/.chronicle.pre-restore.$TIMESTAMP"
  log "Preserving existing .chronicle as $PRESERVED_PATH"
  run mv "$ROOT_DIR/.chronicle" "$PRESERVED_PATH"
elif [ -d "$ROOT_DIR/.chronicle" ] && [ "$PRESERVE_EXISTING" != "1" ]; then
  log "Replacing existing .chronicle without preservation"
  run rm -rf "$ROOT_DIR/.chronicle"
fi

log "Root dir: $ROOT_DIR"
log "Archive: $ARCHIVE_PATH"

run tar -C "$ROOT_DIR" -xzf "$ARCHIVE_PATH"

if [ "$DRY_RUN" != "1" ]; then
  log "Restore complete"
  printf '%s\n' "$ROOT_DIR/.chronicle"
fi
