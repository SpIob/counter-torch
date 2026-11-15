import { useEffect, useRef } from "react";
import { api } from "../../api/client";
import { useAsync } from "../../api/useAsync";
import type { Investigation, Sourced } from "../../api/types";
import { ConfBadge, ErrorBox, fmtRange, Loading, Sources, Status, stripParen } from "../../components/ui";

function show(v: unknown): string | null {
  if (v === null || v === undefined) return null;
  if (Array.isArray(v)) return v.length ? v.join(", ") : null;
  if (typeof v === "object") return fmtRange(v as never);
  return String(v);
}

function Field({ label, node }: { label: string; node: Sourced<unknown> }) {
  const v = show(node.value);
  return (
    <div className="field">
      <dt>{label} <ConfBadge c={node.confidence} /></dt>
      <dd>{v ?? <span className="unknown-text">unknown</span>}
        {node.note && <p className="muted small" style={{ marginTop: 4 }}>{node.note}</p>}
        {node.sources.length > 0 && <Sources list={node.sources} />}
      </dd>
    </div>
  );
}

export function Drawer({ id, onClose }: { id: string; onClose: () => void }) {
  const st = useAsync<Investigation>(() => api.investigation(id), [id]);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.focus();
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  const r = st.data;
  return (
    <>
    <div className="scrim" onClick={onClose} aria-hidden="true" />
    <div className="drawer" role="dialog" aria-modal="true" aria-label="Investigation details" tabIndex={-1} ref={ref}>
      <button className="btn close" onClick={onClose} aria-label="Close details">Close ✕</button>
      {st.loading && <Loading what="record" />}
      {st.error && <ErrorBox msg={st.error} />}
      {r && (
        <>
          <h2>{stripParen(r.name)}</h2>
          <div className="chips"><Status s={r.review.status} /><span className="badge">{r.status}</span>
            {r.project_type && <span className="badge">{r.project_type}</span>}
            {r.psi_url && <a className="small" href={r.psi_url} target="_blank" rel="noreferrer">PSI record {r.psi_accession ?? ""}</a>}</div>
          <dl>
            <Field label="Objective" node={r.objective} />
            <Field label="Platform" node={r.platform} />
            <Field label="Safety function" node={r.safety_functions} />
            <Field label="Fuel phase" node={r.fuel_phase} />
            <Field label="Fuel materials" node={r.fuel_materials} />
            <Field label="Fuel geometry" node={r.fuel_geometry} />
            <Field label="Oxygen" node={r.conditions.o2_percent} />
            <Field label="Pressure" node={r.conditions.pressure_psi} />
            <Field label="Airflow" node={r.conditions.airflow} />
            <Field label="Gravity" node={r.conditions.gravity_g} />
            <Field label="Diluents" node={r.conditions.diluents} />
            <Field label="Facility" node={r.hardware.facility} />
            <Field label="Apparatus" node={r.hardware.apparatus} />
            <Field label="Variables swept" node={r.variables_swept} />
            <Field label="Held constant" node={r.held_constant} />
            <Field label="Sensors" node={r.sensors} />
            <Field label="Relevance" node={r.relevance_notes} />
            <Field label="Earth applications" node={r.earth_applications} />
          </dl>
          {r.review.notes.length > 0 && <><h3>Review notes</h3><ul>{r.review.notes.map((n, i) => <li key={i}>{n}</li>)}</ul></>}
          {r.publications.length > 0 && <><h3>Publications</h3><ul>{r.publications.map((p, i) => <li key={i}>{p.url ? <a href={p.url} target="_blank" rel="noreferrer">{p.title ?? p.url}</a> : p.title}</li>)}</ul></>}
        </>
      )}
    </div>
    </>
  );
}
