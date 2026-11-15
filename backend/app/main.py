import logging
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import ask as askmod
from . import coverage as cov
from . import llm
from .data import load_store
from .ranking import rank as do_rank, resolve_scenario

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Project Counter-Torch API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])

STORE = load_store()
INDEX = askmod.Index(askmod.build_chunks(STORE))


class Range(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    unit: str = ""


class Scenario(BaseModel):
    habitat_id: Optional[str] = None
    o2_percent: Optional[Range] = None
    pressure_psi: Optional[Range] = None
    gravity_g: Optional[Range] = None
    airflow: Optional[Range] = None


class RankRequest(BaseModel):
    scenario: Scenario
    concern: Literal["prevention", "detection", "suppression", "any"]
    fuel: Literal["solid", "gas", "liquid_droplet", "any"]
    limit: int = Field(10, ge=1, le=50)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    scenario: Optional[Scenario] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/investigations")
def investigations(family: Optional[str] = None, safety_function: Optional[str] = None, fuel_phase: Optional[str] = None,
                   status: Optional[str] = None, q: Optional[str] = None):
    out = []
    for r in STORE.records.values():
        if family and r["family"] != family:
            continue
        if status and r["status"] != status:
            continue
        if fuel_phase and r["fuel_phase"]["value"] != fuel_phase:
            continue
        if safety_function and safety_function not in (r["safety_functions"]["value"] or []):
            continue
        if q:
            hay = " ".join([r["name"], *r["aliases"], str(r["objective"]["value"] or "")]).lower()
            if q.lower() not in hay:
                continue
        out.append(r)
    return out


@app.get("/investigations/{rid}")
def investigation(rid: str):
    if rid not in STORE.records:
        raise HTTPException(404, "unknown id")
    return STORE.records[rid]


@app.get("/coverage")
def coverage():
    return cov.coverage(STORE)


@app.get("/points")
def points():
    """Individual tests from PSI experimental tables: accession -> [[o2_percent, pressure_psi], ...]."""
    names = {STORE.acc_of[i]: i for i in STORE.acc_of}
    return {"investigations": [{"id": names.get(a, a), "accession": a, "name": STORE.records[names[a]]["name"] if a in names else a,
                                "points": pts} for a, pts in STORE.points.items()],
            "total": cov.n_points(STORE), "zones": cov.zone_counts(STORE)}


@app.post("/rank")
def rank(req: RankRequest):
    scn = req.scenario.model_dump()
    return do_rank(STORE, scn, req.concern, req.fuel, req.limit, lambda s: cov.scenario_note(STORE, s))


@app.post("/ask")
def ask(req: AskRequest):
    return askmod.ask(INDEX, req.question)
