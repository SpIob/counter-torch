#!/usr/bin/env python3
"""Compute O2, pressure and flow ranges from the downloaded PSI experimental tables.

Input : data/source/psi/tables/index.json (from psi_tables.py) and the CSVs.
Output: data/source/psi/tables/conditions.json and a printed summary.

Column detection is by header name, so the output lists which columns were used.
Heuristics are flagged: O2 given as a fraction (all values <= 1) is converted to
percent; pressure is converted to psi from the unit in the header. A column with
no unit in its header is reported raw with unit "unknown" and is NOT converted.
Skips non-Combustion records (PSI-108 fluid physics, PSI-181 materials).

    python3 scripts/psi_table_summary.py
"""
import argparse
import csv
import io
import json
import re
import statistics
from pathlib import Path

PSI = Path("data/source/psi")
TO_PSI = {"atm": 14.6959, "bar": 14.5038, "mmhg": 0.0193368, "torr": 0.0193368,
          "kpa": 0.145038, "psi": 1.0, "psia": 1.0}

O2_RE = re.compile(r"oxygen|xo2|\bo2\b|^o\s+(initial|final)|\bo initial", re.I)
P_RE = re.compile(r"pressure|^p(init|final|mean)?\s*\(|approx p\b", re.I)
FLOW_RE = re.compile(r"air flow|inlet velocity|air rate|flow velocity", re.I)
OUTCOME_RE = re.compile(r"final|after|mean", re.I)
SKIP_RE = re.compile(r"mg/s|sccm|flow rate|\bmfc\b|bottle|note", re.I)
NUM = re.compile(r"\d+(?:\.\d+)?")


def nums(cell):
    return [float(x) for x in NUM.findall(cell or "")]


def column_values(rows, i):
    out = []
    for r in rows:
        if i < len(r):
            n = nums(r[i])
            if n:
                out.extend(n)
    return out


def classify(h):
    h = h.strip()
    if SKIP_RE.search(h) and not re.search(r"percent|mole fraction|\(atm\)|\(bar\)", h, re.I):
        return None
    if P_RE.search(h):
        return "p"
    if O2_RE.search(h):
        return "o2"
    if FLOW_RE.search(h) and "cm/s" in h.lower():
        return "flow"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--detail', nargs='*', default=[], help='print per-column detail for these accessions')
    args = ap.parse_args()
    idx = json.loads((PSI / "tables" / "index.json").read_text())
    area = {r["accession"]: r["research_area"] for r in json.loads((PSI / "index.json").read_text())}
    res = {}
    for t in idx:
        acc = t["accession"]
        if "Combustion" not in area.get(acc, ""):
            continue
        text = Path(t["file"]).read_text(encoding="utf-8-sig", errors="replace")
        rows = list(csv.reader(io.StringIO(text)))
        if not rows:
            continue
        header, body = rows[0], rows[1:]
        rec = res.setdefault(acc, {"tables": [], "n_rows": 0, "o2": [], "pressure": [], "flow": []})
        rec["tables"].append(t["file"])
        rec["n_rows"] += len(body)
        for i, h in enumerate(header):
            if "atmosphere" in h.lower():
                pv = []
                for r in body:
                    if i < len(r):
                        pv += [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", r[i])]
                pv = [x for x in pv if 0 < x <= 100]
                if pv:
                    rec["o2"].append({"column": h.strip(), "min": min(pv), "max": max(pv), "unit": "%",
                                      "note": "approximate: parsed from text such as '~30% O2 with He'",
                                      "flag": True, "role": "condition"})
                continue
            kind = classify(h)
            vals = column_values(body, i)
            if not kind or not vals:
                continue
            if kind == "o2":
                pct = "percent" in h.lower() or "%" in h or "% by vol" in h.lower()
                keep = [x for x in vals if 0 < x <= 100]
                gone = [x for x in vals if not (0 < x <= 100)]
                why = []
                conv = "as given"
                if keep and not pct:
                    if statistics.median(keep) <= 1.0:
                        gone += [x for x in keep if x > 1.0]
                        keep = [x * 100 for x in keep if x <= 1.0]
                        conv = "converted from fraction"
                    else:
                        small = [x for x in keep if x <= 1.0]
                        if small:
                            gone += small
                            keep = [x for x in keep if x > 1.0]
                if gone:
                    why.append(f"{len(gone)} value(s) dropped as impossible/ambiguous, e.g. " + ", ".join(f"{x:g}" for x in gone[:4]))
                if not keep:
                    continue
                rec["o2"].append({"column": h.strip(), "min": min(keep), "max": max(keep), "unit": "%",
                                  "note": "; ".join([conv] + why), "flag": bool(why),
                                  "role": "outcome" if OUTCOME_RE.search(h) else "condition"})
            elif kind == "p":
                keep = [x for x in vals if x > 0]
                why = [f"{len(vals) - len(keep)} zero/negative value(s) dropped"] if len(keep) != len(vals) else []
                role = "outcome" if OUTCOME_RE.search(h) else "condition"
                if not keep:
                    continue
                m = re.search(r"\b(atm|bar|mmhg|torr|kpa|psia?)\b", h, re.I)
                u = m.group(1).lower() if m else None
                if u:
                    f = TO_PSI[u]
                    rec["pressure"].append({"column": h.strip(), "min": min(keep) * f, "max": max(keep) * f,
                                            "unit": "psi", "note": "; ".join([f"converted from {u}"] + why), "flag": bool(why), "role": role})
                else:
                    rec["pressure"].append({"column": h.strip(), "min": min(keep), "max": max(keep),
                                            "unit": "unknown", "note": "; ".join(["no unit in header; not converted"] + why), "flag": True, "role": role})
            else:
                rec["flow"].append({"column": h.strip(), "min": min(vals), "max": max(vals), "unit": "cm/s", "note": "", "flag": False, "role": "condition"})
        rec.setdefault("headers", []).append({"file": t["file"], "header": [h.strip() for h in header]})

    def span(items):
        cond = [x for x in items if x.get("role") == "condition"] or items
        ok = [x for x in cond if x["unit"] != "unknown"] or cond
        if not ok:
            return None
        return {"min": round(min(x["min"] for x in ok), 3), "max": round(max(x["max"] for x in ok), 3),
                "unit": ok[0]["unit"], "columns": [x["column"] for x in ok],
                "unit_known": all(x["unit"] != "unknown" for x in ok),
                "flagged": any(x.get("flag") for x in ok)}

    out = {}
    both = 0
    print(f"{'acc':8} {'rows':>5}  {'O2 %':>14}  {'pressure psi':>16}  {'flow cm/s':>12}")
    for acc in sorted(res, key=lambda a: int(a.split('-')[1])):
        r = res[acc]
        o2, p, fl = span(r["o2"]), span(r["pressure"]), span(r["flow"])
        out[acc] = {"tables": r["tables"], "n_rows": r["n_rows"], "o2": o2, "pressure": p, "flow": fl, "detail": r}
        f = lambda s: "-" if not s else f"{s['min']:g}-{s['max']:g}" + ("" if s["unit_known"] else "?") + ("*" if s["flagged"] else "")
        if o2 and p:
            both += 1
        print(f"{acc:8} {r['n_rows']:5}  {f(o2):>14}  {f(p):>16}  {f(fl):>12}")
    (PSI / "tables" / "conditions.json").write_text(json.dumps(out, indent=1))
    lines = []
    for acc in sorted(res, key=lambda a: int(a.split("-")[1])):
        for h in res[acc]["headers"]:
            lines.append(f"{acc} | {Path(h['file']).name} | " + " | ".join(h["header"]))
    (PSI / "tables" / "headers.txt").write_text("\n".join(lines) + "\n")
    for acc in args.detail:
        print(f"\n== {acc}")
        for k in ("o2", "pressure", "flow"):
            for x in res.get(acc, {}).get(k, []):
                print(f"  {k:8} {x['column'][:40]:40} {x['min']:g}-{x['max']:g} {x['unit']} {x.get('role','')}  [{x['note']}]")
    print(f"\nwith BOTH an O2 range and a pressure range: {both} of {len(out)} combustion investigations")
    print("('?' = pressure unit missing in the header, value not converted; '*' = values dropped as impossible or ambiguous, see --detail ACC)")
    print(f"wrote {PSI}/tables/conditions.json and headers.txt")


if __name__ == "__main__":
    main()
