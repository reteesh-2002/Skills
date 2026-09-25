---
name: frontend-artisan
description: Build distinctive, handcrafted, production-grade frontend applications and Generative UI widgets that break free from generic AI design clichés (purple gradients, identical 3-card grids, default Inter font). Works across any frontend stack (Vanilla HTML/CSS, Tailwind CSS, React, Vue, Svelte, Next.js, Astro). Enforces curated design archetypes, expressive typography, tactile micro-interactions, and strict WCAG AA accessibility. Use when building or styling web apps, dashboards, landing pages, or UI components.
---

# Frontend Artisan

Transform standard, repetitive AI frontend code into bespoke, memorable, and polished user interfaces. Replace cookie-cutter SaaS templates with curated design archetypes, thoughtful typography, sensory micro-interactions, and rock-solid responsive layouts across **any frontend stack**.

## Boundaries and Core Invariants

1. **Zero External Runtime Dependencies (By Default)**:
   - Rely strictly on native CSS or Tailwind CSS utilities already installed in the project, plus inline SVG.
   - Do NOT import uninstalled animation libraries (Framer Motion, GSAP, Anime.js) or external font packages unless explicitly requested and confirmed in `package.json`.
2. **Framework & Stack Agnostic**:
   - Seamlessly adapt styling idioms to the target stack: Vanilla HTML/CSS, Tailwind CSS, React (JSX/TSX), Vue 3 (`.vue`), Svelte 5 (`.svelte`), Next.js, or Astro.
   - Consult [Framework Adapters](references/framework-adapters.md) for idiomatic component patterns.
3. **Non-Negotiable Accessibility (WCAG 2.1 AA)**:
   - Normal text must achieve a minimum contrast ratio of **4.5:1** against its background; large text/interactive borders must reach **3:1**.
   - Interactive elements must include visible `:focus-visible` rings with proper contrast.
4. **Mobile-First Responsiveness**:
   - Every layout (bento grids, asymmetric splits) MUST collapse to a single column (`grid-cols-1` or `repeat(auto-fit, minmax(...))`) on mobile viewports (<640px). Zero horizontal scrolling.
5. **Motion Safety**:
   - All interactive scale, bounce, or translation classes must include `motion-reduce:transition-none motion-reduce:transform-none` or `@media (prefers-reduced-motion: reduce)`.

---

## 1. The Expressiveness Knob

Tailor the visual personality to the domain by selecting one of three intensity levels:

| Level | Ideal Domain | Key Characteristics |
| :--- | :--- | :--- |
| **Subtle** | Enterprise B2B, developer tooling, financial dashboards | Clean, high-density layout; refined typography pairing; muted, professional palette; subtle 1px border elevation; standard accessible grid. |
| **Balanced** *(Default)* | Modern SaaS, consumer web apps, productivity tools | Tactile micro-interactions (`active:scale-[0.98]`); bento grid rhythm; warm neutral background; distinct primary accent; subtle inner shadows. |
| **Bold** | Landing pages, creative portfolios, Web3, consumer brands | High-contrast archetype expression (e.g. Neo-Brutalist offset shadows, Editorial stark typography, Cyber terminal minimalism); expressive layout asymmetry. |

---

## 2. The Anti-Pattern Ban-List

Always enforce [Anti-Patterns Reference](references/anti-patterns.md) before writing code:
- ❌ **BAN** the "AI Purple Cliché" (`bg-slate-900` with `from-purple-500 to-indigo-500` text/glow).
- ❌ **BAN** the uniform 3-card grid with identical padding, icons, and heights.
- ❌ **BAN** unstyled, low-contrast placeholder text (`text-slate-400` on white).
- ❌ **BAN** floating cards without tactile hover or active press states.
- ❌ **BAN** generic centered heroes with two identical pill buttons ("Get Started" / "Learn More").

---

## 3. The 10 Archetypes Canon & Decision Triage Matrix

Consult the matrix below to select the exact visual archetype matching your project domain, then load its dedicated reference guide:

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

### Archetype Non-Negotiable Invariants:
- **Dot-Matrix (#06)**: NEVER set body text in dot-matrix font; use for metrics, counters, and hero badges only.
- **Terminal & Telemetry (#01, #02)**: ALWAYS wrap dense multi-column tabular data in an `overflow-x-auto` container with sticky row headers to prevent mobile viewport clipping.
- **Cinematic Dark Kinetic (#10)**: Achieve depth via native CSS 3D perspectives and ambient gradients by default. If Three.js is used, keep all typography and buttons in the accessible HTML DOM above the canvas.

---

## 4. Multi-Stack Tokens & Micro-Interactions

Select the token reference matching the project stack:

- **Tailwind Projects (Vite, Next.js, Generative UI)**: Use [Tailwind Tokens](references/tokens-tailwind.md).
  - Tactile button: `transition-all duration-150 ease-out hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98]`
  - Neo-brutalist stamp: `border-2 border-black shadow-[4px_4px_0px_#000] active:translate-x-1 active:translate-y-1 active:shadow-none`
- **Vanilla HTML/CSS Projects (Zero Build Steps)**: Use [Vanilla CSS Tokens](references/tokens-vanilla-css.md).
  - Fluid typography: `clamp(1rem, 0.95rem + 0.25vw, 1.25rem)`
  - Native CSS custom properties: `--tactile-bg`, `--tactile-surface`, `--tactile-border`
- **Framework Components (React / Vue / Svelte)**: Use [Framework Adapters](references/framework-adapters.md) for typed props, variant classes, and component encapsulation.

---

## 5. Verification Checklist

Before delivering frontend code, verify:
1. Does it look distinct from a generic AI template?
2. Does it resize gracefully to 375px without horizontal scrolling?
3. Does all text pass WCAG AA contrast (≥4.5:1)?
4. Are all interactive elements equipped with tactile `:hover`, `:active`, and `:focus-visible` states?
5. Does it run with zero uninstalled external dependencies?
