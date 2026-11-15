#!/usr/bin/env python3
"""Show the shape of a JSON file so you can see what an API returned.

  python3 scripts/psi_peek.py data/source/psi-search.json
"""
import json
import sys


def biggest_list(node, path="$"):
    """Find the largest list of objects anywhere in the JSON (the likely result list)."""
    best = (0, path, None)
    if isinstance(node, list):
        if node and all(isinstance(x, dict) for x in node):
            best = (len(node), path, node)
        for i, x in enumerate(node[:3]):
            c = biggest_list(x, f"{path}[{i}]")
            if c[0] > best[0]:
                best = c
    elif isinstance(node, dict):
        for k, v in node.items():
            c = biggest_list(v, f"{path}.{k}")
            if c[0] > best[0]:
                best = c
    return best


def short(v, n=90):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "..."


if len(sys.argv) != 2:
    sys.exit(__doc__)
try:
    d = json.load(open(sys.argv[1]))
except (OSError, json.JSONDecodeError) as e:
    sys.exit(f"Not valid JSON ({e}). If it starts with '<', the server sent HTML, not the API response.")

print("top level:", type(d).__name__, list(d)[:15] if isinstance(d, dict) else f"{len(d)} items")
n, path, items = biggest_list(d)
if not items:
    sys.exit("no list of records found")
print(f"\nrecords: {n} at {path}\nfields of the first record:")
for k, v in items[0].items():
    print(f"  {k}: {short(v)}")
want = [k for k in items[0] if any(t in k.lower() for t in ("id", "title", "name", "type", "area", "acronym"))][:4]
print(f"\nfirst 30 records, fields {want}:")
for it in items[:30]:
    print("  " + " | ".join(str(it.get(k))[:60] for k in want))