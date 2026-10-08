import dataclasses

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording
from test_traces import fake_trace

from chhaya.eval import expiry as ex
from chhaya.eval.fingersticks import estimates
from chhaya.twin.assimilate import FilterConfig

SPLIT = 3 * 1440


def _drifting(shift: float, from_day: int = 5, days: int = 8, seed: int = 11):
    """From day `from_day` on the patient's glucose runs `shift` mg/dL higher."""
    rec = make_recording(days=days, seed=seed)
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= from_day * 1440
    cgm.loc[late, "glucose_mgdl"] = np.clip(cgm.loc[late, "glucose_mgdl"] + shift, 40, 400)
    return dataclasses.replace(rec, cgm=cgm)


def _cohort(n: int = 7):
    rec = _drifting(40.0)
    return [dataclasses.replace(rec, rec_id=f"r{i}", patient_id=f"p{i}") for i in range(n)]


def test_the_daily_shape_is_the_control_that_section_f_scored():
    rec = dataclasses.replace(_drifting(0.0), start=pd.Timestamp("2026-01-01 09:37"))
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)
    e = estimates(dataclasses.replace(rec, fingersticks=sticks), 3, FilterConfig(), (0.0, 1.0))
    mine = ex.shape_at(ex.daily_shape(rec, SPLIT), rec, e["t"])
    assert np.array_equal(mine, e["control"])


def test_a_shape_is_read_by_the_clock_of_the_recording_it_is_applied_to():
    rec = dataclasses.replace(make_recording(days=2), start=pd.Timestamp("2026-03-01 09:00"))
    bins = np.arange(48.0)
    assert ex.shape_at(bins, rec, [0, 30, 900]).tolist() == [18.0, 19.0, 0.0]


def test_the_shape_is_built_before_the_split_only():
    rec = _drifting(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    assert np.array_equal(
        ex.daily_shape(rec, SPLIT), ex.daily_shape(dataclasses.replace(rec, cgm=cgm), SPLIT)
    )
    assert not np.array_equal(ex.daily_shape(rec, SPLIT), ex.daily_shape(rec))
    with pytest.raises(ValueError, match="no sensor reading"):
        ex.daily_shape(rec, 0.0)


def test_the_profile_is_true_until_the_patient_changes_and_wrong_after():
    rows = {r["day"]: r for r in ex.profile_rows(_drifting(40.0, from_day=5), 3)}
    assert sorted(rows) == [0, 1, 2, 3, 4, 5]  # day 0 is inside the wear; days 1 and 2 are before the change
    assert rows[0]["moved"] == 0.0 and rows[1]["moved"] == 0.0 and rows[2]["moved"] == 0.0
    assert rows[3]["moved"] == 1.0 and rows[3]["dmean"] > 30.0
    assert rows[3]["control_rmse"] > rows[1]["control_rmse"] + 15.0
    assert (
        rows[1]["control_rmse"] < rows[0]["control_rmse"] + 5.0
    )  # unaged, it errs no more than inside the wear


def test_a_recording_too_short_to_hide_a_day_is_counted_with_its_reason():
    short = make_recording(days=3, seed=2)
    assert ex.profile_rows(short, 3) is None
    block = ex.shanghai_block([*_cohort(), short], 3.0)
    assert block["n_patients"] == 7 and block["recordings"] == 7
    assert block["skipped"] == {"too short to hold out a day after calibration": 1}
    assert ex.shanghai_block([short], 3.0) == {"k_days": 3.0, "n_patients": 0, "skipped": block["skipped"]}


def test_each_later_day_is_read_against_day_zero_of_the_same_patient():
    block = ex.shanghai_block(_cohort(), 3.0)
    by_day = {r["day"]: r for r in block["by_day"]}
    assert (
        by_day[0]["n_patients"] == 7 and by_day[3]["share_moved"] == 1.0 and by_day[1]["share_moved"] == 0.0
    )
    assert by_day[1]["share_of_cohort"] == 1.0 and "share_of_cohort" in ex.SHANGHAI_SHOWN
    zero = {(r["column"], r["day"]): r for r in block["against_day_zero"]}
    assert zero[("abs_dmean", 4)]["median_diff"] > 25.0 and abs(zero[("abs_dmean", 1)]["median_diff"]) < 8.0
    assert {column for column, _ in zero} == {"abs_dmean"}  # day 0 is no yardstick for the point error
    slope = next(s for s in block["slopes"] if s["column"] == "abs_dmean")
    assert slope["n_patients"] == 7 and slope["median_slope"] > 5.0


def test_trace_rows_score_the_twin_its_control_and_its_band_by_day():
    rows = {r["day"]: r for r in ex.trace_rows(fake_trace("p1", off=5.0))}
    assert sorted(rows) == [0, 1, 2, 3] and "twin_rmse" not in rows[0]  # day 0 has no estimate to score
    assert rows[2]["twin_rmse"] == pytest.approx(5.0) and rows[2]["control_rmse"] == pytest.approx(10.0)
    assert rows[2]["avgday_rmse"] == pytest.approx(20.0) and rows[2]["cov80"] == 1.0
    assert (
        rows[2]["twin_mean_err"] == pytest.approx(5.0)
        and rows[2]["abs_dmean"] < 1e-9
        and rows[2]["group"] == "t2d"
    )
    outside = fake_trace("p2", off=15.0)  # 15 above the truth, band of +-10: the truth is never inside
    assert {r["cov80"] for r in ex.trace_rows(outside) if r["day"] > 0} == {0.0}


def test_the_cgmacros_block_pairs_the_twin_with_its_control_and_counts_groups():
    traces = [fake_trace(f"p{i}", off=5.0 + 0.1 * i, group="t2d" if i < 3 else "healthy") for i in range(8)]
    block = ex.cgmacros_block(traces, 3.0)
    day1 = next(r for r in block["by_day"] if r["day"] == 1)
    assert day1["n_patients"] == 8 and day1["twin_rmse_vs_control_rmse"]["frac_better"] == 1.0
    assert (
        day1["twin_mean_err_vs_abs_dmean"]["median_diff"] > 0
    )  # here the stale report's mean is the better one
    assert block["groups"] == {"healthy": 5, "t2d": 3}
    assert [r["n_patients"] for r in block["by_day_t2d"]] == [3, 3, 3, 3]
    assert ex.cgmacros_block([], 3.0) == {"k_days": 3.0, "n_patients": 0}


def _again(first, days_later: int, shift: float, **changes):
    cgm = first.cgm.assign(glucose_mgdl=np.clip(first.cgm["glucose_mgdl"] + shift, 40, 400))
    start = first.start + pd.Timedelta(days=days_later)
    return dataclasses.replace(
        first, rec_id=f"{first.rec_id}-later{days_later}", start=start, cgm=cgm, **changes
    )


def test_the_case_series_applies_the_first_wears_profile_to_each_later_wear():
    first = dataclasses.replace(
        make_recording(days=6, seed=4), static={"agents": "metformin", "group": "t2d"}
    )
    pump = pd.DataFrame({"t_min": [10.0], "drug": ["Novolin R"], "dose": [np.nan], "route": ["csii"]})
    later = _again(first, 40, 30.0, doses=pump, static={"agents": "metformin, acarbose", "group": "t2d"})
    much_later = _again(first, 150, 0.0)
    alone = make_recording(days=6, seed=5)
    rows = ex.repeat_cases([later, alone, much_later, first])  # any order; the earliest wear is the reference
    assert [r["days_between_starts"] for r in rows] == [40.0, 150.0]
    a, b = rows
    assert a["days_since_first_sensor"] == 34.0 and a["first_wear_days"] == 6.0
    assert a["moved"] == 1.0 and 25.0 < a["dmean"] <= 30.0
    assert (
        a["old_profile_rmse"] > a["fresh_profile_rmse"] + 10.0
    )  # a new wear would describe this patient better
    assert (a["insulin_first"], a["insulin_later"], a["pump_later"], a["agents_changed"]) == (
        False,
        True,
        True,
        True,
    )
    assert (
        b["moved"] == 0.0
        and b["agents_changed"] is False
        and b["old_profile_rmse"] < a["old_profile_rmse"] - 10.0
    )
    assert (
        abs(b["old_profile_rmse"] - b["first_wear_rmse"]) < 6.0
    )  # nothing changed: as good as inside the first wear

    block = ex.cases_block([first, later, much_later, alone])
    assert (block["n_patients"], block["n_cases"], block["n_moved"], block["n_treatment_changed"]) == (
        1,
        2,
        1,
        1,
    )
    assert ex.cases_block([alone]) == {"n_patients": 0, "n_cases": 0, "cases": []}


def test_reports_say_what_they_are_and_by_day_reports_name_no_patient():
    result = {"confirmatory": False, "by_k": [ex.shanghai_block(_cohort(), 3.0), ex.shanghai_block([], 5.0)]}
    text = ex._by_day_report(
        "Expiry by day: ShanghaiT2DM", "note", result, ["day", "n_patients", "control_rmse"]
    )
    assert (
        "Not confirmatory" in text
        and "No recording could be run" in text
        and "p0" not in text
        and "r0" not in text
    )
    first = make_recording(days=6, seed=4)
    cases = {"confirmatory": True, **ex.cases_block([first, _again(first, 40, 30.0)])}
    assert "case series" in ex._cases_report(cases) and "no test" in ex._cases_report(cases)
    assert "one row per later wear" in ex._cases_report(cases) and cases["unit"] == "later wear"
