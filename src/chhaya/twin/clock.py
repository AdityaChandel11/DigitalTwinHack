"""Per-patient meal-clock offset: some meal logs run on a different clock from the sensor."""

from __future__ import annotations

import dataclasses

import numpy as np

from chhaya.data.schema import Recording

CANDIDATES = tuple(range(-30, 91, 15))  # minutes; real files show logs up to an hour early
RISE_MIN = 60
MIN_MEALS = 5


def meal_clock_offset(cgm_t, cgm_g, meal_t, t_end: float, candidates=CANDIDATES) -> int:
    """Minutes to add to logged meal times so that glucose rises after them.

    Picks the shift with the largest mean 60-minute glucose rise following a meal. Only readings and
    meals before `t_end` (the calibration split) are used, so nothing from the hidden window leaks in.
    Returns 0 when fewer than MIN_MEALS meals can be scored.
    """
    cgm_t = np.asarray(cgm_t, dtype=float)
    cgm_g = np.asarray(cgm_g, dtype=float)
    seen = cgm_t < t_end
    cgm_t, cgm_g = cgm_t[seen], cgm_g[seen]
    meal_t = np.asarray(meal_t, dtype=float)
    meal_t = meal_t[meal_t < t_end]
    if cgm_t.size < 2:
        return 0
    scores = {}
    for lag in candidates:
        t = meal_t + lag
        ok = (t >= cgm_t[0]) & (t + RISE_MIN <= cgm_t[-1])
        if ok.sum() >= MIN_MEALS:
            rise = np.interp(t[ok] + RISE_MIN, cgm_t, cgm_g) - np.interp(t[ok], cgm_t, cgm_g)
            scores[lag] = float(rise.mean())
    if 0 not in scores:
        return 0
    return int(max(scores, key=lambda lag: (scores[lag], -abs(lag))))  # ties go to the smaller shift


def shift_meals(rec: Recording, minutes: int) -> Recording:
    """The recording with every meal moved by `minutes`; meals pushed outside the recording are dropped."""
    if minutes == 0:
        return rec
    meals = rec.meals.assign(t_min=rec.meals["t_min"] + minutes)
    meals = meals[(meals["t_min"] >= 0) & (meals["t_min"] < rec.n_min)].reset_index(drop=True)
    return dataclasses.replace(rec, meals=meals, static={**rec.static, "meal_clock_offset_min": minutes})
