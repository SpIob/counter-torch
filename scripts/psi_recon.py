#!/usr/bin/env python3
"""Recon of NASA PSI's public S3 bucket (no AWS account needed, standard library only).

  python3 scripts/psi_recon.py                      # top-level folders; combustion-looking ones get a *
  python3 scripts/psi_recon.py --prefix SOME/PATH/  # one level inside a folder: subfolders, files, sizes
  python3 scripts/psi_recon.py --grep bass          # only show folders whose name contains this text

Everything you run is saved to data/reports/psi-recon.json so the orchestrator can read it.
Needs internet access to nasa-psi.s3.us-west-2.amazonaws.com. If it is blocked, the AWS CLI does the same:
  aws s3 ls --no-sign-request s3://nasa-psi/
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://nasa-psi.s3.us-west-2.amazonaws.com"
KEYWORDS = ["combust", "flame", "fire", "bass", "same", "flex", "acme", "saffire", "spice", "slice",
            "sofie", "flare", "mdca", "daft", "fm2", "luci", "smoke", "burn", "droplet", "soot"]


def local(tag):
    return tag.rsplit("}", 1)[-1]


def list_level(base, prefix):
    """Folders and files directly under prefix, following S3 pagination."""
    folders, files, token = [], [], None
    while True:
        q = {"list-type": "2", "delimiter": "/", "max-keys": "1000"}
        if prefix:
            q["prefix"] = prefix
        if token:
            q["continuation-token"] = token
        url = f"{base}/?{urllib.parse.urlencode(q)}"
        with urllib.request.urlopen(url, timeout=30) as r:
            root = ET.fromstring(r.read())
        token = None
        for el in root:
            tag = local(el.tag)
            if tag == "CommonPrefixes":
                folders += [c.text for c in el if local(c.tag) == "Prefix"]
            elif tag == "Contents":
                kv = {local(c.tag): c.text for c in el}
                files.append({"key": kv.get("Key"), "size": int(kv.get("Size") or 0)})
            elif tag == "NextContinuationToken":
                token = el.text
        if not token:
            return folders, files


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--grep")
    ap.add_argument("--base", default=BASE)
    a = ap.parse_args()

    try:
        folders, files = list_level(a.base, a.prefix)
    except Exception as e:  # network, 403, bad XML
        print(f"FAILED: {e}")
        print(f"Try the AWS CLI instead: aws s3 ls --no-sign-request s3://nasa-psi/{a.prefix}")
        return 1

    g = a.grep.lower() if a.grep else None
    shown = [f for f in folders if not g or g in f.lower()]
    print(f"{len(folders)} folders and {len(files)} files directly under '{a.prefix or '/'}'"
          + (f" ({len(shown)} folders match '{a.grep}')" if g else ""))
    print("* = name looks combustion related (a guess from keywords, not a fact)")
    for f in shown:
        mark = "*" if any(k in f.lower() for k in KEYWORDS) else " "
        print(f" {mark} {f}")
    for f in files[:50]:
        print(f"    {f['key']}  ({human(f['size'])})")
    if len(files) > 50:
        print(f"    ... {len(files) - 50} more files")

    out = Path(__file__).resolve().parent.parent / "data" / "reports" / "psi-recon.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        saved = json.loads(out.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        saved = {}
    saved[a.prefix or "/"] = {
        "folders": folders,
        "files": files,
        "total_file_bytes_at_this_level": sum(f["size"] for f in files),
    }
    out.write_text(json.dumps(saved, indent=2) + "\n")
    print(f"saved -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
