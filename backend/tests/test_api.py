import os

import pytest
from fastapi.testclient import TestClient

os.environ["LLM_MODE"] = "offline"
from app.main import app  # loads the real repo fixtures

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_coverage_shape_from_real_data():
    c = client.get("/coverage").json()
    assert set(c) == {"points", "habitats", "gaps", "facts"}
    assert len(c["points"]) >= 20
    # Gap content depends on which records are loaded (real PSI data closes the Moon O2 x pressure gap),
    # so only the shape is asserted here. Gap logic is tested with fixed fixtures in test_coverage_ask.py.
    assert isinstance(c["gaps"], list)
    assert all({"habitat_id", "dimension", "message"} <= set(g) for g in c["gaps"])


def test_rank_shape():
    body = {"scenario": {"habitat_id": "lunar_habitat_expected"}, "concern": "prevention", "fuel": "solid", "limit": 5}
    r = client.post("/rank", json=body).json()
    assert len(r["items"]) == 5 and "coverage_note" in r
    top = r["items"][0]
    assert set(top) >= {"id", "name", "score", "components", "unknown_dims", "review_status", "why", "sources", "bounding"}
    assert all(0 <= i["score"] <= 1 for i in r["items"])
    assert r["items"] == sorted(r["items"], key=lambda i: (-i["score"], i["id"]))


def test_investigation_404_and_filter():
    assert client.get("/investigations/nope").status_code == 404
    assert all(i["family"] == "saffire" for i in client.get("/investigations?family=saffire").json())


def test_ask_unsupported_is_a_coverage_gap():
    r = client.post("/ask", json={"question": "What is the melting point of tungsten carbide?"}).json()
    assert r["coverage_gap"] is True and r["citations"] == []


def test_ask_validation():
    assert client.post("/ask", json={"question": "x"}).status_code == 422
    assert client.post("/rank", json={"scenario": {}, "concern": "bogus", "fuel": "any"}).status_code == 422


def test_points_has_zone_counts():
    p = client.get("/points").json()
    assert {"investigations", "total", "zones"} <= set(p)
    assert all({"habitat_id", "name", "count"} <= set(z) for z in p["zones"])
