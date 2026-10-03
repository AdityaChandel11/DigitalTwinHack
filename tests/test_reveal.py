import dataclasses

import pytest
from conftest import make_recording

from chhaya.eval.reveal import run_reveal


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
