# Archetype 08: Technical Blueprint / Schematic

**Inspiration**: Aeronautical charts (SkyVector), CAD tools (Onshape, Fusion 360), NASA technical specs, architecture schematics.  
**Best for**: Hardware products, developer API docs, network topologies, architecture diagrams, engineering tools.

---

## 1. Core Hallmarks & Commitment
- **Drafting Linework & Registration Marks**: Fine 1px hair-lines, corner registration crosshairs (`+`), and precise dimension callouts.
- **Schematic Annotation Texture**: Coordinate readouts (`X: 142.08, Y: 89.12`), revision tags (`REV: B.2`), and figure labels integrated as structural layout elements.
- **Drafting Palette**: Deep drafting blueprint blue (`#0c213b`) with white/pale-cyan linework, or clean drafting paper (warm white, graphite lines, single red-pencil accent).

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Drafting Blueprint (Dark) | Drafting Paper (Light) |
| :--- | :--- | :--- |
| **Canvas** | `#0a192f` (`bg-[#0a192f]`) | `#f6f4ee` (`bg-[#f6f4ee]`) |
| **Grid Lines** | `rgba(255,255,255,0.08)` | `rgba(0,0,0,0.06)` |
| **Linework & Marks** | `#8892b0` (`border-[#8892b0]`) | `#4b5563` (`border-gray-600`) |
| **Text Primary** | `#ccd6f6` (`text-[#ccd6f6]`) | `#1f2937` (`text-gray-900`) |
| **Red Pencil Accent**| `#ff5252` (`text-[#ff5252]`) | `#dc2626` (`text-red-600`) |

---

## 3. Tailwind CSS Recipe

```html
<!-- Technical Blueprint Panel with Corner Crosshairs -->
<div class="bg-[#0a192f] text-[#ccd6f6] font-mono text-xs p-6 border border-[#8892b0]/30 relative rounded-none max-w-xl">
  <!-- Corner Registration Marks -->
  <span class="absolute top-0 left-0 text-[#8892b0]/60 -translate-x-1/2 -translate-y-1/2 text-sm select-none">+</span>
  <span class="absolute top-0 right-0 text-[#8892b0]/60 translate-x-1/2 -translate-y-1/2 text-sm select-none">+</span>
  <span class="absolute bottom-0 left-0 text-[#8892b0]/60 -translate-x-1/2 translate-y-1/2 text-sm select-none">+</span>
  <span class="absolute bottom-0 right-0 text-[#8892b0]/60 translate-x-1/2 translate-y-1/2 text-sm select-none">+</span>

  <!-- Schematic Meta Header -->
  <div class="flex items-center justify-between border-b border-[#8892b0]/30 pb-2 text-[10px] text-[#8892b0] uppercase">
    <span>DWG NO: SCH-9902-A</span>
    <span>SCALE: 1:1</span>
    <span class="text-[#ff5252]">REV 04.2</span>
  </div>

  <div class="my-4 space-y-2">
    <div class="text-sm font-bold text-white uppercase tracking-wider">TOPOLOGY: WORKTREE MESH</div>
    <p class="text-xs text-[#8892b0] leading-relaxed">
      Parallel execution paths maintain independent working directories under .git/.orch-worktrees/.
    </p>
  </div>

  <!-- Dimension Indicator Strip -->
  <div class="flex items-center gap-2 pt-2 border-t border-[#8892b0]/30 text-[10px] text-[#8892b0]">
    <span>DIM: 12-15+ FILES</span>
    <span class="flex-1 border-t border-dashed border-[#8892b0]/40"></span>
    <span class="text-white font-bold">100% PARALLEL</span>
  </div>
</div>
```

---

## 4. The Traps to Avoid
- ❌ **Decorative Stock Overlays**: Scattering fake plus-signs and arbitrary random dimensions that mean nothing. Every coordinate and label should correspond to real architecture or metadata.
