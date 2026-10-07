import dataclasses

import numpy as np
import pandas as pd
from conftest import make_recording

from chhaya.eval import fingersticks as fx
from chhaya.twin.assimilate import FilterConfig

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(shift: float, every_min: int = 240):
    """Seven days; after day 3 the patient's glucose runs `shift` mg/dL higher. Fingersticks read the sensor exactly."""
    rec = make_recording(days=7, seed=11)
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= SPLIT
    cgm.loc[late, "glucose_mgdl"] = np.clip(cgm.loc[late, "glucose_mgdl"] + shift, 40, 400)
    sticks = cgm[cgm["t_min"] % every_min == 0].reset_index(drop=True)
    return dataclasses.replace(rec, cgm=cgm, fingersticks=sticks)


def test_fingersticks_help_when_the_patient_has_changed():
    row = fx.run_recording(_recording(40.0), 3, FilterConfig(slow=True), POOLED)
    assert row["live_rmse"] < row["control_rmse"] - 8.0
    assert row["hindsight_rmse"] <= row["live_rmse"] + 1.0
    assert row["n_sticks"] > 20 and row["sensor_within15"] == 100.0
    assert row["live_within15"] > row["control_within15"]


def test_fingersticks_do_no_harm_when_nothing_changed():
    row = fx.run_recording(_recording(0.0), 3, FilterConfig(), POOLED)
    assert row["live_rmse"] < row["control_rmse"] + 2.0


def test_hidden_sensor_readings_never_reach_the_estimate():
    rec = _recording(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    a = fx.estimates(rec, 3, FilterConfig(), POOLED)
    b = fx.estimates(dataclasses.replace(rec, cgm=cgm), 3, FilterConfig(), POOLED)
    assert np.allclose(a["live"], b["live"]) and np.allclose(a["hindsight"], b["hindsight"])


def test_recordings_that_cannot_be_scored_say_why(rec):
    assert "fingerstick" in fx.why_not(rec, 3)  # no fingersticks at all
    early = dataclasses.replace(
        _recording(0.0), fingersticks=_recording(0.0).fingersticks.query("t_min < @SPLIT")
    )
    assert "after the split" in fx.why_not(early, 3)
    assert fx.run_recording(rec, 3, FilterConfig(), POOLED) is None


def test_thinning_keeps_the_first_fingerstick_of_the_day():
    t = np.array([400.0, 800.0, 1200.0, 1900.0, 2300.0, 3300.0])
    day = t // 1440
    assert fx.thin(t, day, "all").sum() == 6
    assert fx.thin(t, day, "2/day").tolist() == [True, False, True, True, True, True]
    assert fx.thin(t, day, "1/day").tolist() == [True, False, False, True, False, True]
    assert fx.thin(t, day, "every 2nd day").tolist() == [True, False, False, False, False, True]


def test_verdict_needs_a_reliable_gain():
    good = pd.DataFrame(
        {
            "patient_id": [f"p{i}" for i in range(10)],
            "control_rmse": 30.0,
            "live_rmse": np.linspace(27, 29.5, 10),
            "hindsight_rmse": np.linspace(25, 29, 10),
        }
    )
    assert fx.verdict(fx.summarise(good)) == {
        "f1_live_beats_control": True,
        "f2_hindsight_beats_control": True,
    }
    bad = good.assign(live_rmse=np.linspace(29, 33, 10))
    assert fx.verdict(fx.summarise(bad))["f1_live_beats_control"] is False


def test_a_fingerstick_with_no_sensor_reading_beside_it_still_feeds_the_estimate():
    rec = _recording(40.0)
    cgm = rec.cgm[(rec.cgm["t_min"] < SPLIT) | ~rec.cgm["t_min"].between(SPLIT + 1000, SPLIT + 1500)]
    gap = dataclasses.replace(rec, cgm=cgm)  # no hidden sensor reading near the fingersticks in the gap
    e = fx.estimates(gap, 3, FilterConfig(), POOLED)
    assert ((e["ft"] > SPLIT + 1000) & (e["ft"] < SPLIT + 1500)).any()
    row = fx.run_recording(gap, 3, FilterConfig(), POOLED)
    assert row["n_scored"] < row["n_sticks"]  # scored only where a sensor reading is beside it


def test_scoring_covers_the_same_fingersticks_whatever_the_thinning_rule():
    rec = _recording(40.0)
    rows = {rule: fx.run_recording(rec, 3, FilterConfig(), POOLED, rule) for rule in fx.RULES}
    assert len({r["n_scored"] for r in rows.values()}) == 1
    assert rows["1/day"]["n_sticks"] < rows["2/day"]["n_sticks"] < rows["all"]["n_sticks"]


def test_the_confirmatory_run_takes_no_filter_overrides_and_only_committed_code():
    fx.check_confirm(None, False, "")
    for tau, slow, status, why in (
        (60.0, False, "", "defaults"),
        (None, True, "", "defaults"),
        (None, False, " M src/x.py", "uncommitted"),
        (None, False, None, "git"),
    ):
        try:
            fx.check_confirm(tau, slow, status)
        except SystemExit as err:
            assert why in str(err)
        else:
            raise AssertionError("should have refused")
