import dataclasses

import numpy as np
import pytest
from conftest import make_recording

from chhaya.eval.reveal import RevealConfig, run_reveal


@pytest.fixture(scope="module")
def reveal():
    return run_reveal(make_recording(days=6, seed=3, with_ref=True), k_days=4, n_members=60)


@pytest.mark.slow
def test_twin_beats_the_average_day_when_meals_vary(reveal):
    m = reveal.metrics
    assert m["twin_rmse"] < m["day_rmse"]
    assert m["twin_rmse"] < 15.0  # mg/dL; sensor noise alone is about 7
    assert reveal.twin.shape == reveal.truth.shape == reveal.lo.shape
    assert (reveal.t_test >= 4 * 1440).all()  # nothing from the calibration window is scored


@pytest.mark.slow
def test_band_is_neither_useless_nor_overconfident(reveal):
    assert (reveal.lo < reveal.hi).all()
    assert 0.55 <= reveal.metrics["twin_cov80"] <= 0.97


@pytest.mark.slow
def test_second_sensor_gives_a_noise_floor(reveal):
    assert 3.0 < reveal.metrics["floor_rmse"] < 20.0
    assert reveal.metrics["twin_rmse_vs_ref"] > 0.0


def test_too_short_to_hold_out_a_day_returns_none(rec):
    assert run_reveal(rec, k_days=6) is None  # six-day recording, nothing left to test on
    short = dataclasses.replace(rec, cgm=rec.cgm[rec.cgm["t_min"] < 4 * 1440 + 600])
    assert run_reveal(short, k_days=4) is None  # only ten hours after the split


def _scramble_hidden(rec, split):
    cgm = rec.cgm.copy()
    hidden = cgm["t_min"] >= split
    cgm.loc[hidden, "glucose_mgdl"] = np.random.default_rng(1).uniform(60.0, 300.0, int(hidden.sum()))
    return dataclasses.replace(rec, cgm=cgm)


@pytest.mark.slow
def test_hidden_readings_cannot_change_the_estimate():
    rec = make_recording(days=6, seed=4)
    a = run_reveal(rec, k_days=4, n_members=20)
    b = run_reveal(_scramble_hidden(rec, 4 * 1440), k_days=4, n_members=20)
    assert np.array_equal(a.twin, b.twin) and np.array_equal(a.lo, b.lo) and np.array_equal(a.hi, b.hi)
    assert np.array_equal(a.day, b.day)
    assert not np.array_equal(a.truth, b.truth)  # the scramble did reach the scored readings


@pytest.mark.slow
def test_meal_log_on_the_wrong_clock_is_repaired():
    rec = make_recording(days=6, seed=5)
    early = dataclasses.replace(rec, meals=rec.meals.assign(t_min=rec.meals["t_min"] - 60))
    fixed = run_reveal(early, k_days=4, n_members=20)
    broken = run_reveal(early, k_days=4, n_members=20, cfg=RevealConfig(meal_clock=False))
    assert fixed.metrics["meal_clock_offset_min"] in (45.0, 60.0, 75.0)
    assert fixed.metrics["ode_rmse"] < broken.metrics["ode_rmse"] - 3.0


@pytest.mark.slow
def test_blend_recovers_a_daily_habit_the_log_misses():
    rec = make_recording(days=6, seed=6)
    tod = rec.meals["t_min"] % 1440
    no_dinner_logged = dataclasses.replace(rec, meals=rec.meals[tod < 18 * 60])  # eaten but never logged
    out = run_reveal(no_dinner_logged, k_days=4, n_members=20)
    assert out.metrics["twin_rmse"] < out.metrics["ode_rmse"] - 2.0
    assert np.allclose(out.twin, 0.5 * out.ode + 0.5 * out.day)
    alone = run_reveal(no_dinner_logged, k_days=4, n_members=20, cfg=RevealConfig(blend=1.0))
    assert np.array_equal(alone.twin, alone.ode)
