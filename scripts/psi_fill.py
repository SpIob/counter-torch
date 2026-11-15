#!/usr/bin/env python3
"""Set the PSI fields on records deterministically (no LLM involved).

For each record whose id is in data/source/psi-map.json, sets:
    psi_accession, in_psi (true), psi_url, project_type (from the local PSI record).
Records without a map entry are left alone. Run it after extraction and after
verification; it only writes files whose content changes.

    python3 scripts/psi_fill.py                       # data/extracted and data/verified
    python3 scripts/psi_fill.py data/fixtures/investigations.seed.json
"""
import json
import sys
from pathlib import Path

PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/"
TYPES = {"Microgravity Investigation": "Microgravity", "Ground Investigation": "Ground"}


def project_type(acc):
    f = Path(f"data/source/psi/{acc}.json")
    if f.exists():
        raw = json.loads(f.read_text()).get("projectType")
        if raw:
            return TYPES.get(raw, None)
    return None


def fill(rec, amap):
    acc = amap.get(rec.get("id"))
    if not acc:
        return False
    new = {"psi_accession": acc, "in_psi": True, "psi_url": PAGE + acc}
    pt = project_type(acc)
    if pt:
        new["project_type"] = pt
    changed = any(rec.get(k) != v for k, v in new.items())
    rec.update(new)
    return changed


def main():
    amap = json.loads(Path("data/source/psi-map.json").read_text())["map"]
    targets = [Path(a) for a in sys.argv[1:]] or sorted(
        list(Path("data/extracted").glob("*.json")) + list(Path("data/verified").glob("*.json")))
    for p in targets:
        data = json.loads(p.read_text())
        recs = data["investigations"] if isinstance(data, dict) and "investigations" in data else [data]
        n = sum(fill(r, amap) for r in recs)
        if n:
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"{'updated' if n else 'ok     '} {p} ({n} changed)")


if __name__ == "__main__":
    main()
