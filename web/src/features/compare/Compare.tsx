import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import { useAsync } from "../../api/useAsync";
import type { Investigation, Sourced } from "../../api/types";
import { acronym, ConfDot, ErrorBox, fmtRange, Loading, Sources } from "../../components/ui";

type Row = { label: string; get: (r: Investigation) => Sourced<unknown> };
const ROWS: Row[] = [
  { label: "Objective", get: (r) => r.objective }, { label: "Fuel phase", get: (r) => r.fuel_phase },
  { label: "Fuel materials", get: (r) => r.fuel_materials }, { label: "Fuel geometry", get: (r) => r.fuel_geometry },
  { label: "Oxygen", get: (r) => r.conditions.o2_percent }, { label: "Pressure", get: (r) => r.conditions.pressure_psi },
  { label: "Airflow", get: (r) => r.conditions.airflow }, { label: "Gravity", get: (r) => r.conditions.gravity_g },
  { label: "Diluents", get: (r) => r.conditions.diluents }, { label: "Sensors", get: (r) => r.sensors },
  { label: "Variables swept", get: (r) => r.variables_swept }, { label: "Held constant", get: (r) => r.held_constant },
];
const text = (v: unknown): string | null => v === null || v === undefined ? null : Array.isArray(v) ? (v.length ? v.join(", ") : null) : typeof v === "object" ? fmtRange(v as never) : String(v);
const norm = (v: unknown) => JSON.stringify(v, Object.keys((v ?? {}) as object).sort());
const DEFAULT = ["saffire-1", "saffire-2", "saffire-3"];

export function Compare() {
  const st = useAsync(api.investigations, []);
  const [sel, setSel] = useState<string[]>([]);
  const [all, setAll] = useState(false);
  const recs = useMemo(() => st.data ?? [], [st.data]);
  const byId = (id: string) => recs.find((r) => r.id === id);

  useEffect(() => {
    if (!recs.length) return;
    const d = DEFAULT.filter((id) => byId(id));
    setSel(d.length >= 2 ? d : recs.slice(0, 2).map((r) => r.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recs]);

  const chosen = sel.map(byId).filter((r): r is Investigation => !!r);
  const add = (id: string) => setSel((s) => (s.includes(id) || s.length >= 4 ? s : [...s, id]));
  const drop = (id: string) => setSel((s) => s.filter((x) => x !== id));
  const suggested = useMemo(() => {
    const ids = new Set<string>();
    for (const r of chosen) for (const t of r.hardware.shared_with) if (byId(t) && !sel.includes(t)) ids.add(t);
    return [...ids].slice(0, 6);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chosen, sel]);

  if (st.loading) return <Loading what="records" />;
  if (st.error) return <ErrorBox msg={st.error} />;

  const verdict = (row: Row) => {
    const vals = chosen.map((r) => row.get(r).value);
    if (vals.every((v) => text(v) === null)) return "empty";
    if (vals.some((v) => text(v) === null)) return "unknown";
    return vals.every((v) => norm(v) === norm(vals[0])) ? "same" : "diff";
  };
  const visible = ROWS.filter((row) => all || !["same", "empty"].includes(verdict(row)));
  const diffCount = ROWS.filter((row) => verdict(row) === "diff").length;

  return (
    <>
      <div className="picker">
        {chosen.map((r) => <button key={r.id} className="chip on" onClick={() => drop(r.id)} aria-label={`Remove ${r.name}`} title={r.name}>{acronym(r.name)}<span className="x">✕</span></button>)}
        {chosen.length < 4 && (
          <select value="" onChange={(e) => e.target.value && add(e.target.value)} aria-label="Add an investigation">
            <option value="">+ Add investigation</option>
            {recs.filter((r) => !sel.includes(r.id)).map((r) => <option key={r.id} value={r.id}>{acronym(r.name)}</option>)}
          </select>
        )}
      </div>
      {suggested.length > 0 && chosen.length < 4 && (
        <div className="suggest">Shares hardware with your selection:
          {suggested.map((id) => <button key={id} className="chip" onClick={() => add(id)}>+ {acronym(byId(id)?.name ?? id)}</button>)}
        </div>
      )}

      {chosen.length < 2 ? <p className="empty">Choose at least two investigations to compare.</p> : (
        <>
          <div className="cmp-tools">
            <span>{diffCount} of {ROWS.length} fields differ. An unknown value never counts as a match.</span>
            <label><input type="checkbox" checked={all} onChange={(e) => setAll(e.target.checked)} />Also show matching and empty fields</label>
          </div>
          <div className="tablewrap">
            <table className="matrix cmp" style={{ minWidth: 130 + chosen.length * 190 }}>
              <thead><tr><th scope="col">Field</th>{chosen.map((r) => <th key={r.id} scope="col" title={r.name}>{acronym(r.name)}</th>)}</tr></thead>
              <tbody>
                {visible.map((row, i) => (
                  <tr key={row.label} className={verdict(row) === "diff" ? "diff" : ""} style={{ "--i": i } as React.CSSProperties}>
                    <th scope="row">{row.label}</th>
                    {chosen.map((r) => {
                      const n = row.get(r); const t = text(n.value);
                      return (
                        <td key={r.id}>
                          {t ? <>{t}<span className="val"><ConfDot c={n.confidence} /></span></> : <span className="na">–</span>}
                          {n.sources.length > 0 && <details className="src"><summary>{n.sources.length} {n.sources.length === 1 ? "source" : "sources"}</summary><Sources list={n.sources} /></details>}
                        </td>);
                    })}
                  </tr>
                ))}
                {visible.length === 0 && <tr><td colSpan={chosen.length + 1} className="empty">No differences recorded. Fields that match or are empty are hidden.</td></tr>}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
