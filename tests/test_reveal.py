import dataclasses

import numpy as np
import pytest
from conftest import make_recording

from chhaya.eval.reveal import RevealConfig, run_reveal, why_skipped


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


def test_default_configuration_is_the_one_chosen_on_development_patients():
    assert RevealConfig() == RevealConfig(meal_clock=True, blend=0.5, loss="linear", f_scale=1.0)


@pytest.mark.slow
def test_noise_floor_ignores_hours_the_second_sensor_did_not_record():
    rec = make_recording(days=6, seed=3, with_ref=True)
    cut = 4 * 1440 + 720  # the second sensor stops half a day into the hidden window
    short = dataclasses.replace(rec, cgm_ref=rec.cgm_ref[rec.cgm_ref["t_min"] < cut])
    out = run_reveal(short, k_days=4, n_members=20)
    assert (out.t_test < cut).sum() <= out.metrics["floor_n"] <= (out.t_test <= cut + 10).sum()
    assert (
        3.0 < out.metrics["floor_rmse"] < 20.0
    )  # two sensors with 7 mg/dL noise each, not a flat extrapolation


@pytest.mark.slow
def test_band_stays_honest_with_a_single_calibration_day():
    out = run_reveal(make_recording(days=4, seed=21), k_days=1, n_members=40)
    assert 0.65 <= out.metrics["twin_cov80"] <= 0.99


def test_blend_weight_must_be_a_fraction(rec):
    for w in (-0.1, 1.7):
        with pytest.raises(ValueError, match="blend"):
            run_reveal(rec, k_days=4, cfg=RevealConfig(blend=w))


def test_band_needs_at_least_two_ensemble_members(rec):
    with pytest.raises(ValueError, match="n_members"):
        run_reveal(rec, k_days=4, n_members=1)


@pytest.mark.slow
def test_reveal_carries_a_physiology_free_control_and_its_own_diagnostics(reveal):
    # Half average day, half mean: no meals, no model. Any gain over it is what the physiology adds.
    assert np.allclose(reveal.shrunk, 0.5 * reveal.day + 0.5 * reveal.mean)
    m = reveal.metrics
    assert m["shrunk_rmse"] > 0.0 and m["n_cal"] == 4 * 96 and m["cal_coverage"] == 1.0
    assert m["fit_nfev"] > 0 and m["fit_status"] in (0.0, 1.0, 2.0, 3.0, 4.0) and 0 <= m["fit_at_bound"] <= 7


def test_calibration_window_that_is_mostly_empty_is_skipped_with_a_reason(rec):
    # 16 hours of sensor, then nothing until day 4: "four days of calibration" would be a fiction.
    t = rec.cgm["t_min"]
    sparse = dataclasses.replace(rec, cgm=rec.cgm[(t < 16 * 60) | (t >= 4 * 1440)])
    assert "calibration window" in why_skipped(sparse, 4)
    assert run_reveal(sparse, k_days=4) is None
    assert why_skipped(rec, 4) is None
    assert "hold out" in why_skipped(rec, 6)
