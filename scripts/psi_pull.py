#!/usr/bin/env python3
"""Pull PSI investigation records from the JSON API behind psi.nasa.gov.

Reads the search response you saved (data/source/psi-search.json), then fetches
each investigation's detail record:
    GET https://psi.nasa.gov/geode-py/ws/repo/investigations/<ACCESSION>

Writes, under --out (default data/source/psi):
    <ACC>.search.json   the search hit's _source (objectives, approach, project type...)
    <ACC>.json          the full detail record (experimentalTable, factors, file list...)
    index.json          one summary row per investigation

It does NOT download data files (CSV, video, HDF5). It sends no cookies or tokens.
Standard library only.

Usage:
    python3 scripts/psi_pull.py
    python3 scripts/psi_pull.py --extra PSI-27 PSI-28     # ids missing from the search
    python3 scripts/psi_pull.py --force                    # refetch existing files
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://psi.nasa.gov/geode-py/ws/repo/investigations/"
UA = "Mozilla/5.0 (compatible; Counter-Torch-hackathon/0.1)"


def get_json(url, ua, retries=2, timeout=30):
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": ua}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (401, 403, 404):  # retrying will not help
                break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = str(e)
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{url} -> {last}")


def text(v):
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return "" if v is None else str(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--search", default="data/source/psi-search.json")
    ap.add_argument("--out", default="data/source/psi")
    ap.add_argument("--base", default=BASE, help="detail endpoint prefix (for testing)")
    ap.add_argument("--extra", nargs="*", default=[], help="accession ids not in the search file")
    ap.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    ap.add_argument("--force", action="store_true", help="refetch files that already exist")
    ap.add_argument("--ua", default=UA)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    hits = []
    sp = Path(args.search)
    if sp.exists():
        data = json.loads(sp.read_text())
        hits = data.get("hits", {}).get("hits", [])
    else:
        print(f"note: {sp} not found, using --extra ids only", file=sys.stderr)

    entries = {}  # accession -> _source (or {})
    for h in hits:
        src = h.get("_source", {})
        acc = src.get("Accession")
        if acc:
            entries[acc] = src
    for acc in args.extra:
        entries.setdefault(acc, {})

    if not entries:
        sys.exit("nothing to fetch: no accessions found")

    rows, failures = [], []
    for i, (acc, src) in enumerate(sorted(entries.items(), key=lambda kv: int(kv[0].split("-")[-1]) if kv[0].split("-")[-1].isdigit() else 0), 1):
        if src:
            (out / f"{acc}.search.json").write_text(json.dumps(src, indent=1))
        detail_path = out / f"{acc}.json"
        detail = None
        if detail_path.exists() and not args.force:
            detail = json.loads(detail_path.read_text())
            status = "cached"
        else:
            try:
                detail = get_json(args.base + acc, args.ua)
                detail_path.write_text(json.dumps(detail, indent=1))
                status = "fetched"
                time.sleep(args.delay)
            except RuntimeError as e:
                failures.append(f"{acc}: {e}")
                status = "FAILED"
        files = (detail or {}).get("added") or []
        rows.append({
            "accession": acc,
            "acronym": text(src.get("Acronym")),
            "title": text(src.get("Title")),
            "research_area": text(src.get("Research Area")),
            "sub_research_area": text(src.get("SubResearch Area")),
            "project_type": text(src.get("Project Type")),
            "flight_platform": text(src.get("Flight Platform")),
            "n_files": len(files) if isinstance(files, list) else 0,
            "total_mb": round(sum(f.get("file_size", 0) for f in files if isinstance(f, dict)) / 1e6, 2) if isinstance(files, list) else 0,
            "has_experimental_table": bool((detail or {}).get("experimentalTable")),
            "n_experiments": len((detail or {}).get("experiments") or []),
            "status": status,
        })
        print(f"[{i}/{len(entries)}] {acc:8} {status:8} {rows[-1]['project_type'][:18]:18} {rows[-1]['title'][:55]}")

    (out / "index.json").write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {out}/index.json ({len(rows)} rows)")
    if failures:
        print("\nFAILED:")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("all fetched OK")


if __name__ == "__main__":
    main()
