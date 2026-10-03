import numpy as np
import pytest

from chhaya.eval.baselines import average_day_baseline, lodo_average_day, mean_baseline


def test_mean_baseline():
    assert mean_baseline([100.0, 140.0], 3).tolist() == [120.0, 120.0, 120.0]


def test_average_day_reproduces_a_repeating_daily_pattern():
    t = np.arange(0, 3 * 1440, 15)
    g = 120.0 + 40.0 * np.sin(2 * np.pi * (t % 1440) / 1440.0)
    cal = t < 2 * 1440
    pred = average_day_baseline(t[cal], g[cal], t[~cal], bin_min=15)
    assert np.allclose(pred, g[~cal])


def test_average_day_fills_hours_never_seen_in_calibration():
    cal_tod = np.array([0, 30, 720])  # nothing between 01:00 and 12:00
    pred = average_day_baseline(cal_tod, np.array([100.0, 100.0, 200.0]), np.array([360]))
    assert 100.0 < pred[0] < 200.0


def test_average_day_handles_clock_times_past_midnight():
    pred = average_day_baseline(np.array([1440 + 60]), np.array([150.0]), np.array([60, 2 * 1440 + 60]))
    assert pred.tolist() == [150.0, 150.0]


def test_average_day_needs_calibration_data():
    with pytest.raises(ValueError):
        average_day_baseline(np.array([], dtype=int), np.array([]), np.array([0]))


def test_left_out_day_prediction_never_sees_its_own_day():
    t = np.arange(0, 3 * 1440, 15)
    day = t // 1440
    g = np.where(day == 1, 300.0, 100.0)  # the middle day is wildly different
    pred = lodo_average_day(day, t, g)
    assert pred.shape == g.shape
    assert np.allclose(pred[day == 1], 100.0)  # predicted from the two ordinary days only
    assert np.allclose(pred[day == 0], 200.0)  # the mean of an ordinary and the odd day


def test_left_out_day_prediction_with_a_single_day_falls_back_to_that_day():
    t = np.arange(0, 1440, 15)
    g = 100.0 + t / 20.0
    assert np.allclose(lodo_average_day(t // 1440, t, g, bin_min=15), g)
