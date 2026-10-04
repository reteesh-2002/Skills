# Motion, Parallax & Interactive Effects Reference

Production engineering standards and implementations for rich interactive effects, parallax scrolling, 3D tilt, and micro-interactions.

---

## 1. Parallax Scrolling Effects

### A. Multi-Layer Differential Parallax (Hero / Landers)
Create atmospheric depth where background stars/mesh move slower than foreground typography:
- **Implementation (Pure CSS / Lightweight)**:
  ```css
  .parallax-container {
    perspective: 1px;
    height: 100vh;
    overflow-x: hidden;
    overflow-y: auto;
  }
  .parallax-layer-back {
    transform: translateZ(-1px) scale(2);
    z-index: -1;
  }
  .parallax-layer-fore {
    transform: translateZ(0);
  }
  ```
- **Implementation (React / Framer Motion)**:
  ```tsx
  import { useScroll, useTransform, motion } from "framer-motion";

  export function ParallaxHero() {
    const { scrollY } = useScroll();
    const yBg = useTransform(scrollY, [0, 500], [0, 150]); // slower
    const yText = useTransform(scrollY, [0, 500], [0, -50]); // faster / lift

    return (
      <div className="relative h-screen overflow-hidden">
        <motion.div style={{ y: yBg }} className="absolute inset-0 bg-cover bg-center" />
        <motion.h1 style={{ y: yText }} className="relative z-10">Hero Title</motion.h1>
      </div>
    );
  }
  ```

---

## 2. Scroll-Driven Sticky Stacking Cards
Cards that scroll in, stick to the top, and subsequent cards slide over them with subtle scale down:
- **Pure CSS Sticky Stacking**:
  ```html
  <div class="space-y-8">
    <div class="sticky top-20 rounded-2xl bg-zinc-900 border border-white/10 p-8 shadow-2xl">
      Card 1
    </div>
    <div class="sticky top-24 rounded-2xl bg-zinc-800 border border-white/10 p-8 shadow-2xl">
      Card 2
    </div>
    <div class="sticky top-28 rounded-2xl bg-zinc-700 border border-white/10 p-8 shadow-2xl">
      Card 3
    </div>
  </div>
  ```

---

## 3. Cursor Spotlight & 3D Tilt Card

### A. Mouse Spotlight Border / Glow
A radial gradient that follows the user's cursor across cards (Linear/Raycast style):
```tsx
function SpotlightCard({ children }: { children: React.ReactNode }) {
  const [coords, setCoords] = React.useState({ x: 0, y: 0 });

  return (
    <div
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        setCoords({ x: e.clientX - rect.left, y: e.clientY - rect.top });
      }}
      className="group relative overflow-hidden rounded-xl border border-white/10 bg-zinc-950 p-6"
    >
      <div
        className="pointer-events-none absolute -inset-px opacity-0 transition duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(600px circle at ${coords.x}px ${coords.y}px, rgba(255,255,255,0.08), transparent 40%)`,
        }}
      />
      {children}
    </div>
  );
}
```

### B. 3D Gyroscopic Card Tilt
Card tilts in 3D perspective based on mouse cursor position:
```tsx
function TiltCard({ children }: { children: React.ReactNode }) {
  const [rotation, setRotation] = React.useState({ x: 0, y: 0 });

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setRotation({ x: -y * 15, y: x * 15 });
  }

  return (
    <div
      style={{ perspective: 1000 }}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setRotation({ x: 0, y: 0 })}
    >
      <div
        style={{
          transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg)`,
          transition: "transform 0.15s ease-out",
        }}
        className="rounded-2xl border border-white/10 bg-zinc-900 p-8"
      >
        {children}
      </div>
    </div>
  );
}
```

---

## 4. Magnetic Buttons & Micro-Spring Physics

Buttons that pull subtly toward the cursor on hover:
```tsx
import { motion, useMotionValue, useSpring } from "framer-motion";

export function MagneticButton({ children }: { children: React.ReactNode }) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springConfig = { damping: 15, stiffness: 150 };
  const smoothX = useSpring(x, springConfig);
  const smoothY = useSpring(y, springConfig);

  function handleMouseMove(e: React.MouseEvent<HTMLButtonElement>) {
    const { clientX, clientY, currentTarget } = e;
    const { left, top, width, height } = currentTarget.getBoundingClientRect();
    x.set((clientX - (left + width / 2)) * 0.35);
    y.set((clientY - (top + height / 2)) * 0.35);
  }

  function handleMouseLeave() {
    x.set(0);
    y.set(0);
  }

  return (
    <motion.button
      style={{ x: smoothX, y: smoothY }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="rounded-full px-6 py-3 font-medium bg-white text-black"
    >
      {children}
    </motion.button>
  );
}
```

---

## 5. Infinite Marquee / Logo Ticker
GPU-accelerated horizontal scroll ticker that pauses on hover:
```css
@keyframes marquee {
  0% { transform: translateX(0%); }
  100% { transform: translateX(-50%); }
}

.animate-marquee {
  display: flex;
  width: max-content;
  animation: marquee 25s linear infinite;
}

.animate-marquee:hover {
  animation-play-state: paused;
}
```

---

## 6. Motion Accessibility & Vestibular Safety (Mandatory Invariant)
Every animation, parallax shift, and gyroscope effect must respect user system preferences:
```css
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```
In Framer Motion:
```tsx
import { useReducedMotion } from "framer-motion";
const shouldReduceMotion = useReducedMotion();
const y = shouldReduceMotion ? 0 : calculatedY;
```
