import dataclasses

import numpy as np
import pandas as pd

from chhaya.eval.events import (
    CONTEXT,
    HISTORY,
    RECORD,
    SENSOR,
    STICKS,
    drug_flags,
    excursion,
    meal_table,
    merge_meals,
)

SPLIT = 3 * 1440


def test_entries_within_an_hour_are_one_meal():
    assert merge_meals([300.0, 100.0, 130.0, 170.0]).tolist() == [100.0, 170.0, 300.0]


def test_excursion_needs_two_consecutive_readings_above_the_threshold():
    t = np.arange(0.0, 240.0, 15.0)
    g = np.full(t.size, 140.0)
    g[4] = 200.0  # one reading alone is not an event
    assert excursion(t, g, 30.0) is False
    g[5] = 190.0
    assert excursion(t, g, 30.0) is True
    assert excursion(t, g, 30.0, threshold=250.0) is False
    assert excursion(t[:5], g[:5], 30.0) is None  # fewer than six readings after the meal


def test_drug_flags_read_the_agents_list():
    f = drug_flags("metformin, Humulin 70/30, gliclazide")
    assert f == {"r_insulin": 1.0, "r_secretagogue": 1.0, "r_agi": 0.0, "r_metformin": 1.0}
    assert drug_flags("acarbose")["r_agi"] == 1.0
    assert set(drug_flags("none").values()) == {0.0}  # the record says: no agents


def test_a_missing_agents_entry_is_missing_not_no_drugs():
    for absent in (None, "", "nan", float("nan")):
        assert all(np.isnan(v) for v in drug_flags(absent).values())


def test_record_fields_that_cannot_be_read_are_missing_not_an_error(rec):
    static = {**rec.static, "age": "unknown", "sex": "Male", "agents": None}
    row = meal_table(dataclasses.replace(rec, static=static), 3.0).iloc[0]
    assert np.isnan(row["r_age"]) and np.isnan(row["r_male"]) and np.isnan(row["r_insulin"])


def test_personal_rate_is_the_raw_share_of_calibration_meals_with_the_event(rec):
    tab = meal_table(rec, 3.0)
    assert "h_share" not in CONTEXT + RECORD + HISTORY + STICKS + SENSOR  # the baseline, not a feature
    share = float(tab["h_share"].iloc[0])
    assert 0.0 <= share <= 1.0 and (tab["h_share"] == share).all()
    # a plain fraction of at most nine calibration meals, with no smoothing
    assert any(abs(share * n - round(share * n)) < 1e-9 for n in range(1, 10))
    late_only = dataclasses.replace(rec, meals=rec.meals[rec.meals["t_min"] >= SPLIT])
    tab = meal_table(late_only, 3.0)
    assert tab["h_share"].isna().all() and (tab["h_rate"] == 0.5).all()  # 0 of 0 is undefined, not zero


def test_table_has_one_row_per_meal_after_the_split(rec):
    tab = meal_table(rec, 3.0)
    assert len(tab) == 9 and (tab["t_min"] >= SPLIT).all()  # three meals a day on days 4 to 6
    for col in (
        CONTEXT
        + RECORD
        + HISTORY
        + STICKS
        + SENSOR
        + ["y", "y250", "start_high", "dev", "hidden_days", "pump"]
    ):
        assert col in tab.columns
    assert (tab["f_has"] == 0).all() and tab["f_last"].isna().all()  # no fingersticks in this recording


def _flat_after_the_split(rec, level: float = 100.0):
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = level
    return dataclasses.replace(rec, cgm=cgm)


def test_hidden_sensor_readings_reach_only_the_label_and_the_sensor_arm(rec):
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)  # the same fingersticks in both
    rec = dataclasses.replace(rec, fingersticks=sticks)
    a, b = meal_table(rec, 3.0), meal_table(_flat_after_the_split(rec), 3.0)
    off = CONTEXT + RECORD + HISTORY + STICKS + ["h_share"]
    pd.testing.assert_frame_equal(a[off], b[off])
    assert (
        a["f_has"].sum() > 0 and a["f_last"].nunique() > 1
    )  # the fingerstick columns are not constants here
    assert a["y"].sum() > 0 and b["y"].sum() == 0  # the label did move
    assert not np.allclose(a["s_last"], b["s_last"]) and not np.allclose(a["s_mean"], b["s_mean"])


def test_only_fingersticks_taken_before_the_meal_are_used(rec):
    first = float(meal_table(rec, 3.0)["t_min"].iloc[0])
    sticks = pd.DataFrame(
        {"t_min": [SPLIT - 50.0, first - 60.0, rec.n_min - 10.0], "glucose_mgdl": [300.0, 150.0, 90.0]}
    )
    tab = meal_table(dataclasses.replace(rec, fingersticks=sticks), 3.0)
    row = tab.iloc[0]
    assert row["f_has"] == 1 and row["f_last"] == 150.0 and row["f_age"] == 60.0 and row["f_n"] == 1
    assert tab["f_n"].iloc[-1] == 1  # the fingerstick at the end of the recording is after every meal
    assert tab["f_mean"].iloc[-1] == 150.0  # and the one before the split is not counted


def test_a_fingerstick_at_the_meal_minute_or_long_before_it_is_not_the_last_fingerstick(rec):
    meals = meal_table(rec, 3.0)["t_min"].to_numpy()
    sticks = pd.DataFrame({"t_min": [meals[0], meals[1] - 200.0], "glucose_mgdl": [210.0, 130.0]})
    tab = meal_table(dataclasses.replace(rec, fingersticks=sticks), 3.0)
    assert tab["f_has"].iloc[0] == 0 and tab["f_n"].iloc[0] == 0  # stamped at the meal time: not before it
    assert tab["f_has"].iloc[1] == 0 and np.isnan(tab["f_last"].iloc[1])  # older than three hours
    assert tab["f_n"].iloc[1] == 2 and tab["f_mean"].iloc[1] == 170.0  # but both count as earlier ones


def test_fingersticks_out_of_order_give_the_same_features(rec):
    first = float(meal_table(rec, 3.0)["t_min"].iloc[0])
    sticks = pd.DataFrame({"t_min": [first - 30.0, first - 90.0], "glucose_mgdl": [150.0, 250.0]})
    a = meal_table(dataclasses.replace(rec, fingersticks=sticks), 3.0)
    b = meal_table(dataclasses.replace(rec, fingersticks=sticks.iloc[::-1].reset_index(drop=True)), 3.0)
    pd.testing.assert_frame_equal(a[STICKS], b[STICKS])
    assert a["f_last"].iloc[0] == 150.0 and a["f_age"].iloc[0] == 30.0


def test_no_meal_before_the_split_is_ever_scored(rec):
    tab = meal_table(rec, 3.0)
    assert (tab["t_min"] >= SPLIT).all() and tab["t_min"].is_monotonic_increasing


def test_minutes_to_the_first_high_reading_is_reported_but_is_never_a_feature(rec):
    from chhaya.eval.events import minutes_to_high

    t = np.arange(0.0, 240.0, 15.0)
    g = np.full(t.size, 140.0)
    assert np.isnan(minutes_to_high(t, g, 30.0))
    g[4:6] = 200.0  # readings at minutes 60 and 75
    assert minutes_to_high(t, g, 30.0) == 30.0
    assert np.isnan(minutes_to_high(t, g, 100.0))  # both are before this meal
    tab = meal_table(rec, 3.0)
    assert "mins_to_high" not in CONTEXT + RECORD + HISTORY + STICKS + SENSOR  # it is known only afterwards
    assert (tab["y"] == 1).any() and tab.loc[tab["y"] == 1, "mins_to_high"].between(0.0, 120.0).all()
    quiet = meal_table(_flat_after_the_split(rec), 3.0)
    assert (quiet["y"] == 0).all() and quiet["mins_to_high"].isna().all()


def test_short_recording_gives_no_rows(rec):
    short = dataclasses.replace(rec, cgm=rec.cgm[rec.cgm["t_min"] < SPLIT + 600])
    assert meal_table(short, 3.0).empty
