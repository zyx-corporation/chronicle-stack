# Chronicle Stack curl-based Local Deployment

Status: v1.4 local deployment guide  
Scope: local CLI installation only

## Purpose

This document describes how to install Chronicle Stack locally using a curl-friendly bootstrap installer.

Chronicle Stack is local-first. This deployment path installs local CLI commands. It does not install a daemon, web server, system service, HTTP runtime, model runtime, GraphRAG engine, vector database, or graph database.

## Safety Boundary

Running shell scripts from `curl | bash` is convenient but risky. Prefer the inspect-first flow when possible.

Recommended:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh -o /tmp/chronicle-install-local.sh
less /tmp/chronicle-install-local.sh
bash /tmp/chronicle-install-local.sh
```

Convenience one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh | bash
```

Pinned ref example:

```bash
CHRONICLE_STACK_REF=v1.3.0 \
  curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh | bash
```

If a tag has not yet been published, use `main` or a known commit SHA:

```bash
CHRONICLE_STACK_REF=main \
  curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh | bash
```

## Requirements

The installer requires:

```text
git
python3 >= 3.11
python3 venv support
```

It does not require `sudo`.

## Default Install Layout

By default the installer uses:

```text
checkout: ~/.local/share/chronicle-stack
venv:     ~/.local/share/chronicle-stack/.venv
commands: ~/.local/bin
```

The installer symlinks these commands into `~/.local/bin`:

```text
chronicle
chronicle-context
chronicle-export
chronicle-package
chronicle-graph
```

Primary CLI aliases are available under `chronicle`:

```bash
chronicle context ...
chronicle package ...
chronicle graph ...
chronicle export profile ...
```

Auxiliary commands remain available for compatibility.

## Configuration

You can override the defaults with environment variables.

| Variable | Default | Purpose |
|---|---|---|
| `CHRONICLE_STACK_REPO_URL` | `https://github.com/zyx-corporation/chronicle-stack.git` | Git repository to clone |
| `CHRONICLE_STACK_REF` | `main` | Branch, tag, or commit SHA to checkout |
| `INSTALL_DIR` | `~/.local/share/chronicle-stack` | Local checkout directory |
| `BIN_DIR` | `~/.local/bin` | Symlink target directory |
| `PYTHON_BIN` | `python3` | Python executable |
| `VENV_DIR` | `$INSTALL_DIR/.venv` | Virtual environment directory |
| `DRY_RUN` | `0` | Print commands without executing when set to `1` |
| `CHRONICLE_STACK_ALLOW_MOVED_TAG` | `1` | Force-refresh a requested local tag from origin when set to `1` |

Example custom install:

```bash
INSTALL_DIR="$HOME/.chronicle-stack/app" \
BIN_DIR="$HOME/bin" \
CHRONICLE_STACK_REF=main \
bash /tmp/chronicle-install-local.sh
```

Dry run:

```bash
DRY_RUN=1 bash /tmp/chronicle-install-local.sh
```

## Moved or Recreated Tags

Release tags should normally be immutable. If a release tag must be corrected, record the reason in the release issue and rerun smoke evidence after correction.

Existing local installer checkouts can retain stale local tag objects. The installer therefore fetches the requested branch/tag explicitly before checkout. For tag refs, the default behavior is to force-refresh the requested local tag from origin:

```text
CHRONICLE_STACK_ALLOW_MOVED_TAG=1
```

To disable that behavior and keep ordinary non-forced tag fetch semantics:

```bash
CHRONICLE_STACK_ALLOW_MOVED_TAG=0 bash /tmp/chronicle-install-local.sh
```

After a corrective retag, verify the installed checkout:

```bash
git -C "$INSTALL_DIR" rev-parse HEAD
git -C "$INSTALL_DIR" rev-parse "$CHRONICLE_STACK_REF"
grep 'version =' "$INSTALL_DIR/pyproject.toml"
chronicle --version
```

For high-confidence release smoke after a retag, a clean install directory is still recommended.

## Verify Install

After install:

```bash
chronicle --version
chronicle --help
chronicle doctor --help
chronicle package --help
chronicle context --help
chronicle graph --help
chronicle export --help
```

If `chronicle` is not found, add the bin directory to `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add that line to your shell profile, such as `~/.zshrc` or `~/.bashrc`, if needed.

## Create a Local Chronicle

```bash
mkdir -p /tmp/chronicle-local-smoke
cd /tmp/chronicle-local-smoke
chronicle init --title "Local Smoke"
chronicle add-context --title "Install Context" --summary "curl local deploy smoke" --scope task --visibility private
chronicle doctor
chronicle export --format yaml
```

## Upgrade

Run the installer again.

```bash
curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh | bash
```

For a pinned release:

```bash
CHRONICLE_STACK_REF=v1.3.0 \
  curl -fsSL https://raw.githubusercontent.com/zyx-corporation/chronicle-stack/main/scripts/install-local.sh | bash
```

The installer fetches the requested branch/tag ref, checks it out, recreates or refreshes the virtual environment, reinstalls the package, and refreshes command symlinks.

## Uninstall

Default uninstall:

```bash
rm -rf "$HOME/.local/share/chronicle-stack"
rm -f "$HOME/.local/bin/chronicle"
rm -f "$HOME/.local/bin/chronicle-context"
rm -f "$HOME/.local/bin/chronicle-export"
rm -f "$HOME/.local/bin/chronicle-package"
rm -f "$HOME/.local/bin/chronicle-graph"
```

This removes the installed application checkout and command symlinks. It does not remove Chronicle project data you created elsewhere, such as `.chronicle/` directories inside your projects.

## Non-goals

This deployment path does not:

- install a server
- install a daemon
- install a systemd service
- install a web UI
- install an HTTP bridge
- install GraphRAG, vector DB, or graph DB services
- call external model APIs
- provide security certification
- provide access-control enforcement
- perform physical deletion or lifecycle enforcement

## RDE Review

### Preserved

- Chronicle Stack remains local-first.
- CLI commands remain local user commands.
- No external model/runtime/GraphRAG service is introduced.
- Auxiliary CLI compatibility remains available.

### Transformed

- Local installation becomes more robust against stale local tags after exceptional release correction.
- Release deployment remains inspect-first while recording moved-tag risk explicitly.

### Complemented

- The installer supports pinned refs for repeatable release installation.
- The documentation distinguishes inspect-first usage from convenience `curl | bash` usage.
- Corrective retag behavior is made explicit instead of hidden in release operator memory.

### Deviation Risks

- Do not imply `curl | bash` is risk-free.
- Do not imply local install is a server deployment.
- Do not imply the installer provides security, sandboxing, or access control.
- Do not treat installation success as semantic correctness certification.
- Do not normalize moving release tags; it remains exceptional and should be evidence-recorded.
