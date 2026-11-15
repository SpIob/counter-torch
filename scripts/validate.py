#!/usr/bin/env python3
"""Validate Flame Atlas data against the schemas.

Usage:
  python3 scripts/validate.py                 # fixtures + data/extracted + data/verified
  python3 scripts/validate.py PATH [PATH ...] # specific files or folders
  python3 scripts/validate.py --fill          # also print how much of each record is filled in

Exit code 0 = everything valid, 1 = at least one problem.
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
INV_SCHEMA = json.loads((ROOT / "schema" / "investigation.schema.json").read_text())
HAB_SCHEMA = json.loads((ROOT / "schema" / "habitats.schema.json").read_text())
INV_VALIDATOR = Draft202012Validator(INV_SCHEMA)
HAB_VALIDATOR = Draft202012Validator(HAB_SCHEMA)


def is_sourced(node):
    return isinstance(node, dict) and {"value", "confidence", "sources"} <= set(node)


def walk_sourced(node, path=""):
    if is_sourced(node):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_sourced(v, f"{path}.{k}" if path else k)


def range_problems(rec):
    out = []
    for path, node in walk_sourced(rec):
        v = node["value"]
        if isinstance(v, dict) and v.get("min") is not None and v.get("max") is not None and v["min"] > v["max"]:
            out.append(f"{rec['id']}: {path} has min > max")
    return out


def load_records(path):
    data = json.loads(path.read_text())
    if isinstance(data, dict) and "habitats" in data:
        return "habitats", data
    if isinstance(data, dict) and "investigations" in data:
        return "investigations", data["investigations"]
    if isinstance(data, dict) and "id" in data:
        return "investigations", [data]
    return "other", data


def collect(paths):
    files = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            files += sorted(p.rglob("*.json"))
        elif p.exists():
            files.append(p)
        else:
            print(f"MISSING  {p}")
    return files


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show_fill = "--fill" in sys.argv
    if args:
        files = collect(args)
    else:
        files = collect([
            ROOT / "data" / "fixtures",
            ROOT / "data" / "extracted",
            ROOT / "data" / "verified",
        ])

    errors = 0
    all_ids = set()
    loaded = []  # (path, kind, records)
    for f in files:
        try:
            kind, recs = load_records(f)
        except json.JSONDecodeError as e:
            print(f"FAIL     {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f}: invalid JSON ({e})")
            errors += 1
            continue
        loaded.append((f, kind, recs))
        if kind == "investigations":
            all_ids |= {r.get("id") for r in recs if isinstance(r, dict)}
    # Fixtures are always part of the id universe so shared_with refs resolve in partial runs.
    seed = ROOT / "data" / "fixtures" / "investigations.seed.json"
    if seed.exists():
        all_ids |= {r["id"] for r in json.loads(seed.read_text())["investigations"]}

    for f, kind, recs in loaded:
        rel = f.relative_to(ROOT) if f.is_relative_to(ROOT) else f
        problems = []
        if kind == "habitats":
            problems += [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in HAB_VALIDATOR.iter_errors(recs)]
            n = len(recs["habitats"])
        elif kind == "investigations":
            seen = set()
            for r in recs:
                rid = r.get("id", "<no id>") if isinstance(r, dict) else "<not an object>"
                if rid in seen:
                    problems.append(f"{rid}: duplicate id in file")
                seen.add(rid)
                for e in INV_VALIDATOR.iter_errors(r):
                    problems.append(f"{rid}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message[:160]}")
                if isinstance(r, dict) and "hardware" in r:
                    for ref in r["hardware"].get("shared_with", []):
                        if ref not in all_ids:
                            problems.append(f"{rid}: shared_with references unknown id '{ref}'")
                    problems += range_problems(r)
                # extracted/verified single-record files must be named <id>.json
                if len(recs) == 1 and f.parent.name in ("extracted", "verified") and f.stem != rid:
                    problems.append(f"{rid}: file name should be {rid}.json")
            n = len(recs)
        else:
            continue
        if problems:
            errors += len(problems)
            print(f"FAIL     {rel} ({len(problems)} problems)")
            for p in problems[:20]:
                print(f"           - {p}")
            if len(problems) > 20:
                print(f"           ... {len(problems) - 20} more")
        else:
            print(f"ok       {rel} ({n} records)")
            if show_fill and kind == "investigations":
                for r in recs:
                    nodes = [n_ for _, n_ in walk_sourced(r)]
                    known = sum(1 for n_ in nodes if n_["confidence"] != "unknown")
                    print(f"           {r['id']:<16} {known:>2}/{len(nodes)} fields sourced  [{r['review']['status']}]")

    print("OK" if not errors else f"FAILED ({errors} problems)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
