#!/usr/bin/env python3
"""Write O2, pressure and airflow ranges computed from PSI tables into records.

Reads data/source/psi/tables/conditions.json (psi_table_summary.py) and
data/source/psi-map.json. For each record whose id maps to a PSI accession, it
replaces conditions.o2_percent, conditions.pressure_psi and conditions.airflow
with the table-derived range and a `psi` source. Gravity and diluents are not touched.

  * flagged columns (values dropped, or O2 parsed from text) get confidence "medium"
  * a pressure column with no unit is skipped, the field is left as it is
  * only "condition" columns are used (initial values), never final/mean outcomes

    python3 scripts/psi_apply_conditions.py                  # data/extracted + data/verified
    python3 scripts/psi_apply_conditions.py FILE [FILE ...]
"""
import json
import sys
from pathlib import Path

PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/"


def table_names(acc):
    f = Path(f"data/source/psi/{acc}.json")
    if not f.exists():
        return []
    return [t.get("file_name", "") for t in json.loads(f.read_text()).get("experimentalTable") or []]


def build(acc, c, key, unit):
    s = c.get(key)
    if not s or (key == "pressure" and not s.get("unit_known")):
        return None
    det = c["detail"][key]
    used = [x for x in det if x["column"] in s["columns"]]
    notes = [f"{x['column']}: {x['note']}" for x in used if x.get("flag")]
    flagged = bool(s.get("flagged"))
    names = ", ".join(table_names(acc)) or "experimental table"
    note = (f"Range over {c['n_rows']} test rows of {names}, columns: {'; '.join(s['columns'])}. "
            "Computed by scripts/psi_table_summary.py (initial conditions only)."
            + (" Check: " + " | ".join(notes) if notes else ""))
    return {
        "value": {"min": s["min"], "max": s["max"], "unit": unit},
        "confidence": "medium" if flagged else "high",
        "sources": [{"kind": "psi", "url": PAGE + acc, "note": f"PSI {acc} experimental table {names}; per-test conditions, min and max of the listed columns"[:400]}],
        "note": note[:900],
    }


def main():
    cond = json.loads(Path("data/source/psi/tables/conditions.json").read_text())
    amap = json.loads(Path("data/source/psi-map.json").read_text())["map"]
    targets = [Path(a) for a in sys.argv[1:]] or sorted(
        list(Path("data/extracted").glob("*.json")) + list(Path("data/verified").glob("*.json")))
    for p in targets:
        rec = json.loads(p.read_text())
        acc = amap.get(rec.get("id"))
        c = cond.get(acc) if acc else None
        if not c:
            print(f"skip    {p} (no table conditions)")
            continue
        changed = []
        for key, field, unit in (("o2", "o2_percent", "%"), ("pressure", "pressure_psi", "psi"), ("flow", "airflow", "cm/s")):
            new = build(acc, c, key, unit)
            if new:
                rec["conditions"][field] = new
                changed.append(field)
        if changed:
            p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        print(f"{'updated' if changed else 'nothing'} {p}: {', '.join(changed) or 'no usable columns'}")


if __name__ == "__main__":
    main()
