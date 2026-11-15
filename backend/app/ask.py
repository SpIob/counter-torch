"""Retrieval-augmented Q&A. BM25 over record fields plus the brief. Refuses when retrieval finds no support."""
import math
import re
from collections import Counter

from . import llm

STOP = set("a an the of in on at to for and or is are was were be been it its this that with by from as what which who how "
           "does do did can could would should there their they them about any have has had not no into than then".split())


def tok(s):
    out = []
    for w in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", s.lower()):
        if w in STOP or len(w) < 2:
            continue
        out.append(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w)
    return out


def value_text(v):
    if v is None:
        return None
    if isinstance(v, dict) and "min" in v:
        lo, hi, u = v.get("min"), v.get("max"), v.get("unit", "")
        sep = "" if u == "%" else " "
        if lo is not None and hi is not None:
            return f"{lo}{sep}{u}" if lo == hi else f"{lo}\u2013{hi}{sep}{u}"
        return f"at least {lo}{sep}{u}" if lo is not None else f"at most {hi}{sep}{u}"
    if isinstance(v, list):
        return ", ".join(map(str, v)) if v else None
    return str(v)


LABEL = {"o2_percent": "Oxygen", "pressure_psi": "Pressure", "gravity_g": "Gravity", "airflow": "Airflow"}


def field_label(path):
    last = path.split(".")[-1]
    return LABEL.get(last, last.replace("_", " ").capitalize())


def build_chunks(store):
    chunks = []

    def walk(rid, rec, node, path):
        if isinstance(node, dict) and {"value", "confidence", "sources"} <= set(node):
            vt = value_text(node["value"])
            if vt:
                src = node["sources"][0] if node["sources"] else {}
                chunks.append({"id": rid, "field": path, "text": f"{rec['name']} ({rid}) {path.replace('_', ' ')}: {vt}",
                               "show": f"{rec['name']}. {field_label(path)}: {vt}",
                               "url": src.get("url"), "note": src.get("note", ""), "origin": store.origin[rid]})
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(rid, rec, v, f"{path}.{k}" if path else k)

    for rid, rec in store.records.items():
        for k in ("platform", "objective", "safety_functions", "fuel_phase", "fuel_materials", "fuel_geometry", "hardware",
                  "conditions", "variables_swept", "held_constant", "sensors", "relevance_notes", "earth_applications"):
            walk(rid, rec, rec[k], k)
    for doc, text in store.brief_chunks:
        chunks.append({"id": doc, "field": None, "text": text, "url": None,
                       "note": "Challenge brief" if doc == "brief" else "Challenge video transcript", "origin": doc})
    return chunks


class Index:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [Counter(tok(c["text"])) for c in chunks]
        self.n = len(chunks)
        self.avg = sum(sum(d.values()) for d in self.docs) / max(self.n, 1)
        self.df = Counter(t for d in self.docs for t in d)

    def search(self, q, k=5):
        terms = list(dict.fromkeys(tok(q)))
        scored = []
        for i, d in enumerate(self.docs):
            ln = sum(d.values()) or 1
            s, matched = 0.0, 0
            for t in terms:
                f = d.get(t, 0)
                if not f:
                    continue
                matched += 1
                idf = math.log(1 + (self.n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                s += idf * f * 2.5 / (f + 1.5 * (0.25 + 0.75 * ln / self.avg))
            if matched:
                scored.append((s, matched, i))
        scored.sort(reverse=True)
        return terms, [(s, m, self.chunks[i]) for s, m, i in scored[:k]]


def ask(index, question):
    terms, hits = index.search(question)
    need = max(2, math.ceil(0.5 * len(terms))) if len(terms) > 1 else 1
    good = [h for h in hits if h[1] >= need]
    m = llm.mode()
    if not good:
        return {"answer": "The loaded records and the challenge brief do not cover this question, so I will not guess.",
                "citations": [], "coverage_gap": True, "mode": m}
    cites, seen = [], set()
    for _, _, c in good:
        key = (c["id"], c["field"])
        if key not in seen:
            seen.add(key)
            cites.append({"id": c["id"], "field": c["field"], "url": c["url"], "note": c["note"][:300] or c["text"][:120]})
    excerpt = "\n".join(f"[{c['id']}] {c.get('show') or c['text']}" for _, _, c in good[:4])
    answer = None
    if m == "live":
        answer = llm.chat("Answer using ONLY the numbered excerpts. Cite record ids in square brackets. "
                          "If the excerpts do not answer the question, say so. Never add facts.",
                          f"Question: {question}\n\nExcerpts:\n{excerpt}")
    if not answer:
        answer = "Closest matches in the loaded records:\n" + excerpt
        m = "offline" if m == "live" else m
    return {"answer": answer, "citations": cites, "coverage_gap": False, "mode": m}
