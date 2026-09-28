# Contributing to the Antigravity Skills Suite

Thank you for contributing to the Antigravity Skills Suite! This guide outlines our design principles, quality standards, and automated verification requirements.

---

## 🏛️ Skill Architecture & Layout

Every skill must live in a dedicated top-level directory named in `kebab-case` matching its skill `name`:

```text
<skill-name>/
├── SKILL.md                 # Primary instruction entry point (required)
├── references/              # Extended documentation, standards, or checklists (optional)
├── presets/                 # Reusable configurations, design systems, or templates (optional)
├── scripts/                 # Standalone helper scripts, hooks, or CLI tools (optional)
└── CHANGELOG.md             # Version history and notable changes (recommended)
```

---

## 📝 Frontmatter Specification

Every `SKILL.md` file must begin with YAML frontmatter containing `name` and `description`:

```yaml
---
name: your-skill-name
description: Clear, 1–2 sentence description explaining what the skill does and when the agent should activate it.
---
```

### Frontmatter Rules
1. `name`: Must be lowercase `kebab-case` matching the directory name exactly (e.g. `deep-debugger`, `schema-craft`).
2. `description`: Must be actionable and concise. It is indexed by Antigravity's intent router to determine when the skill should be invoked.

---

## 🔬 Context Budget & Progressive Disclosure

To prevent polluting the model's context window:
1. **Core Prompt Budget**: Target $\le 1,500$ tokens for standard `SKILL.md` bodies.
2. **Progressive Disclosure**: Detailed specifications, multi-framework adapters, and domain reference guides belong in `references/` or `presets/`. Link to them using relative Markdown paths (e.g. `[Tailwind Tokens](references/tokens-tailwind.md)`).
3. **Hard Gates over Soft Suggestions**: If a behavior is mandatory (e.g. TDD, anti-slop banlist), define it as an explicit, step-by-step gate with clear stop-the-line criteria.

---

## 🎨 Zero-Slop Design Principles (UI Skills)

When creating or modifying frontend skills:
1. **Never default to generic AI tropes**:
   - 🚫 No obligatory 4-card metric KPI grids on non-analytics utility pages.
   - 🚫 No muddy navy (`#0B132B`) with glowing neon green (`#00F5A0`) buttons.
   - 🚫 No infinite card-in-card nesting. Use clean 1px hairline dividers and whitespace.
   - 🚫 No pill badge wrappers on raw tabular data.
2. **Generative UI Protocol**: Ensure visual artifacts generate a self-contained `.html` mini-widget embeddable via `<agent-embed>`.

---

## 🧪 Verification & Automated Testing

All contributions must pass the local test and validation suite before submitting:

```bash
# 1. Validate all skill frontmatter, metadata, and relative links
python3 scripts/validate-skills.py

# 2. Run the 27-test runtime conformance and adversarial suite
./scripts/exec-proxy.sh --label test_runtime bash tests/verify_runtime.sh

# 3. Verify the release gate
./scripts/verify-release-gate.sh
```

---

## 📦 Pull Requests & Release Hygiene

1. **Commit Messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
2. **Clean Working Tree**: Ensure no temporary test outputs, debug scripts, or `.evidence/logs` are tracked by git.
3. **Changelog**: When introducing significant capability or protocol updates to a skill, add an entry to `<skill>/CHANGELOG.md`.
