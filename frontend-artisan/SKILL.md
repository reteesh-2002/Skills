---
name: frontend-artisan
description: Master frontend engineering and design orchestrator. Coordinates image-to-code (Taste Skill visual generation & anti-slop), design-md (Linear, Stripe, Vercel design systems), web-interface-guidelines (Vercel production standards), playwright-cli (headless browser verification), and generative_ui (interactive mini-widgets). Use when building, styling, or refactoring web apps, landing pages, dashboards, or UI components.
---

# Frontend Artisan (Unified Frontend Architecture & Design Orchestrator)

Act as the master design director and frontend architect. Rather than relying on abstract presets or cookie-cutter templates, `frontend-artisan` orchestrates a dedicated suite of specialized, industry-standard frontend engineering skills:

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

## 🚀 The 5-Stage Orchestration Workflow

Whenever designing, building, or restyling frontend user interfaces, execute in this precise order:

### 1. Visual Ideation & Anti-Slop Art Direction (`image-to-code`)
- **Activate [`image-to-code`](../image-to-code/SKILL.md)** for landing pages, heroes, marketing pages, or creative components.
- **The Image-First Rule**: Generate a reference visual image using `generate_image` *first*. Inspect typography hierarchy, spatial rhythm, negative space, and tonal warmth before touching implementation code.
- **Anti-Slop Layout**: Strictly eliminate "cards-inside-cards-inside-cards" nesting, cramped mobile heroes, generic purple gradients, and synthetic SaaS badge pills.

### 2. Design System & Brand Token Ingestion (`design-md`)
- **Activate [`design-md`](../design-md/SKILL.md)** to establish color palettes, typography scales, border radii, and spacing tokens.
- **Workspace Ingestion**: Inspect the project root for a `DESIGN.md` file. If present, strictly adhere to its tokens.
- **Brand Presets**: If no local `DESIGN.md` exists, adopt one of the 15 production brand presets from [`design-md/presets/`](../design-md/presets/):
  - **Linear Dark Minimalist** (`linear.app.DESIGN.md`): Ultra-clean `#08090a` canvas, tabular nums, `#5e6ad2` indigo accent.
  - **Vercel Monochrome Modern** (`vercel.DESIGN.md`): High-contrast black/white mono, Geist typography, hairline borders.
  - **Stripe Editorial Opulence** (`stripe.DESIGN.md`): Vibrant multi-layer gradients, opulent spacing, blurple `#635bff`.
  - **Supabase Emerald Studio** (`supabase.DESIGN.md`): Dark developer studio with `#3ecf8e` emerald accents.
  - **Raycast Command Palette** (`raycast.DESIGN.md`): High-density keyboard-first ergonomics.

### 3. Production Interaction & Accessibility (`web-interface-guidelines`)
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

### 4. Mandatory Generative UI Interactive Mini-Widget (`generative_ui`)
- Create a self-contained `.html` mini-widget artifact in `<appDataDir>/brain/<conversation-id>/` with `UserFacing: true` using the `generative_ui` skill pattern.
- Use the host's semantic design system tokens (`--background`, `--card`, `--border`, `--foreground`, `--primary`, etc.) and the official gstatic Tailwind CDN (`<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>`).
- Include interactive color palette swatches, typography scales, tactile button states (`active:scale-[0.98]`), and interactive controls previewing the interface.
- Embed inline in the chat response using:
  `<agent-embed src="file:///<artifact_path>/widget.html"></agent-embed>`
  so the user can immediately interact with the color choices and interface states.

### 5. Automated Browser & Accessibility Verification (`playwright-cli`)
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
