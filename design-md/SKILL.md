---
name: design-md
description: Design system specification and token manager. Ingests and enforces DESIGN.md brand guidelines, color palettes, typography hierarchies, and component styling rules from world-class developer tools (Linear, Vercel, Stripe, Raycast, Supabase, Apple, Figma, Resend). Use when styling or restyling an application to match an elite brand aesthetic.
---

# Design MD (Design System Specification Engine)

Adopt, generate, and enforce company-grade design systems and design tokens across full-stack applications.

---

## 1. How It Works

1. **Workspace Ingestion (Primary)**:
   - Check the project root for an existing `DESIGN.md` or design system configuration.
   - If present, parse its design tokens, color scales, spacing scales, typography pairings, and layout primitives.
   - **Always prioritize existing project tokens** over external presets. Do not overwrite established project guidelines unless explicitly asked to restyle.

2. **Contextual Preset Adoption (Optional)**:
   - If no project `DESIGN.md` exists, adopt an optional preset from `presets/` matched to the application's domain.
   - Presets are **contextual guidance, not rigid boilerplate**. Adapt tokens flexibly to fit the application's specific content and user needs.

3. **Application**:
   - Translate design tokens directly into Tailwind utility classes, CSS custom properties, or component library theme props.

---

## 2. Core Brand Presets

When creating a new design system or restyling without an existing `DESIGN.md`, choose the preset that matches the application domain:

### Apple Atmospheric Glass (`presets/apple.DESIGN.md`)
*Best for: Consumer applications, media tools, modern dashboards*
- **Canvas**: Fullscreen atmospheric dark or light gradients with subtle depth.
- **Surfaces**: Layered frosted glass: `backdrop-blur-xl bg-black/25 border border-white/10 text-white shadow-2xl rounded-2xl`.
- **Typography**: SF Pro / Inter: hero headings with light weights (`font-extralight tracking-tighter`), labels in high-contrast small caps (`text-[11px] font-semibold uppercase tracking-wider text-white/60`).

### Linear Dark Minimalist (`presets/linear.app.DESIGN.md`)
*Best for: Developer tools, issue trackers, high-density data tables*
- **Canvas**: `#08090a` · Surface: `#121316` · Border: `#222326` · Accent: `#5e6ad2`.
- **Typography**: Inter or Geist, `tabular-nums` on all numbers, crisp 12px/13px secondary metadata.
- **Components**: 1px subtle hairline borders, compact padding, keyboard shortcut badges (`⌘K`).

### Vercel Modern Monochrome (`presets/vercel.DESIGN.md`)
*Best for: Cloud infrastructure, developer portals, admin consoles*
- **Canvas**: Pure `#000000` · Cards: `#0a0a0a` · Borders: `#1f1f1f` · Text: `#ffffff`.
- **Typography**: Geist Sans & Geist Mono, high-contrast monochrome hierarchy.
- **Components**: Zero colored badge clutter, crisp status indicators, high-contrast black/white buttons.

### Stripe Vibrant Multi-Layer (`presets/stripe.DESIGN.md`)
*Best for: Fintech, payments, marketing landers, SaaS billing*
- **Canvas**: Clean neutral canvas with vibrant layered mesh/gradient backdrops.
- **Accent**: Blurple `#635bff`, rich indigo, and radiant secondary gradients.
- **Components**: Opulent card spacing, smooth multi-layer shadows, pill badges with semantic status colors.

---

## 3. Additional Bundled Presets

Available on-demand in `presets/`:
- **Developer & Studio**: [Supabase](presets/supabase.DESIGN.md), [Raycast](presets/raycast.DESIGN.md), [Cursor](presets/cursor.DESIGN.md), [Warp](presets/warp.DESIGN.md), [PostHog](presets/posthog.DESIGN.md)
- **Product & Creative**: [Figma](presets/figma.DESIGN.md), [Framer](presets/framer.DESIGN.md), [Resend](presets/resend.DESIGN.md), [Notion](presets/notion.DESIGN.md), [Claude](presets/claude.DESIGN.md), [Shopify](presets/shopify.DESIGN.md)

---

## 4. Implementation Guidelines

- **Token Discipline**: Avoid hardcoded hex colors or arbitrary values (e.g. `bg-[#1a2b3c]`) scattered across markup; reference defined CSS variables or Tailwind theme keys.
- **Responsive Primitives**: Ensure typography scales down cleanly on mobile (`text-3xl sm:text-5xl lg:text-7xl`).
- **Accessible Contrast**: All text color tokens must maintain WCAG AA minimum contrast (≥ 4.5:1 against their surface token).

---

## 5. Token Provenance & Change Record

When modifying or proposing design tokens, record token provenance so subsequent agents know what was established vs proposed:

```markdown
### 📐 Design-MD Change Record
* **Priority Order Applied**: [1. User Explicit Direction | 2. Local DESIGN.md | 3. Optional Preset]
* **Tokens Modified**:
  - `[token-name]`: `[old_value]` ➔ `[new_value]` (Provenance: [Approved / Proposed])
* **Scope**: Specific tokens updated; unselected presets kept unloaded.
```

