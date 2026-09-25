# Archetype 05: Tactile Hardware Skeuomorphism

**Inspiration**: Teenage Engineering (OP-1, TX-6, field guides), Braun & Dieter Rams audio equipment, Ableton Push, Playdate handheld.  
**Best for**: Music synthesizers, creative audio tools, timers, smart-home dashboards, interactive physical controllers.

---

## 1. Core Hallmarks & Commitment
- **Physical Controls & Detents**: Rotary knobs, slider faders, physical push buttons with deep click depression (`active:translate-y-0.5 active:scale-[0.98]`), and illuminated LED indicators.
- **Industrial Silkscreen Labels**: Tiny uppercase labels (9–11px bold sans), serial numbers, and part-number markings.
- **Consistent Light Direction**: Realistic, subtle highlight bevels and drop shadows that share a single unified light source.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Value | Purpose |
| :--- | :--- | :--- |
| **Aluminum Matte Body** | `#e8e6e1` (`bg-[#e8e6e1]`) | Anodized aluminum chassis |
| **Dark Rubber Grip** | `#1c1b18` (`bg-[#1c1b18]`) | Rotary knobs / toggles |
| **Silkscreen Text** | `#33312b` (`text-[#33312b]`) | 9.4:1 contrast on chassis |
| **Safety Orange Accent** | `#ff5c00` (`bg-[#ff5c00]`) | Teenage Engineering signature pop |
| **Active LED Green** | `#00e575` (`text-[#00e575]`) | Hardware status indicator |

---

## 3. Tailwind CSS Recipe

```html
<!-- Hardware Control Plate -->
<div class="bg-[#e8e6e1] border-2 border-[#c7c4bb] rounded-xl p-6 max-w-lg shadow-[inset_0_1px_0_rgba(255,255,255,0.8),0_4px_8px_rgba(0,0,0,0.06)] font-sans">
  <!-- Silkscreen Header -->
  <div class="flex items-center justify-between pb-4 border-b border-[#c7c4bb] text-[10px] font-bold tracking-widest text-[#5c584e] uppercase">
    <span>SYNTH-UNIT // OP-01</span>
    <span class="inline-flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#ff5c00] shadow-[0_0_6px_#ff5c00]"></span> PWR ON</span>
  </div>

  <!-- Tactile Control Bank -->
  <div class="grid grid-cols-3 gap-4 mt-6">
    <!-- Push Button 1 -->
    <button class="bg-[#f2f1ed] border border-[#b8b5ab] rounded-lg p-4 flex flex-col items-center justify-center shadow-[0_3px_0_#9e9b92,0_4px_6px_rgba(0,0,0,0.08)] active:translate-y-[3px] active:shadow-none transition-all duration-75 text-[#33312b]">
      <span class="text-xs font-black uppercase">TRIG 1</span>
      <span class="text-[9px] text-[#736e62] mt-1 font-mono">0.25S</span>
    </button>

    <!-- Push Button 2 (Safety Orange) -->
    <button class="bg-[#ff5c00] border border-[#cc4a00] rounded-lg p-4 flex flex-col items-center justify-center shadow-[0_3px_0_#993700,0_4px_6px_rgba(0,0,0,0.1)] active:translate-y-[3px] active:shadow-none transition-all duration-75 text-white">
      <span class="text-xs font-black uppercase">RECORD</span>
      <span class="text-[9px] text-white/80 mt-1 font-mono">ARMED</span>
    </button>

    <!-- Push Button 3 (Dark Rubber) -->
    <button class="bg-[#1c1b18] border border-black rounded-lg p-4 flex flex-col items-center justify-center shadow-[0_3px_0_#0a0a09,0_4px_6px_rgba(0,0,0,0.15)] active:translate-y-[3px] active:shadow-none transition-all duration-75 text-white">
      <span class="text-xs font-black uppercase">MUTE</span>
      <span class="text-[9px] text-stone-400 mt-1 font-mono">CH-01</span>
    </button>
  </div>
</div>
```

---

## 4. The Traps to Avoid
- ❌ **2010 Skeuomorphism Relapse**: Blindly applying heavy outer glow and generic drop-shadows. Real hardware tactility depends on tight, consistent 2–3px physical extrusion and believable materials.
