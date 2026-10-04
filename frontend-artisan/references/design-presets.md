# Design System Brand Presets & Tokens

When creating a new design system or restyling without an existing `DESIGN.md`, choose the preset that matches the application domain. Presets provide contextual tokens, not rigid constraints.

---

## 1. Linear Dark Minimalist
*Best for: Developer tools, issue trackers, dashboards, high-density data tables*
- **Canvas / Background**: `#08090a` (Deep cosmic black)
- **Surfaces**: `#121316` (Card background), `#1b1c20` (Hovered row/card)
- **Borders & Dividers**: `1px solid #222326` (Subtle hairline divider)
- **Accent**: `#5e6ad2` (Linear blurple/indigo), active hover `#6875e5`
- **Typography**: Inter or Geist, `tabular-nums` on all metrics/numbers, 12px/13px secondary metadata
- **Components**: Compact padding (`px-3 py-1.5`), keyboard shortcut badges (`⌘K`), subtle status dots

---

## 2. Apple Atmospheric Glass
*Best for: Consumer applications, media tools, weather/audio, modern dashboards*
- **Canvas**: Fullscreen atmospheric gradient with subtle depth and dynamic lighting
- **Surfaces**: Layered frosted glass: `backdrop-blur-xl bg-black/25 border border-white/10 text-white shadow-2xl rounded-2xl`
- **Typography**: SF Pro / Inter: hero headings with light weights (`font-extralight tracking-tighter`), labels in high-contrast small caps (`text-[11px] font-semibold uppercase tracking-wider text-white/60`)
- **Accents**: Radiant translucent highlights, smooth spring animations (`ease-out duration-300`)

---

## 3. Vercel Modern Monochrome
*Best for: Cloud infrastructure, developer portals, settings, admin consoles*
- **Canvas**: Pure `#000000` · Cards: `#0a0a0a` · Borders: `#1f1f1f` · Text: `#ffffff`
- **Typography**: Geist Sans & Geist Mono, high-contrast monochrome hierarchy
- **Accents**: Pure black and white contrast; zero colored badge clutter
- **Status**: Crisp semantic indicators (Green dot `#0070f3` or `#50e3c2`), high-contrast pill action buttons

---

## 4. Stripe Vibrant Multi-Layer
*Best for: Fintech, payments, SaaS marketing landers, billing portals*
- **Canvas**: Crisp neutral light canvas (`#f8fafc`) with layered mesh/gradient backdrops
- **Accent**: Blurple `#635bff`, rich indigo `#4f46e5`, radiant secondary gradients
- **Surfaces**: Opulent card spacing, smooth multi-layer shadows (`shadow-sm hover:shadow-md`)
- **Components**: Pill badges with semantic status colors, generous hit areas, refined micro-copy

---

## 5. Raycast High-Contrast Fast
*Best for: Command bars, quick switchers, high-efficiency keyboard workflows*
- **Canvas**: `#111111` · Surfaces: `#1a1a1a` · Focus: `#ff6363` (Raycast coral red)
- **Keyboard Affordance**: Prominent keyboard hints (`↵ to open`, `⇥ for actions`, `Esc to clear`)
- **Density**: Single-line list rows, crisp leading icons, zero nested card boxes
