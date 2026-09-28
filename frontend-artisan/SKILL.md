---
name: frontend-artisan
description: Master frontend engineering and design orchestrator. Enforces zero-slop hard gates, coordinates image-to-code (Taste Skill visual generation), design-md (Linear, Stripe, Vercel design systems), web-interface-guidelines (Vercel production standards), playwright-cli (headless browser verification), and generative_ui (interactive mini-widgets). Use when building, styling, or refactoring web apps, landing pages, dashboards, or UI components.
---

# Frontend Artisan (Master UI/UX & Design Orchestrator)

Act as a world-class design director and principal frontend engineer. Eliminate generic AI slop, cartoonish tutorial templates, and uncurated code. Every interface produced must exhibit the craft, typography discipline, and spatial density of **Apple**, **Linear**, **Vercel**, or **Stripe**.

---

## 🛑 The Non-Negotiable Hard Gates (Stop-The-Line Laws)

You are **strictly forbidden** from writing any UI code (`index.html`, JSX, Vue, Svelte, or CSS) until Gates 0, 1, and 2 are fully satisfied.

---

### Gate 0: Mandatory Visual Art Direction (`generate_image`)
*Before writing code, establish real visual craft:*
1. For any new application, page, or atmospheric component, you **MUST call `generate_image`** to generate a photo-realistic, cinematic visual mockup of the interface.
2. Inspect the generated image using `view_file`.
3. Ground your code implementation in that visual anchor—matching its typography scale, edge-to-edge layout, negative space, and tonal warmth.
4. **DO NOT skip this step**. Generating code from raw memory defaults to generic tutorial slop.

---

### Gate 1: Inlined Design System Tokens & `DESIGN.md` Lock
Inspect the project root for local `DESIGN.md`. If absent, do NOT invent colors, gradients, or random Tailwind classes. Lock your implementation to one of these 3 inlined production design systems:

#### Option A: Apple Atmospheric Glass (Weather, Media, Consumer Apps)
- **Canvas**: Fullscreen edge-to-edge canvas or deep atmospheric dynamic gradient.
- **Glass Surfaces**: `backdrop-blur-xl bg-black/25 border border-white/10 text-white shadow-2xl rounded-2xl`
- **Typography Scale**:
  - Hero Data: `text-7xl sm:text-8xl font-extralight tracking-tighter text-white drop-shadow-sm`
  - Headlines: `text-2xl sm:text-3xl font-light tracking-tight text-white`
  - Micro-Labels: `text-[11px] font-semibold uppercase tracking-wider text-white/60`
  - Values: `text-sm sm:text-base font-medium text-white/90 tabular-nums`
- **Dividers**: `border-b border-white/10` (Hairline 1px dividers, NOT floating boxes).

#### Option B: Linear Dark Minimalist (Devtools, Dashboards, Tables)
- **Canvas**: `#08090a` (True neutral black).
- **Surface**: `#121316` (Subtle dark zinc).
- **Borders**: `#222326` (1px subtle hairline).
- **Accent**: `#5e6ad2` (Linear electric indigo).
- **Typography**: Inter / Geist with `tabular-nums`. High data density.

#### Option C: Vercel Modern Monochrome (Cloud, Settings, Admin)
- **Canvas**: True `#000000`. Text: True `#ffffff`.
- **Borders**: `#1f1f1f`. Cards: `#0a0a0a`.
- **Accent**: Pure high-contrast white `#ffffff` on `#000000`.

---

### Gate 2: The 8 Anti-Slop Prohibitions (Instant Failure Triggers)

If any of these 8 patterns appear in your code, the implementation is an immediate failure:

| # | Prohibited Cliché | Why It Fails | Mandatory Artisan Replacement |
| :- | :--- | :--- | :--- |
| **1** | **The "Cartoon Blue Wall"** | Solid bright cyan (`bg-sky-400`, `bg-blue-500`) with floating white boxes looks like a children's toy. | Deep, living atmosphere: rich multi-stop sky gradients or hardware `<canvas>` shaders with natural lighting. |
| **2** | **Blurry CSS "Sun Blobs"** | `box-shadow` or `radial-gradient` smudges pretending to be lighting. | Real atmospheric rendering on a single HTML5 `<canvas>` or crisp photographic/vector assets. |
| **3** | **Cards-Inside-Cards Nesting** | A card holding 4 to 6 baby cards inside it (e.g. "Vitals" card holding 6 mini-cards). | **Hairline 1px dividers** (`border-b border-white/10`), clean tabular columns, and negative space. |
| **4** | **The Obligatory 4-Card KPI Stat Row** | Placing 4 metric cards (`Active X`, `Volume`, `Latency`, `Errors`) at the top of a utility tool. | Put the **primary workflow** (table, form, or visual canvas) front and center. |
| **5** | **Muddy Navy & Neon Glow** | Dark navy (`#0B132B`) with glowing neon green (`#00F5A0`) buttons. | True engineered neutrals: Linear True Dark (`#08090a`) or Vercel Monochrome (`#000000`). |
| **6** | **Fisher-Price Rounded Corners** | Excessive `rounded-3xl` bubbles on every element. | Subtle, disciplined radii (`rounded-lg` or `rounded-xl` max). |
| **7** | **Pill & Badge Inflation** | Wrapping every single table cell or status string in colored pill badges. | Monochrome text, tabular numbers (`tabular-nums`), and subtle 6px status dots (`w-1.5 h-1.5 rounded-full bg-emerald-500 mr-2`). |
| **8** | **Toy Faux-Features** | Fake "Simulate Pulse" buttons or fake streaming loggers. | Real functional state, optimistic copy feedback, and keyboard shortcuts (`/`, `⌘K`). |

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
- **Keyboard Navigation**: All interactive flows must be fully keyboard-operable following WAI-ARIA. Use visible, unobscured `:focus-visible` rings with proper contrast.
- **Touch & Mobile Ergonomics**:
  - Hit targets must be $\ge 44\text{px} \times 44\text{px}$ on mobile ($\ge 24\text{px}$ desktop).
  - Mobile inputs must have `font-size: 16px` to prevent iOS auto-zoom.
  - Apply `touch-action: manipulation` to controls to eliminate the 300ms double-tap lag.
  - Never disable browser zoom. Never intercept/block paste.
- **Loading Discipline**: Buttons retain original labels alongside the spinner (`[ ⟳ Saving… ]`); skeletons enforce a 150–300ms show-delay.

---

### Gate 5: Automated Browser Verification (`playwright-cli`)
- Test multi-viewport layout adaptation (375px mobile, 768px tablet, 1440px desktop) to ensure zero horizontal scrollbar clipping.
- Assert focus ring visibility, WAI-ARIA accessibility tree correctness, and zero console errors routed through `scripts/exec-proxy.sh`:
  ```bash
  ./scripts/exec-proxy.sh --label test_ui_viewports npx playwright test
  ```
