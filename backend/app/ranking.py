"""Deterministic ranking. Contract: AGENTS.md ("Ranking contract"). The LLM never scores."""
from .data import rng

W = {"conditions": 0.35, "function": 0.25, "fuel": 0.20, "evidence": 0.20}
AXIS = {"o2_percent": (0.0, 100.0), "pressure_psi": (0.0, 50.0), "gravity_g": (0.0, 1.0), "airflow": (0.0, 100.0)}
POINT_TOL = {"o2_percent": 5.0, "pressure_psi": 0.75, "gravity_g": 0.05, "airflow": 5.0}  # 5% of axis
DIMS = ("o2_percent", "pressure_psi", "gravity_g", "airflow")
BASE = {"verified": 1.0, "extracted": 0.6, "seed": 0.4, "disputed": 0.1}


def resolve_scenario(scn, habitats):
    """Custom values override the habitat. Returns {dim: (lo, hi) | None}."""
    out = {d: None for d in DIMS}
    hab = next((h for h in habitats if h["id"] == (scn or {}).get("habitat_id")), None)
    for d in ("o2_percent", "pressure_psi", "gravity_g"):
        if hab and hab.get(d):
            out[d] = (hab[d].get("min"), hab[d].get("max"))
    for d in DIMS:
        v = (scn or {}).get(d)
        if v:
            out[d] = (v.get("min"), v.get("max"))
    for d, v in out.items():
        if v is not None and v[0] is None and v[1] is None:
            out[d] = None
    return out


def dim_score(dim, inv, scen):
    """Return (score, label, unknown). inv is (min, max, unit) or None."""
    if inv is None or (inv[0] is None and inv[1] is None) or (dim == "airflow" and inv[2] not in (None, "cm/s")):
        return 0.3, "unknown", True
    lo, hi, _ = inv
    partial = lo is None or hi is None
    lo = hi if lo is None else lo
    hi = lo if hi is None else hi
    a_lo, a_hi = AXIS[dim]
    slo = a_lo if scen[0] is None else scen[0]
    shi = a_hi if scen[1] is None else scen[1]
    if lo <= shi and hi >= slo:
        return 1.0, "overlaps", partial
    gap = slo - hi if hi < slo else lo - shi
    tol = POINT_TOL[dim] if slo == shi else 0.25 * (shi - slo)
    if gap <= tol:
        return 0.5, "near", partial
    return 0.0, "outside", partial


def sourced_share(rec):
    nodes = []

    def walk(n):
        if isinstance(n, dict):
            if {"value", "confidence", "sources"} <= set(n):
                nodes.append(n)
            else:
                for v in n.values():
                    walk(v)
    walk(rec)
    return (sum(1 for n in nodes if n["confidence"] != "unknown") / len(nodes)) if nodes else 0.0


def score_record(rec, scenario, concern, fuel):
    """scenario: output of resolve_scenario. Returns dict with score, components, unknown_dims, bounding, labels."""
    cond_parts, unknown, labels, bounding = [], [], {}, False
    for d in DIMS:
        scen = scenario[d]
        if scen is None:
            continue
        inv = rng(rec["conditions"][d if d != "airflow" else "airflow"])
        s, label, unk = dim_score(d, inv, scen)
        if d == "gravity_g" and scen[0] is not None and scen[1] is not None and scen[0] > 0 and scen[1] < 1 \
                and inv and inv[1] is not None and inv[1] <= 0.01:
            s, label, unk = 0.5, "bounding", False
            bounding = True
        if unk:
            unknown.append(d)
        cond_parts.append(s)
        labels[d] = label
    conditions = sum(cond_parts) / len(cond_parts) if cond_parts else 0.5

    sf = rec["safety_functions"]["value"]
    if concern == "any":
        function, f_label = 1.0, "any"
    elif sf and concern in sf:
        function, f_label = 1.0, "matches"
    elif not sf or "fundamental" in sf:
        function, f_label = 0.3, "unknown or fundamental"
    else:
        function, f_label = 0.0, "other function"

    fp = rec["fuel_phase"]["value"]
    if fuel == "any":
        fuel_s, fu_label = 1.0, "any"
    elif fp == fuel:
        fuel_s, fu_label = 1.0, "matches"
    elif fp == "mixed":
        fuel_s, fu_label = 0.5, "mixed"
    elif fp is None:
        fuel_s, fu_label = 0.3, "unknown"
    else:
        fuel_s, fu_label = 0.0, "other fuel phase"

    status = rec["review"]["status"]
    share = sourced_share(rec)
    evidence = BASE[status] * (0.5 + 0.5 * share)
    comps = {"conditions": conditions, "function": function, "fuel": fuel_s, "evidence": evidence}
    total = sum(W[k] * v for k, v in comps.items())
    return {"score": total, "components": comps, "unknown_dims": unknown, "bounding": bounding,
            "labels": {**labels, "function": f_label, "fuel": fu_label}, "share": share, "status": status}


DIM_NAME = {"o2_percent": "O2", "pressure_psi": "pressure", "gravity_g": "gravity", "airflow": "airflow"}


DIM_PHRASE = {
    "o2_percent": {"overlaps": "oxygen range overlaps", "near": "oxygen range is close", "outside": "oxygen range is outside", "unknown": "oxygen range is unknown", "bounding": "oxygen range overlaps"},
    "pressure_psi": {"overlaps": "pressure range overlaps", "near": "pressure range is close", "outside": "pressure range is outside", "unknown": "pressure range is unknown", "bounding": "pressure range overlaps"},
    "gravity_g": {"overlaps": "gravity overlaps", "near": "gravity is close", "outside": "gravity is outside", "unknown": "gravity is unknown", "bounding": "gravity is a bounding estimate from microgravity data"},
    "airflow": {"overlaps": "airflow overlaps", "near": "airflow is close", "outside": "airflow is outside", "unknown": "airflow is unknown", "bounding": "airflow overlaps"},
}
SENT = {"matches": "matches", "any": "any", "unknown or fundamental": "is fundamental or unrecorded", "other function": "does not match",
        "mixed": "is mixed", "unknown": "is unrecorded", "other fuel phase": "does not match"}


def why_text(rec, r):
    L = r["labels"]
    cond = [DIM_PHRASE[d][lab] for d, lab in L.items() if d in DIM_PHRASE]
    out = [("; ".join(cond)).capitalize() + "." if cond else "The scenario sets no conditions."]
    extra = []
    if L["function"] != "any":
        extra.append(f"safety function {SENT[L['function']]}")
    if L["fuel"] != "any":
        extra.append(f"fuel phase {SENT[L['fuel']]}")
    if extra:
        out.append("; ".join(extra).capitalize() + ".")
    out.append(f"Evidence: {r['status']} record, {round(r['share'] * 18)} of 18 fields sourced.")
    return " ".join(out)


def collect_sources(rec, limit=6):
    out, seen = [], set()
    for node in (rec["conditions"]["o2_percent"], rec["conditions"]["pressure_psi"], rec["conditions"]["gravity_g"],
                 rec["conditions"]["airflow"], rec["safety_functions"], rec["fuel_phase"]):
        for s in node.get("sources", []):
            key = (s["kind"], s["url"], s["note"])
            if key not in seen:
                seen.add(key)
                out.append({"kind": s["kind"], "url": s["url"], "note": s["note"]})
    return out[:limit]


def rank(store, scn, concern, fuel, limit=10, coverage_note_fn=None):
    scenario = resolve_scenario(scn, store.habitats)
    items = []
    for rid, rec in store.records.items():
        r = score_record(rec, scenario, concern, fuel)
        items.append({"id": rid, "name": rec["name"], "score": round(r["score"], 4),
                      "components": {k: round(v, 4) for k, v in r["components"].items()},
                      "unknown_dims": r["unknown_dims"], "bounding": r["bounding"], "review_status": r["status"],
                      "why": why_text(rec, r), "sources": collect_sources(rec)})
    items.sort(key=lambda x: (-x["score"], x["id"]))
    note = coverage_note_fn(scenario) if coverage_note_fn else None
    return {"items": items[:limit], "coverage_note": note}
