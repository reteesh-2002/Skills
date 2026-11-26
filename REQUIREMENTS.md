# Antigravity Skills Suite: System & Tool Requirements

This document specifies the runtime binaries and host tools used by the **15 Antigravity skills**.

---

## 1. Core System Binaries

| Binary | Minimum Version | Required By Skills | Purpose |
| :--- | :---: | :--- | :--- |
| **`python3`** | $\ge 3.9$ | `scripts/*`, `qa-sentinel`, `deep-debugger`, `schema-craft` | Installer, validator, doctor, anti-retry hook, SQLite checks |
| **`git`** | $\ge 2.30$ | `ship-it`, `deep-debugger`, `code-reviewer` *(optional)* | Diff inspection, Git Assertion Lock (`HEAD` immutability) |
| **`node` & `npm`** | $\ge 18.0$ | `playwright-cli`, `frontend-artisan` *(optional)* | Syntax check (`node -c`), browser automation |
| **`pytest`** | Any | Python test suites *(optional)* | Optional test runner detected by `skills-doctor.py` |
| **`curl`** | Any | `qa-sentinel` *(optional)* | Endpoint health checks |

---

## 2. Browser Automation (`playwright-cli`, Optional)

For headless browser testing and visual viewport verification:

```bash
npm install -g playwright
npx playwright install chromium
```

> [!NOTE]
> On Arch Linux / CachyOS, do **not** pass `--with-deps` (which calls `apt-get`).

---

## 3. Automated Diagnostics (`scripts/skills-doctor.py`)

Run the diagnostic doctor to verify Python, core scripts, hooks, and optional binaries:

```bash
python3 scripts/skills-doctor.py
python3 scripts/skills-doctor.py --project-dir /path/to/your-project --fix
```
