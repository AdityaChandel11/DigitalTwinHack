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
    assert drug_flags(None)["r_insulin"] == 0.0 and drug_flags("acarbose")["r_agi"] == 1.0


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


def test_hidden_sensor_readings_reach_only_the_label_and_the_sensor_arm(rec):
    cgm = rec.cgm.copy()
    hidden = cgm["t_min"] >= SPLIT
    cgm.loc[hidden, "glucose_mgdl"] = np.clip(cgm.loc[hidden, "glucose_mgdl"] + 60.0, 40.0, 400.0)
    a, b = meal_table(rec, 3.0), meal_table(dataclasses.replace(rec, cgm=cgm), 3.0)
    pd.testing.assert_frame_equal(
        a[CONTEXT + RECORD + HISTORY + STICKS], b[CONTEXT + RECORD + HISTORY + STICKS]
    )
    assert not np.allclose(a["s_last"], b["s_last"])


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
    assert tab.loc[tab["y"] == 0, "mins_to_high"].isna().all()
    assert tab.loc[tab["y"] == 1, "mins_to_high"].between(0.0, 120.0).all()


def test_short_recording_gives_no_rows(rec):
    short = dataclasses.replace(rec, cgm=rec.cgm[rec.cgm["t_min"] < SPLIT + 600])
    assert meal_table(short, 3.0).empty
