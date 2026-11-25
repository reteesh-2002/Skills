---
name: frontend-artisan
description: Frontend engineering and design orchestrator. Handles UI, CSS, component, DESIGN.md tokens, image-to-code, anti-slop layout rules, and web interface guidelines (keyboard navigation, touch targets, accessibility). Apply when building, styling, or refactoring web apps, landing pages, dashboards, or UI components. Explicit only — not auto-activated.
---

# Frontend Artisan

Deliver frontend work with intentional craft: correct layout, accessible interaction, appropriate visual quality, and honest verification. The approach scales to the task — a bug fix does not need a concept image; a new product page does.

---

## 1. Design Preset & Motion Selection (Step 0, Greenfield Only)

- **Existing Design / Targeted Edits / Bug Fixes**: Skip this step and adhere strictly to existing tokens or `DESIGN.md`.
- **New Page / Greenfield Concept**: If the user's prompt already implies an aesthetic (e.g. "Linear-style dark devtools", "clean Notion docs"), proceed directly with the closest preset. Only ask when the aesthetic is genuinely ambiguous.
- **Presets & Motion**: Load [`references/design-presets.md`](references/design-presets.md) (Linear Dark, Apple Glass, Vercel Monochrome, Stripe, Raycast, Supabase, Tailwind Catalyst, Resend, GitHub, Notion, Synthwave, or `DESIGN.md`) and [`references/motion-effects.md`](references/motion-effects.md) (Parallax, Sticky Cards, 3D Tilt, Magnetic Micro-Springs, Marquee, or Clean Static) on demand.

---

## 2. Image-to-Code Workflow

Once the design preset is confirmed, execute the 5-step image-to-code pipeline:

```
[1. Confirm Design] ──> [2. Inspect / Generate] ──> [3. Extract Decisions] ──> [4. Implement] ──> [5. Verify]
```

1. **Inspect or Generate Reference**:
   - **Supplied Reference Mode**: If the user provided a screenshot or mockup, inspect it directly using `read_file` (crop/zoom allowed to examine subtle borders, spacing, and typography).
   - **New Concept Mode**: Delegate to the `image-generator` subagent via `invoke_subagent` to establish a visual baseline matching the chosen design preset (16:9 for desktop/hero or 3:2). Generate at most 1 overview and 1 detail image maximum.
   - **Existing Design / Bugfix**: Skip image generation; adhere strictly to existing tokens.
2. **Extract Design Decisions**:
   - Identify exact canvas color, surface elevations, hairline borders (`1px border-white/10` or `border-slate-200`), font hierarchy, accent color, and interactive states.
3. **Implement**:
   - Translate extracted decisions into production code following [`references/interface-guidelines.md`](references/interface-guidelines.md).
4. **Verify**:
   - Verify layout stability, keyboard navigation, touch targets, and WCAG AA contrast.

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

## 7. Design-Source Decision & Output Format

Follow [`references/output-policy.md`](../references/output-policy.md). Every frontend delivery must document its governing design authority:

```markdown
### 🎨 Frontend Artisan: [Mode] — [Summary]
* **Design Source**: `[Existing project tokens (DESIGN.md) | Supplied reference (path/url) | Approved concept (preset)]`
* **Components / Surface**: [`file1.ext`](file:///...) (components styled), [`file2.ext`](file:///...)
* **States Preserved**: Loading, empty, error, focus-visible, and mobile responsive boundaries.
* **Verification Proof**: [Playwright browser measurement / Heuristic static scan] across 375px/768px/1440px.
```

---

## Reference files

- [`references/anti-patterns.md`](references/anti-patterns.md) — consolidated anti-pattern reference
- [`references/design-presets.md`](references/design-presets.md) — Linear, Apple, Vercel, Stripe brand presets
- [`references/motion-effects.md`](references/motion-effects.md) — Parallax scrolling, sticky stacking, 3D tilt, springs
- [`references/interface-guidelines.md`](references/interface-guidelines.md) — keyboard, touch, loading, CLS standards
- [`references/tokens-tailwind.md`](references/tokens-tailwind.md) — Tailwind token reference
- [`references/tokens-vanilla-css.md`](references/tokens-vanilla-css.md) — vanilla CSS token reference
- [`references/framework-adapters.md`](references/framework-adapters.md) — React, Vue, Svelte adapters

