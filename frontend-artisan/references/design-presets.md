# Design System Brand Presets & Tokens

When creating a new design system, building UI, or restyling an application without an existing `DESIGN.md`, choose the preset that matches the application domain. Presets provide battle-tested tokens, color palettes, and typographic hierarchies.

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
- **Status**: Crisp semantic indicators (Accent dot `#0070f3` blue or `#50e3c2` teal), high-contrast pill action buttons

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

---

## 6. Supabase Emerald Matrix
*Best for: Developer backends, database consoles, SQL editors, hacker dashboards*
- **Canvas / Background**: `#121212` (Obsidian dark)
- **Surfaces**: `#181818` (Card background), `#242424` (Hovered row/border)
- **Borders & Dividers**: `1px solid #2e2e2e`
- **Accent**: `#3ecf8e` (Supabase emerald green), dark emerald hover `#34b27b`
- **Typography**: Inter Sans paired with JetBrains Mono / Fira Code for queries and tables
- **Components**: Terminal badge status, SQL code blocks, crisp emerald action buttons

---

## 7. Tailwind Catalyst Modern Clean
*Best for: Polished enterprise SaaS, modern web applications, client portals*
- **Canvas / Background**: `#ffffff` (Clean white) or `#0f172a` (Slate dark)
- **Surfaces**: `#f8fafc` (Slate 50), borders `#e2e8f0` (Slate 200)
- **Accent**: Indigo `#4f46e5` or Sky `#0284c7`
- **Typography**: Plus Jakarta Sans or Inter, balanced line-heights, clear visual weight hierarchy
- **Components**: Soft drop shadows (`shadow-sm`), refined input borders, pill badges with light backgrounds

---

## 8. Resend Exquisite Typography
*Best for: High-craft marketing, email platforms, design studios, developer documentation*
- **Canvas / Background**: Pure `#000000` with subtle dotted radial grid (`bg-[radial-gradient(#27272a_1px,transparent_1px)]`)
- **Typography**: Editorial contrast; micro-spaced headers (`tracking-tight`), crisp silver body (`text-zinc-400`), pure white headings
- **Accents**: Subtle white glow highlights, hair-line 1px borders (`border-white/10`)
- **Components**: Ultra-clean minimalist cards, zero garish badges, exquisite letter-spacing

---

## 9. GitHub High-Density Dev
*Best for: Code repositories, PR reviews, audit logs, issue boards*
- **Canvas / Background**: `#0d1117` (GitHub Dark Canvas)
- **Surfaces**: `#161b22` (Card surface), `#21262d` (Subtle header/button background)
- **Borders & Dividers**: `1px solid #30363d`
- **Accents**: GitHub Green `#238636` (Success/Merge), Blue `#58a6ff` (Links), Purple `#8957e5` (PRs)
- **Typography**: System font stack (`-apple-system, BlinkMacSystemFont`), mono labels
- **Components**: Octicon icons, high data density, compact table rows, commit SHA badges

---

## 10. Notion Calm Editorial
*Best for: Documentation, knowledge bases, note-taking apps, content publishing*
- **Canvas / Background**: Warm paper `#f7f6f3` (Light) or warm obsidian `#191919` (Dark)
- **Typography**: Editorial serif headers (Charter / Lyon / Lora / Georgia) paired with clean sans body
- **Surfaces**: Flat, unbordered cards with subtle hover tints (`hover:bg-black/5`)
- **Accents**: Warm earth tones, subtle pastel highlight pills (amber, olive, sage)
- **Components**: Tactile block handles, collapsible callout boxes, distraction-free reading width

---

## 11. Cyberpunk Neon Synthwave
*Best for: Gaming hubs, crypto web3 tools, creative studios, audio visualizers*
- **Canvas / Background**: Deep space `#0a0a14`
- **Surfaces**: `#121124` with neon edge glow (`box-shadow: 0 0 15px rgba(0, 240, 255, 0.15)`)
- **Borders & Dividers**: `1px solid #ff0055` / `rgba(0, 240, 255, 0.3)`
- **Accents**: Neon Cyan `#00f0ff`, Electric Magenta `#ff0055`, Acid Yellow `#ffe600`
- **Typography**: Space Grotesk / Orbitron headers with monospace technical readouts
- **Components**: Cyberpunk angled clipped corners (`clip-path`), scanline textures, glowing status pills
