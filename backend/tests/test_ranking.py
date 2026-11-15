import pytest

from app.ranking import rank, resolve_scenario, score_record, sourced_share
from conftest import rec, store_with


def scen(store, habitat=None, **kw):
    return resolve_scenario({"habitat_id": habitat, **kw}, store.habitats)


def test_earth_air_full_overlap():
    # Hand-computed: O2 21 in 17-30 -> 1; pressure 14.7 in 7-45 -> 1; gravity 1 vs micro-g: point scenario,
    # gap 1.0 > 0.05 -> 0.   conditions = (1 + 1 + 0) / 3 = 0.6667. function: any -> 1. fuel: any -> 1.
    r = rec(o2=(17, 30), p=(7, 45), g=(0, 0), funcs=["prevention"], fuel="solid", status="verified")
    s = store_with(r)
    out = score_record(r, scen(s, "air"), "any", "any")
    assert out["components"]["conditions"] == pytest.approx(2 / 3)
    assert out["components"]["function"] == 1.0 and out["components"]["fuel"] == 1.0
    ev = 1.0 * (0.5 + 0.5 * sourced_share(r))
    assert out["components"]["evidence"] == pytest.approx(ev)
    assert out["score"] == pytest.approx(0.35 * 2 / 3 + 0.25 + 0.20 + 0.20 * ev)
    assert out["unknown_dims"] == [] and not out["bounding"]


def test_moon_partial_gravity_is_bounding():
    # O2 scen >=30 (open to 100) vs 21-40 -> overlaps 1. Pressure scen <=10.2 (0..10.2) vs 14-30: gap 3.8 > 25% of 10.2 (2.55) -> 0.
    # Gravity 0.166 vs micro-g -> 0.5 bounding. conditions = 1.5 / 3 = 0.5.
    r = rec(o2=(21, 40), p=(14, 30), g=(0, 0), funcs=["suppression"], fuel="gas", status="extracted")
    s = store_with(r)
    out = score_record(r, scen(s, "moon"), "prevention", "solid")
    assert out["components"]["conditions"] == pytest.approx(0.5)
    assert out["bounding"] is True
    assert out["components"]["function"] == 0.0      # records suppression only, asked prevention
    assert out["components"]["fuel"] == 0.0          # gas vs solid
    ev = 0.6 * (0.5 + 0.5 * sourced_share(r))
    assert out["score"] == pytest.approx(0.35 * 0.5 + 0.20 * ev)


def test_unknown_range_scores_point_three_and_is_listed():
    # O2 unknown -> 0.3 + listed; pressure near: scen 14.7 point, record 15.2-20 -> gap 0.5 <= 0.75 -> 0.5; airflow not asked.
    r = rec(o2=None, p=(15.2, 20), g=(1, 1), funcs=None, fuel=None, status="seed")
    s = store_with(r)
    out = score_record(r, scen(s, "air"), "detection", "liquid_droplet")
    assert out["unknown_dims"] == ["o2_percent"]
    assert out["components"]["conditions"] == pytest.approx((0.3 + 0.5 + 1.0) / 3)
    assert out["components"]["function"] == 0.3 and out["components"]["fuel"] == 0.3


def test_custom_values_override_habitat_and_airflow_only_when_given():
    r = rec(o2=(21, 21), p=(14.7, 14.7), g=(1, 1), af=(5, 10))
    s = store_with(r)
    a = scen(s, "air", airflow={"min": 5, "max": 5, "unit": "cm/s"})
    assert score_record(r, a, "any", "any")["components"]["conditions"] == 1.0
    b = scen(s, "air", o2_percent={"min": 40, "max": 40, "unit": "%"})
    assert score_record(r, b, "any", "any")["components"]["conditions"] == pytest.approx(2 / 3)


def test_rank_orders_by_score_and_returns_note():
    good = rec("good", o2=(21, 40), p=(5, 10), g=(0, 0), funcs=["prevention"], fuel="solid", status="verified")
    bad = rec("bad", o2=(60, 90), p=(30, 40), g=(1, 1), funcs=["detection"], fuel="gas", status="seed")
    s = store_with(bad, good)
    out = rank(s, {"habitat_id": "moon"}, "prevention", "solid", 10, lambda sc: "note")
    assert [i["id"] for i in out["items"]] == ["good", "bad"]
    assert out["items"][0]["score"] > out["items"][1]["score"]
    assert out["coverage_note"] == "note"
