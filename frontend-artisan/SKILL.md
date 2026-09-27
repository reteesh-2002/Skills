---
name: frontend-artisan
description: Master frontend engineering and design orchestrator. Enforces zero-slop hard gates, coordinates image-to-code (Taste Skill visual generation), design-md (Linear, Stripe, Vercel design systems), web-interface-guidelines (Vercel production standards), playwright-cli (headless browser verification), and generative_ui (interactive mini-widgets). Use when building, styling, or refactoring web apps, landing pages, dashboards, or UI components.
---

# Frontend Artisan (Unified Frontend Architecture & Design Orchestrator)

Act as the master design director and frontend architect. Rather than relying on default LLM cliches or cookie-cutter templates, `frontend-artisan` enforces a strict, **hard-gated zero-slop engineering workflow** coordinating industry-standard frontend disciplines:

```
                          ┌───────────────────────────┐
                          │     frontend-artisan      │
                          └─────────────┬─────────────┘
                                        │
     ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
     ▼                  ▼                               ▼                  ▼
┌──────────────┐ ┌──────────────┐              ┌─────────────────┐ ┌──────────────┐
│image-to-code │ │  design-md   │              │ web-interface-  │ │playwright-cli│
│(Visual Vibe) │ │(Brand Tokens)│              │   guidelines    │ │(Verification)│
└──────────────┘ └──────────────┘              │  (Vercel Rules) │ └──────────────┘
                                               └─────────────────┘
                                        │
                                        ▼
                                ┌─────────────────┐
                                │  generative_ui  │
                                │ (Inline Embed)  │
                                └─────────────────┘
```

---

## 🛑 The Zero-Slop Hard Gates (Mandatory Protocol)

To eliminate AI slop, **you are strictly forbidden from jumping directly into writing UI code (`index.html`, JSX, Vue, Svelte, or CSS) until Gates 1–3 are fully satisfied.**

---

### Gate 1: Mandatory Token Ingestion & `DESIGN.md` Lock (Stop-The-Line)
1. **Workspace Inspection**: Inspect the project root for `DESIGN.md` using `view_file`.
2. **Preset Ingestion**: If no local `DESIGN.md` exists, **YOU MUST FIRST READ** one of the 15 production presets from `~/.gemini/config/skills/design-md/presets/`:
   - **Linear Dark Minimalist** (`linear.app.DESIGN.md`): Ultra-clean `#08090a` canvas, tabular nums, `#5e6ad2` indigo accent.
   - **Vercel Monochrome Modern** (`vercel.DESIGN.md`): High-contrast black/white mono, Geist typography, hairline borders.
   - **Stripe Editorial Opulence** (`stripe.DESIGN.md`): Vibrant multi-layer gradients, opulent spacing, blurple `#635bff`.
   - **Supabase Emerald Studio** (`supabase.DESIGN.md`): Dark developer studio with `#3ecf8e` emerald accents.
   - **Raycast Command Palette** (`raycast.DESIGN.md`): High-density keyboard-first ergonomics.
3. **Instantiate `DESIGN.md`**: Write or update `DESIGN.md` in the project root before generating UI code. Every hex color, font stack, and border-radius in the implementation must trace directly to this file.

---

### Gate 2: The 5 Anti-Slop Prohibitions (Instant Failure Triggers)

You must actively reject the default LLM dashboard cliches:

| # | Prohibited Pattern | Why It Fails | Mandatory Artisan Replacement |
| :- | :--- | :--- | :--- |
| **1** | **The Obligatory 4-Card KPI Stat Row** | Placing 4 metric cards (`Active X`, `Volume`, `Latency`, `Errors`) at the top of a utility page is generic AI slop. | Put the **primary workflow** (tables, forms, canvas, or controls) front and center. Only add metrics if the user explicitly requested an analytics dashboard. |
| **2** | **Muddy Navy & Neon Glow** | Dark navy (`#0B132B`, `#0f172a`) paired with glowing neon cyan/green (`#00F5A0`) looks like cheap 2021 crypto sludge. | Use true engineered palettes: Linear True Dark (`#08090a`, `#141518`), Vercel Monochrome (`#000000`, `#ffffff`, `#171717`), or clean light zinc. |
| **3** | **Infinite Card-in-Card Nesting** | Wrapping every table, section, and badge in rounded cards with gray borders creates visual clutter. | Use **hairline 1px dividers** (`border-b border-zinc-800`), edge-to-edge tabular data, and generous whitespace. |
| **4** | **Pill & Badge Pollution** | Wrapping every table column or string in rounded colored pill badges ruins scannability. | Use clean, compact monochrome typography, high-density tabular numbers (`tabular-nums`), and subtle 6px status dots (`w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2`). |
| **5** | **Toy Faux-Features** | Adding fake "Simulate Pulse", fake streaming logs, or toy animations that weren't requested. | Build real, functional state management, empty states, copy-to-clipboard feedback, and keyboard shortcuts (`⌘K`). |

---

### Gate 3: Mandatory Generative UI Interactive Mini-Widget Artifact
- Before declaring UI implementation complete, you **MUST** generate a self-contained `.html` mini-widget artifact in `<appDataDir>/brain/<conversation-id>/` with `UserFacing: true` using `generative_ui`.
- Use semantic design tokens and the official gstatic Tailwind CDN:
  `<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>`
- Include interactive color palette swatches, typography scales, tactile button states (`active:scale-[0.98]`), and a live functional preview of the core component.
- Embed inline in the chat response using:
  `<agent-embed src="file:///<artifact_path>/widget.html"></agent-embed>`
  so the user can immediately interact with the design system tokens and interface states.

---

### Gate 4: Production Interaction & Accessibility (`web-interface-guidelines`)
- **Enforce [`web-interface-guidelines`](../web-interface-guidelines/SKILL.md)** across all markup and components:
  - **Keyboard Navigation**: All interactive flows must be fully keyboard-operable following WAI-ARIA. Use visible, unobscured `:focus-visible` rings with proper contrast. Set `:focus-within` for composite controls.
  - **Touch & Mobile Ergonomics**:
    - Hit targets must be $\ge 44\text{px} \times 44\text{px}$ on mobile ($\ge 24\text{px}$ desktop).
    - Mobile inputs must have `font-size: 16px` to prevent iOS auto-zoom.
    - Apply `touch-action: manipulation` to controls to eliminate the 300ms double-tap lag.
    - Never disable browser zoom. Never intercept/block paste.
  - **Loading Discipline**: Buttons retain original labels alongside the spinner (`[ ⟳ Saving… ]`); skeletons enforce a 150–300ms show-delay and 300–500ms minimum display duration.
  - **State Hygiene**: URL query parameters as the single source of truth for tabs/filters/pagination (`nuqs` / `searchParams`); optimistic UI with graceful rollback.
  - **Layout & Motion**: `overscroll-behavior: contain` on modals/drawers; `inert` and `select-none` applied during drag; motion safety (`motion-reduce:transition-none`).

---

### Gate 5: Visual Ideation for Landing Pages & Heroes (`image-to-code`)
- For landing pages, hero sections, marketing pages, or novel creative components, **activate [`image-to-code`](../image-to-code/SKILL.md)**:
  - Generate a reference visual image using `generate_image` *first*.
  - Inspect typography hierarchy, spatial rhythm, negative space, and tonal warmth before touching implementation code.

---

### Gate 6: Automated Browser Verification (`playwright-cli`)
- **Activate [`playwright-cli`](../playwright-cli/SKILL.md)** for headless browser verification:
  - Test multi-viewport layout adaptation (375px mobile, 768px tablet, 1440px desktop) to ensure zero horizontal scrollbar clipping.
  - Assert focus ring visibility, WAI-ARIA accessibility tree correctness, and zero console/hydration errors routed through `scripts/exec-proxy.sh`:
    ```bash
    ./scripts/exec-proxy.sh --label test_ui_viewports npx playwright test
    ```
  - When automated browser tooling is not installed in the workspace, explicitly disclose that responsive rendering was statically verified and requires manual visual confirmation.

---

## 📚 Multi-Stack References
- For Tailwind utility classes and micro-interactions, consult [Tailwind Tokens](references/tokens-tailwind.md).
- For zero-dependency vanilla setups, consult [Vanilla CSS Tokens](references/tokens-vanilla-css.md).
- For React, Vue 3, Svelte 5, and Next.js component templates, consult [Framework Adapters](references/framework-adapters.md).
- For common design flaws to avoid, consult [Anti-Patterns](references/anti-patterns.md).
