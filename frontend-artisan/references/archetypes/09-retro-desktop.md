# Archetype 09: Retro-OS Desktop Metaphor

**Inspiration**: Poolsuite FM, Playdate OS, classic Mac System 7, Windows 95, Webamp.  
**Best for**: Media & music applications, personal creative portfolios, retro tools, indie onboarding experiences.

---

## 1. Core Hallmarks & Commitment
- **Real Draggable Window Chrome**: Title bars with functional close/minimize boxes, system bevels, retro scrollbars, and window stacking.
- **Warm Nostalgia (Not Neon Vaporwave)**: Muted warm palettes (faded teal, salmon, bone cream, 1-bit monochrome) resembling warm CRT displays or 90s personal computing.
- **Playful Tactility**: 1-bit icons, system-style pointer cursors, pixel-art details, and instant mechanical state feedback.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Classic System 7 (1-Bit) | Faded 90s OS |
| :--- | :--- | :--- |
| **Desktop Canvas** | `#808080` (Dithered gray) | `#2a7571` (Vintage OS Teal) |
| **Window Surface** | `#ffffff` (`bg-white`) | `#d4d0c8` (`bg-[#d4d0c8]`) |
| **Active Title Bar**| `#000000` / `#000080` | `#000080` (Navy) |
| **Bevel Highlights**| 1px solid `#ffffff` | 1px solid `#ffffff` |
| **Bevel Shadows** | 1px solid `#000000` | 1px solid `#808080` |

---

## 3. Tailwind CSS Recipe

```html
<!-- Retro OS Window -->
<div class="bg-[#d4d0c8] border-2 border-t-white border-l-white border-b-black border-r-black p-1 max-w-md shadow-md font-sans">
  <!-- Title Bar -->
  <div class="bg-[#000080] text-white px-2 py-1 flex items-center justify-between text-xs font-bold select-none">
    <div class="flex items-center gap-1.5">
      <span class="text-[10px]">💾</span>
      <span>System_Monitor.exe</span>
    </div>
    <div class="flex items-center gap-1">
      <button class="w-4 h-4 bg-[#d4d0c8] border border-t-white border-l-white border-b-black border-r-black text-black text-[9px] font-black flex items-center justify-center active:border-t-black active:border-l-black active:border-b-white active:border-r-white">_</button>
      <button class="w-4 h-4 bg-[#d4d0c8] border border-t-white border-l-white border-b-black border-r-black text-black text-[9px] font-black flex items-center justify-center active:border-t-black active:border-l-black active:border-b-white active:border-r-white">✕</button>
    </div>
  </div>

  <!-- Window Body -->
  <div class="bg-white border-2 border-t-black border-l-black border-b-white border-r-white p-4 m-1 text-xs text-black space-y-3 font-mono">
    <div class="flex items-center justify-between pb-2 border-b border-gray-200">
      <span>DISK DRIVE C:</span>
      <span class="font-bold text-emerald-700">ONLINE</span>
    </div>
    <div class="text-[11px] text-gray-700 leading-normal font-sans">
      Memory allocation nominal. 640K conventional memory available for execution.
    </div>
    <button class="px-4 py-1.5 bg-[#d4d0c8] border-2 border-t-white border-l-white border-b-black border-r-black text-xs font-bold text-black active:border-t-black active:border-l-black active:border-b-white active:border-r-white cursor-pointer">
      Run Diagnostics
    </button>
  </div>
</div>
```

---

## 4. The Traps to Avoid
- ❌ **Pastiche without Function**: If windows don't behave like windows, it's just costume jewelry. Avoid mixing incompatible eras (e.g. Win95 title bars with vaporwave neon statues).
