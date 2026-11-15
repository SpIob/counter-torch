"""Coverage points, habitat zones and gaps. Gap text is computed here, never by the LLM."""
from .data import rng
from .ranking import AXIS, DIMS

NAMES = {"o2_percent": "oxygen", "pressure_psi": "pressure", "gravity_g": "gravity", "airflow": "airflow"}
UNIT = {"o2_percent": "%", "pressure_psi": " psi", "gravity_g": " g", "airflow": " cm/s"}

FACTS = [
    "PSI currently holds no partial-gravity combustion data.",
    "Moon habitats are expected to use 30% oxygen or more at 10.2 psi or less.",
    "Microgravity and normal-gravity results could bound what happens at intermediate gravity.",
    "ACME E-FIELD Flames mimicked partial gravity with an electric field acting on flame ions.",
]


def fmt(dim, lo, hi):
    u = UNIT[dim]
    if lo is not None and hi is not None:
        return f"{lo:g}{u}" if lo == hi else f"{lo:g}\u2013{hi:g}{u}"
    if lo is not None:
        return f"{lo:g}{u} or more"
    return f"{hi:g}{u} or less"


def overlaps(dim, inv, h):
    """inv: (min, max, unit) or None; h: (lo, hi) habitat range, None bound = open. Unknown inv never overlaps."""
    if inv is None or (inv[0] is None and inv[1] is None):
        return False
    lo = inv[1] if inv[0] is None else inv[0]
    hi = inv[0] if inv[1] is None else inv[1]
    a_lo, a_hi = AXIS[dim]
    h_lo = a_lo if h[0] is None else h[0]
    h_hi = a_hi if h[1] is None else h[1]
    return lo <= h_hi and hi >= h_lo


def point_row(rec, store, rid):
    c = rec["conditions"]
    acc = store.acc_of.get(rid) or rec.get("psi_accession")
    idx = store.psi_index.get(acc, {}) if acc else {}
    node = lambda d: c[d]
    out = {"id": rid, "name": rec["name"], "family": rec["family"], "status": rec["status"],
           "review_status": rec["review"]["status"], "psi_accession": acc,
           "project_type": rec.get("project_type") or idx.get("project_type"),
           "psi_files": idx.get("n_files"), "psi_size_mb": idx.get("total_mb"),
           "fuel_phase": rec["fuel_phase"]["value"], "safety_functions": rec["safety_functions"]["value"],
           "confidence": {}, "unplaced_dims": []}
    for d in DIMS:
        r = rng(node(d))
        out[d] = None if r is None else {"min": r[0], "max": r[1], "unit": r[2]}
        out["confidence"][d] = node(d)["confidence"]
        if r is None or (r[0] is None and r[1] is None):
            out["unplaced_dims"].append(d)
    return out


def n_points(store):
    return sum(len(v) for v in store.points.values())


def gaps(store):
    out = []
    recs = list(store.records.items())
    for h in store.habitats:
        known = {}
        for d in ("o2_percent", "pressure_psi", "gravity_g"):
            hr = h.get(d)
            if not hr:
                continue
            hh = (hr.get("min"), hr.get("max"))
            known[d] = hh
            cands = [rng(r["conditions"][d]) for _, r in recs]
            if not any(c is not None and (c[0] is not None or c[1] is not None) for c in cands):
                out.append({"habitat_id": h["id"], "dimension": d,
                            "message": f"{h['name']}: no investigation records a {NAMES[d]} range"})
            elif not any(overlaps(d, c, hh) for c in cands):
                out.append({"habitat_id": h["id"], "dimension": d,
                            "message": f"{h['name']}: no investigation covers {NAMES[d]} of {fmt(d, *hh)}"})
            else:
                # Covered only by records that have no PSI entry: still a gap for a PSI-powered tool.
                hits = [(rid, r) for rid, r in recs if overlaps(d, rng(r["conditions"][d]), hh)]
                if not any(r.get("in_psi") for _, r in hits):
                    ids = ", ".join(sorted(rid.upper() for rid, _ in hits))
                    out.append({"habitat_id": h["id"], "dimension": d,
                                "message": f"{h['name']}: no PSI investigation covers {NAMES[d]} of {fmt(d, *hh)}. Only {ids} lists it, and {'it has' if len(hits) == 1 else 'they have'} no data in PSI yet."})
        if "o2_percent" in known and "pressure_psi" in known:
            both = [rid for rid, r in recs
                    if overlaps("o2_percent", rng(r["conditions"]["o2_percent"]), known["o2_percent"])
                    and overlaps("pressure_psi", rng(r["conditions"]["pressure_psi"]), known["pressure_psi"])]
            lab = f"oxygen of {fmt('o2_percent', *known['o2_percent'])} with pressure of {fmt('pressure_psi', *known['pressure_psi'])}"
            if not both:
                out.append({"habitat_id": h["id"], "dimension": "combined",
                            "message": f"{h['name']}: no investigation covers {lab}"})
            if store.points:
                hit = [1 for pts in store.points.values() for o, p in pts
                       if overlaps("o2_percent", (o, o, "%"), known["o2_percent"])
                       and overlaps("pressure_psi", (p, p, "psi"), known["pressure_psi"])]
                if not hit:
                    out.append({"habitat_id": h["id"], "dimension": "combined",
                                "message": f"{h['name']}: none of the {n_points(store):,} individual tests "
                                           f"({len(store.points)} investigations) ran at {lab}."})
    return out


def zone_counts(store):
    """Per habitat with both an O2 and a pressure range: how many individual PSI-table tests fall inside it."""
    out = []
    for h in store.habitats:
        o, p = h.get("o2_percent"), h.get("pressure_psi")
        if not o or not p:
            continue
        ho, hp = (o.get("min"), o.get("max")), (p.get("min"), p.get("max"))
        if ho[0] == ho[1] and hp[0] == hp[1]:
            continue  # a single reference point, not a zone
        n = sum(1 for pts in store.points.values() for x, y in pts
                if overlaps("o2_percent", (x, x, "%"), ho) and overlaps("pressure_psi", (y, y, "psi"), hp))
        out.append({"habitat_id": h["id"], "name": h["name"], "count": n})
    return out


def coverage(store):
    return {"points": [point_row(r, store, rid) for rid, r in store.records.items()],
            "habitats": store.habitats, "gaps": gaps(store), "facts": FACTS}


def scenario_note(store, scenario):
    notes = []
    g = scenario.get("gravity_g")
    if g and g[0] is not None and g[1] is not None and g[0] > 0 and g[1] < 1:
        notes.append("PSI has no partial-gravity combustion data yet, so partial-gravity scores are bounding estimates from microgravity data.")
    o, p = scenario.get("o2_percent"), scenario.get("pressure_psi")
    if o and p:
        ok = [1 for r in store.records.values()
              if overlaps("o2_percent", rng(r["conditions"]["o2_percent"]), o)
              and overlaps("pressure_psi", rng(r["conditions"]["pressure_psi"]), p)]
        if not ok:
            notes.append("No loaded investigation has oxygen and pressure ranges that both overlap this scenario.")
    return " ".join(notes) or None
