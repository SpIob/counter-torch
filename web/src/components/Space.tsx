import { useEffect, useRef } from "react";

type Star = { x: number; y: number; s: number; ph: number; sp: number; k: number; plus: boolean };
type Rock = { x: number; y: number; vx: number; vy: number; a: number; va: number; pts: number[]; r: number; warm: boolean };

const rand = (a: number, b: number) => a + Math.random() * (b - a);

function rock(w: number, h: number, small: boolean): Rock {
  const r = small ? rand(12, 26) : rand(26, 52);
  const n = Math.floor(rand(8, 12));
  const pts: number[] = [];
  for (let i = 0; i < n; i++) {
    const ang = (i / n) * Math.PI * 2, rr = r * rand(0.68, 1.15);
    pts.push(Math.cos(ang) * rr, Math.sin(ang) * rr);
  }
  const sp = rand(5, 16), dir = rand(0, Math.PI * 2);
  return { x: rand(0, w), y: rand(0, h), vx: Math.cos(dir) * sp, vy: Math.sin(dir) * sp, a: rand(0, 6.28), va: rand(-0.18, 0.18), pts, r, warm: Math.random() < 0.22 };
}

/** Fixed, non-interactive backdrop: a jittered grid of twinkling stars and slow wireframe asteroids. */
export function Space() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current!, ctx = cv.getContext("2d")!;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0, h = 0, wrapH = 0, scroll = 0, raf = 0, last = performance.now();
    let stars: Star[] = [], rocks: Rock[] = [];
    const CELL = 54;

    const layout = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = window.innerWidth; h = window.innerHeight;
      cv.width = w * dpr; cv.height = h * dpr; cv.style.width = `${w}px`; cv.style.height = `${h}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const rows = Math.ceil(h / CELL) + 2, cols = Math.ceil(w / CELL) + 1;
      wrapH = rows * CELL; stars = [];
      for (let gy = 0; gy < rows; gy++) for (let gx = 0; gx < cols; gx++) {
        if (Math.random() > 0.52) continue;
        const big = Math.random();
        stars.push({ x: gx * CELL + rand(6, CELL - 6), y: gy * CELL + rand(6, CELL - 6), s: big < 0.1 ? 1.7 : big < 0.4 ? 1.15 : 0.75,
          ph: rand(0, 6.28), sp: rand(0.4, 1.5), k: rand(0.02, 0.09), plus: big < 0.05 });
      }
      const count = w < 760 ? 4 : 8;
      rocks = Array.from({ length: count }, (_, i) => rock(w, h, i % 3 === 0));
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        const y = (((s.y - scroll * s.k) % wrapH) + wrapH) % wrapH;
        if (y > h) continue;
        const a = 0.22 + 0.5 * (0.5 + 0.5 * Math.sin(t * s.sp + s.ph));
        ctx.fillStyle = `rgba(214,226,255,${a})`;
        ctx.fillRect(s.x, y, s.s, s.s);
        if (s.plus) {
          ctx.strokeStyle = `rgba(214,226,255,${a * 0.6})`; ctx.lineWidth = 0.8;
          ctx.beginPath(); ctx.moveTo(s.x - 4, y + 0.4); ctx.lineTo(s.x + 4.8, y + 0.4); ctx.moveTo(s.x + 0.4, y - 4); ctx.lineTo(s.x + 0.4, y + 4.8); ctx.stroke();
        }
      }
      ctx.lineWidth = 1.2; ctx.lineJoin = "round";
      for (const r of rocks) {
        ctx.save(); ctx.translate(r.x, r.y); ctx.rotate(r.a);
        ctx.strokeStyle = r.warm ? "rgba(245,165,36,.26)" : "rgba(170,196,255,.24)";
        ctx.beginPath(); ctx.moveTo(r.pts[0], r.pts[1]);
        for (let i = 2; i < r.pts.length; i += 2) ctx.lineTo(r.pts[i], r.pts[i + 1]);
        ctx.closePath(); ctx.stroke(); ctx.restore();
      }
    };

    const tick = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000); last = now;
      for (const r of rocks) {
        r.x += r.vx * dt; r.y += r.vy * dt; r.a += r.va * dt;
        const m = r.r * 1.3;
        if (r.x < -m) r.x = w + m; else if (r.x > w + m) r.x = -m;
        if (r.y < -m) r.y = h + m; else if (r.y > h + m) r.y = -m;
      }
      draw(now / 1000);
      raf = requestAnimationFrame(tick);
    };

    const onScroll = () => { scroll = window.scrollY; if (reduce) draw(0); };
    const onResize = () => { layout(); draw(performance.now() / 1000); };
    layout(); draw(0);
    if (!reduce) raf = requestAnimationFrame(tick);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onResize); };
  }, []);
  return <canvas ref={ref} className="space" aria-hidden="true" />;
}
