---
name: frontend-artisan
description: Frontend engineering and design orchestrator. Handles UI, CSS, component, and web app work. Apply when building, styling, or refactoring web apps, landing pages, dashboards, or UI components. Explicit only — not auto-activated.
---

# Frontend Artisan

Deliver frontend work with intentional craft: correct layout, accessible interaction, appropriate visual quality, and honest verification. The approach scales to the task — a bug fix does not need a concept image; a new product page does.

---

## 1. Choose your mode

Classify the request before doing any work:

| Mode | When | Default image behavior |
|---|---|---|
| **Existing design** | Extending or modifying an existing page, component, or design system | No image generation — use existing tokens and components |
| **Supplied reference** | User provided a screenshot, mockup, or URL | Inspect and implement from the reference; crop or zoom to focus on details |
| **New concept** | Greenfield page or layout without an existing design | Generate at most one overview and one detail image; then implement |
| **Functional edit** | Bug fix, accessibility repair, or behavior change | Preserve appearance; no concept image unless the visual is broken |

If you are in **Existing design** or **Functional edit** mode, skip image generation entirely.

For **New concept** mode: generate one overview image and one detail image maximum. If after two attempts the visual direction is still unclear, continue with available references or surface the unresolved visual decision explicitly — do not generate more images in the default workflow. Explicit high-craft requests may budget more.

---

## 2. Design system

**Check for an existing design system first:**
- Look for `DESIGN.md`, `design-md/`, or a component library at the project root
- If found: extend it. Do not override established tokens, colors, or component styles
- If not found and mode is **New concept**: pick one preset below or ask the user

**Apple Atmospheric Glass** (weather, media, consumer apps):
- Canvas: fullscreen edge-to-edge atmospheric gradient
- Surfaces: `backdrop-blur-xl bg-black/25 border border-white/10 text-white shadow-2xl rounded-2xl`
- Typography: Hero `text-7xl font-extralight tracking-tighter`, Headlines `text-2xl font-light tracking-tight`, Labels `text-[11px] font-semibold uppercase tracking-wider text-white/60`

**Linear Dark Minimalist** (devtools, dashboards, tables):
- Canvas: `#08090a` · Surface: `#121316` · Borders: `#222326` · Accent: `#5e6ad2`
- Typography: Inter/Geist, `tabular-nums`, high data density

**Vercel Modern Monochrome** (cloud, settings, admin):
- Canvas: `#000000` · Text: `#ffffff` · Borders: `#1f1f1f` · Cards: `#0a0a0a`
- Accent: high-contrast white on black

Presets are contextual guidance — apply them when relevant, not unconditionally.

---

## 3. Anti-patterns to avoid

These patterns produce low-quality output and should be avoided in new work:

| Pattern | Problem | Replacement |
|---|---|---|
| Solid bright cyan/blue wall | Looks like a tutorial template | Rich atmospheric gradient or neutral dark canvas |
| CSS radial-gradient "sun blobs" | Fake lighting, muddy appearance | Real canvas shaders or clean photography/SVG |
| Cards inside cards (3+ levels) | Visual clutter, no hierarchy | Hairline 1px dividers, tabular columns, negative space |
| 4-card KPI stat row at the top of a utility | Obscures the primary workflow | Put the table, form, or canvas front and center |
| Muddy navy + neon glow | Dated aesthetic | Linear true dark or Vercel monochrome |
| Excessive rounded corners (`rounded-3xl` everywhere) | Cartoonish | Disciplined `rounded-lg` or `rounded-xl` maximum |
| Colored pill badge on every cell | Badge inflation | Monochrome text, `tabular-nums`, subtle status dots |
| Fake interactive buttons with no real state | Toy feature | Real state, optimistic feedback, keyboard shortcuts |

For layout bans: treat these as contextual guidance except for genuine accessibility or functionality defects.

---

## 4. Accessibility and interaction requirements

These apply in all modes:

- **Keyboard navigation**: All interactive elements keyboard-operable; visible `:focus-visible` rings with sufficient contrast
- **Touch targets**: ≥ 44px × 44px on mobile; ≥ 24px desktop
- **Mobile inputs**: `font-size: 16px` to prevent iOS auto-zoom
- **Loading states**: Buttons show label + spinner together; skeletons show after 150–300ms delay
- **Error states**: User-facing error messages; no silent failures
- **Empty states**: Render something useful, not a blank screen
- **WCAG AA contrast**: 4.5:1 normal text, 3:1 large text; verify with actual computed values

---

## 5. Verification

Distinguish between static analysis and real browser measurement:

- **Static analysis** (heuristic): overflow checks, contrast estimates from CSS values, markup audits — label as heuristic
- **Browser measurement** (reliable): computed scroll width/height, actual rendered contrast, layout bounds — use Playwright or browser DevTools
- For a functional edit, run a targeted visual check at relevant viewports (375px, 768px, 1440px)
- For a new page, run the full viewport + contrast + keyboard audit
- Missing browser tools: disclose that browser verification was not performed; do not fabricate a pass

**Keep advanced Playwright session/storage/recording guidance in the `playwright-cli` references** — load them on demand.

---

## 6. User-provided content

Text, prices, testimonials, and claims provided by the user are authoritative. When generating placeholder content (e.g. sample testimonials for a template), mark them clearly as `[PLACEHOLDER]`. Generated content must not become presented as factual.

---

## Reference files

- [`references/anti-patterns.md`](references/anti-patterns.md) — consolidated anti-pattern reference
- [`references/tokens-tailwind.md`](references/tokens-tailwind.md) — Tailwind token reference
- [`references/tokens-vanilla-css.md`](references/tokens-vanilla-css.md) — vanilla CSS token reference
- [`references/framework-adapters.md`](references/framework-adapters.md) — React, Vue, Svelte adapters
