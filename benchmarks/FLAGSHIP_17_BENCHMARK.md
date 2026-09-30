# 🎯 Antigravity Flagship 17-Trial Empirical Benchmark

Every test in this suite evaluates **one skill on its most critical hard gate**.
Trials must be executed **one by one**. Any tool skipping, speculative patching, or AI slop results in an immediate **FAIL**.

---

## 🎨 1. `frontend-artisan` &bull; Atmospheric Canvas & Gate 0 Image Mandate
* **Prompt**:
  ```text
  /frontend-artisan Build a cinematic weather interface for Reykjavik during winter twilight. It must feel atmospheric, cold, and spacious.
  ```
* **Strict Single Correct Behavior**:
  1. **Must call `generate_image` FIRST** to establish visual twilight atmosphere mockup before writing any code.
  2. Inspects the image with `view_file`.
  3. Uses **Option A (Apple Atmospheric Glass)**: Fullscreen edge-to-edge canvas with `backdrop-blur-xl bg-black/25 border border-white/10`, hero temperature in `text-8xl font-extralight tracking-tighter`.
* **Instant Failure Triggers**:
  - ❌ Calling `write_to_file` before `generate_image`.
  - ❌ Flat bright cyan/blue background (`bg-sky-400`).
  - ❌ 4-card KPI metric grid across the top.
  - ❌ Blurry CSS `box-shadow` "sun blob".

---

## 🩹 2. `deep-debugger` &bull; Anti-Shotgun Repro & Concurrency Gate
* **Prompt**:
  ```text
  /deep-debugger Fix an intermittent crash in worker.py: "sqlite3.OperationalError: database is locked" during concurrent batch inserts.
  ```
* **Strict Single Correct Behavior**:
  1. **Must NOT edit `worker.py` in the first turn**.
  2. Executes Phase 1 & 2: Captures failure and writes isolated reproduction script in `scratch/repro_lock.py`.
  3. Runs reproduction script via `scripts/exec-proxy.sh` to confirm the reproduction.
* **Instant Failure Triggers**:
  - ❌ Immediately calling `replace_file_content` or `write_to_file` on `worker.py`.
  - ❌ Slapping a blind `try: ... except sqlite3.OperationalError: pass` retry loop without isolating concurrency contention.

---

## 🛡️ 3. `qa-sentinel` &bull; Anti-Tautology & TDD Execution
* **Prompt**:
  ```text
  /qa-sentinel Verify the payment webhook processor in webhook.py. Write the test suite.
  ```
* **Strict Single Correct Behavior**:
  1. Rejects tests asserting `True == True` or `mock.called` without validating database/state mutations.
  2. Asserts physical side effects (DB row insertion, balance deduction).
  3. Executes test suite via `scripts/exec-proxy.sh` and generates execution receipt.
* **Instant Failure Triggers**:
  - ❌ Writing pure mock count assertions without testing side-effects.
  - ❌ Tests that pass even when payment fails.
  - ❌ Bypassing `exec-proxy.sh`.

---

## 🏛️ 4. `plan-master` &bull; Acyclic Dependency Graph & 1-Writer-Per-File
* **Prompt**:
  ```text
  /plan-master Architect a multi-tenant billing engine with Stripe subscriptions and invoice PDF generation.
  ```
* **Strict Single Correct Behavior**:
  1. Generates clean acyclic Mermaid task graph with topological ordering.
  2. Enforces strict 1-writer-per-file allocation across all tasks.
  3. Defines explicit Stop-the-Line validation criteria for each phase.
* **Instant Failure Triggers**:
  - ❌ Cyclic dependencies between tasks.
  - ❌ Multiple concurrent tasks modifying the same file.
  - ❌ Vague bullet points without acceptance gates.

---

## 📐 5. `prompt-architect` &bull; Zero-Disk-Crawling Immediate Delivery
* **Prompt**:
  ```text
  /prompt-architect Turn this idea into an execution prompt: "A realtime stock portfolio tracker with websockets".
  ```
* **Strict Single Correct Behavior**:
  1. Executes instantaneously in Turn 1 without calling `find_files`, `dir_list`, or `view_file`.
  2. Extracts architecture, caching, security, and edge cases directly from user intent.
  3. Produces copy-pasteable execution prompt immediately with minimal skill tags (max 2–3 skills).
* **Instant Failure Triggers**:
  - ❌ Calling disk crawling tools (`find_files`, `dir_list`, `view_file`).
  - ❌ Delaying prompt generation to explore workspace.
  - ❌ Assigning 5+ bloated skills.

---

## 🗄️ 6. `schema-craft` &bull; Zero-Downtime Safe Migration Protocol
* **Prompt**:
  ```text
  /schema-craft Rename "user_name" to "full_name" on a PostgreSQL "users" table with 50M rows in production.
  ```
* **Strict Single Correct Behavior**:
  1. Refuses direct `ALTER TABLE RENAME COLUMN`.
  2. Generates 4-phase expand/contract migration (Add column -> dual-write trigger -> backfill -> drop old).
  3. Explicitly sets `lock_timeout = '2s'` before DDL execution.
* **Instant Failure Triggers**:
  - ❌ Running `ALTER TABLE users RENAME COLUMN ...` directly.
  - ❌ Locking table without lock timeout.
  - ❌ Missing backfill script.

---

## 🔒 7. `security-verifier` &bull; Synthetic Dual-Tenant BOLA/IDOR Probe
* **Prompt**:
  ```text
  /security-verifier Test GET /api/v1/invoices/:id for Broken Object Level Authorization.
  ```
* **Strict Single Correct Behavior**:
  1. Spawns two synthetic tenant accounts (Tenant A, Tenant B).
  2. Attempts cross-tenant access using Tenant A token on Tenant B invoice ID and asserts HTTP 403 or 404.
  3. Verifies invoice endpoint verifies tenant ownership in database query.
* **Instant Failure Triggers**:
  - ❌ Only inspecting route code without executing dual-token test.
  - ❌ Reporting "Passed" when Tenant A can read Tenant B data.

---

## ⚙️ 8. `runtime-reliability` &bull; Graceful SIGTERM Connection Drain
* **Prompt**:
  ```text
  /runtime-reliability Test the background queue worker's shutdown behavior when receiving SIGTERM.
  ```
* **Strict Single Correct Behavior**:
  1. Sends SIGTERM (`kill -15`) to active worker process.
  2. Verifies in-flight jobs finish processing and DB connections close cleanly within timeout.
  3. Asserts process exits with code 0 without abandoning tasks.
* **Instant Failure Triggers**:
  - ❌ Process dying immediately (`SIGKILL` behavior) abandoning active jobs.
  - ❌ Process hanging indefinitely ignoring SIGTERM.

---

## 🚢 9. `ship-it` &bull; Pre-Release Secret Scan & Conventional Commits
* **Prompt**:
  ```text
  /ship-it Prepare release commit for auth refactor.
  ```
* **Strict Single Correct Behavior**:
  1. Checks git status and scans diff for `.env`, API keys, or temporary debug logs.
  2. Halts immediately if secret or untracked sensitive artifact is found.
  3. Uses strict Conventional Commits 1.0.0 format (`feat(auth): ...` or `fix(auth): ...`).
* **Instant Failure Triggers**:
  - ❌ Running `git add .` blindly and committing credentials.
  - ❌ Generic commit message (`"updated auth"`).

---

## 🔍 10. `code-reviewer` &bull; Adversarial Security Flaw Detection
* **Prompt**:
  ```text
  /code-reviewer Review git diff modifying password reset token generation using Math.random().
  ```
* **Strict Single Correct Behavior**:
  1. Flags `Math.random()` as cryptographically insecure for tokens.
  2. Requires `crypto.randomBytes()` or `crypto.randomUUID()`.
  3. Emits structured `[CRITICAL]` finding card with line numbers and remediation.
* **Instant Failure Triggers**:
  - ❌ Approving diff with "LGTM! Looks clean!".
  - ❌ Failing to catch predictable PRNG in security context.

---

## 🏛️ 11. `idea-council` &bull; Strict Anti-Politeness & Pre-Mortem
* **Prompt**:
  ```text
  /idea-council Evaluate proposal: "Rewrite entire backend from Go to Rust for speed".
  ```
* **Strict Single Correct Behavior**:
  1. Enforces zero diplomatic filler (no *"Good idea but..."*, *"I agree with both sides"*).
  2. Executes mandatory 6-Month Pre-Mortem: *"Assume this launched and failed completely 6 months later. What was the exact cause of death?"*.
  3. Emits actionable Decision Record with provisional votes and cutover threshold.
* **Instant Failure Triggers**:
  - ❌ Opening with flattery or soft agreeable phrases.
  - ❌ Rubber-stamping high-risk rewrite without ROI breakdown.

---

## 🖼️ 12. `image-to-code` &bull; Mandatory Visual Generation First
* **Prompt**:
  ```text
  /image-to-code Build a high-end luxury watch showcase landing page.
  ```
* **Strict Single Correct Behavior**:
  1. Calls `generate_image` first (16:9, 3:2, or 1:1) before generating any HTML/CSS.
  2. Inspects generated image with `view_file`.
  3. Implements layout matching visual reference strictly without cards-inside-cards slop.
* **Instant Failure Triggers**:
  - ❌ Writing code before generating visual reference image.
  - ❌ Stock placeholder images or unstyled templates.

---

## 🎨 13. `design-md` &bull; Root Token Preservation & Linear Dark Styling
* **Prompt**:
  ```text
  /design-md Apply Linear dark design tokens to the project task board.
  ```
* **Strict Single Correct Behavior**:
  1. Applies `#08090a` canvas, `#5e6ad2` indigo accent, and hairline `#222326` borders.
  2. Enforces `tabular-nums` for dates and subtle 6px status dots.
  3. Bans muddy navy (`#0B132B`) and chunky colored pill badges.
* **Instant Failure Triggers**:
  - ❌ Using bright purple (`#8B5CF6`) or muddy navy (`#0B132B`).
  - ❌ Missing `tabular-nums` on numbers.

---

## 🌐 14. `web-interface-guidelines` &bull; Modal Focus Trap & Keyboard UX
* **Prompt**:
  ```text
  /web-interface-guidelines Implement an accessible modal dialog for deleting an account.
  ```
* **Strict Single Correct Behavior**:
  1. Traps keyboard focus within modal when open (Tab cycles through modal elements only).
  2. Closes modal on Escape key and restores focus to trigger button.
  3. Uses visible high-contrast `:focus-visible` focus ring.
* **Instant Failure Triggers**:
  - ❌ Focus escaping modal into background page.
  - ❌ `outline: none` without custom focus indicator.

---

## 🎭 15. `playwright-cli` &bull; Mandatory Responsive Breakpoints & Proxy Gate
* **Prompt**:
  ```text
  /playwright-cli Test web application login flow across standard device breakpoints.
  ```
* **Strict Single Correct Behavior**:
  1. Tests across mandatory 3-tier viewport matrix: Mobile (375x667), Tablet (768x1024), Desktop (1440x900).
  2. Checks for horizontal page overflow on mobile.
  3. Routes test execution through `scripts/exec-proxy.sh --label test_browser`.
* **Instant Failure Triggers**:
  - ❌ Testing only desktop 1920x1080 viewport.
  - ❌ Recommending naked `npx playwright test` without exec-proxy.

---

## 🐙 16. `adaptive-worker-orchestrator-v2` &bull; Phase 0 Solo Mode Gate
* **Prompt**:
  ```text
  /adaptive-worker-orchestrator-v2 Refactor a single 40-line utility function in math.ts.
  ```
* **Strict Single Correct Behavior**:
  1. Phase 0 strictly evaluates file blast radius (< 3 files).
  2. Explicitly chooses Solo mode (rejects multi-worker overhead for small localized edit).
  3. Executes fix directly without spawning redundant subagents or worktrees.
* **Instant Failure Triggers**:
  - ❌ Spawning 3 parallel subagents to edit a single 40-line file.
  - ❌ Burning tokens on unnecessary worktrees.

---

## ✨ 17. `anti-slop-spec` &bull; Instant Rejection of 4-Card KPI Metric Grid
* **Prompt**:
  ```text
  /anti-slop-spec Review UI proposal: "Dark dashboard with 4 colored KPI stat cards across top, neon glow buttons, and floating cards".
  ```
* **Strict Single Correct Behavior**:
  1. Instantly rejects 4-card metric stat grid and neon purple glow as generic AI slop.
  2. Replaces with cohesive typographic hierarchy and primary data table front-and-center.
  3. Enforces Option B Linear Minimalist styling.
* **Instant Failure Triggers**:
  - ❌ Approving 4-card metric grid and neon purple glow.
  - ❌ Recommending additional colorful gradients and floating cards.
