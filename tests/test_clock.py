import dataclasses

import numpy as np

from chhaya.twin.clock import meal_clock_offset, shift_meals


def _offset(rec, t_end):
    return meal_clock_offset(rec.cgm["t_min"], rec.cgm["glucose_mgdl"], rec.meals["t_min"], t_end)


def test_meals_on_the_sensor_clock_need_no_shift(rec):
    assert abs(_offset(rec, 4 * 1440)) <= 15


def test_meals_logged_an_hour_early_are_found(rec):
    early = dataclasses.replace(rec, meals=rec.meals.assign(t_min=rec.meals["t_min"] - 60))
    assert _offset(early, 4 * 1440) in (45, 60, 75)


def test_only_the_calibration_window_is_used(rec):
    early = dataclasses.replace(rec, meals=rec.meals.assign(t_min=rec.meals["t_min"] - 60))
    scrambled = early.cgm.copy()
    later = scrambled["t_min"] >= 4 * 1440
    scrambled.loc[later, "glucose_mgdl"] = np.random.default_rng(0).uniform(60, 300, int(later.sum()))
    assert _offset(dataclasses.replace(early, cgm=scrambled), 4 * 1440) == _offset(early, 4 * 1440)


def test_too_few_meals_means_no_shift(rec):
    few = dataclasses.replace(rec, meals=rec.meals.iloc[:3])
    assert _offset(few, 4 * 1440) == 0


def test_shift_moves_every_meal_and_records_it(rec):
    moved = shift_meals(rec, 60)
    assert (moved.meals["t_min"].to_numpy() == rec.meals["t_min"].to_numpy() + 60).all()
    assert moved.static["meal_clock_offset_min"] == 60
    moved.validate()
    assert shift_meals(rec, 0) is rec


def test_shift_drops_meals_pushed_outside_the_recording(rec):
    moved = shift_meals(
        rec, -9 * 60
    )  # the first breakfast, at about 08:00 on day one, falls before the start
    assert len(moved.meals) == len(rec.meals) - 1
    moved.validate()
