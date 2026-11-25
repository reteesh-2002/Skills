---
name: playwright-cli
description: Automate browser interactions, test web pages and work with Playwright tests.
---

# Browser Automation with Playwright

Automate browser interactions, perform responsive visual verifications, inspect snapshots, and execute end-to-end tests.

---

## 1. Package Entrypoint & Installation

Playwright commands can be executed using either the global/local `playwright-cli` executable or standard `npx playwright`:

```bash
# Verify available entrypoint
which playwright-cli || which playwright || npx playwright --version

# When playwright-cli binary is available in PATH:
playwright-cli <command>

# When using local project dependencies:
npx playwright <command>
```

To install Playwright in a project if not already present:
```bash
npm install -D @playwright/test
npx playwright install --with-deps
```

---

## 2. Core Workflow & Quick Start

```bash
# 1. Open browser session and navigate to target URL
playwright-cli open https://localhost:3000

# 2. Capture accessibility and DOM snapshot
playwright-cli snapshot

# 3. Target elements using snapshot refs (e.g. e15) or CSS selectors
playwright-cli fill e5 "user@example.com" --submit
playwright-cli click e15

# 4. Capture screenshot for visual inspection
playwright-cli screenshot --filename=verification.png

# 5. Cleanly close browser session
playwright-cli close
```

---

## 3. Essential Commands

### Navigation & Viewports
```bash
playwright-cli open <url>
playwright-cli goto <url>
playwright-cli reload
playwright-cli resize 1440 900   # Desktop viewport
playwright-cli resize 375 667    # Mobile viewport
playwright-cli close
```

### Interactions
```bash
playwright-cli click <ref-or-selector>
playwright-cli fill <ref-or-selector> "text" [--submit]
playwright-cli type "text"
playwright-cli press Enter
playwright-cli hover <ref-or-selector>
playwright-cli select <ref-or-selector> "value"
playwright-cli check <ref-or-selector>
```

### Snapshot & Evaluation
```bash
playwright-cli snapshot
playwright-cli find "Submit Order"
playwright-cli eval "document.title"
playwright-cli eval "el => el.getBoundingClientRect().height" <ref>
```

### Screenshots
```bash
playwright-cli screenshot --filename=desktop.png
playwright-cli screenshot <ref> --filename=component.png
```

---

## 4. Visual & Accessibility Verifications

Use Playwright to execute concrete checks against interface standards:

1. **Touch Target Size (≥44px Mobile, ≥24px Desktop)**:
   ```bash
   playwright-cli eval "el => { const r = el.getBoundingClientRect(); return { w: r.width, h: r.height }; }" <ref>
   ```
2. **Mobile Input Font Size (≥16px)**:
   ```bash
   playwright-cli eval "el => window.getComputedStyle(el).fontSize" <ref>
   ```
3. **Focus Visible Outline**:
   ```bash
   playwright-cli press Tab
   playwright-cli eval "el => window.getComputedStyle(document.activeElement).outlineStyle"
   ```
4. **Horizontal Overflow Check**:
   ```bash
   playwright-cli eval "document.documentElement.scrollWidth <= window.innerWidth"
   ```

---

## 5. On-Demand Advanced References

Advanced flows and specialized workflows are documented in modular reference files:

- **Browser Sessions & Profiles**: [references/session-management.md](references/session-management.md)
- **Storage State (Cookies & LocalStorage)**: [references/storage-state.md](references/storage-state.md)
- **Tracing & Diagnostics**: [references/tracing.md](references/tracing.md)
- **Video Recording**: [references/video-recording.md](references/video-recording.md)
- **Request Interception & Mocking**: [references/request-mocking.md](references/request-mocking.md)
- **Running Playwright Code & Scripts**: [references/running-code.md](references/running-code.md)
- **Inspecting Element Attributes**: [references/element-attributes.md](references/element-attributes.md)
- **Playwright Test Runner & E2E**: [references/playwright-tests.md](references/playwright-tests.md)
- **Test Generation (Plan / Generate / Heal)**: [references/test-generation.md](references/test-generation.md)
- **PR Attachments with `gh`**: [references/pr-attachments.md](references/pr-attachments.md)

---

## 6. Session Ownership & Evidence Summary

Follow [`references/output-policy.md`](../references/output-policy.md):

- **Task-Owned Session Identity**: Use unique session flags (e.g. `--session=task_<id>`). When closing, close only task-owned sessions; **never execute broad killall commands or terminate unrelated browser processes**.
- **Functional Assertions vs. Screenshots**: A screenshot alone does **not** count as a functional assertion. Functional assertions must check DOM state, computed styles, text values, or network responses.
- **Unavailable Browser Disclosure**: If Playwright or browser binaries are missing, report status as `UNVERIFIED (browser unavailable)` rather than fabricating a pass.

### Evidence Summary Format:
```markdown
### 🎭 Playwright Verification: [Target Page / Component]
* **Session**: `task_[id]` (isolated session closed cleanly)
* **Assertions Executed**: [N] checks (e.g. input font-size >= 16px, focus-visible outline, scrollWidth <= innerWidth)
* **Viewports Tested**: Mobile 375x667, Desktop 1440x900
* **Console / Network**: 0 console errors, 0 unhandled 5xx failures
* **Captured Artifacts**: `[screenshot_path.png]`
```

