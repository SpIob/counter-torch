from app import ask as askmod
from app import coverage as cov
from conftest import rec, store_with


def test_moon_gap_detected_when_no_record_reaches_it():
    a = rec("a", o2=(21, 21), p=(14.7, 14.7), g=(0, 0))
    b = rec("b", o2=(20, 85), p=(14, 30), g=(0, 0))
    s = store_with(a, b)
    msgs = [g["message"] for g in cov.gaps(s) if g["habitat_id"] == "moon"]
    assert any("gravity of 0.166 g" in m for m in msgs)
    assert any("no investigation covers oxygen of 30% or more with pressure of 10.2 psi or less" in m for m in msgs)


def test_moon_gap_absent_when_a_record_reaches_it():
    c = rec("c", o2=(30, 50), p=(5, 10), g=(0.166, 0.166))
    s = store_with(c)
    assert [g for g in cov.gaps(s) if g["habitat_id"] == "moon"] == []


def test_points_gap_uses_individual_tests():
    a = rec("a", o2=(21, 85), p=(5, 30), g=(0, 0))
    s = store_with(a, points={"PSI-1": [[21, 14.7], [85, 20.0], [40, 11.0]]})
    msgs = [g["message"] for g in cov.gaps(s) if g["habitat_id"] == "moon" and g["dimension"] == "combined"]
    assert any("none of the 3 individual tests" in m for m in msgs)
    s2 = store_with(a, points={"PSI-1": [[35, 9.0]]})
    assert not any("individual tests" in g["message"] for g in cov.gaps(s2) if g["habitat_id"] == "moon")


def test_unplaced_dims_listed_not_dropped():
    r = rec("r", o2=None, p=(1, 2), g=(0, 0))
    row = cov.point_row(r, store_with(r), "r")
    assert "o2_percent" in row["unplaced_dims"] and row["o2_percent"] is None


def test_ask_refuses_unsupported_and_cites_supported(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "offline")
    r = rec("flexlike", o2=(12, 34), p=(10, 44), g=(0, 0))
    r["objective"] = {"value": "Droplet burning with diluents CO2 and helium suppresses flames", "confidence": "high",
                      "sources": [{"kind": "nasa_page", "url": "https://example.org/flex", "note": "page"}]}
    s = store_with(r)
    s.brief_chunks = [("brief", "Partial gravity data: there is currently no partial-gravity combustion data available in PSI.")]
    idx = askmod.Index(askmod.build_chunks(s))
    no = askmod.ask(idx, "What is the ignition temperature of titanium in a vacuum chamber?")
    assert no["coverage_gap"] is True and no["citations"] == [] and no["mode"] == "offline"
    yes = askmod.ask(idx, "Do diluents like helium suppress droplet flames?")
    assert yes["coverage_gap"] is False
    assert yes["citations"][0]["id"] == "flexlike" and yes["citations"][0]["url"] == "https://example.org/flex"
    pg = askmod.ask(idx, "Is there partial-gravity combustion data in PSI?")
    assert pg["coverage_gap"] is False and pg["citations"][0]["id"] == "brief"


def test_gap_when_only_non_psi_record_covers_dimension():
    r = rec("fm", g=(0.166, 0.166))
    r["in_psi"] = False
    s = store_with(r)
    msgs = [g["message"] for g in cov.gaps(s) if g["habitat_id"] == "moon" and g["dimension"] == "gravity_g"]
    assert msgs and "Only FM" in msgs[0] and "no data in PSI" in msgs[0]
    s2 = store_with(rec("fm", g=(0.166, 0.166)))
    assert not [g for g in cov.gaps(s2) if g["habitat_id"] == "moon" and g["dimension"] == "gravity_g"]
