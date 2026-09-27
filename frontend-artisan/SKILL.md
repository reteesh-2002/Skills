---
name: frontend-artisan
description: Elite frontend engineering and design architecture skill. Implements the Taste Skill anti-slop visual discipline, Vercel Web Interface Guidelines, DESIGN.md design system ingestion, Playwright headless browser verification, and Generative UI interactive previews. Enforces curated archetypes, image-first art direction, tactile micro-interactions, flicker-free loading states, and strict WCAG AA accessibility across any frontend stack (Tailwind, React, Vue, Svelte, Next.js, HTML/CSS).
---

# Frontend Artisan (Anti-Slop & Web Interface Engineering)

Transform raw specifications into distinctive, handcrafted, production-grade frontend interfaces. Combines the **[Taste Skill](https://tasteskill.dev) Anti-Slop discipline**, **[Vercel Web Interface Guidelines](https://vercel.com/design/guidelines)**, **[DESIGN.md](references/design-md-presets.md) design systems**, **[Playwright](references/playwright-verification.md) headless verification**, and **[Generative UI](references/tokens-tailwind.md)** interactive mini-widget previews.

---

## 🛡️ Non-Negotiable Engineering Invariants

### 1. Anti-Slop Layout & Image-First Art Direction ([Taste Skill](references/image-first-art-direction.md))
- **Image-First Protocol**: For major visual designs (landing pages, heroes, flagship dashboards), execute **Image Generation First** using `generate_image`. Inspect the generated image for tonal warmth, typography scale, asymmetry, and spatial rhythm *before* writing code.
- **The Anti-Card Rule**: Never wrap every element in a rounded card with a border. Break the "cards-inside-cards-inside-cards" nesting loop using generous negative space, hairline dividers (`border-t border-neutral-200/60`), and tonal canvas shifts.
- **Spacious Hero**: Heroes must breathe. Keep primary copy and CTAs comfortably legible on a 13-inch laptop screen without scrolling. Avoid badge spam and synthetic SaaS metric pills.
- **Zero Generic AI Gradients**: Reject monotonous `from-purple-600 to-indigo-600` dark backdrops. Use curated palettes (Warm Stone & Ember, Obsidian & Emerald, Neo-Swiss Red, High-Tech Blueprint).

### 2. Vercel Web Interface Engineering ([Vercel Guidelines](references/vercel-interface-guidelines.md))
- **Keyboard Works Everywhere**: All interactive flows must be fully keyboard-operable (WAI-ARIA). Use visible, unobscured `:focus-visible` rings with proper contrast. Set `:focus-within` for composite controls.
- **Touch & Click Ergonomics**:
  - Touch hit targets must be $\ge 44\text{px} \times 44\text{px}$ on mobile; desktop minimum is $\ge 24\text{px}$.
  - Mobile `<input>` and `<textarea>` font size must be $\ge 16\text{px}$ to prevent iOS Safari auto-zooming.
  - Apply `touch-action: manipulation` to interactive controls to eliminate the 300ms double-tap zoom delay.
  - Never disable browser zoom (`user-scalable=no` is forbidden).
  - Never intercept or disable paste in form inputs.
- **Loading & State Discipline**:
  - **Loading Buttons Retain Labels**: Show an inline spinner while **keeping the original button label visible** (e.g. `[ ⟳ Saving… ]`). Never replace button text with an isolated spinner.
  - **Flicker-Free Skeletons**: Apply a 150–300ms show-delay to avoid flashing on fast responses, and maintain a 300–500ms minimum visible duration once shown.
  - **URL as State**: Persist active tabs, filters, queries, and pagination in URL search parameters (`searchParams` / `nuqs`).
  - **Optimistic Updates**: Update the UI immediately on user action; reconcile on response with graceful rollback on error.
  - **Ellipsis Syntax**: Menu options or buttons opening a subsequent dialog (e.g. "Rename…", "Export…") must end with a typographical ellipsis (`…`).
- **Layout & Motion Safety**:
  - Apply `overscroll-behavior: contain` to modal dialogs and slide-over drawers.
  - While dragging elements, apply `inert` and `select-none` to prevent erratic hover/selection.
  - Enforce `@media (prefers-reduced-motion: reduce)` (`motion-reduce:transition-none motion-reduce:transform-none`).

### 3. DESIGN.md & Brand System Ingestion ([Awesome Design MD](references/design-md-presets.md))
- Check the workspace root for `DESIGN.md`. If present, adopt its design tokens, color scales, and typography hierarchies.
- If absent, select and adhere to one of the curated [DESIGN.md Presets](references/design-md-presets.md):
  - **Linear Dark Minimalist**: Ultra-clean `#08090a` canvas, tabular numerals, `#5e6ad2` indigo accent.
  - **Vercel Monochrome Modern**: Razor-sharp high contrast black/white with Geist typography.
  - **Stripe Editorial Opulence**: Expansive whitespace, soft multi-layer drop shadows, vibrant accents.
  - **Supabase Emerald Studio**: Developer hacker utility with `#3ecf8e` emerald dark mode.

---

## 🎨 The 10 Archetypes Canon

When starting greenfield work without an existing design system, consult the Archetype Canon:

| # | Archetype | Ideal Project Domain | Core Commitment | Reference Guide |
| :-: | :--- | :--- | :--- | :--- |
| **01** | **Terminal-Grade Density** | DevTools, Log Viewers, Observability, Trading | 11–13px mono, hairline dividers, tabular nums, zero cards | [01-terminal-density.md](references/archetypes/01-terminal-density.md) |
| **02** | **Mission-Control Telemetry HUD** | IoT, Infrastructure Monitoring, Robotics, Cockpits | Instrument clusters, huge numerals, linear gauge arcs, alarm logic | [02-telemetry-hud.md](references/archetypes/02-telemetry-hud.md) |
| **03** | **Neo-Swiss / Typographic** | Creative Tools, Design Systems, Authoritative B2B | Asymmetric visible grid, flush-left type, single grotesk, index numbers | [03-neo-swiss.md](references/archetypes/03-neo-swiss.md) |
| **04** | **Luxury Editorial Print** | Long-form Publishing, Architecture, Premium E-Commerce | High-contrast serifs, drop-caps, printed newsprint tones, literary margins | [04-editorial-print.md](references/archetypes/04-editorial-print.md) |
| **05** | **Tactile Hardware Skeuomorphism** | Audio Synthesizers, Creative Instruments, Smart Home | Anodized aluminum plates, silkscreen labels, physical click depression | [05-tactile-hardware.md](references/archetypes/05-tactile-hardware.md) |
| **06** | **Dot-Matrix / Segment Display** | Hardware Companions, Wearables, Minimalist Clocks | 7-segment/dot-matrix display type, monochrome OLED, pattern glyphs | [06-dot-matrix-minimal.md](references/archetypes/06-dot-matrix-minimal.md) |
| **07** | **Raw Neo-Brutalism** | Indie Software, Creator Tools, Event Posters, Web3 | 2px black borders, hard 4px offset block shadows, saturated flat fills | [07-neo-brutalism.md](references/archetypes/07-neo-brutalism.md) |
| **08** | **Technical Blueprint** | CAD Specs, NASA/Aviation Docs, Network Topologies | 1px drafting linework, corner registration crosshairs (+), dimension marks | [08-technical-blueprint.md](references/archetypes/08-technical-blueprint.md) |
| **09** | **Retro-OS Desktop** | Media Players, Playful Portfolios, Community Spaces | Draggable window chrome, 1-bit icons, system title bars, 90s OS warmth | [09-retro-desktop.md](references/archetypes/09-retro-desktop.md) |
| **10** | **Cinematic Dark Kinetic** | Product Launches, Flagship Landing Pages, Interactive Hero | Pure CSS 3D perspective, ambient mesh gradients, optional Three.js | [10-kinetic-dark.md](references/archetypes/10-kinetic-dark.md) |

---

## 📱 Mandatory Generative UI Interactive Mini-Widget

Whenever any frontend design or UI component is being designed, styled, or implemented:
1. **Generate a Mini Interactive Generative UI Widget**:
   - Save a self-contained `.html` artifact in `<appDataDir>/brain/<conversation-id>/` with `UserFacing: true` using the `generative_ui` skill pattern.
   - Use semantic host tokens (`--background`, `--card`, `--border`, `--foreground`, `--primary`, etc.) and the official gstatic Tailwind CDN (`<script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>`).
   - Include interactive color palette swatches, typography scales, tactile button states (`active:scale-[0.98]`), and interactive controls previewing the interface.
2. **Embed in Chat**:
   - Embed the widget inline in the chat response using:
     `<agent-embed src="file:///<artifact_path>/widget.html"></agent-embed>`
     allowing the user to preview and interact with color choices and interface states directly.

---

## 🔍 Automated Verification & Playwright Protocol ([Playwright](references/playwright-verification.md))

Before delivering frontend work, verify:
1. **Viewport Responsiveness**: Test layout adaptation across 375px (mobile), 768px (tablet), and 1440px (desktop). Zero horizontal scrollbar clipping.
2. **WCAG AA Contrast**: Ensure text contrast meets $\ge 4.5:1$ for normal body text and $\ge 3:1$ for large text/interactive borders.
3. **Tactile Feedback**: Verify `:hover`, `:active`, and `:focus-visible` rings on all interactive elements.
4. **Loading & Fallback Integrity**: Verify loading skeletons, empty states, and error fallbacks.
5. **Headless Execution**:
   - Where Playwright is available, execute automated viewport and accessibility audits via `scripts/exec-proxy.sh`:
     ```bash
     ./scripts/exec-proxy.sh --label test_ui_viewports npx playwright test
     ```
   - When automated browser tooling is not installed in the workspace, explicitly disclose that responsive rendering was statically verified and requires manual visual confirmation.
