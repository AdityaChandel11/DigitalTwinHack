"""Staleness alarm: has the patient moved away from the profile their last sensor wear gave?

A cumulative sum of standardised fingerstick surprises against the frozen profile (Amendment 3, "Staleness
alarm"). A surprise is how far a fingerstick, put on the sensor's scale, lies from the daily shape at that
clock time. One odd reading is not a drift; a run of readings on the same side is.
"""

from __future__ import annotations

import numpy as np

KAPPA = 0.5  # allowance per fingerstick, in standard deviations: half of the one-SD shift the sum looks for


def surprise_scale(profile_sd: float, fingerstick_sd: float) -> float:
    """Standard deviation of a surprise when nothing has changed: the shape's own spread plus the meter's."""
    return float(np.hypot(profile_sd, fingerstick_sd))


def cusum(z, kappa: float = KAPPA) -> np.ndarray:
    """After each fingerstick, the larger of the upward and the downward cumulative sum of the surprises `z`.

    Each sum adds the surprise less the allowance and is never below zero, so readings near the profile pull
    it back down. `z` must be in time order.
    """
    z = np.asarray(z, dtype=float)
    out = np.empty(z.size)
    up = down = 0.0
    for i, v in enumerate(z):
        up = max(0.0, up + v - kappa)
        down = max(0.0, down - v - kappa)
        out[i] = max(up, down)
    return out


def first_alarm(t, stat, threshold: float) -> float | None:
    """The time of the first fingerstick at which the sum is above the threshold; None when it never is."""
    hit = np.flatnonzero(np.asarray(stat, dtype=float) > threshold)
    return float(np.asarray(t, dtype=float)[hit[0]]) if hit.size else None
