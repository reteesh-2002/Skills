---
name: design-md
description: Design system specification and token manager. Ingests and enforces DESIGN.md brand guidelines, color palettes, typography hierarchies, and component styling rules from world-class developer tools (Linear, Vercel, Stripe, Raycast, Supabase, Apple, Figma, Resend). Use when styling or restyling an application to match an elite brand aesthetic.
---

# Design MD (Design System Specification Engine)

Adopt, generate, and strictly enforce company-grade `DESIGN.md` specifications across any frontend codebase.

## 1. How It Works

1. **Workspace Ingestion**:
   - Check the project root for a `DESIGN.md`. If present, parse its design tokens, color scales, spacing scales, typography pairings, and layout primitives.
2. **Preset Activation**:
   - If no project `DESIGN.md` exists, you can adopt any of the 15 bundled flagship company presets in `presets/`:
     - `linear.app.DESIGN.md`: Ultra-clean dark minimalism, tabular numbers, `#5e6ad2` indigo.
     - `vercel.DESIGN.md`: High-contrast black/white mono, Geist typography, hairline borders.
     - `stripe.DESIGN.md`: Vibrant multi-layer gradients, opulent spacing, blurple `#635bff`.
     - `supabase.DESIGN.md`: Dark developer studio with `#3ecf8e` emerald accents.
     - `raycast.DESIGN.md`: Compact keyboard-centric command palette styling.
     - `resend.DESIGN.md`: Stark monochrome with warm accents.
     - `apple.DESIGN.md`, `figma.DESIGN.md`, `framer.DESIGN.md`, `posthog.DESIGN.md`, `claude.DESIGN.md`, `notion.DESIGN.md`, `warp.DESIGN.md`.
3. **Application**:
   - Translate the design tokens directly into Tailwind classes, CSS custom properties, or framework component props.
