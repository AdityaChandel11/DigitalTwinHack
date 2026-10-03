"""Sensor-off baselines: what you can say about hidden glucose without a twin."""

from __future__ import annotations

import numpy as np


def mean_baseline(cal_g, n_test: int) -> np.ndarray:
    """The patient's calibration-window mean, repeated."""
    return np.full(n_test, float(np.mean(cal_g)))


def average_day_baseline(cal_tod, cal_g, test_tod, bin_min: int = 30) -> np.ndarray:
    """The patient's own average daily curve: mean glucose per time-of-day bin in the calibration window.

    `*_tod` are minutes of the day (0-1439). Empty bins are filled from their neighbours around the clock.
    """
    cal_tod = np.asarray(cal_tod, dtype=int) % 1440
    cal_g = np.asarray(cal_g, dtype=float)
    n_bins = 1440 // bin_min
    sums = np.bincount(cal_tod // bin_min, weights=cal_g, minlength=n_bins)
    counts = np.bincount(cal_tod // bin_min, minlength=n_bins)
    have = counts > 0
    if not have.any():
        raise ValueError("no calibration readings")
    profile = np.where(have, sums / np.maximum(counts, 1), np.nan)
    if not have.all():
        centres = np.arange(n_bins)
        known = centres[have]
        profile = np.interp(centres, known, profile[have], period=n_bins)
    return profile[(np.asarray(test_tod, dtype=int) % 1440) // bin_min]


def lodo_average_day(day, tod, g, bin_min: int = 30) -> np.ndarray:
    """For every reading, the average-day value built from the *other* days.

    This is what the average-day baseline would have said about a day it had not seen, which gives an
    honest noise scale inside the calibration window. With a single day there is no other day, so the
    prediction is that day's mean: returning its own curve would report zero error and make the
    uncertainty band far too narrow.
    """
    day = np.asarray(day)
    tod = np.asarray(tod, dtype=int)
    g = np.asarray(g, dtype=float)
    days = np.unique(day)
    if days.size < 2:
        return np.full(g.shape, float(g.mean()))
    out = np.empty_like(g)
    for d in days:
        held = day == d
        out[held] = average_day_baseline(tod[~held], g[~held], tod[held], bin_min)
    return out
