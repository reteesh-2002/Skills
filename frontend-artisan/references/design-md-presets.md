# DESIGN.md Presets & Design System Ingestion

Inspired by [Awesome Design MD](https://github.com/voltagent/awesome-design-md).

`frontend-artisan` automatically checks for a `DESIGN.md` in the workspace root. If present, it takes absolute precedence over all generic styling. When no `DESIGN.md` exists, you can explicitly select from one of these curated design system presets:

## Preset 1: Linear Dark Minimalist
- **Core Philosophy**: Ultra-clean, dark, keyboard-centric product design.
- **Palette**:
  - Background: `#08090a` (canvas), `#101114` (surface/card)
  - Borders: `#1f2128` (subtle border), `#2e323d` (active border)
  - Text: `#f7f8f8` (primary), `#8a8f98` (secondary), `#62666d` (tertiary)
  - Accent: `#5e6ad2` (indigo primary), `#6872db` (hover)
- **Geometry**: `rounded-md` (6px) or `rounded-lg` (8px). 1px crisp borders.
- **Typography**: Inter / Geist Sans. Strict tabular numbers for metrics (`font-mono tabular-nums`).

## Preset 2: Vercel Monochrome Modern
- **Core Philosophy**: High-contrast, monochromatic precision with razor-sharp typography.
- **Palette**:
  - Background: `#000000` (dark), `#ffffff` (light)
  - Surfaces: `#0a0a0a` / `#111111`
  - Borders: `#222222` / `#eaeaea`
  - Text: `#ffffff` / `#000000` (100% contrast headers), `#888888` / `#666666` (body)
  - Accent: Pure white/black invert; blue `#0070f3` used strictly for system links.
- **Geometry**: `rounded-sm` (4px) or `rounded-md` (6px). Hairline borders (`border border-neutral-200 dark:border-neutral-800`).
- **Typography**: Geist Sans & Geist Mono. High density, clean tabular metrics.

## Preset 3: Stripe Editorial Opulence
- **Core Philosophy**: Vibrant gradients, expansive white space, friendly typography, and rich visual depth.
- **Palette**:
  - Background: `#ffffff` (light), `#0a2540` (dark hero)
  - Text: `#0a2540` (slate navy headers), `#425466` (muted body)
  - Accent: `#635bff` (Stripe blurple), `#00d4aa` (mint green), `#ff7b00` (sunset orange)
- **Geometry**: `rounded-2xl` (16px) or `rounded-full` pills. Multi-layered soft drop shadows (`shadow-[0_13px_27px_-5px_rgba(50,50,93,0.25),0_8px_16px_-8px_rgba(0,0,0,0.3)]`).
- **Typography**: Sohne / Inter paired with expressive editorial serif accents.

## Preset 4: Supabase Emerald Studio
- **Core Philosophy**: Developer-focused hacker utility with rich emerald dark mode accents.
- **Palette**:
  - Background: `#171717` (app base), `#1c1c1c` (surface)
  - Borders: `#2e2e2e`
  - Text: `#ededed` (primary), `#9e9e9e` (secondary)
  - Accent: `#3ecf8e` (Supabase emerald), `#2bb879` (hover)
- **Geometry**: `rounded-md` (6px). Dark matte cards with emerald glow on active focus.
