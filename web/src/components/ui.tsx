import { useEffect, useState } from "react";
import type { Conf, Range, ReviewStatus, SourceRef } from "../api/types";

export const stripParen = (s: string) => s.replace(/\s*\([^)]*\)\s*$/, "").trim();
export const acronym = (s: string) => s.match(/\(([^)]+)\)\s*$/)?.[1] ?? s;
export const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

export function Status({ s }: { s: ReviewStatus }) {
  const cls = s === "verified" ? "good" : s === "disputed" ? "bad" : s === "extracted" ? "blue" : "";
  return <span className={`badge ${cls}`}>{s}</span>;
}
export function StatusDot({ s }: { s: ReviewStatus }) {
  return <i className={`dot st-${s}`} role="img" aria-label={`review status: ${s}`} title={s} />;
}
export function ConfDot({ c }: { c: Conf }) {
  return <i className={`dot cf-${c}`} role="img" aria-label={`confidence: ${c}`} title={`confidence: ${c}`} />;
}
export function ConfBadge({ c }: { c: Conf }) {
  return <span className="muted small" style={{ display: "inline-flex", gap: 6, alignItems: "center" }}><ConfDot c={c} />{c}</span>;
}
export function Loading({ what }: { what: string }) {
  return <div role="status" aria-label={`Loading ${what}`} style={{ display: "grid", gap: 12, padding: "12px 0" }}>
    <div className="skel" style={{ width: "60%" }} /><div className="skel" style={{ width: "85%" }} /><div className="skel" style={{ width: "45%" }} />
  </div>;
}
export function ErrorBox({ msg }: { msg: string }) {
  return <div className="error" role="alert">{msg}</div>;
}

const num = (n: number) => String(Math.round(n * 1000) / 1000);
export function fmtRange(r: Range | null): string | null {
  if (!r || (r.min === null && r.max === null)) return null;
  const u = r.unit === "%" ? "%" : ` ${r.unit}`;
  if (r.min !== null && r.max !== null) return r.min === r.max ? `${num(r.min)}${u}` : `${num(r.min)} to ${num(r.max)}${u}`;
  return r.min !== null ? `≥ ${num(r.min)}${u} (upper bound unknown)` : `≤ ${num(r.max as number)}${u} (lower bound unknown)`;
}
export function fmtShort(r: Range | null): string | null {
  if (!r || (r.min === null && r.max === null)) return null;
  const u = r.unit === "%" ? "%" : ` ${r.unit}`;
  if (r.min !== null && r.max !== null) return r.min === r.max ? `${num(r.min)}${u}` : `${num(r.min)}–${num(r.max)}${u}`;
  return r.min !== null ? `≥ ${num(r.min)}${u}` : `≤ ${num(r.max as number)}${u}`;
}

export function Sources({ list }: { list: SourceRef[] }) {
  if (!list.length) return <span className="muted small">no source</span>;
  return (
    <ul className="sources">
      {list.map((s, i) => (
        <li key={i}>
          <span className="badge kind">{s.kind}</span>
          {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.note || s.url}</a> : <span className="muted">{s.note}</span>}
        </li>
      ))}
    </ul>
  );
}

export function Seg<T extends string>({ value, options, onChange, label }: { value: T; options: { v: T; label: string }[]; onChange: (v: T) => void; label: string }) {
  return (
    <div className="seg" role="group" aria-label={label}>
      {options.map((o) => <button key={o.v} type="button" aria-pressed={value === o.v} className={value === o.v ? "on" : ""} onClick={() => onChange(o.v)}>{o.label}</button>)}
    </div>
  );
}

export function CountUp({ to }: { to: number }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setV(to); return; }
    let raf = 0; const t0 = performance.now();
    const tick = (t: number) => {
      const k = Math.min(1, (t - t0) / 900);
      setV(Math.round(to * (1 - Math.pow(1 - k, 3))));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to]);
  return <>{v.toLocaleString()}</>;
}
