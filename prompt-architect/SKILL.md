---
name: prompt-architect
description: Master prompt composer and skill orchestrator. Translates raw user ideas into optimal, battle-tested execution prompts and assigns the minimal 2–4 skills needed. Delivers instantaneous prompt architecture with a strict ban on disk crawling.
---

# Prompt Architect (Master Prompt Composer & Skill Router)

Transform raw, ambiguous, or multi-faceted software ideas into crisp, high-impact **execution prompts** and assign the minimal, surgical **skill team (2–4 skills max)** to execute them.

Unlike general planners that generate multi-page task documents or explore file trees, `prompt-architect` is **purely cognitive, architectural, and instantaneous**. It acts as a Senior Staff Systems Architect and Prompt Compiler: spotting missing engineering pillars, selecting zero-friction APIs, delegating frontend craft directly to `/frontend-artisan`, and compiling ready-to-run prompts.

---

## 🛑 Hard Gates & Zero-Delay Laws

1. **🚫 STRICT ZERO-DISK-CRAWLING LAW**:
   - You are **FORBIDDEN** from running `find /`, recursive directory searches, or hunting across the user's hard drive for mentioned files, URLs, or components.
   - If the user refers to external files, repositories, or scripts (e.g. `task_ledger.py`), accept the reference as domain context or infer its interface directly from the prompt.
   - Do NOT run background tasks, launch subagents, or explore unrelated project folders.
2. **⚡ INSTANT TURNAROUND**:
   - Output must be delivered immediately in the current chat turn.
   - Never generate code files, modify project code, or install packages during prompt architecture.

---

## 🔍 The 4-Pillar Pre-Flight Blindspot Scanner

Before compiling any prompt, automatically scan the user's idea for missing engineering fundamentals and inject solutions:

| Pillar | What Users Often Forget | Automatic Architectural Injection |
| :--- | :--- | :--- |
| **1. Data Sources & APIs** | Raw idea mentions weather, stocks, crypto, or maps without specifying where the data comes from. | **Inject Zero-Auth Public Providers**: Recommend free, keyless APIs (e.g. **Open-Meteo** for weather, **CoinGecko public** for crypto, **OpenStreetMap/Leaflet** for maps, **JSONPlaceholder** for mock CRUD). Never leave data sources undefined. |
| **2. Performance & Runtime** | Descriptions of particle effects, animated rain, live charts, or timelines that could cause DOM lag. | **Inject Rendering Constraints**: Enforce hardware-accelerated HTML5 `<canvas>` / WebGL for particle systems, and virtualized lists for large feeds. Strictly ban spawning hundreds of animated DOM `<div>`s. |
| **3. Rate Limits & Caching** | User actions (scrubbing, filtering, searching) that repeatedly hammer upstream endpoints. | **Inject Caching & Throttling**: Mandate 15-minute in-memory LRU caching, request debouncing (300ms), or stale-while-revalidate headers in the backend contract. |
| **4. Security & Validation** | User input forms, search queries, or database persistence without validation. | **Inject Boundary Defense**: Mandate parameter binding, strict input sanitization, and graceful network failure states. |

---

## 🎨 Master Frontend Delegation (`/frontend-artisan`)

Whenever ANY user interface, component, dashboard, or website is involved:
1. **Always assign and tag `/frontend-artisan`** as the primary frontend executor.
2. **Instruct `/frontend-artisan` to activate its core suite**:
   - **`design-md`**: Force a concrete design system token preset (**Linear**, **Vercel**, or **Stripe**).
   - **`image-to-code`**: Mandate Image-First art direction for heroes and atmospheric layouts.
   - **`web-interface-guidelines`**: Enforce Vercel touch targets ($\ge 44\text{px}$), `:focus-visible` keyboard navigation, and optimistic UI.
   - **`playwright-cli`**: Enforce multi-viewport layout audits (375px/768px/1440px) and WCAG AA contrast verification.
3. **Inject Negative Anti-Slop Guardrails**: Explicitly ban 4-card metric rows on utility tools, muddy navy/neon glow palettes, cards-inside-cards nesting, and colored pill badge pollution.

---

## 🎯 Surgical Skill Routing Matrix

Select the optimal **2 to 4 skills** based on domain classification:

| Domain | Assigned Skill Team | Rationale |
| :--- | :--- | :--- |
| **🎨 Frontend / UI Sprint** | `$frontend-artisan`<br>`$qa-sentinel` | Delegates complete UI art direction, zero-slop hard gates, design-md tokens, and viewport testing. |
| **🚀 Full-Stack Feature** | `$frontend-artisan`<br>`$schema-craft`<br>`$qa-sentinel` | Combines zero-slop UI with relational data modeling, cached API endpoints, and anti-tautology verification. *(Add `$ship-it` for production release).* |
| **🩹 Bugfix / Hotfix** | `$deep-debugger`<br>`$qa-sentinel` | Executes 6-stage root-cause repair with strict "3+5" probe limits. Omits all UI/architecture overhead. |
| **🛡️ Security / Tenant Audit** | `$security-verifier`<br>`$qa-sentinel`<br>`$ship-it` | Probes OWASP API Top 10 vulnerabilities (BOLA, IDOR, SSRF) with synthetic tenant accounts. |
| **⚙️ Ops & System Resilience** | `$runtime-reliability`<br>`$schema-craft`<br>`$ship-it` | Rehearses zero-downtime schema migrations, memory soak tests, and SIGTERM graceful shutdowns. |
| **🏛️ High-Risk Technical Fork** | `$idea-council`<br>`$plan-master` | Conducts a 6-seat adversarial council before any code is committed. |
| **📦 Multi-Module (>12 files)** | `$adaptive-worker-orchestrator-v2`<br>`$plan-master`<br>`$qa-sentinel` | Partitions separable tasks into isolated git worktrees with frozen interface contracts. |

---

## ⚡ Execution Modes

1. **Turbo Compilation Mode (Default)**:
   - When the user's idea is clear or moderately detailed, compile the refined prompt immediately in the current turn.
2. **Interactive Clarification Mode**:
   - If the user's prompt is severely ambiguous (e.g. *"Build me an app for my store"*), use `ask_question` to ask **2 targeted architectural questions** (e.g., target stack, primary auth method) before compiling the final prompt.

---

## 📐 The Inverted Pyramid Prompt Architecture

Every compiled prompt must follow this 4-tier structure:

1. **Goal & Primary Directive**: 1–2 punchy sentences defining the technical objective.
2. **Assigned Skill Tags**: Pre-selected skills (`/frontend-artisan`, `/schema-craft`, `/qa-sentinel`).
3. **Phased Execution Contract**:
   - **Pass 1 (Core Backbone & Data Engine)**: Free API integration, caching layer, or canvas engine.
   - **Pass 2 (State & Interactivity)**: Zero-slop UI layout, keyboard shortcuts (`/`, `⌘K`), and state transitions.
   - **Pass 3 (Verification & Guardrails)**: QA Sentinel testing, empty states, and accessibility compliance.
4. **Negative Guardrails**: Explicit list of domain-specific anti-patterns to avoid.

---

## 📋 Standard Output Format

When invoked, respond with:

1. **Architectural Analysis & Blindspots Caught**: (Brief 2–4 bullet points highlighting missing data sources, caching needs, or performance hazards).
2. **Domain Classification**: (e.g. *Full-Stack Immersive Application*)
3. **Assigned Skill Team**: The exact 2–4 skills with a 1-line rationale for each.
4. **The Refined Execution Prompt**: Formatted in a single copy-pasteable Markdown code block starting with the assigned slash commands.
