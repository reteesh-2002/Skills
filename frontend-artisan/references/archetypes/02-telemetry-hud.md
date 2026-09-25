# Archetype 02: Mission-Control Telemetry HUD

**Inspiration**: SpaceX Dragon touchscreen avionics, F1 live-timing dashboards, Flightradar24, NASA JPL Eyes on the Solar System, aircraft glass cockpits.  
**Best for**: Infrastructure telemetry, IoT & edge devices, robotics control, real-time logistics, drone feeds, live analytics.

---

## 1. Core Hallmarks & Commitment
- **Instrument Cluster Architecture**: Segmented cockpit panels with labeled perimeter corners, live-updating numerals, and thin circular/linear gauge arcs.
- **Extreme Scale Contrast**: Massive primary readouts (32–48px bold mono) immediately adjacent to microscopic uppercase unit labels (10px tracking-widest).
- **Ambient Coordinates & Timestamps**: UTC timestamps, frame counters, and lat/long coordinates integrated as structural ambient texture.
- **Single-Signal Alert Logic**: The UI remains deep charcoal and gray. Red or magenta alert rings appear *only* when a threshold breaches, acting as a genuine emergency alarm.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Hex Code / Tailwind | Purpose |
| :--- | :--- | :--- |
| **Cockpit Background** | `#0a0c10` (`bg-[#0a0c10]`) | Deep avionics void |
| **Panel Surface** | `#12151c` (`bg-[#12151c]`) | Segmented instrument plate |
| **Hairline Dividers** | `#1e2430` (`border-[#1e2430]`) | 1px precision structural frames |
| **Primary Telemetry** | `#f0f4f8` (`text-[#f0f4f8]`) | Bright instrument readouts |
| **Muted Metadata** | `#6e7a8e` (`text-[#6e7a8e]`) | 4.8:1 contrast on `#12151c` (Passes AA) |
| **Signature Accent** | `#ff6b00` (`text-[#ff6b00]`) | Safety / Telemetry Amber-Orange |
| **Critical Alarm** | `#ff2a5f` (`bg-[#ff2a5f]`) | Real anomaly flash state |

---

## 3. Tailwind CSS Recipe

```html
<!-- Cockpit Instrument Panel -->
<div class="bg-[#0a0c10] text-[#f0f4f8] font-mono p-4 border border-[#1e2430] rounded-lg space-y-4">
  <!-- Top Telemetry Header -->
  <div class="flex items-center justify-between border-b border-[#1e2430] pb-2 text-[10px] text-[#6e7a8e] uppercase tracking-widest">
    <span>SYS.TELEMETRY // ORBIT-2</span>
    <span class="text-stone-300 font-bold">UTC 19:24:12.842</span>
    <span class="text-[#ff6b00] flex items-center gap-1">● CARRIER LOCKED</span>
  </div>

  <!-- Telemetry Cluster (Single column on mobile, 3-col on desktop) -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
    <!-- Readout 1: Velocity -->
    <div class="bg-[#12151c] border border-[#1e2430] p-4 rounded relative overflow-hidden">
      <div class="text-[10px] uppercase tracking-wider text-[#6e7a8e]">Velocity (Orbital)</div>
      <div class="flex items-baseline gap-2 my-2">
        <span class="text-4xl font-black tracking-tight text-white">7,814</span>
        <span class="text-xs text-[#ff6b00] font-bold">M/S</span>
      </div>
      <!-- Thin Linear Gauge -->
      <div class="w-full bg-[#1e2430] h-1 rounded-full overflow-hidden">
        <div class="bg-[#ff6b00] h-full" style="width: 82%"></div>
      </div>
      <div class="flex justify-between text-[9px] text-[#6e7a8e] mt-1">
        <span>0</span>
        <span>STAGE-2 MAX: 9,200</span>
      </div>
    </div>

    <!-- Readout 2: Hull Pressure -->
    <div class="bg-[#12151c] border border-[#1e2430] p-4 rounded">
      <div class="text-[10px] uppercase tracking-wider text-[#6e7a8e]">Cabin Pressure</div>
      <div class="flex items-baseline gap-2 my-2">
        <span class="text-4xl font-black tracking-tight text-white">101.3</span>
        <span class="text-xs text-emerald-400 font-bold">KPA</span>
      </div>
      <div class="w-full bg-[#1e2430] h-1 rounded-full overflow-hidden">
        <div class="bg-emerald-400 h-full" style="width: 95%"></div>
      </div>
      <div class="text-[9px] text-emerald-400 mt-1">NOMINAL RANGE</div>
    </div>

    <!-- Readout 3: Thermal Anomaly Sensor -->
    <div class="bg-[#12151c] border border-[#1e2430] p-4 rounded flex flex-col justify-between">
      <div class="flex justify-between items-center text-[10px] text-[#6e7a8e] uppercase">
        <span>Thermal P9</span>
        <span class="bg-emerald-950 text-emerald-300 border border-emerald-800 px-1 rounded text-[9px]">NORMAL</span>
      </div>
      <div class="my-2">
        <span class="text-3xl font-black text-white">+42.8°</span>
        <span class="text-xs text-[#6e7a8e]">C</span>
      </div>
      <div class="text-[9px] text-[#6e7a8e] font-mono">SENSOR ID: THM-X-9981</div>
    </div>
  </div>
</div>
```

---

## 4. The Traps to Avoid
- ❌ **Decorative Sci-Fi Tropes**: Rotating ornamental rings, fake glowing borders, and unmapped charts turn software into a video game costume. Every line must describe a real measurement.
- ❌ **Rainbow Charts**: Telemetry works through monochrome restraint with one high-contrast accent. Multiple rainbow colors degrade operational focus.
