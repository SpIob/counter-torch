#!/usr/bin/env python3
"""Add all-unknown seed entries for ids that have a PSI record but no seed record.

    python3 scripts/make_stubs.py acme-flame-design PSI-10
    python3 scripts/make_stubs.py psi-117 PSI-117 --family other --status active

Name and aliases come from data/source/psi/ACC.search.json (Title, Acronym). Every sourced
field starts as null/unknown, so the ingestion worker fills it from sources. Appends to
data/fixtures/investigations.seed.json; does nothing if the id already exists.
"""
import argparse
import copy
import json
from pathlib import Path

SEED = Path("data/fixtures/investigations.seed.json")
PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/"


def blank(node):
    """Reset every sourced field in a record template to null/unknown."""
    if isinstance(node, dict):
        if {"value", "confidence", "sources"} <= set(node):
            return {"value": None, "confidence": "unknown", "sources": []}
        return {k: blank(v) for k, v in node.items()}
    return node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("accession")
    ap.add_argument("--family", default=None)
    ap.add_argument("--status", default="flown", choices=["flown", "active", "planned"])
    a = ap.parse_args()

    seed = json.loads(SEED.read_text())
    recs = seed["investigations"]
    if any(r["id"] == a.id for r in recs):
        print(f"{a.id} already in seed; nothing to do")
        return
    src = Path(f"data/source/psi/{a.accession}.search.json")
    if not src.exists():
        raise SystemExit(f"missing {src}; run scripts/psi_pull.py first")
    s = json.loads(src.read_text())
    tmpl = copy.deepcopy(next(r for r in recs if r["id"] == "luci"))
    rec = blank(tmpl)
    acr = s.get("Acronym") or ""
    rec.update({
        "id": a.id,
        "name": (s.get("Title") or a.id)[:200],
        "aliases": [x.strip() for x in acr.split("/") if x.strip()],
        "family": a.family or ("acme" if a.id.startswith("acme") else "other"),
        "status": a.status,
        "in_psi": True,
        "psi_url": PAGE + a.accession,
        "publications": [],
    })
    rec["review"] = {**rec["review"], "status": "seed", "extracted_by": "stub:scripts/make_stubs.py",
                     "verified_by": None, "verified_at": None,
                     "notes": [f"Stub from the PSI record {a.accession}; all fields unknown until ingestion."]}
    recs.append(rec)
    SEED.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n")
    print(f"added {a.id} ({a.accession}) to seed: {rec['name']}")


if __name__ == "__main__":
    main()