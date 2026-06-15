#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${CHRONICLE_STACK_REPO_URL:-https://github.com/zyx-corporation/chronicle-stack.git}"
REF="${CHRONICLE_STACK_REF:-main}"
INSTALL_DIR="${INSTALL_DIR:-${HOME}/.local/share/chronicle-stack}"
BIN_DIR="${BIN_DIR:-${HOME}/.local/bin}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-${INSTALL_DIR}/.venv}"
DRY_RUN="${DRY_RUN:-0}"

COMMANDS=(
  chronicle
  chronicle-context
  chronicle-export
  chronicle-package
  chronicle-graph
)

log() {
  printf '[chronicle-install] %s\n' "$*"
}

run() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '[chronicle-install] dry-run: %q' "$1"
    shift || true
    for arg in "$@"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return 0
  fi
  "$@"
}

need_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf '[chronicle-install] error: required command not found: %s\n' "$1" >&2
    exit 1
  fi
}

ensure_parent_dirs() {
  run mkdir -p "$INSTALL_DIR" "$BIN_DIR"
}

clone_or_update_repo() {
  if [ -d "$INSTALL_DIR/.git" ]; then
    log "Updating existing checkout at $INSTALL_DIR"
    run git -C "$INSTALL_DIR" fetch --tags --prune origin
  elif [ -e "$INSTALL_DIR" ] && [ "$(find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')" != "0" ]; then
    printf '[chronicle-install] error: INSTALL_DIR exists but is not a git checkout: %s\n' "$INSTALL_DIR" >&2
    printf '[chronicle-install] set INSTALL_DIR to a new path or remove the directory.\n' >&2
    exit 1
  else
    log "Cloning $REPO_URL into $INSTALL_DIR"
    run git clone "$REPO_URL" "$INSTALL_DIR"
  fi

  log "Checking out ref: $REF"
  run git -C "$INSTALL_DIR" checkout "$REF"
}

create_venv_and_install() {
  log "Creating virtual environment at $VENV_DIR"
  run "$PYTHON_BIN" -m venv "$VENV_DIR"

  log "Upgrading pip"
  run "$VENV_DIR/bin/python" -m pip install --upgrade pip

  log "Installing Chronicle Stack from local checkout"
  run "$VENV_DIR/bin/python" -m pip install "$INSTALL_DIR"
}

link_commands() {
  log "Linking commands into $BIN_DIR"
  for command_name in "${COMMANDS[@]}"; do
    source_path="$VENV_DIR/bin/$command_name"
    target_path="$BIN_DIR/$command_name"
    if [ ! -e "$source_path" ] && [ "$DRY_RUN" != "1" ]; then
      printf '[chronicle-install] error: expected command not found after install: %s\n' "$source_path" >&2
      exit 1
    fi
    run ln -sfn "$source_path" "$target_path"
  done
}

print_post_install() {
  cat <<EOF

Chronicle Stack local install complete.

Installed checkout:
  $INSTALL_DIR

Command directory:
  $BIN_DIR

Verify:
  $BIN_DIR/chronicle --version
  $BIN_DIR/chronicle --help

If '$BIN_DIR' is not on PATH, add this to your shell profile:
  export PATH="$BIN_DIR:\$PATH"

Installed commands:
  chronicle
  chronicle-context
  chronicle-export
  chronicle-package
  chronicle-graph

Notes:
  - This installer does not install a daemon, service, web server, or HTTP runtime.
  - It does not call external model APIs, GraphRAG engines, vector DBs, or graph DBs.
  - Inspect the script before piping it to bash in production-like environments.
EOF
}

main() {
  log "Chronicle Stack local installer"
  log "Repository: $REPO_URL"
  log "Ref: $REF"
  log "Install dir: $INSTALL_DIR"
  log "Bin dir: $BIN_DIR"

  need_command git
  need_command "$PYTHON_BIN"

  ensure_parent_dirs
  clone_or_update_repo
  create_venv_and_install
  link_commands
  print_post_install
}

main "$@"
