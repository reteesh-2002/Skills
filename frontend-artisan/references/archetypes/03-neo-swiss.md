# Archetype 03: Neo-Swiss / International Typographic

**Inspiration**: Ableton, Pentagram, Vercel Geist design system, Josef Müller-Brockmann, Stripe Press print layouts.  
**Best for**: Design tools, creative platforms, architectural studios, B2B platforms seeking timeless typographic authority without generic SaaS decoration.

---

## 1. Core Hallmarks & Commitment
- **Asymmetric Visible Grid**: High-contrast, mathematically disciplined grid structure with visible structural hairline rules and large flush-left headlines.
- **Neo-Grotesk Family Rigor**: Uses a single neutral neo-grotesk (Neue Haas, Helvetica Now, Geist, Inter tightly tracked) in 2–3 weights, with oversized section numbers and uppercase micro-labels.
- **Radical Negative Space**: Generous whitespace, absence of rounded pill badges or gradients, and clinical, confident typography.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Light Mode Value | Dark Mode Value |
| :--- | :--- | :--- |
| **Paper Canvas** | `#f8f8f7` (`bg-[#f8f8f7]`) | `#0d0d0d` (`bg-[#0d0d0d]`) |
| **Structural Rule** | `#e2e2df` (`border-[#e2e2df]`) | `#222222` (`border-[#222222]`) |
| **Type Ink** | `#111111` (`text-[#111111]`) | `#f5f5f5` (`text-[#f5f5f5]`) |
| **Type Secondary** | `#4a4a47` (`text-[#4a4a47]`) | `#8a8a85` (`text-[#8a8a85]`) |
| **National Accent** | International Orange (`#e03131`) or Cobalt (`#1864ab`)| Vibrant Signal Yellow (`#fcc419`) |

---

## 3. Tailwind CSS Recipe

```html
<!-- Neo-Swiss Section with Asymmetrical Grid -->
<section class="bg-[#f8f8f7] text-[#111111] p-6 md:p-12 border-t-2 border-[#111111]">
  <div class="grid grid-cols-1 md:grid-cols-12 gap-8 items-baseline">
    <!-- Column 1: Index Number & Micro-Label -->
    <div class="md:col-span-3 space-y-1">
      <span class="text-xs uppercase tracking-widest font-mono text-[#4a4a47] block">[ 01 ] SPECIFICATION</span>
      <span class="text-5xl font-black tracking-tight block">10.0</span>
    </div>

    <!-- Column 2: Flush-Left Bold Headline -->
    <div class="md:col-span-6">
      <h2 class="text-3xl md:text-4xl font-extrabold tracking-tight leading-none text-[#111111]">
        STRUCTURAL DISCIPLINE IN DIGITAL SYSTEMS
      </h2>
      <p class="text-base text-[#4a4a47] mt-4 leading-relaxed font-normal">
        Swiss typography prioritizes universal communication through asymmetric layout, objective presentation, and absolute geometric clarity.
      </p>
    </div>

    <!-- Column 3: Saturated Accent Callout -->
    <div class="md:col-span-3 border-t md:border-t-0 md:border-l border-[#e2e2df] pt-4 md:pt-0 md:pl-6 space-y-3">
      <span class="inline-block w-3 h-3 bg-[#e03131]"></span>
      <div class="text-xs font-mono uppercase text-[#4a4a47]">NORMATIVE RULE</div>
      <p class="text-xs text-[#111111] font-medium leading-normal">
        All columns align strictly to baseline increments. No gratuitous decorative cards.
      </p>
    </div>
  </div>
</section>
```

---

## 4. The Traps to Avoid
- ❌ **Inter + Lots of Whitespace $\neq$ Swiss**: Without a committed visible grid, oversized index numbers, and stark typographical contrast, it devolves into an empty generic template.
