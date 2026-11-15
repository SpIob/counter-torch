import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest

from app.data import Store


def node(value=None, conf="unknown", sources=None):
    return {"value": value, "confidence": conf if value is not None else "unknown", "sources": sources or ([] if value is None else [{"kind": "brief", "url": None, "note": "t"}])}


def rec(rid="r1", o2=None, p=None, g=None, af=None, funcs=None, fuel=None, status="extracted", known_extra=0):
    r = lambda t: None if t is None else {"min": t[0], "max": t[1], "unit": "x"}
    return {"id": rid, "name": rid.upper(), "aliases": [], "family": "other", "status": "flown", "in_psi": True,
            "platform": node(), "objective": node(),
            "safety_functions": node(funcs, "high") if funcs else node(),
            "fuel_phase": node(fuel, "high") if fuel else node(),
            "fuel_materials": node(), "fuel_geometry": node(),
            "hardware": {"facility": node(), "apparatus": node()},
            "conditions": {"o2_percent": node(r(o2), "high"), "pressure_psi": node(r(p), "high"),
                           "airflow": node(None if af is None else {"min": af[0], "max": af[1], "unit": "cm/s"}, "high"), "gravity_g": node(r(g), "high"), "diluents": node()},
            "variables_swept": node(), "held_constant": node(), "sensors": node(), "relevance_notes": node(),
            "earth_applications": node(), "publications": [],
            "review": {"status": status, "extracted_by": "t", "verified_by": None, "verified_at": None, "notes": []}}


def store_with(*records, points=None):
    s = Store(root=Path("."))
    for r in records:
        s.records[r["id"]] = r
        s.origin[r["id"]] = r["review"]["status"]
    s.habitats = [
        {"id": "moon", "name": "Moon base", "o2_percent": {"min": 30, "max": None, "unit": "%"},
         "pressure_psi": {"min": None, "max": 10.2, "unit": "psi"}, "gravity_g": {"min": 0.166, "max": 0.166, "unit": "g"}, "basis": "t"},
        {"id": "air", "name": "Earth air", "o2_percent": {"min": 21, "max": 21, "unit": "%"},
         "pressure_psi": {"min": 14.7, "max": 14.7, "unit": "psi"}, "gravity_g": {"min": 1, "max": 1, "unit": "g"}, "basis": "t"},
    ]
    s.points = points or {}
    return s
