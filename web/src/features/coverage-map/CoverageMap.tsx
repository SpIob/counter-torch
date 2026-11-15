import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../../api/client";
import { useAsync } from "../../api/useAsync";
import type { CoveragePoint, Dim, Gap, Habitat, Range } from "../../api/types";
import { cap, ConfDot, CountUp, ErrorBox, fmtShort, Loading, StatusDot, stripParen } from "../../components/ui";
import { useReveal } from "../../components/useReveal";
import { Drawer } from "./Drawer";
import { Scatter } from "./Scatter";

const DIMS: { k: Dim; label: string }[] = [
  { k: "o2_percent", label: "Oxygen" }, { k: "pressure_psi", label: "Pressure" },
  { k: "gravity_g", label: "Gravity" }, { k: "airflow", label: "Airflow" },
];
const known = (r: CoveragePoint) => DIMS.filter((d) => r[d.k]).length + (r.fuel_phase ? 1 : 0) + (r.safety_functions ? 1 : 0);
const isMoon = (id: string) => /lunar|moon|rover/.test(id);
const order = (id: string) => (/lunar|moon/.test(id) ? 0 : /rover/.test(id) ? 1 : /suit/.test(id) ? 2 : /mars/.test(id) ? 3 : 4);

function Val({ r, k }: { r: CoveragePoint; k: Dim }) {
  const v = fmtShort(r[k] as Range | null);
  return v ? <td className="val">{v}<ConfDot c={r.confidence[k]} /></td> : <td className="na">–</td>;
}

/** Group gaps by habitat; habitats with identical messages share one row. When a combined O2 x pressure gap exists, the single-dimension O2 and pressure lines are redundant and hidden. */
function groupGaps(gaps: Gap[], habitats: Habitat[]) {
  const by = new Map<string, Gap[]>();
  for (const g of gaps) by.set(g.habitat_id, [...(by.get(g.habitat_id) ?? []), g]);
  const merged = new Map<string, { names: string[]; ids: string[]; msgs: string[] }>();
  for (const [id, list] of [...by.entries()].sort((a, b) => order(a[0]) - order(b[0]))) {
    const h = habitats.find((x) => x.id === id);
    const full = h?.name ?? id;
    const hasCombined = list.some((g) => g.dimension === "combined");
    const msgs = list.filter((g) => !hasCombined || !["o2_percent", "pressure_psi"].includes(g.dimension)).map((g) => cap(g.message.replace(`${full}: `, "")));
    const sig = msgs.join("|");
    const e = merged.get(sig);
    if (e) { e.names.push(stripParen(full)); e.ids.push(id); } else merged.set(sig, { names: [stripParen(full)], ids: [id], msgs });
  }
  return [...merged.values()];
}

const sentence = (s: string) => (/[.!?]$/.test(s) ? s : `${s}.`);

export function CoverageMap() {
  const cov = useAsync(api.coverage, []);
  const pts = useAsync(api.points, []);
  const hero = useRef<HTMLDivElement>(null);
  const rest = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [all, setAll] = useState(false);

  const rows = useMemo(() => {
    const f = (cov.data?.points ?? []).filter((r) => (r.name + r.id + (r.psi_accession ?? "")).toLowerCase().includes(q.toLowerCase()));
    return [...f].sort((a, b) => known(b) - known(a) || a.name.localeCompare(b.name));
  }, [cov.data, q]);

  const loaded = !!cov.data;
  useReveal(loaded && !!pts.data);
  useEffect(() => {
    const el = hero.current;
    if (!el || window.matchMedia("(max-width: 760px)").matches || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let raf = 0;
    const update = () => { raf = 0; const p = Math.min(1, Math.max(0, window.scrollY / (el.offsetHeight * 0.8))); el.style.setProperty("--p", p.toFixed(3)); };
    const on = () => { if (!raf) raf = requestAnimationFrame(update); };
    update();
    window.addEventListener("scroll", on, { passive: true }); window.addEventListener("resize", on);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("scroll", on); window.removeEventListener("resize", on); };
  }, [loaded]);

  if (cov.loading) return <Loading what="coverage" />;
  if (cov.error || !cov.data) return <ErrorBox msg={cov.error ?? "No data"} />;
  const c = cov.data;
  const moon = pts.data?.zones.find((z) => isMoon(z.habitat_id));
  const groups = groupGaps(c.gaps, c.habitats);
  const shown = all || q ? rows : rows.slice(0, 10);

  return (
    <div className="cov">
      <div className="cov-hero" ref={hero}>
        <div className="stats">
          <div className="stat"><b><CountUp to={c.points.length} /></b><span>investigations</span></div>
          <div className="stat"><b>{pts.data ? <CountUp to={pts.data.total} /> : "–"}</b><span>tests with oxygen and pressure</span></div>
          {moon && <div className="stat hot" title="Oxygen 30% or more at 10.2 psi or less"><b><CountUp to={moon.count} /></b><span>tests in the Moon-base zone</span></div>}
        </div>
        {pts.loading && <div className="panel chart"><Loading what="test points" /></div>}
        {pts.error && <div className="chart"><ErrorBox msg={pts.error} /></div>}
        {pts.data && pts.data.total > 0 && <Scatter data={pts.data} habitats={c.habitats} />}
        {pts.data && pts.data.total === 0 && <p className="muted chart">No test points loaded. Run <code>python3 scripts/psi_points.py</code>.</p>}
        <button className="hint" onClick={() => rest.current?.scrollIntoView({ behavior: "smooth" })} aria-label="Scroll to gaps and investigations"><span>Gaps and investigations</span><i aria-hidden="true">⌄</i></button>
      </div>

      <div className="cov-rest" ref={rest}>
      <section className="sec first" aria-labelledby="gaps-h">
        <div className="sec-head rv"><h2 id="gaps-h">Where the evidence runs out</h2></div>
        <ul className="gaps">
          {groups.map((g, i) => (
            <li key={i} className={`gap rv ${g.ids.some(isMoon) ? "hot" : ""}`} style={{ "--i": i } as React.CSSProperties}>
              <span className="gap-name">{g.names.join(" / ")}</span>
              <span className="gap-msgs">{g.msgs.map((m, j) => <span key={j}>{sentence(m)}</span>)}</span>
            </li>
          ))}
          {groups.length === 0 && <li className="gap"><span className="gap-msgs">No gaps found against the loaded records.</span></li>}
        </ul>
        <details className="brief rv"><summary>From the challenge brief</summary><ul>{c.facts.map((f, i) => <li key={i}>{f}</li>)}</ul></details>
      </section>

      <section className="sec" aria-labelledby="mx-h">
        <div className="sec-head rv">
          <h2 id="mx-h">Investigations</h2>
          <div className="tools">
            <div className="key" aria-label="Confidence key">
              <span><i className="dot cf-high" />high</span><span><i className="dot cf-medium" />medium</span><span><i className="dot cf-inferred" />inferred</span><span className="na">– unknown</span>
            </div>
            <input className="search" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search" aria-label="Search investigations" />
          </div>
        </div>
        <div className="tablewrap rv">
          <table className="matrix">
            <thead><tr><th scope="col">Investigation</th>{DIMS.map((d) => <th key={d.k} scope="col">{d.label}</th>)}<th scope="col">Fuel</th><th scope="col">Function</th></tr></thead>
            <tbody>
              {shown.map((r) => (
                <tr key={r.id}>
                  <th scope="row" className="name-cell" title={r.psi_files === 0 ? "PSI lists 0 data files for this investigation" : undefined}>
                    <button className="name-btn" onClick={() => setOpen(r.id)}><StatusDot s={r.review_status} />{stripParen(r.name)}</button>
                    <span className="id">{r.psi_accession ?? "not in PSI"}{r.psi_files === 0 ? " · 0 files" : ""}</span>
                  </th>
                  {DIMS.map((d) => <Val key={d.k} r={r} k={d.k} />)}
                  <td>{r.fuel_phase ? r.fuel_phase.replace("_", " ") : <span className="na">–</span>}</td>
                  <td>{r.safety_functions?.join(", ") ?? <span className="na">–</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <p className="empty">No investigation matches.</p>}
          {!all && !q && rows.length > 10 && <div className="more"><button className="btn" onClick={() => setAll(true)}>Show all {rows.length}</button></div>}
        </div>
      </section>
      {open && <Drawer id={open} onClose={() => setOpen(null)} />}
      </div>
    </div>
  );
}
