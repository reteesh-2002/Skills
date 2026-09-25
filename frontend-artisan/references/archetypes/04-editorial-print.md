# Archetype 04: Luxury Editorial Print

**Inspiration**: Kinfolk, Monocle, Apartamento, Aesop, The New York Times T Magazine.  
**Best for**: Long-form publishing, luxury e-commerce, architectural journals, reading/note applications, high-end portfolios.

---

## 1. Core Hallmarks & Commitment
- **High-Contrast Serif & Drop-Caps**: Striking, elegant display serif headlines paired with a quiet, highly legible sans or mono for captions.
- **Printed Ink Atmosphere**: Warms neutrals (bone, ecru, newsprint ivory, ink black) with muted earth accents (oxblood, moss, terracotta). Color feels like printed ink on heavyweight stock, never bright screen luminescence.
- **Folios & Hairlines**: Page folios (issue numbers, volume tags, date stamps), fine 1px hairline rules, and generous literary margins.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Light Mode Value | Dark Mode Value |
| :--- | :--- | :--- |
| **Heavy Newsprint** | `#f9f8f5` (`bg-[#f9f8f5]`) | `#121211` (`bg-[#121211]`) |
| **Printer Ink** | `#1a1918` (`text-[#1a1918]`) | `#f0eee8` (`text-[#f0eee8]`) |
| **Muted Caption** | `#63605a` (`text-[#63605a]`) | `#9c988f` (`text-[#9c988f]`) |
| **Divider Rule** | `#e6e3db` (`border-[#e6e3db]`) | `#292724` (`border-[#292724]`) |
| **Editorial Accent** | Oxblood (`#7c2d12`) / Moss (`#3f6212`) | Deep Amber / Terracotta |

---

## 3. Tailwind CSS Recipe

```html
<article class="bg-[#f9f8f5] text-[#1a1918] max-w-4xl mx-auto p-6 md:p-12 font-serif border border-[#e6e3db]">
  <!-- Folio Header -->
  <div class="flex items-center justify-between border-b border-[#e6e3db] pb-3 text-xs font-sans uppercase tracking-widest text-[#63605a]">
    <span>Issue 04 • Architectural Notes</span>
    <span>Autumn Edition</span>
    <span>Folio 148</span>
  </div>

  <!-- Headline & Subtitle -->
  <header class="my-8 md:my-12">
    <h1 class="text-3xl md:text-5xl font-normal tracking-tight text-[#1a1918] leading-tight">
      The Geometry of Unhurried Interfaces
    </h1>
    <p class="font-sans text-sm md:text-base text-[#63605a] mt-3 font-normal max-w-xl">
      On the intentional restraint of motion, typographical pacing, and the quiet dignity of printed space.
    </p>
  </header>

  <!-- Content with Drop Cap -->
  <div class="text-base md:text-lg leading-relaxed space-y-6 text-[#1a1918]/90 font-serif">
    <p class="first-letter:text-5xl first-letter:font-normal first-letter:float-left first-letter:mr-3 first-letter:leading-none">
      When digital spaces prioritize physical tranquility over algorithmic agitation, the interface ceases to demand attention and instead offers contemplation.
    </p>
  </div>
</article>
```

---

## 4. The Traps to Avoid
- ❌ **Slapping a Serif on a SaaS Dashboard**: Editorial print requires genuine literary rhythm, deliberate captions, and generous margins.
