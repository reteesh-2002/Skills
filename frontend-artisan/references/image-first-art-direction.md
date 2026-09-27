# Image-First Art Direction & Anti-Slop Protocol

Inspired by [Taste Skill](https://tasteskill.dev) and the `image-to-code` discipline.

## 1. The Core Image-First Mandate

When implementing landing pages, hero sections, marketing sites, or brand interfaces:
1. **Never Code Blindly**: AI models left to pure code generation converge on repetitive clichés:
   - Nested card spam ("cards inside cards inside cards").
   - Cramped hero sections with tiny text squeezed on a laptop screen.
   - Low-contrast purple/indigo gradient backdrops.
   - Pill and badge overload with fake SaaS buzzwords.
2. **Order of Operations**:
   - **Step 1: Visual Generation**: For major visual designs, generate a reference design image using `generate_image`. Choose an appropriate aspect ratio (`16:9` for heroes, `3:2` for cards/sections, `1:1` for components).
   - **Step 2: Deep Extraction**: Inspect the generated image for:
     - Background tonal warmth and texture (e.g. noise overlay, warm stone `#f5f4f2`, stark obsidian `#0a0a0a`).
     - Dominant typographic scale (display serif vs. geometric sans vs. technical mono).
     - Spatial hierarchy and asymmetrical layout rhythm.
     - Focal point and negative space generosity.
   - **Step 3: Pixel-Accurate Implementation**: Code the interface faithfully matching the extracted visual tokens while strictly respecting responsive web standards.

## 2. Anti-Slop Layout Invariants

- **The Anti-Card Rule**:
  - Do NOT wrap every section, feature, and statistic in a rounded card with a border. Use generous whitespace, hairline rule dividers (`border-t border-neutral-200/60`), editorial columns, or background tonal shifts instead.
- **The Spacious Hero**:
  - The hero must feel open and breathable. Keep key copy readable without scrolling on a standard 13-inch laptop (height $\sim 800\text{px}$).
  - Avoid cramming 15 different badges, icons, and CTAs into the first screen.
- **Typography Dignity**:
  - Pair an expressive headline face (e.g. serif, high-contrast grotesque) with a clean, high-legibility body sans.
  - Never set body copy in decorative, dot-matrix, or handwriting fonts.
- **Zero Monotonous AI Gradients**:
  - Replace generic `from-purple-600 to-indigo-600` gradients with curated color harmonies:
    - Warm Stone & Terracotta (`#f5f4f2` base, `#151515` ink, `#ff6b00` ember accent)
    - Deep Obsidian & Emerald (`#09090b` base, `#fafafa` ink, `#10b981` emerald accent)
    - Neo-Swiss Stark (`#ffffff` base, `#000000` ink, `#dc2626` safety red accent)
    - High-Tech Blueprint (`#0b132b` navy, `#e0e1dd` chalk, `#48cae4` cyan wireframe)
