"""One patient's bundle: what the patient screen draws, and what it must never contain."""

import dataclasses
import json

import numpy as np
from conftest import make_recording

from chhaya.product import patient as pt

K = 3.0
SPLIT = int(K * 1440)
POOLED = (0.0, 1.0)
THRESHOLDS = {3.0: 5.41, 5.0: 5.61}


def _recording(days: int = 8, every: int = 240, seed: int = 11):
    rec = make_recording(days=days, seed=seed)
    sticks = rec.cgm[rec.cgm["t_min"] % every == 0].reset_index(drop=True)
    return dataclasses.replace(rec, fingersticks=sticks, rec_id="p", patient_id="p")


def _bundle(rec, k: float = K):
    return pt.patient_bundle(
        rec, k, name="Mr. Chen", cohort="supervised", estimate=pt.stick_estimate(rec, k, POOLED),
        pooled=POOLED, thresholds=THRESHOLDS,
    )  # fmt: skip


def _without_sensor(bundle: dict) -> dict:
    out = json.loads(json.dumps(bundle))
    for day in out["days"]:
        day.pop("sensor")
        day.pop("inside_band")
    return out


def test_changing_the_hidden_sensor_moves_nothing_but_the_sensor_itself():
    rec = _recording()
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= SPLIT
    cgm.loc[late, "glucose_mgdl"] = np.random.default_rng(0).uniform(20, 600, int(late.sum()))
    a, b = _bundle(rec), _bundle(dataclasses.replace(rec, cgm=cgm))
    assert _without_sensor(a) == _without_sensor(b)
    assert a["days"][0]["sensor"] != b["days"][0]["sensor"]


def test_the_bundle_is_strict_json_and_holds_nothing_the_product_may_not_show():
    text = json.dumps(_bundle(_recording()), allow_nan=False)
    for banned in ('"tir"', '"tbr"', "gmi", "hba1c_est", "alarm", "time_in_range"):
        assert banned not in text.lower(), banned


def test_each_day_since_the_sensor_carries_the_estimate_its_band_and_the_days_fingersticks():
    b = _bundle(_recording())
    assert (
        b["schema"] == pt.SCHEMA and b["days_since"] == 5 and [d["day"] for d in b["days"]] == [1, 2, 3, 4, 5]
    )
    day = b["days"][0]
    n = len(day["t"])
    assert n == 96 and all(len(day[k]) == n for k in ("est", "lo", "hi", "avg", "sensor"))
    assert all(lo < e < hi for lo, e, hi in zip(day["lo"], day["est"], day["hi"], strict=True))
    assert len(day["sticks"]) == 6 and 0 <= day["inside_band"] <= 100 and day["clock0"] == 0
    assert b["estimate"]["kind"] == "fingersticks"


def test_a_gap_in_the_sensor_is_a_break_in_every_line_not_a_bridge():
    rec = _recording()
    cgm = rec.cgm[~rec.cgm["t_min"].between(SPLIT + 300, SPLIT + 600)].reset_index(drop=True)
    day = _bundle(dataclasses.replace(rec, cgm=cgm))["days"][0]
    i = day["sensor"].index(None)
    assert day["est"][i] is None and day["lo"][i] is None and 300 < day["t"][i] < 600


def test_the_figures_since_the_sensor_are_withheld_below_the_tested_frequency():
    shown = _bundle(_recording())["since"]
    assert shown["state"] == "shown" and shown["n"] == 30 and shown["per_day"] == 6.0
    assert shown["sensor_equivalent"]["mean"] > 0 and 0 <= shown["meter"]["above_180"] <= 100
    few = _bundle(_recording(every=480))["since"]  # three a day
    assert few["state"] == "withheld" and few["reason"] == "few_sticks" and "sensor_equivalent" not in few
    none = _bundle(make_recording(days=8))["since"]
    assert none["state"] == "withheld" and none["n"] == 0


def test_the_prompt_has_three_states_and_is_computed_only_inside_the_tested_range():
    assert _bundle(_recording())["prompt"]["state"] in ("raised", "not_raised")
    assert _bundle(_recording(every=480))["prompt"] == {"state": "not_computed", "reason": "few_sticks"}
    assert _bundle(_recording(days=9), k=4.0)["prompt"] == {"state": "not_computed", "reason": "wear_length"}
    assert _bundle(make_recording(days=8))["prompt"] == {"state": "not_computed", "reason": "few_sticks"}


def test_a_drift_after_the_sensor_raises_the_prompt_with_its_day_and_the_plain_comparison():
    rec = _recording()
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] -= 45.0
    sticks = cgm[cgm["t_min"] % 240 == 0].reset_index(drop=True)
    prompt = _bundle(dataclasses.replace(rec, cgm=cgm, fingersticks=sticks))["prompt"]
    assert prompt["state"] == "raised" and 1 <= prompt["day"] <= 3
    assert prompt["report_mean"] - prompt["stick_mean"] > 30.0


def test_past_day_eleven_an_unraised_prompt_is_not_computed_and_the_figures_are_marked():
    b = _bundle(_recording(days=16))
    assert b["days_since"] == 13 and b["since"]["outside"] is True
    assert b["prompt"]["state"] in ("raised", "not_computed")
    if b["prompt"]["state"] == "not_computed":
        assert b["prompt"]["reason"] == "too_late"


def test_without_an_estimate_the_days_hold_measured_things_only():
    rec = _recording()
    b = pt.patient_bundle(
        rec, K, name="x", cohort="supervised", estimate=None, pooled=POOLED, thresholds=THRESHOLDS
    )
    assert b["estimate"] is None and b["days"][0]["est"] is None and len(b["days"][0]["sensor"]) == 96


def test_the_wear_report_is_what_the_sensor_measured_before_the_split():
    wear = _bundle(_recording())["wear"]
    assert wear["days"] == 3 and 40 < wear["mean"] < 400 and len(wear["profile"]["p50"]) == 48
    p = wear["profile"]
    assert all(a <= b <= c for a, b, c in zip(p["p05"], p["p50"], p["p95"], strict=True))
