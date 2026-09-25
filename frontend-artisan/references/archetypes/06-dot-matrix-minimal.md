# Archetype 06: Dot-Matrix / Segment-Display Minimalism

**Inspiration**: Nothing Phone (Nothing OS / Glyph Interface), Teenage Engineering Pocket Operators, vintage Casio watches, airport departure boards.  
**Best for**: Hardware companions, wearable UIs, minimalist clocks/timers, edge sensor widgets, compact dashboards.

---

## 1. Core Hallmarks & Commitment
- **Dot-Matrix / 7-Segment Readouts**: Reserved strictly for headlines, live metric counters, and status tickers. Body text remains crisp, clean sans-serif for legibility.
- **Extreme Monochromatic Discipline**: 100% black, white, and neutral grays, with exactly ONE signal accent (e.g. sharp LCD red or amber) for a hot alert.
- **Pattern Data Visuals**: Dot arrays, segment meters, and glyph bars replace standard rounded charts.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| **OLED Black** | `#000000` (`bg-black`) | Infinite contrast ground |
| **Phosphor White** | `#ffffff` (`text-white`) | 21:1 contrast ratio |
| **Grid Dots** | `#262626` (`border-neutral-800`) | Structural dot matrix pattern |
| **Hot Signal Red** | `#ff0033` (`bg-[#ff0033]` / `text-[#ff0033]`) | Single high-contrast alarm accent |

---

## 3. Tailwind CSS Recipe

```html
<!-- Dot-Matrix Minimalist Tile -->
<div class="bg-black text-white p-6 max-w-sm border border-neutral-800 rounded-none font-mono">
  <!-- Status Strip -->
  <div class="flex items-center justify-between text-[10px] tracking-widest text-neutral-400 uppercase">
    <span>NOTHING // TELEMETRY</span>
    <span class="inline-flex items-center gap-1.5"><span class="w-1.5 h-1.5 rounded-full bg-[#ff0033]"></span> LIVE</span>
  </div>

  <!-- Segment Counter Readout -->
  <div class="my-6">
    <div class="text-xs uppercase text-neutral-500 font-bold">ACTIVE WORKFLOWS</div>
    <div class="text-5xl font-black tracking-tighter text-white mt-1">
      08<span class="text-neutral-600">/12</span>
    </div>
  </div>

  <!-- Dot Array Meter (12 Dots) -->
  <div class="grid grid-cols-12 gap-1.5 py-2 border-t border-b border-neutral-900 my-4">
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-white"></div>
    <div class="h-2 bg-neutral-800"></div>
    <div class="h-2 bg-neutral-800"></div>
    <div class="h-2 bg-neutral-800"></div>
    <div class="h-2 bg-neutral-800"></div>
  </div>

  <!-- Accessible Clean Sans Body -->
  <p class="font-sans text-xs text-neutral-400 leading-normal">
    Workers executing within isolated git worktrees. Memory consumption nominal.
  </p>
</div>
```

---

## 4. The Traps to Avoid
- ❌ **Setting Body Copy in Dot-Matrix**: Renders small sentences completely unreadable. Always pair dot-matrix headlines with clean, readable sans-serif body copy.
