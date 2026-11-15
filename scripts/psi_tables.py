#!/usr/bin/env python3
"""Download the small 'Experimental table' CSV files listed in the local PSI records.

Reads data/source/psi/PSI-*.json (from psi_pull.py), finds each record's
`experimentalTable` entries and downloads CSVs up to --max-mb (default 5 MB) to
data/source/psi/tables/ACC.csv, using the same endpoint the PSI website uses:

    GET /geode-py/ws/studies/ACC/download?file=FILE_ID&version=V&studyVersion=SV&redirect=false

That call returns a temporary link (or the file itself); the script follows it.
It never touches the big data files. Standard library only.

    python3 scripts/psi_tables.py
    python3 scripts/psi_tables.py --only PSI-69 PSI-102
"""
import argparse
import csv
import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

HOST = "https://psi.nasa.gov"
UA = "Mozilla/5.0 (compatible; Counter-Torch-hackathon/0.1)"


def fetch(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def find_link(obj):
    if isinstance(obj, str):
        return obj if obj.startswith("http") else None
    if isinstance(obj, dict):
        for v in obj.values():
            hit = find_link(v)
            if hit:
                return hit
    if isinstance(obj, list):
        for v in obj:
            hit = find_link(v)
            if hit:
                return hit
    return None


def download(host, acc, entry, study_version, ua):
    fid = (entry.get("_id") or {}).get("$oid")
    if not fid:
        raise RuntimeError("entry has no _id")
    api = (f"{host}/geode-py/ws/studies/{acc}/download?file={fid}"
           f"&version={entry.get('version', 1)}&studyVersion={study_version}&redirect=false")
    body = fetch(api, ua)
    text = body.decode("utf-8-sig", "replace").strip()
    link = None
    if text.startswith("http"):
        link = text.strip('"')
    else:
        try:
            link = find_link(json.loads(text))
        except json.JSONDecodeError:
            pass
    if link:
        body = fetch(link, ua)
        text = body.decode("utf-8-sig", "replace").strip()
    if text[:1] in "<{[" and "," not in text.split("\n")[0]:
        raise RuntimeError("not a CSV; response began: " + text[:160].replace("\n", " "))
    return body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--psi-dir", default="data/source/psi")
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--max-mb", type=float, default=5.0)
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--ua", default=UA)
    args = ap.parse_args()

    psi = Path(args.psi_dir)
    out = psi / "tables"
    out.mkdir(parents=True, exist_ok=True)
    index, problems = [], []

    for p in sorted(psi.glob("PSI-*.json"), key=lambda x: int(re.search(r"(\d+)", x.stem).group(1))):
        if p.name.endswith(".search.json"):
            continue
        acc = p.stem
        if args.only and acc not in args.only:
            continue
        d = json.loads(p.read_text())
        entries = d.get("experimentalTable") or []
        for n, t in enumerate(entries):
            name, size = t.get("file_name", ""), t.get("file_size", 0)
            if not name.lower().endswith(".csv"):
                print(f"{acc:8} skip (not a CSV): {name}")
                continue
            if size > args.max_mb * 1e6:
                print(f"{acc:8} skip (too big, {size/1e6:.1f} MB): {name}")
                continue
            dest = out / (f"{acc}.csv" if n == 0 else f"{acc}_{n+1}.csv")
            status = "cached"
            if not dest.exists():
                try:
                    dest.write_bytes(download(args.host, acc, t, d.get("version", 1), args.ua))
                    status = "fetched"
                except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
                    problems.append(f"{acc}: {e}")
                    print(f"{acc:8} FAILED: {e}")
                    continue
            rows = list(csv.reader(io.StringIO(dest.read_text(encoding="utf-8-sig", errors="replace"))))
            header = rows[0] if rows else []
            index.append({"accession": acc, "file": str(dest), "rows": max(len(rows) - 1, 0), "columns": header})
            print(f"{acc:8} {status:8} {len(rows)-1:4} rows  cols: {' | '.join(header)[:150]}")

    (out / "index.json").write_text(json.dumps(index, indent=1))
    print(f"\n{len(index)} tables, index at {out}/index.json")
    if problems:
        print("problems:\n  " + "\n  ".join(problems))


if __name__ == "__main__":
    main()
