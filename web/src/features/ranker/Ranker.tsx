import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { useAsync } from "../../api/useAsync";
import type { Dim, Habitat, RankResponse, Range, Scenario } from "../../api/types";
import { ErrorBox, Seg, Sources, StatusDot, stripParen } from "../../components/ui";

type Box = { min: string; max: string };
type Form = { habitat: string; o2: Box; p: Box; g: Box; af: Box; concern: string; fuel: string };
const E: Box = { min: "", max: "" };
const BLANK: Form = { habitat: "", o2: E, p: E, g: E, af: E, concern: "any", fuel: "any" };
const KEYS = ["o2", "p", "g", "af"] as const;
const DIM_LABEL: Record<Dim, string> = { o2_percent: "oxygen", pressure_psi: "pressure", gravity_g: "gravity", airflow: "airflow" };
const COMP: { k: keyof RankResponse["items"][number]["components"]; label: string; w: string }[] = [
  { k: "conditions", label: "Conditions", w: "35%" }, { k: "function", label: "Safety function", w: "25%" },
  { k: "fuel", label: "Fuel phase", w: "20%" }, { k: "evidence", label: "Evidence", w: "20%" },
];
const DEFAULT_HABITAT = "lunar_habitat_expected";

function fromUrl(): Form {
  const p = new URLSearchParams(location.search);
  const f: Form = { ...BLANK, habitat: p.get("h") ?? "", concern: p.get("concern") ?? "any", fuel: p.get("fuel") ?? "any" };
  for (const k of KEYS) f[k] = { min: p.get(`${k}min`) ?? "", max: p.get(`${k}max`) ?? "" };
  return f;
}
function toUrl(f: Form) {
  const p = new URLSearchParams();
  if (f.habitat) p.set("h", f.habitat);
  p.set("concern", f.concern); p.set("fuel", f.fuel);
  for (const k of KEYS) { if (f[k].min) p.set(`${k}min`, f[k].min); if (f[k].max) p.set(`${k}max`, f[k].max); }
  history.replaceState(null, "", `?${p.toString()}${location.hash}`);
}
const rng = (b: Box, unit: string): Range | null => {
  const lo = b.min === "" ? null : Number(b.min), hi = b.max === "" ? null : Number(b.max);
  return lo === null && hi === null ? null : { min: lo, max: hi, unit };
};
const box = (r: Range | null | undefined): Box => ({ min: r?.min == null ? "" : String(r.min), max: r?.max == null ? "" : String(r.max) });
const withHabitat = (f: Form, h: Habitat): Form => ({ ...f, habitat: h.id, o2: box(h.o2_percent), p: box(h.pressure_psi), g: box(h.gravity_g) });

function Pair({ title, v, set }: { title: string; v: Box; set: (b: Box) => void }) {
  return (
    <div className="pair" role="group" aria-label={title}>
      <span className="t">{title}</span>
      <label>min<input inputMode="decimal" value={v.min} onChange={(e) => set({ ...v, min: e.target.value })} placeholder="any" /></label>
      <label>max<input inputMode="decimal" value={v.max} onChange={(e) => set({ ...v, max: e.target.value })} placeholder="any" /></label>
    </div>
  );
}

export function Ranker() {
  const cov = useAsync(api.coverage, []);
  const [f, setF] = useState<Form>(fromUrl);
  const [res, setRes] = useState<RankResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [adv, setAdv] = useState(false);
  const [ready, setReady] = useState(false);
  const seq = useRef(0);
  const hadUrl = useRef(!!location.search);
  const habitats = cov.data?.habitats ?? [];

  useEffect(() => {
    if (!cov.data || ready) return;
    if (!hadUrl.current) {
      const h = cov.data.habitats.find((x) => x.id === DEFAULT_HABITAT) ?? cov.data.habitats[0];
      if (h) setF((cur) => withHabitat(cur, h));
    }
    setReady(true);
  }, [cov.data, ready]);

  useEffect(() => {
    if (!ready) return;
    const id = ++seq.current;
    const t = setTimeout(() => {
      toUrl(f);
      const scenario: Scenario = { habitat_id: f.habitat || null, o2_percent: rng(f.o2, "%"), pressure_psi: rng(f.p, "psi"), gravity_g: rng(f.g, "g"), airflow: rng(f.af, "cm/s") };
      api.rank({ scenario, concern: f.concern, fuel: f.fuel, limit: 10 }).then(
        (r) => { if (id === seq.current) { setRes(r); setErr(null); } },
        (e: Error) => { if (id === seq.current) setErr(e.message); });
    }, 250);
    return () => clearTimeout(t);
  }, [f, ready]);

  const edit = (k: (typeof KEYS)[number], b: Box) => setF({ ...f, [k]: b, habitat: "" });

  return (
    <>
      <div className="controls">
        <div className="chips" role="group" aria-label="Scenario">
          {habitats.map((h) => <button key={h.id} className={`chip ${f.habitat === h.id ? "on" : ""}`} aria-pressed={f.habitat === h.id} onClick={() => setF(withHabitat(f, h))}>{stripParen(h.name)}</button>)}
          <button className={`chip ${!f.habitat ? "on" : ""}`} aria-pressed={!f.habitat} onClick={() => { setAdv(true); setF({ ...f, habitat: "" }); }}>Custom</button>
        </div>
        <div className="controls-row">
          <span><span className="lbl">Safety function</span><Seg label="Safety function" value={f.concern} onChange={(v) => setF({ ...f, concern: v })} options={["any", "prevention", "detection", "suppression"].map((v) => ({ v, label: v }))} /></span>
          <span><span className="lbl">Fuel</span><Seg label="Fuel" value={f.fuel} onChange={(v) => setF({ ...f, fuel: v })} options={[{ v: "any", label: "any" }, { v: "solid", label: "solid" }, { v: "gas", label: "gas" }, { v: "liquid_droplet", label: "droplet" }]} /></span>
          <button className="btn" onClick={() => setAdv(!adv)} aria-expanded={adv}>{adv ? "Hide values" : "Edit values"}</button>
        </div>
        {adv && (
          <div className="fine">
            <Pair title="Oxygen (%)" v={f.o2} set={(b) => edit("o2", b)} />
            <Pair title="Pressure (psi)" v={f.p} set={(b) => edit("p", b)} />
            <Pair title="Gravity (g)" v={f.g} set={(b) => edit("g", b)} />
            <Pair title="Airflow (cm/s)" v={f.af} set={(b) => edit("af", b)} />
          </div>
        )}
      </div>

      {err && <div style={{ marginTop: 18 }}><ErrorBox msg={err} /></div>}
      {res?.coverage_note && <p className="note" role="note"><span aria-hidden="true">◆</span>{res.coverage_note}</p>}
      <ol className="rank">
        {res?.items.map((it, i) => (
          <li key={it.id} className={`rank-item ${open === it.id ? "open" : ""}`} style={{ "--i": i } as React.CSSProperties}>
            <button className="rank-head" aria-expanded={open === it.id} onClick={() => setOpen(open === it.id ? null : it.id)}>
              <span className="rk">{i + 1}</span>
              <span>
                <span className="rk-name"><StatusDot s={it.review_status} />{stripParen(it.name)}
                  {it.bounding && <span className="badge amber" title="The scenario is partial gravity. This microgravity record is scored as a bounding case.">bounding</span>}
                  {it.unknown_dims.map((d) => <span key={d} className="badge" title="This investigation has no recorded range for this condition">{DIM_LABEL[d]} unknown</span>)}</span>
                <span className="rk-why">{it.why}</span>
              </span>
              <span className="rk-score" aria-label={`Score ${it.score.toFixed(2)} of 1`}>
                <b>{it.score.toFixed(2)}</b><span className="meter"><i style={{ width: `${it.score * 100}%`, "--i": i } as React.CSSProperties} /></span>
              </span>
            </button>
            {open === it.id && (
              <div className="rk-body">
                <div className="comps">{COMP.map((c) => (
                  <div key={c.k} className="comp">{c.label} <span className="faint">{c.w}</span><b>{it.components[c.k].toFixed(2)}</b>
                    <span className="meter"><i style={{ width: `${it.components[c.k] * 100}%` }} /></span></div>))}</div>
                <details><summary>Sources ({it.sources.length})</summary><Sources list={it.sources} /></details>
              </div>
            )}
          </li>
        ))}
      </ol>
      {res && res.items.length === 0 && <p className="empty">Nothing matches these settings.</p>}
    </>
  );
}
