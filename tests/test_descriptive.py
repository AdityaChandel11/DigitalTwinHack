import dataclasses
import json

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.config import REPO_ROOT
from chhaya.eval import descriptive as ds
from chhaya.eval.baselines import average_day_baseline
from chhaya.eval.metrics import rmse

SPLIT = 3 * 1440.0


def test_days_since_the_sensor_are_24_hour_blocks_from_the_split():
    t = np.array([SPLIT, SPLIT + 1439, SPLIT + 1440, SPLIT + 4 * 1440 + 5])
    assert ds.day_index(t, SPLIT).tolist() == [1, 1, 2, 5]
    with pytest.raises(ValueError, match="before the split"):
        ds.day_index(np.array([SPLIT - 15]), SPLIT)


def test_a_report_states_mean_time_above_180_and_time_in_range():
    assert ds.glucose_report([100.0, 200.0, 60.0, 180.0]) == {"mean": 135.0, "tar": 25.0, "tir": 50.0}
    for empty in (lambda: ds.glucose_report([]), lambda: ds.estimated_report([], 20.0)):
        with pytest.raises(ValueError, match="no readings"):
            empty()


def test_a_flat_estimate_at_180_is_above_it_half_the_time_once_its_spread_is_counted():
    est = np.full(96, 180.0)
    assert ds.glucose_report(est)["tar"] == 0.0  # counting crossings of a smooth estimate undercounts
    r = ds.estimated_report(est, sigma=30.0)
    assert abs(r["tar"] - 50.0) < 1e-9 and abs(r["tir"] - 50.0) < 0.02 and r["mean"] == 180.0
    assert ds.estimated_report(est, sigma=0.0) == ds.glucose_report(est)


def test_the_spread_recovers_the_time_above_180_that_a_smooth_estimate_misses():
    rng = np.random.default_rng(0)
    smooth = 150.0 + 30.0 * np.sin(np.linspace(0, 20 * np.pi, 4000))
    truth = smooth + rng.normal(0.0, 25.0, smooth.size)
    true = ds.glucose_report(truth)
    assert abs(ds.estimated_report(smooth, 25.0)["tar"] - true["tar"]) < 2.0
    assert abs(ds.glucose_report(smooth)["tar"] - true["tar"]) > 5.0


def test_the_spread_around_the_daily_shape_is_measured_on_days_the_shape_has_not_seen():
    rng = np.random.default_rng(1)
    clock = np.arange(0, 4 * 1440, 15)
    g = 140.0 + rng.normal(0.0, 10.0, clock.size)
    assert g.std() < ds.profile_sigma(clock, g) < g.std() + 1.0  # a little above the noise, never below it
    one_day = clock < 1440  # no other day to learn from: the spread about that day's mean, not zero
    assert abs(ds.profile_sigma(clock[one_day], g[one_day]) - g[one_day].std()) < 1e-9


def test_the_spread_leaves_the_scored_day_out_of_both_halves_of_the_shape():
    rng = np.random.default_rng(0)
    t = np.arange(0, 4 * 1440, 15)
    g = 140.0 + np.repeat([0.0, 30.0, -20.0, 10.0], 96) + rng.normal(0.0, 5.0, t.size)  # days at four levels
    day = t // 1440
    unseen, flattered = np.empty_like(g), np.empty_like(g)
    for d in np.unique(day):
        held = day == d
        shape = average_day_baseline(t[~held], g[~held], t[held])
        unseen[held] = 0.5 * shape + 0.5 * g[~held].mean()
        flattered[held] = 0.5 * shape + 0.5 * g.mean()  # the day's own readings inside its own mean
    assert ds.profile_sigma(t, g) == pytest.approx(rmse(unseen, g), rel=1e-9)
    assert rmse(unseen, g) > rmse(flattered, g) + 1.0  # which is why the day must be left out of both


def test_daily_rows_score_each_day_with_enough_readings():
    t = SPLIT + np.arange(0, 2 * 1440 + 20 * 15, 15.0)  # two full days and five hours of a third
    truth = np.full(t.size, 150.0)
    est = truth + np.where(t >= SPLIT + 1440, 10.0, 0.0)
    rows = ds.daily_rows(t, SPLIT, truth, {"shadow": est})
    assert [r["day"] for r in rows] == [1, 2] and rows[0]["n"] == 96  # the short third day is not scored
    assert rows[0]["shadow_rmse"] == 0.0 and abs(rows[1]["shadow_rmse"] - 10.0) < 1e-9
    assert rows[1]["shadow_mean"] == 160.0 and ds.day_report(rows[1]) == {
        "mean": 150.0,
        "tar": 0.0,
        "tir": 100.0,
    }


def test_aging_says_how_far_a_day_is_from_the_report():
    report = {"mean": 150.0, "tar": 20.0, "tir": 78.0}
    near = ds.aging({"mean": 162.0, "tar": 31.0, "tir": 68.0}, report)
    assert near == {"dmean": 12.0, "abs_dmean": 12.0, "moved": 0.0, "abs_dtar": 11.0, "abs_dtir": 10.0}
    assert ds.aging({"mean": 125.0, "tar": 20.0, "tir": 78.0}, report)["moved"] == 1.0  # 25 below also counts


def test_day_zero_is_one_day_of_the_wear_against_its_other_days():
    t = np.arange(0, 3 * 1440, 15.0)
    steady = ds.inside_the_wear(t, np.full(t.size, 150.0))
    assert steady["abs_dmean"] == 0.0 and steady["moved"] == 0.0
    third_high = np.where(t >= 2 * 1440, 180.0, 150.0)
    floor = ds.inside_the_wear(t, third_high)
    assert abs(floor["abs_dmean"] - 20.0) < 1e-9  # 15, 15 and 30 mg/dL: each day against the other two
    assert abs(floor["moved"] - 1 / 3) < 1e-9
    assert ds.inside_the_wear(t[:96], np.full(96, 150.0)) is None  # one day has no other day


def _per(n=10):
    return pd.DataFrame({"shadow": np.linspace(8, 12, n), "stale": np.linspace(10, 14, n)}, index=range(n))


def test_paired_summary_is_over_patients_and_ignores_a_patient_without_both():
    s = ds.paired_summary(_per(), "shadow", "stale")
    assert s["n_patients"] == 10 and s["median_diff"] == -2.0 and s["frac_better"] == 1.0 and s["p"] < 0.05
    assert s["diff_lo"] == s["diff_hi"] == -2.0 and s["median"] == 10.0 and s["median_against"] == 12.0
    per = _per()
    per.loc[0, "stale"] = np.nan
    assert ds.paired_summary(per, "shadow", "stale")["n_patients"] == 9
    empty = ds.paired_summary(per.iloc[:0], "shadow", "stale")
    assert empty == {"of": "shadow", "against": "stale", "alternative": "less", "n_patients": 0}
    worse = ds.paired_summary(_per(), "stale", "shadow", "greater")  # the same question asked the other way
    assert worse["median_diff"] == 2.0 and worse["p"] == s["p"]
    assert worse["frac_larger"] == 1.0 and "frac_better" not in worse and "frac_larger" not in s
    with pytest.raises(ValueError, match="alternative"):
        ds.paired_summary(_per(), "shadow", "stale", "two-sided")


def _days():
    rows = []
    for p in range(8):
        for d in range(0, 5):
            if d == 4 and p >= 3:
                continue  # only three patients reach day 4
            rows.append(
                {
                    "patient_id": f"p{p}",
                    "rec_id": f"r{p}",
                    "day": d,
                    "control_rmse": 20.0 + 2.0 * d + p,
                    "twin_rmse": 19.0 + 2.0 * d + p,
                    "abs_dmean": 10.0 + (8.0 if d >= 3 else 0.0),
                    "moved": float(d >= 3 and p < 4),
                }
            )
    return pd.DataFrame(rows)


def test_days_are_summarised_over_patients_and_thin_days_get_no_comparison():
    by_day = {r["day"]: r for r in ds.summarise_days(_days(), (("twin_rmse", "control_rmse"),))}
    assert by_day[1]["n_patients"] == 8 and by_day[1]["control_rmse"] == 25.5
    assert by_day[1]["twin_rmse_vs_control_rmse"]["median_diff"] == -1.0
    assert by_day[3]["share_moved"] == 0.5 and "moved" not in by_day[3]
    assert by_day[4]["n_patients"] == 3 and "twin_rmse_vs_control_rmse" not in by_day[4]
    assert by_day[1]["share_of_cohort"] == 1.0 and by_day[4]["share_of_cohort"] == 3 / 8


def test_the_share_of_the_cohort_counts_every_patient_not_the_best_attended_day():
    rows = [
        {"patient_id": f"p{i}", "day": d, "x": 1.0}
        for i in range(10)
        for d in (1, 2, 3)
        if (i, d) not in ((7, 1), (8, 2), (9, 3))  # each day misses a different patient
    ]
    out = ds.summarise_days(pd.DataFrame(rows))
    assert [r["n_patients"] for r in out] == [9, 9, 9] and [r["share_of_cohort"] for r in out] == [0.9] * 3


def test_two_recordings_of_one_patient_count_once_per_day():
    df = pd.concat([_days(), _days().assign(rec_id="again", control_rmse=0.0)], ignore_index=True)
    day1 = next(r for r in ds.summarise_days(df) if r["day"] == 1)
    assert day1["n_patients"] == 8 and day1["control_rmse"] == 25.5 / 2


def test_the_slope_is_taken_inside_each_patient():
    s = ds.slope_per_day(_days(), "control_rmse")
    assert s["n_patients"] == 8 and abs(s["median_slope"] - 2.0) < 1e-9 and s["frac_rising"] == 1.0
    two_days = _days()[
        _days()["day"].isin([0, 1, 2])
    ]  # day 0 is not a day since the sensor: two days are too few
    assert ds.slope_per_day(two_days, "control_rmse") == {"column": "control_rmse", "n_patients": 0}


def test_each_day_is_read_against_the_same_patients_day_zero():
    rows = ds.excess_over_day_zero(_days(), "abs_dmean")
    by_day = {r["day"]: r for r in rows}
    assert sorted(by_day) == [1, 2, 3]  # day 4 has three patients
    assert by_day[1]["median_diff"] == 0.0 and by_day[3]["median_diff"] == 8.0
    assert by_day[3]["alternative"] == "greater" and by_day[3]["p"] < 0.05  # has it aged? yes, by day 3
    assert ds.excess_over_day_zero(_days()[_days()["day"] >= 1], "abs_dmean") == []


def test_a_second_pass_must_reproduce_the_committed_numbers():
    committed = {"n_patients": 29, "control_rmse": 36.708231}
    assert ds.differences({"n_patients": 29, "control_rmse": 36.7082312, "extra": 1.0}, committed) == []
    bad = ds.differences({"n_patients": 28, "control_rmse": 36.9}, committed)
    assert len(bad) == 2 and "committed 29, found 28" in bad[0]
    assert len(ds.differences({}, committed)) == 2


def test_the_pooled_sensor_line_needs_development_pairs():
    rec = make_recording(days=4, seed=1)
    with pytest.raises(ValueError, match="pooled sensor map"):
        ds.pooled_line([], 3.0)
    with pytest.raises(ValueError, match="pooled sensor map"):
        ds.pooled_line([rec], 3.0)  # a recording without fingersticks gives no pair
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)
    intercept, slope = ds.pooled_line([dataclasses.replace(rec, fingersticks=sticks)], 3.0)
    assert abs(slope - 1.0) < 1e-9 and abs(intercept) < 1e-6  # these fingersticks read the sensor exactly


def test_test_patients_are_read_only_on_committed_code():
    ds.check_committed("")
    with pytest.raises(SystemExit, match="uncommitted"):
        ds.check_committed(" M src/chhaya/eval/expiry.py")
    with pytest.raises(SystemExit, match="git"):
        ds.check_committed(None)


def test_nothing_is_written_when_any_of_the_three_files_cannot_be(tmp_path):
    with pytest.raises(TypeError):
        ds.write_outputs(tmp_path / "run", {"n": 1}, "# report\n", {"where": tmp_path})  # a path is not JSON
    with pytest.raises(TypeError):
        ds.write_outputs(tmp_path / "run", {"n": {1, 2}}, "# report\n")  # nor is a set
    assert not (tmp_path / "run").exists()  # so no half-written folder can pass for a finished run


def test_a_folder_that_holds_any_file_of_an_earlier_pass_closes_the_pass(tmp_path):
    ds.refuse_second_pass(tmp_path / "never-run")
    for name in ("summary.json", "report.md", "provenance.json"):
        folder = tmp_path / name
        folder.mkdir()
        (folder / name).write_text("{}", encoding="utf-8")
        with pytest.raises(SystemExit, match="already"):
            ds.refuse_second_pass(folder)  # a report without its summary still holds test numbers


def test_a_path_in_a_results_file_is_relative_to_the_repository():
    assert ds.repo_path(REPO_ROOT / "results" / "fingersticks" / "shanghai" / "summary.json") == (
        "results/fingersticks/shanghai/summary.json"
    )
    assert "Users" not in ds.repo_path(REPO_ROOT / "results")


def test_outputs_are_strict_json_and_a_table_leaves_nested_values_out(tmp_path):
    result = {"n": np.int64(3), "ok": np.bool_(True), "nan": float("nan"), "rows": [{"day": 1, "x": 1.26}]}
    ds.write_outputs(tmp_path, result, "# report\n", {"commit": "abc"})
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved == {"n": 3, "ok": True, "nan": None, "rows": [{"day": 1, "x": 1.26}]}
    assert json.loads((tmp_path / "provenance.json").read_text(encoding="utf-8")) == {"commit": "abc"}
    text = ds.table([{"day": 1, "x": 1.26, "pair": {"p": 0.5}}])
    assert "1.3" in text and "pair" not in text and ds.table([]) == "(no rows)"
