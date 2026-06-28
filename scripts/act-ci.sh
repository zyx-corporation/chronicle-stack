#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKFLOW_FILE="${CHRONICLE_ACT_WORKFLOW:-$ROOT_DIR/.act/workflows/ci.yml}"
EVENT_NAME="${CHRONICLE_ACT_EVENT:-workflow_dispatch}"

if ! command -v act >/dev/null 2>&1; then
  cat >&2 <<'MSG'
error: act is not installed.

Install act first, then rerun this script.
See: https://github.com/nektos/act
MSG
  exit 127
fi

if [ ! -f "$WORKFLOW_FILE" ]; then
  echo "error: act workflow not found: $WORKFLOW_FILE" >&2
  exit 1
fi

cd "$ROOT_DIR"
exec act "$EVENT_NAME" \
  --workflows "$WORKFLOW_FILE" \
  --container-architecture linux/amd64 \
  "$@"
