#!/usr/bin/env python3
"""Extract individual test points (O2 %, pressure psi) from the PSI experimental tables.

For each table with an O2 column and a pressure column that has a known unit, it writes one
[o2_percent, pressure_psi] pair per row where both parse. Initial-condition columns only
(never final/mean). Output: data/source/psi/tables/points.json  {accession: [[o2, p], ...]}.
Reuses the column rules of psi_table_summary.py. Skips non-Combustion records.

    python3 scripts/psi_points.py
"""
import csv
import io
import json
import re
import statistics
from pathlib import Path

from psi_table_summary import NUM, OUTCOME_RE, TO_PSI, classify

PSI = Path("data/source/psi")


def first_num(cell):
    m = NUM.search(cell or "")
    return float(m.group()) if m else None


def pick(header, kind):
    cols = [i for i, h in enumerate(header) if classify(h) == kind]
    cond = [i for i in cols if not OUTCOME_RE.search(header[i])]
    return (cond or [])[:1]


def main():
    idx = json.loads((PSI / "tables" / "index.json").read_text())
    area = {r["accession"]: r["research_area"] for r in json.loads((PSI / "index.json").read_text())}
    out, report = {}, []
    for t in idx:
        acc = t["accession"]
        if "Combustion" not in area.get(acc, ""):
            continue
        rows = list(csv.reader(io.StringIO(Path(t["file"]).read_text(encoding="utf-8-sig", errors="replace"))))
        if len(rows) < 2:
            continue
        header, body = rows[0], rows[1:]
        oc, pc = pick(header, "o2"), pick(header, "p")
        if not oc or not pc:
            continue
        oi, pi = oc[0], pc[0]
        unit = re.search(r"\b(atm|bar|mmhg|torr|kpa|psia?)\b", header[pi], re.I)
        if not unit:
            report.append(f"{acc}: pressure column '{header[pi].strip()}' has no unit, skipped")
            continue
        f = TO_PSI[unit.group(1).lower()]
        o_raw = [first_num(r[oi]) for r in body if oi < len(r)]
        o_ok = [x for x in o_raw if x is not None and 0 < x <= 100]
        pct = "percent" in header[oi].lower() or "%" in header[oi]
        frac = (not pct) and bool(o_ok) and statistics.median(o_ok) <= 1.0
        n_bad, before = 0, len(out.get(acc, []))
        for r in body:
            if max(oi, pi) >= len(r):
                continue
            o, p = first_num(r[oi]), first_num(r[pi])
            if o is None or p is None or p <= 0 or not (0 < o <= (1.0 if frac else 100)):
                n_bad += 1
                continue
            out.setdefault(acc, []).append([round(o * 100 if frac else o, 3), round(p * f, 3)])
        report.append(f"{acc}: {len(out.get(acc, [])) - before} points from '{header[oi].strip()}' x '{header[pi].strip()}'"
                      + (f" ({n_bad} rows dropped)" if n_bad else ""))
    (PSI / "tables" / "points.json").write_text(json.dumps(out))
    print("\n".join(report))
    print(f"\n{sum(len(v) for v in out.values())} points, {len(out)} investigations -> {PSI}/tables/points.json")


if __name__ == "__main__":
    main()