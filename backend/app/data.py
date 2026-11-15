"""Load records (verified > extracted > seed), habitats, test points and PSI file stats."""
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator

log = logging.getLogger("counter-torch")
ROOT = Path(os.environ.get("COUNTER_TORCH_ROOT", Path(__file__).resolve().parents[2]))


@dataclass
class Store:
    root: Path
    records: dict = field(default_factory=dict)       # id -> record
    origin: dict = field(default_factory=dict)        # id -> verified | extracted | seed
    habitats: list = field(default_factory=list)
    points: dict = field(default_factory=dict)        # accession -> [[o2_percent, pressure_psi], ...]
    psi_index: dict = field(default_factory=dict)     # accession -> {n_files, total_mb, project_type}
    acc_of: dict = field(default_factory=dict)        # id -> accession
    brief_chunks: list = field(default_factory=list)  # (doc_id, text)


def _read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def load_store(root: Path = ROOT) -> Store:
    root = Path(root)
    s = Store(root=root)
    validator = Draft202012Validator(_read(root / "schema" / "investigation.schema.json"))

    def valid(rec, where):
        errs = list(validator.iter_errors(rec))
        if errs:
            log.warning("skip %s (%s): %s", rec.get("id"), where, errs[0].message[:120])
            return False
        return True

    seed = _read(root / "data/fixtures/investigations.seed.json")["investigations"]
    layers = {"seed": {}, "extracted": {}, "verified": {}}
    for r in seed:
        if valid(r, "seed"):
            layers["seed"][r["id"]] = r
    for name in ("extracted", "verified"):
        for f in sorted((root / "data" / name).glob("*.json")):
            try:
                r = _read(f)
            except json.JSONDecodeError:
                log.warning("skip %s (bad JSON)", f)
                continue
            if isinstance(r, dict) and "id" in r and valid(r, name):
                layers[name][r["id"]] = r

    ids = list(layers["seed"]) + [i for i in list(layers["extracted"]) + list(layers["verified"]) if i not in layers["seed"]]
    for i in dict.fromkeys(ids):
        for name in ("verified", "extracted", "seed"):
            if i in layers[name]:
                s.records[i] = layers[name][i]
                s.origin[i] = name
                break
    log.info("loaded %d records: %s", len(s.records),
             {n: sum(1 for v in s.origin.values() if v == n) for n in ("verified", "extracted", "seed")})

    s.habitats = _read(root / "data/fixtures/habitats.json")["habitats"]

    pmap = root / "data/source/psi-map.json"
    amap = _read(pmap)["map"] if pmap.exists() else {}
    for i, r in s.records.items():
        acc = r.get("psi_accession") or amap.get(i)
        if acc:
            s.acc_of[i] = acc

    idx = root / "data/source/psi/index.json"
    if idx.exists():
        for row in _read(idx):
            s.psi_index[row["accession"]] = {"n_files": row.get("n_files"), "total_mb": row.get("total_mb"),
                                             "project_type": row.get("project_type")}
    pts = root / "data/source/psi/tables/points.json"
    if pts.exists():
        s.points = _read(pts)

    for name in ("challenge-brief.txt", "challenge-video-transcript.txt"):
        f = root / "data/source" / name
        if f.exists():
            doc = "brief" if "brief" in name else "video"
            for para in [p.strip() for p in f.read_text(encoding="utf-8").split("\n") if len(p.strip()) > 40]:
                s.brief_chunks.append((doc, para))
    return s


def rng(node):
    """Return (min, max, unit) of a sourced range node, or None when the value is null."""
    v = node.get("value") if node else None
    if not v:
        return None
    return v.get("min"), v.get("max"), v.get("unit")
