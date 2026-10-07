import dataclasses
import json

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.eval import fingersticks as fx
from chhaya.twin.assimilate import FilterConfig

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(shift: float, every_min: int = 240, days: int = 7):
    """Seven days; after day 3 the patient's glucose runs `shift` mg/dL higher. Fingersticks read the sensor exactly."""
    rec = make_recording(days=days, seed=11)
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
    with pytest.raises(SystemExit, match="registered"):
        fx.check_confirm(None, False, "", k=(7.0,))
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


def test_the_sensor_map_never_reads_a_sensor_value_from_after_the_split():
    rec = _recording(0.0)
    near = pd.DataFrame(
        {"t_min": [SPLIT - 5.0], "glucose_mgdl": [150.0]}
    )  # its nearest reading is at the split
    sticks = (
        pd.concat([rec.fingersticks, near], ignore_index=True).sort_values("t_min").reset_index(drop=True)
    )
    rec = dataclasses.replace(rec, fingersticks=sticks)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 300.0
    a = fx.estimates(rec, 3, FilterConfig(), POOLED)
    b = fx.estimates(dataclasses.replace(rec, cgm=cgm), 3, FilterConfig(), POOLED)
    assert (
        a["map"] == b["map"]
        and np.allclose(a["live"], b["live"])
        and np.allclose(a["hindsight"], b["hindsight"])
    )
    assert len(fx.calibration_pairs(rec, 3)) == len(
        fx.calibration_pairs(dataclasses.replace(rec, cgm=cgm), 3)
    )
    assert (fx.calibration_pairs(dataclasses.replace(rec, cgm=cgm), 3)["cgm"] < 300.0).all()


def test_the_run_says_whose_map_was_used():
    own = fx.run_recording(_recording(0.0), 3, FilterConfig(), POOLED)
    assert own["map_source"] == "own slope"
    few = _recording(0.0)
    late_only = few.fingersticks[(few.fingersticks["t_min"] >= SPLIT) | (few.fingersticks["t_min"] == 0)]
    row = fx.run_recording(
        dataclasses.replace(few, fingersticks=late_only.reset_index(drop=True)), 3, FilterConfig(), POOLED
    )
    assert row["map_source"] == "pooled map"  # one calibration pair is too few even for an offset
    counts = fx.map_sources(pd.DataFrame([own, own, {**row, "rec_id": "another"}]))  # one count per recording
    assert counts == {"own slope": 1, "pooled map": 1}


def test_each_development_design_writes_to_its_own_folder():
    assert fx.run_name(False, None, False) == "shanghai-dev"
    assert fx.run_name(False, 60.0, True) == "shanghai-dev-tau60-slow"
    assert fx.run_name(False, 240.0, False) == "shanghai-dev-tau240"
    assert fx.run_name(True, None, False) == "shanghai"


def test_the_live_estimate_at_a_fingersticks_own_minute_does_not_use_it():
    e = fx.estimates(_recording(40.0), 3, FilterConfig(), POOLED)
    first = e["t"] == e["ft"][0]
    assert first.sum() == 1
    assert np.allclose(e["live"][first], e["control"][first])  # nothing had been taken before it
    assert not np.allclose(e["live_same_minute"][first], e["control"][first])
    later = e["t"] == e["ft"][0] + 15.0
    assert np.allclose(
        e["live"][later], e["live_same_minute"][later]
    )  # a quarter of an hour on, both know it


def test_thinning_never_drops_a_recording_from_the_cohort():
    rec = _recording(40.0)
    s = rec.fingersticks
    second_day = s[(s["t_min"] < SPLIT) | s["t_min"].between(SPLIT + 1440, SPLIT + 2879)].reset_index(
        drop=True
    )
    rec = dataclasses.replace(
        rec, fingersticks=second_day
    )  # every hidden fingerstick is on the second hidden day
    rows = {rule: fx.run_recording(rec, 3, FilterConfig(), POOLED, rule) for rule in fx.RULES}
    assert all(row is not None for row in rows.values())
    assert rows["every 2nd day"]["n_sticks"] == 0  # that day is skipped: no fingerstick is kept
    assert rows["every 2nd day"]["live_rmse"] == rows["every 2nd day"]["control_rmse"]


def test_every_second_day_starts_with_the_day_the_sensor_came_off():
    rec = dataclasses.replace(_recording(40.0), start=pd.Timestamp("2026-01-01 09:37"))
    e = fx.estimates(rec, 3, FilterConfig(), POOLED, "every 2nd day")
    first_day_end = SPLIT + 1440 - (9 * 60 + 37)  # the clock day that holds the split ends here
    assert e["ft"].size >= 2 and SPLIT <= e["ft"][0] < first_day_end
    assert e["ft"][1] >= first_day_end + 1440  # the next clock day is skipped
    with pytest.raises(ValueError, match="thinning rule"):
        fx.thin(np.array([1.0]), np.array([0]), "2 / day")


def test_every_clarke_zone_is_kept_and_no_scored_time_is_before_the_split():
    row = fx.run_recording(_recording(40.0), 3, FilterConfig(), POOLED)
    for name in ("sensor", "control", "live"):
        zones = [row[f"{name}_zone_{z}"] for z in "abcde"]
        assert abs(sum(zones) - 100.0) < 1e-9
    assert row["sensor_zone_a"] == 100.0  # the fingersticks of this fixture read the sensor exactly


def test_the_default_design_helps_when_the_patient_has_changed():
    row = fx.run_recording(_recording(40.0), 3, FilterConfig(), POOLED)
    assert row["live_rmse"] < row["control_rmse"] - 2.0 and row["hindsight_rmse"] < row["live_rmse"]
    assert row["live_same_minute_rmse"] <= row["live_rmse"]  # reading the same minute can only flatter it


def test_two_recordings_of_one_patient_count_once_and_a_small_unreliable_gain_is_no_verdict():
    rows = [{"patient_id": f"p{i}", "control_rmse": 30.0, "live_rmse": 30.0 + d, "hindsight_rmse": 30.0 + d}
            for i, d in enumerate([-0.4, 0.5, -0.3, 0.6, -0.2, 0.1, -0.1, 0.3])]  # fmt: skip
    df = pd.DataFrame(
        [*rows, {"patient_id": "p0", "control_rmse": 30.0, "live_rmse": 28.0, "hindsight_rmse": 28.0}]
    )
    s = fx.summarise(df)
    assert s["n_patients"] == 8 and s["live_p"] > 0.05
    assert fx.verdict(s)["f1_live_beats_control"] is False
    few = fx.summarise(pd.DataFrame(rows[:4]).assign(live_rmse=20.0, hindsight_rmse=20.0))
    assert np.isnan(few["live_p"]) and fx.verdict(few) == {
        "f1_live_beats_control": False,
        "f2_hindsight_beats_control": False,
    }  # under six patients there is no test, so no pass


def test_recordings_outside_the_cohort_are_told_the_two_day_rule():
    short = _recording(0.0, days=4)  # one hidden day
    assert "two days" in fx.why_not(short, 3)


def test_summary_gives_an_interval_for_each_effect_and_reports_the_same_minute_variant():
    df = pd.DataFrame(
        {
            "patient_id": [f"p{i}" for i in range(10)],
            "control_rmse": 30.0,
            "live_rmse": np.linspace(27, 29.5, 10),
            "live_same_minute_rmse": np.linspace(26, 29, 10),
            "hindsight_rmse": np.linspace(25, 29, 10),
        }
    )
    s = fx.summarise(df)
    assert s["live_diff_lo"] <= s["live_median_diff"] <= s["live_diff_hi"] < 0
    assert s["hindsight_diff_lo"] <= s["hindsight_median_diff"] <= s["hindsight_diff_hi"] < 0
    assert s["live_same_minute_median_diff"] < s["live_median_diff"]
    assert set(fx.verdict(s)) == {
        "f1_live_beats_control",
        "f2_hindsight_beats_control",
    }  # no bar for the variant


def _cohort(n: int = 7):
    rec = _recording(40.0, days=8)
    return [dataclasses.replace(rec, rec_id=f"r{i}", patient_id=f"p{i}") for i in range(n)]


def test_only_the_primary_k_carries_a_verdict(tmp_path):
    recs = _cohort()
    result = fx.run_all(recs, recs, [3.0, 5.0], FilterConfig(), tmp_path, confirmatory=False)
    k3, k5 = result["by_k"]
    assert k3["primary"] is True and k3["rules"]["all"]["f1_live_beats_control"] is True
    assert k5["primary"] is False and k5["rules"]["all"]["n_patients"] == 7
    assert (
        "f1_live_beats_control" not in k5["rules"]["all"]
        and "f1_live_beats_control" not in k3["rules"]["1/day"]
    )
    assert k3["recordings"] == 7 and k3["map_sources"] == {"own slope": 7}
    text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "primary" in text and "p0" not in text and "r0" not in text  # aggregates only


def test_the_primary_result_is_on_disk_before_anything_else_is_scored(tmp_path, monkeypatch):
    recs = _cohort()
    real = fx.run_recording

    def flaky(rec, k, cfg, pooled, rule="all"):
        if rule != "all" or k != 3.0:
            saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
            assert saved["by_k"][0]["rules"]["all"]["n_patients"] == 7
            raise RuntimeError("a later analysis failed")
        return real(rec, k, cfg, pooled, rule)

    monkeypatch.setattr(fx, "run_recording", flaky)
    fx.run_all(recs, recs, [3.0, 5.0], FilterConfig(), tmp_path, confirmatory=True)
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert "f1_live_beats_control" in saved["by_k"][0]["rules"]["all"]
    assert "a later analysis failed" in saved["by_k"][0]["rules"]["1/day"]["error"]
    assert "a later analysis failed" in saved["by_k"][1]["rules"]["all"]["error"]
    with pytest.raises(SystemExit, match="already"):
        fx.refuse_second_run(tmp_path)


def test_the_confirmatory_run_refuses_a_filter_other_than_the_frozen_one():
    fx.check_confirm(None, False, "", cfg=FilterConfig())
    with pytest.raises(SystemExit, match="frozen"):
        fx.check_confirm(None, False, "", cfg=FilterConfig(tau_min=999.0))
    with pytest.raises(SystemExit, match="frozen"):
        fx.check_confirm(None, False, "", cfg=FilterConfig(slow=not FilterConfig().slow))
