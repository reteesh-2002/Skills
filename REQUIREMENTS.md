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
