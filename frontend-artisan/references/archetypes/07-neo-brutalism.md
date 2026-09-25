# Archetype 07: Raw Neo-Brutalism / Anti-Design

**Inspiration**: Gumroad, Bloomberg Businessweek covers, early Balenciaga web experiments, brutalist editorial posters.  
**Best for**: Creator tools, indie software, developer campaigns, event websites, youth-oriented products where brand personality trumps corporate polish.

---

## 1. Core Hallmarks & Commitment
- **Stark Heavy Outlines**: Solid 2px–3px black borders (`border-2 border-black`) on all cards, buttons, and panels.
- **Hard Offset Shadows (Zero Blur)**: Sharp rectangular drop-shadows with zero blur radius (`shadow-[4px_4px_0px_#000]`).
- **Saturated Flat Fills**: High-energy, unblended colors (hot pink, electric lemon, cyan, acid green) on cream or stark white.
- **Stamp Click Physics**: Buttons snap directly into their shadow on click (`active:translate-x-1 active:translate-y-1 active:shadow-none`).

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| **Canvas** | `#fcf8ed` (`bg-[#fcf8ed]`) | Vintage warm cream |
| **Card Surface** | `#ffffff` (`bg-white`) | Clean stark white |
| **Black Border** | `#000000` (`border-2 border-black`) | Essential 2px outline |
| **Accent Electric Lemon**| `#ffe600` (`bg-[#ffe600]`) | 18:1 contrast with black text |
| **Accent Vermilion** | `#ff5a36` (`bg-[#ff5a36]`) | High-energy action pop |
| **Accent Acid Green** | `#00e575` (`bg-[#00e575]`) | 12:1 contrast with black text |

---

## 3. Tailwind CSS Recipe

```html
<!-- Neo-Brutalist Action Card -->
<div class="bg-white border-2 border-black rounded-lg p-6 shadow-[4px_4px_0px_#000] max-w-md font-sans">
  <div class="inline-block px-2.5 py-1 text-xs font-black uppercase tracking-wider bg-[#ffe600] text-black border border-black rounded mb-3">
    VERIFIED DEPLOYMENT
  </div>
  <h3 class="text-2xl font-black text-black tracking-tight leading-none mb-2">
    PARALLEL WORKTREES ACTIVE
  </h3>
  <p class="text-sm font-medium text-stone-800 mb-6 leading-relaxed">
    Zero merge conflicts. Isolated worker branches audited before coordinator merge.
  </p>
  <button class="w-full py-3 bg-[#ff5a36] text-white font-black text-sm uppercase tracking-wider border-2 border-black rounded shadow-[3px_3px_0px_#000] hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[4px_4px_0px_#000] active:translate-x-1 active:translate-y-1 active:shadow-none transition-all duration-100 cursor-pointer">
    Inspect Diff Audit →
  </button>
</div>
```

---

## 4. The Traps to Avoid
- ❌ **The Cookie-Cutter Neo-Brutalist Preset**: Applying black borders and pastel fills to a generic corporate SaaS page is now an AI cliché. Real neo-brutalism commits to bold voice, irreverent typography, and non-standard layouts.
