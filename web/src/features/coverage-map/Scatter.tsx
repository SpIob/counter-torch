import { useEffect, useMemo, useRef, useState } from "react";
import type { Habitat, TestPoints } from "../../api/types";
import { stripParen } from "../../components/ui";

const M = { l: 54, r: 20, t: 18, b: 46 };
const X_MAX = 100, Y_MAX = 50;
const PALETTE = ["#4cc9f0", "#a58bff", "#2ee6a6", "#ff6fae", "#ffd23f", "#7ee0d0", "#ff9d6b", "#9fb3c8"];

type Z = { x0: number; x1: number; y0: number; y1: number; point: boolean };
function zone(h: Habitat): Z | null {
  const o = h.o2_percent, p = h.pressure_psi;
  if (!o && !p) return null;
  const x0 = o?.min ?? 0, x1 = o?.max ?? X_MAX, y0 = p?.min ?? 0, y1 = p?.max ?? Y_MAX;
  return { x0, x1, y0, y1, point: x0 === x1 && y0 === y1 };
}
type Hit = { x: number; y: number; si: number; o: number; p: number };

export function Scatter({ data, habitats }: { data: TestPoints; habitats: Habitat[] }) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [hot, setHot] = useState<string | null>(null);
  const [run, setRun] = useState(0);
  const [size, setSize] = useState({ w: 900, h: 460 });
  const [tip, setTip] = useState<{ hit: Hit; same: number } | null>(null);
  const plot = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = plot.current; if (!el) return;
    const ro = new ResizeObserver(([e]) => setSize({ w: Math.max(300, Math.round(e.contentRect.width)), h: Math.max(240, Math.round(e.contentRect.height)) }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const { w: W, h: H } = size;
  const sx = (v: number) => M.l + (v / X_MAX) * (W - M.l - M.r);
  const sy = (v: number) => H - M.b - (v / Y_MAX) * (H - M.t - M.b);

  const zones = useMemo(() => {
    const map = new Map<string, { names: string[]; ids: string[]; z: Z }>();
    for (const h of habitats) {
      const z = zone(h); if (!z) continue;
      const key = `${z.x0}|${z.x1}|${z.y0}|${z.y1}`;
      const e = map.get(key);
      if (e) { e.names.push(stripParen(h.name)); e.ids.push(h.id); } else map.set(key, { names: [stripParen(h.name)], ids: [h.id], z });
    }
    return [...map.values()];
  }, [habitats]);
  const area = zones.filter((z) => !z.z.point);
  const countOf = (ids: string[]) => data.zones.find((c) => ids.includes(c.habitat_id))?.count;
  const inArea = (o: number, p: number) => area.some(({ z }) => o >= z.x0 && o <= z.x1 && p >= z.y0 && p <= z.y1);
  const toggle = (id: string) => setHidden((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n; });

  const hits = useMemo<Hit[]>(() => data.investigations.flatMap((s, si) => hidden.has(s.id) ? [] : s.points.map(([o, p]) => ({ x: sx(o), y: sy(p), si, o, p }))),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, hidden, W, H]);

  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    let best: Hit | null = null, bd = 14 * 14;
    for (const h of hits) { const d = (h.x - mx) ** 2 + (h.y - my) ** 2; if (d < bd) { bd = d; best = h; } }
    if (!best) { setTip(null); return; }
    const same = hits.filter((h) => Math.abs(h.o - best!.o) < 0.05 && Math.abs(h.p - best!.p) < 0.05).length;
    setTip({ hit: best, same });
  };
  const hv = tip?.hit;
  const tipSeries = hv ? data.investigations[hv.si] : null;

  return (
    <div className="panel chart">
      <div className="chart-head">
        <div className="legend" role="group" aria-label="Show or hide investigations">
          {data.investigations.map((s, i) => (
            <button key={s.id} className={`chip ${hidden.has(s.id) ? "off" : ""}`} aria-pressed={!hidden.has(s.id)}
              onClick={() => toggle(s.id)} onMouseEnter={() => setHot(s.id)} onMouseLeave={() => setHot(null)} onFocus={() => setHot(s.id)} onBlur={() => setHot(null)}>
              <span className="swatch" style={{ background: PALETTE[i % PALETTE.length], boxShadow: `0 0 8px ${PALETTE[i % PALETTE.length]}` }} aria-hidden="true" />
              {s.accession} {s.id.replace(/^acme-/, "")} <span className="faint">{s.points.length}</span>
            </button>
          ))}
        </div>
        <button className="btn" onClick={() => setRun((n) => n + 1)} aria-label="Replay the chart animation">↻ Replay</button>
      </div>
      <div className="plot" ref={plot}>
        <svg key={run} width={W} height={H} role="img" className="scatter" onMouseMove={onMove} onMouseLeave={() => setTip(null)}
          aria-label={`Scatter of ${data.total} individual tests from PSI experimental tables, oxygen percent against pressure in psi, with habitat zones`}>
          <defs>
            <linearGradient id="zone-g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#f5a524" stopOpacity=".2" /><stop offset="1" stopColor="#f5a524" stopOpacity=".05" /></linearGradient>
          </defs>
          <g className="fade">
            {[0, 10, 20, 30, 40, 50].map((v) => (
              <g key={`y${v}`}><line x1={M.l} x2={W - M.r} y1={sy(v)} y2={sy(v)} className={v === 0 ? "base" : "grid"} /><text x={M.l - 12} y={sy(v) + 4} className="tick" textAnchor="end">{v}</text></g>
            ))}
            {[0, 20, 40, 60, 80, 100].map((v) => (
              <g key={`x${v}`}><line x1={sx(v)} x2={sx(v)} y1={M.t} y2={H - M.b} className="grid v" /><text x={sx(v)} y={H - M.b + 20} className="tick" textAnchor="middle">{v}</text></g>
            ))}
            <text x={(W + M.l - M.r) / 2} y={H - 6} className="axis" textAnchor="middle">OXYGEN (%)</text>
            <text transform={`translate(13 ${(H - M.b + M.t) / 2}) rotate(-90)`} className="axis" textAnchor="middle">PRESSURE (psi)</text>
          </g>
          {area.map(({ z, names, ids }, i) => {
            const n = countOf(ids), zw = sx(z.x1) - sx(z.x0), zh = sy(z.y0) - sy(z.y1);
            const label = `${zw < 330 ? names[0] : names.join(" / ")}${n !== undefined ? ` · ${n} ${n === 1 ? "test" : "tests"}` : ""}`;
            const pw = Math.min(zw - 20, label.length * 6.7 + 24);
            return (
              <g key={i}>
                <rect x={sx(z.x0)} y={sy(z.y1)} width={zw} height={zh} rx="8" fill="url(#zone-g)" className="zone-fill" />
                <rect x={sx(z.x0)} y={sy(z.y1)} width={zw} height={zh} rx="8" className="zone-edge" pathLength={1} />
                <g className="fade late">
                  <rect x={sx(z.x0) + 10} y={sy(z.y0) - 34} width={pw} height="24" rx="12" className="zone-pill" />
                  <text x={sx(z.x0) + 22} y={sy(z.y0) - 18} className="zone-label">{label}</text>
                </g>
              </g>
            );
          })}
          {data.investigations.map((s, si) => !hidden.has(s.id) && (
            <g key={s.id} className={`series ${hot && hot !== s.id ? "dim" : ""}`} fill={PALETTE[si % PALETTE.length]}>
              {s.points.map(([o, p], i) => (
                <circle key={i} cx={sx(o)} cy={sy(p)} r="2.7" className={`pt ${inArea(o, p) ? "in" : ""}`} style={{ animationDelay: `${Math.min(si * 70 + i * 1.3, 1000)}ms` }} />
              ))}
            </g>
          ))}
          {zones.filter((z) => z.z.point).map(({ z, names }, i) => {
            const right = z.x0 > 70, cx = sx(z.x0), cy = sy(z.y0);
            return (
              <g key={`p${i}`} className="fade late">
                <circle cx={cx} cy={cy} r="5" className="ping" /><circle cx={cx} cy={cy} r="5.5" className="ref" />
                <text x={cx + (right ? -13 : 13)} y={cy + 4} className="ref-label" textAnchor={right ? "end" : "start"}>{names.join(" / ")}</text>
              </g>
            );
          })}
          {hv && <g pointerEvents="none">
            <line x1={hv.x} x2={hv.x} y1={hv.y} y2={H - M.b} className="cross" /><line x1={M.l} x2={hv.x} y1={hv.y} y2={hv.y} className="cross" />
            <circle cx={hv.x} cy={hv.y} r="6" fill="none" stroke="#fff" strokeWidth="1.5" />
          </g>}
        </svg>
        {hv && tipSeries && (
          <div className="tip" style={{ left: Math.min(hv.x + 14, W - 190), top: Math.max(hv.y - 64, 4) }} role="status">
            <b>{tipSeries.accession}</b> <span className="muted">{tipSeries.id}</span>
            <div>{hv.o}% oxygen · {hv.p} psi</div>
            {tip!.same > 1 && <div className="faint">{tip!.same} tests at these conditions</div>}
          </div>
        )}
      </div>
      <ul className="sr-only">{data.investigations.map((s) => <li key={s.id}>{s.name} ({s.accession}): {s.points.length} tests with both oxygen and pressure recorded</li>)}</ul>
    </div>
  );
}
