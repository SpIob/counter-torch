import { useState } from "react";
import { api } from "../../api/client";
import type { AskResponse } from "../../api/types";
import { ErrorBox, Loading } from "../../components/ui";

const EXAMPLES = [
  "Is there partial-gravity combustion data in PSI?",
  "Which investigations used helium as a diluent?",
  "What oxygen concentration will be used on the Moon?",
];

/** The offline answer is "[id] text" lines. Split them into items; free text (live mode) stays a paragraph. */
function parse(answer: string) {
  const items: { id: string; text: string }[] = [];
  const lead: string[] = [];
  for (const line of answer.split("\n")) {
    const m = line.match(/^\[([^\]]+)\]\s*(.*)$/);
    if (m) items.push({ id: m[1], text: m[2].replace(new RegExp(`\\s*\\(${m[1].replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\)`, "i"), "") });
    else if (items.length) items[items.length - 1].text += ` ${line.trim()}`;
    else if (line.trim()) lead.push(line.trim());
  }
  return { items, lead: lead.join(" ") };
}

export function Ask() {
  const [q, setQ] = useState("");
  const [res, setRes] = useState<AskResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const go = (text: string) => {
    if (text.trim().length < 3) return;
    setBusy(true); setErr(null); setRes(null);
    api.ask(text).then(setRes, (e: Error) => setErr(e.message)).finally(() => setBusy(false));
  };
  const p = res ? parse(res.answer) : null;
  return (
    <div className="ask">
      <form className="ask-form" onSubmit={(e) => { e.preventDefault(); go(q); }}>
        <input value={q} onChange={(e) => setQ(e.target.value)} maxLength={1000} placeholder="Ask a question about the investigations" aria-label="Question" autoFocus />
        <button className="btn primary" disabled={busy}>{busy ? "Asking…" : "Ask"}</button>
      </form>
      <div className="chips">{EXAMPLES.map((x) => <button key={x} className="chip" onClick={() => { setQ(x); go(x); }}>{x}</button>)}</div>
      {busy && <div style={{ marginTop: 28 }}><Loading what="answer" /></div>}
      {err && <div style={{ marginTop: 28 }}><ErrorBox msg={err} /></div>}
      {res && p && (
        <div className="answer" aria-live="polite">
          {res.coverage_gap && <p className="gapnote">{res.answer}</p>}
          {!res.coverage_gap && p.lead && <p className="lead">{p.lead}</p>}
          {p.items.length > 0 ? (
            <ul className="items">{p.items.map((it, i) => <li key={i} style={{ "--i": i } as React.CSSProperties}><span className="idc">{it.id}</span><span>{it.text}</span></li>)}</ul>
          ) : !p.lead && !res.coverage_gap && <p>{res.answer}</p>}
          {res.citations.length > 0 && (
            <details><summary>Citations ({res.citations.length})</summary>
              <ul className="sources">{res.citations.map((c, i) => (
                <li key={i}><span className="badge kind">{c.id}{c.field ? ` · ${c.field}` : ""}</span>
                  {c.url ? <a href={c.url} target="_blank" rel="noreferrer">{c.note}</a> : <span className="muted">{c.note}</span>}</li>))}</ul>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
