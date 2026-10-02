# 📋 Antigravity Skills Suite: System & Tool Requirements

This document specifies the exact environment, runtime binaries, host tools, and shell configurations required to run and verify all 17 Antigravity skills.

---

## ⚡ 1. Core System Binaries

| Binary | Minimum Version | Required By Skills | Purpose |
| :--- | :---: | :--- | :--- |
| **`python3`** | $\ge 3.10$ | `qa-sentinel`, `deep-debugger`, `schema-craft`, `scripts/*` | Script execution, AST verification, sqlite3 testing |
| **`git`** | $\ge 2.30$ | `ship-it`, `adaptive-worker-orchestrator-v2`, `code-reviewer` | Release gate verification, branch/worktree isolation |
| **`bash`** | $\ge 4.0$ | `exec-proxy.sh`, `verify-release-gate.sh` | Deterministic proxy execution and receipt hashing |
| **`node` & `npm`** | $\ge 18.0$ | `playwright-cli`, `web-interface-guidelines`, `frontend-artisan` | Syntax check (`node -c`), browser automation, Tailwind |
| **`curl`** | Any | `qa-sentinel` (with python `urllib` fallback) | Pre-flight endpoint health and latency probes |

---

## 🎭 2. Browser Automation (`playwright-cli`)

For headless browser testing and UI smoke validation:

### A. NPM Global Configuration (No `sudo` Required)
To avoid `EACCES` permission errors on Linux/macOS:
```bash
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
npm install -g playwright
ln -sf ~/.npm-global/bin/playwright ~/.npm-global/bin/playwright-cli
```

### B. Shell Environment Variables
Ensure `~/.npm-global/bin` and `NODE_PATH` are loaded in your shell:

#### **Fish Shell** (`~/.config/fish/conf.d/npm_global.fish`):
```fish
fish_add_path -a $HOME/.npm-global/bin
set -gx NODE_PATH $HOME/.npm-global/lib/node_modules
```

#### **Bash / Zsh** (`~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$HOME/.npm-global/bin:$PATH"
export NODE_PATH="$HOME/.npm-global/lib/node_modules"
```

### C. Headless Browser Engines
Install Chromium for headless testing:
```bash
# Arch Linux / CachyOS / Fedora / macOS:
npx playwright install chromium

# Ubuntu / Debian (system dependencies):
npx playwright install --with-deps chromium
```
> [!NOTE]
> On Arch Linux / CachyOS, do **NOT** pass `--with-deps` (which calls `apt-get`). The Chromium binary runs out of the box with the standard system libraries.

---

## 🤖 3. Antigravity Host Capabilities & Tools

The following tools must be enabled in the Antigravity session settings:

| Antigravity Tool | Required By | Operational Purpose |
| :--- | :--- | :--- |
| **`generate_image`** | `frontend-artisan`, `image-to-code` | **Mandatory Gate 0**: Generates visual layout/color mockups before writing any code. |
| **`view_file`** | All skills | Inspects images, local code, and design tokens (`DESIGN.md`). |
| **`run_command`** | All skills | Executes tests and proxy wrappers via `scripts/exec-proxy.sh`. |
| **`write_to_file`** | Core workflows | Creates production code, tests, and generative UI widgets (`widget.html`). |
| **`replace_file_content`** | `deep-debugger`, refactoring | Surgical edits adhering to the 1-writer-per-file invariant. |

---

## 🔒 4. Execution Discipline (`scripts/exec-proxy.sh`)

All test execution commands must be wrapped by the proxy script to produce physical receipts:
```bash
./scripts/exec-proxy.sh --label <label_name> <command...>
```
* Generates bounded log output in `.evidence/logs/<hash>.log`
* Records cryptographic SHA-256 receipt in `.evidence/manifest.v1.json`
* Fail-closed on missing dependencies or exit codes $\ne 0$

---

## ✅ 5. Verification Checklist

Run this quick command to verify your environment is 100% compliant:

```bash
python3 -c "import sys, sqlite3; print('✅ Python & SQLite3 OK')" && \
node -e "require('playwright'); console.log('✅ Playwright & Node OK')" && \
playwright --version && \
echo "🎉 All Antigravity skill requirements are satisfied!"
```

---

## 🩺 6. Automated Diagnostics (`scripts/skills-doctor.py`)

Run the automated health doctor to verify core host paths, Python version ($\ge 3.9$), runtime helpers (`exec-proxy.sh`, `verify-release-gate.sh`, `runtime_evidence.py`, `task_ledger.py`, `task_shape_gating.py`), and hook configuration (`.agents/hooks.json`):

```bash
# Human-readable diagnostic report:
python3 scripts/skills-doctor.py

# Machine-readable JSON output (for automated CI/CD and subagents):
python3 scripts/skills-doctor.py --json

# Inspect a specific target workspace or project directory:
python3 scripts/skills-doctor.py --project-dir /path/to/project
```

Missing optional tools (`pytest`, `playwright`, `git`, `node`) are reported with graceful degradation as `"Optional: missing"` without failing the core health check (exit code 0). Missing critical helpers or invalid hooks yield exit code 1.

---

## 📦 7. Skills Suite Installation & Manifest Management (`scripts/install-skills.py`)

Install an explicit inventory of all 17 suite skills and runtime helpers, with safe merging of hooks and routing rules and clean manifest tracking (`.skills-install-manifest.json`):

```bash
# Project workspace installation:
python3 scripts/install-skills.py --workspace --target-dir /path/to/project

# Global installation across all Antigravity projects:
python3 scripts/install-skills.py --global

# Clean uninstallation and restoration of pre-existing user configurations:
python3 scripts/install-skills.py --target-dir /path/to/project --uninstall
```

