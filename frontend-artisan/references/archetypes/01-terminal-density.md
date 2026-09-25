# Archetype 01: Terminal-Grade Density

**Inspiration**: Bloomberg Terminal, Zed Editor, Ghostty, Grafana, htop/btop, Linear's keyboard-first density.  
**Best for**: Developer tools, observability, trading platforms, log viewers, complex admin consoles for power users.

---

## 1. Core Hallmarks & Commitment
- **Extreme Information Density**: Monospace or tight neo-grotesk at 11–13px, with hairline 1px dividers instead of cards, nested boxes, or heavy shadows.
- **State via Color, Never Decoration**: Canvas is near-black or deep warm charcoal. 2–3 semantic accents only (Amber for warnings, Emerald for healthy/OK, Cyan for active row focus). Color denotes system state exclusively.
- **Keyboard-First Affordances**: Inline shortcut badges (`⌘K`, `J/K` navigation, `G G`), tabular numbers (`font-mono` / `tabular-nums`), and inline glyphs rather than bulky pill tags.

---

## 2. Palette & Tokens (WCAG 2.1 AA Compliant)

| Token Name | Light Mode Value | Dark Mode Value | Contrast Ratio |
| :--- | :--- | :--- | :--- |
| **Canvas** | `#f6f6f4` (`bg-[#f6f6f4]`) | `#0d0f12` (`bg-[#0d0f12]`) | Base surface |
| **Surface Elevated** | `#ecece9` (`bg-[#ecece9]`) | `#15181e` (`bg-[#15181e]`) | 1.2:1 to Canvas |
| **Grid / Hairlines** | `#d4d4ce` (`border-[#d4d4ce]`) | `#222630` (`border-[#222630]`) | 3:1 (UI Border) |
| **Text Primary** | `#18181b` (`text-zinc-900`) | `#f4f4f5` (`text-zinc-100`) | 16:1 (AAA) |
| **Text Muted** | `#52525b` (`text-zinc-600`) | `#9ca3af` (`text-zinc-400`) | 5.2:1 (AA) |
| **Status OK** | `#047857` (`text-emerald-700`) | `#10b981` (`text-emerald-400`)| 5.5:1 (AA) |
| **Status Warn** | `#b45309` (`text-amber-700`) | `#f59e0b` (`text-amber-400`) | 5.1:1 (AA) |
| **Active Row Focus** | `rgba(6, 182, 212, 0.08)` | `rgba(6, 182, 212, 0.12)` | Subtle focus band |

---

## 3. Tailwind CSS Recipe

```html
<!-- Terminal Density Table Container with Mobile Scroll Wrapper -->
<div class="w-full bg-[#0d0f12] text-zinc-300 font-mono text-xs border border-[#222630] rounded-none overflow-x-auto">
  <!-- Status Strip -->
  <div class="flex items-center justify-between px-3 py-1.5 bg-[#15181e] border-b border-[#222630] text-[11px] text-zinc-400">
    <div class="flex items-center gap-3">
      <span class="text-zinc-200 font-bold uppercase tracking-wider">CLUSTER-01</span>
      <span class="text-emerald-400 flex items-center gap-1">● RUNNING</span>
      <span>UPTIME 99.98%</span>
    </div>
    <div class="flex items-center gap-2">
      <span class="bg-[#222630] text-zinc-300 px-1.5 py-0.5 rounded text-[10px]">FILTER: ERR</span>
      <span class="text-zinc-500">ROWS: 1,482</span>
    </div>
  </div>

  <!-- Dense Table -->
  <table class="w-full border-collapse text-left whitespace-nowrap">
    <thead>
      <tr class="border-b border-[#222630] text-zinc-500 uppercase text-[10px] tracking-wider bg-[#0d0f12]">
        <th class="py-1.5 px-3 font-semibold">PID</th>
        <th class="py-1.5 px-3 font-semibold">PROCESS</th>
        <th class="py-1.5 px-3 font-semibold">CPU</th>
        <th class="py-1.5 px-3 font-semibold">MEM</th>
        <th class="py-1.5 px-3 font-semibold">STATUS</th>
        <th class="py-1.5 px-3 font-semibold text-right">ACTION</th>
      </tr>
    </thead>
    <tbody class="divide-y divide-[#222630]/60">
      <tr class="hover:bg-[#15181e] cursor-pointer transition-colors duration-75">
        <td class="py-1.5 px-3 text-zinc-400">04192</td>
        <td class="py-1.5 px-3 text-zinc-100 font-medium">worker.sync.pool</td>
        <td class="py-1.5 px-3 text-emerald-400">12.4%</td>
        <td class="py-1.5 px-3 text-zinc-300">412 MB</td>
        <td class="py-1.5 px-3 text-emerald-400">HEALTHY</td>
        <td class="py-1.5 px-3 text-right text-zinc-500"><kbd class="bg-[#222630] px-1 rounded text-[10px]">KILL</kbd></td>
      </tr>
      <tr class="bg-cyan-500/10 border-l-2 border-l-cyan-400 hover:bg-cyan-500/15 cursor-pointer">
        <td class="py-1.5 px-3 text-zinc-400">04198</td>
        <td class="py-1.5 px-3 text-cyan-200 font-medium">orch.diff.audit</td>
        <td class="py-1.5 px-3 text-amber-400">88.1%</td>
        <td class="py-1.5 px-3 text-zinc-300">1.2 GB</td>
        <td class="py-1.5 px-3 text-amber-400">AUDITING</td>
        <td class="py-1.5 px-3 text-right text-zinc-400"><kbd class="bg-[#222630] px-1 rounded text-[10px]">HALT</kbd></td>
      </tr>
    </tbody>
  </table>
</div>
```

---

## 4. The Traps to Avoid
- ❌ **Faking Density with Microscopic Unaligned Text**: True density requires strict column alignment, tabular font numerals (`tabular-nums`), and a clear visual focal row.
- ❌ **The "Hacker Green" Cosplay**: Avoid lime-green neon terminal text on pure black. High-craft tools like Zed and Bloomberg use nuanced slates, warm dark zincs, and muted semantic colors.
- ❌ **Mobile Viewport Crushing**: On small screens, never squish columns into illegible fragments; wrap in an `overflow-x-auto` container with sticky row headers.
