import dataclasses

import numpy as np
import pandas as pd

from chhaya.data.audit import audit, gate1, low_events, write_food_strings


def test_low_event_needs_two_consecutive_readings():
    t = np.arange(0, 120, 15)
    g = np.array([100, 65, 100, 60, 62, 64, 100, 66])
    assert low_events(t, g) == [45]


def test_audit_counts_what_gate1_needs(rec):
    lows = rec.cgm.copy()
    lows.loc[8:11, "glucose_mgdl"] = 60.0  # 02:00-02:45 on the first night
    sticks = pd.DataFrame({"t_min": [100, 800], "glucose_mgdl": [110.0, 190.0]})
    row = audit([dataclasses.replace(rec, cgm=lows, fingersticks=sticks)]).iloc[0]
    assert row["days"] == 6.0 and row["n_meals"] == 18 and row["meals_per_day"] == 3.0
    assert row["n_meals_with_carbs"] == 18 and row["n_fingersticks"] == 2
    assert row["n_low_events"] >= 1 and row["n_nights_with_low"] >= 1
    assert not row["on_insulin"] and row["has_fasting_insulin"]


def test_gate1_threshold():
    df = pd.DataFrame({"days": [5.0] * 60 + [2.0] * 40, "meals_per_day": [3.0] * 59 + [0.5] + [3.0] * 40})
    assert gate1(df) == {"usable_recordings": 59, "required": 60, "go": False}
    df.loc[59, "meals_per_day"] = 2.0
    assert gate1(df)["go"] is True


def test_food_string_worklist_keeps_multi_line_cells_and_one_line_ending(tmp_path):
    foods = pd.Series({"Rice 150 g\nVegetable 100 g": 3, "Noodles 200 g": 1})
    path = tmp_path / "foods.csv"
    write_food_strings(foods, path)
    assert b"\r" not in path.read_bytes()  # same bytes on every platform; no phantom "modified" in git
    back = pd.read_csv(path)
    assert back["text"].tolist() == ["Rice 150 g\nVegetable 100 g", "Noodles 200 g"]
    assert back["count"].tolist() == [3, 1]
