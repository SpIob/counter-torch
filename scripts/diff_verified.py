#!/usr/bin/env python3
"""Diff verified records against the extracted records they came from.

Usage:
  python3 scripts/diff_verified.py                # every id in data/verified
  python3 scripts/diff_verified.py data/extracted/flex.json data/verified/flex.json

For each id: compares every sourced node (value/confidence/sources) and the
review block, and prints what the verifier changed. Exit code 0 = no resets or
corrections found, 1 = at least one record was changed (or is missing a twin).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACTED = ROOT / "data" / "extracted"
VERIFIED = ROOT / "data" / "verified"
MAX_SOURCES = 2


def is_sourced(node):
    return isinstance(node, dict) and {"value", "confidence", "sources"} <= set(node)


def walk_sourced(node, path=""):
    if is_sourced(node):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_sourced(v, f"{path}.{k}" if path else k)


def short(text, n=120):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "\u2026"


def src_note(node):
    srcs = node.get("sources") or []
    if not srcs:
        return ""
    out = []
    for s in srcs[:MAX_SOURCES]:
        kind = s.get("kind", "?")
        note = short(s.get("note", ""), 70)
        out.append(f"{kind}: {note}" if note else kind)
    if len(srcs) > MAX_SOURCES:
        out.append(f"+{len(srcs) - MAX_SOURCES} more")
    return "  [" + "; ".join(out) + "]"


def fmt_value(v):
    return short(json.dumps(v, ensure_ascii=False), 90)


def flatten(node, path=""):
    """Dotted path -> ("sourced", node) or ("plain", value). review.* is excluded."""
    if path == "review" or path.startswith("review."):
        return {}
    out = {}
    if is_sourced(node):
        out[path] = ("sourced", node)
    elif isinstance(node, dict):
        for k, v in node.items():
            out.update(flatten(v, f"{path}.{k}" if path else k))
    else:
        out[path] = ("plain", node)
    return out


def fmt_entry(entry):
    if entry is None:
        return "n/a"
    kind, obj = entry
    if kind == "sourced":
        return f"{fmt_value(obj['value'])} ({obj['confidence']})"
    return fmt_value(obj)


def field_changes(old, new):
    """Per-path differences between two records: sourced nodes and plain fields alike."""
    o, n = flatten(old), flatten(new)
    changes = []
    for path in sorted(set(o) | set(n)):
        a, b = o.get(path), n.get(path)
        if a is None:
            changes.append({"kind": "added", "path": path, "a": None, "b": b, "detail": []})
            continue
        if b is None:
            changes.append({"kind": "removed", "path": path, "a": a, "b": None, "detail": []})
            continue
        if a[0] != b[0]:
            changes.append({"kind": "changed", "path": path, "a": a, "b": b,
                            "detail": [f"shape {a[0]} -> {b[0]}"]})
            continue
        if a[0] == "sourced":
            x, y = a[1], b[1]
            detail = []
            if x["value"] != y["value"]:
                detail.append(f"value {fmt_value(x['value'])} -> {fmt_value(y['value'])}")
            if x["confidence"] != y["confidence"]:
                detail.append(f"confidence {x['confidence']} -> {y['confidence']}")
            if [s.get("url") for s in x["sources"]] != [s.get("url") for s in y["sources"]]:
                detail.append(f"sources {len(x['sources'])} -> {len(y['sources'])}")
        else:
            detail = [] if a[1] == b[1] else [
                f"value {fmt_value(a[1])} -> {fmt_value(b[1])}"]
        if detail:
            changes.append({"kind": "changed", "path": path, "a": a, "b": b, "detail": detail})
    return changes


def review_changes(old, new):
    o, n = old.get("review", {}) or {}, new.get("review", {}) or {}
    out = []
    for key in ("status", "verified_by", "verified_at", "notes", "flags"):
        if key in o or key in n:
            if o.get(key) != n.get(key):
                out.append((key, o.get(key), n.get(key)))
    return out


def report(ext_path, ver_path):
    try:
        old = json.loads(ext_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"MISSING  extracted record unreadable: {ext_path} ({e})")
        return 1
    try:
        new = json.loads(ver_path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"MISSING  verified record unreadable: {ver_path} ({e})")
        return 1

    rid = new.get("id", ver_path.stem)
    status = (new.get("review") or {}).get("status", "?")
    changes = field_changes(old, new)
    rev = review_changes(old, new)

    if not changes and not rev:
        print(f"{rid:<18} {status:<9} no change "
              f"({len(dict(walk_sourced(old)))} sourced + {len(flatten(old))} paths re-checked)")
        return 0

    print(f"{rid:<18} {status:<9} {len(changes)} field change(s), {len(rev)} review change(s)")
    for c in changes:
        path, a, b = c["path"], c["a"], c["b"]
        if c["kind"] == "added":
            print(f"    + {path} = {fmt_entry(b)}")
            continue
        if c["kind"] == "removed":
            print(f"    - {path} (was {fmt_entry(a)})")
            continue
        print(f"    ~ {path}: {'; '.join(c['detail'])}")
        if b[0] == "sourced":
            note = (b[1].get("note") or (a[1].get("note") if a[0] == "sourced" else "") or "")
            if note:
                print(f"        note: {short(note)}")
            if a[0] == "sourced" and b[1].get("sources") != a[1].get("sources"):
                print(f"        now:{src_note(b[1]) or '  (none)'}")
    for key, before, after in rev:
        print(f"    review.{key}: {short(json.dumps(before, ensure_ascii=False), 80)} -> {short(json.dumps(after, ensure_ascii=False), 80)}")
    return 1


def main():
    if len(sys.argv) >= 3 and not sys.argv[1].startswith("-"):
        pairs = [(Path(sys.argv[1]), Path(sys.argv[2]))]
    else:
        pairs = []
        for v in sorted(VERIFIED.glob("*.json")):
            pairs.append((EXTRACTED / v.name, v))

    if not pairs:
        print(f"no records under {VERIFIED.relative_to(ROOT)}")
        return 1

    print(f"diff_verified: data/extracted -> data/verified ({len(pairs)} ids)")
    print()
    changed = 0
    for ext_path, ver_path in pairs:
        changed += report(ext_path, ver_path)
    print()
    print(f"{len(pairs)} ids compared, {changed} with changes")
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
