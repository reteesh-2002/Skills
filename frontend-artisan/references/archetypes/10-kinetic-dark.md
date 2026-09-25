# Archetype 10: Cinematic Dark Kinetic

**Inspiration**: Lusion, Active Theory, Apple Keynote product reveals, Linear release trailers, futuristic automotive interfaces.  
**Best for**: Flagship product launches, landing pages, high-impact hardware reveals, interactive hero showcases.

---

## 1. Core Hallmarks & Commitment
- **Zero-Dependency Kinetic Depth**: Achieved primarily through **native CSS 3D perspective** (`perspective: 1000px`), layered radial mesh lighting, and GPU-accelerated keyframe transforms (`transform: translate3d(...) rotateX(...)`).
- **Dramatic Ambient Lighting**: Pure void-black (`#050505`) backdrop illuminated by subtle, slowly oscillating ambient conic and radial gradients that backlight the content without muddying text contrast.
- **Optional Three.js Integration**: When Three.js or WebGL is explicitly supported in the target project, this archetype seamlessly connects to a background canvas shader while keeping all DOM text and buttons fully accessible.
- **Strict Accessibility Guardrail**: Full fallback support for `@media (prefers-reduced-motion: reduce)` which flattens 3D tilts into crisp, static high-contrast typography.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Hex Code / Tailwind | Purpose |
| :--- | :--- | :--- |
| **Void Canvas** | `#050505` (`bg-[#050505]`) | True cinematic deep black |
| **Glass Card Plate** | `rgba(255,255,255,0.03)` | Ultra-translucent specular layer |
| **Hairline Specular Rim** | `rgba(255,255,255,0.12)` | Subtle light catch on edges |
| **Headline White** | `#ffffff` (`text-white`) | 21:1 contrast on `#050505` |
| **Luminous Accent** | Luminous Cyan (`#00f2fe`) or Molten Amber (`#ff8c00`) | Ambient beam reflection |

---

## 3. Pure-CSS Tailwind Recipe (Zero Dependencies)

```html
<!-- Cinematic Kinetic Card with CSS 3D Perspective -->
<div class="relative max-w-lg mx-auto [perspective:1000px]">
  <!-- Ambient Radial Light Halo (Behind the card) -->
  <div class="absolute -inset-1 bg-gradient-to-r from-cyan-500/20 via-transparent to-amber-500/20 rounded-2xl blur-xl opacity-75"></div>

  <!-- Kinetic 3D Surface -->
  <div class="relative bg-[#080808]/90 text-white p-8 rounded-2xl border border-white/10 backdrop-blur-md shadow-2xl transition-transform duration-500 ease-out hover:[transform:rotateX(4deg)_rotateY(-4deg)_translateZ(10px)] motion-reduce:transform-none">
    
    <!-- Top Luminous Badge -->
    <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold tracking-wider uppercase bg-white/5 border border-white/10 text-cyan-300 mb-6">
      <span class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
      Autonomous Agent Core
    </div>

    <!-- Monumental Typography -->
    <h3 class="text-3xl md:text-4xl font-black tracking-tight leading-none text-white mb-3">
      KINEMATIC SPEED.
    </h3>
    <p class="text-sm text-neutral-400 font-normal leading-relaxed mb-6">
      Engineered for extreme responsiveness with zero-runtime CSS 3D perspective and hardware-accelerated transforms.
    </p>

    <!-- Kinetic Action Button -->
    <div class="flex items-center gap-4">
      <button class="px-6 py-2.5 bg-white text-black font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg hover:bg-neutral-200 active:scale-[0.98] transition-all duration-150 cursor-pointer">
        Initialize Engine
      </button>
      <span class="text-xs font-mono text-neutral-500">LATENCY: 0.4MS</span>
    </div>

  </div>
</div>
```

---

## 4. Optional Three.js / WebGL Integration Guide

When the host environment or project explicitly includes Three.js:
- Mount the canvas in a `fixed inset-0 -z-10 pointer-events-none` container.
- Keep all typography, interactive controls, and links in the HTML DOM above the canvas to maintain 100% keyboard accessibility and screen reader support.
- Throttle the render loop on inactive tabs using `requestAnimationFrame`.

---

## 5. The Traps to Avoid
- ❌ **Scroll-Jacking**: Never hijack native page scrolling for animation. Let the user control velocity.
- ❌ **Performance Meltdowns on Mobile**: Heavy GPU shader passes must degrade to clean static gradient overlays on mobile or battery-saver devices.
