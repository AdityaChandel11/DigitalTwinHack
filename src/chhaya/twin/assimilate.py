"""Fingersticks after the sensor comes off: a deviation from the patient's daily shape that fades.

A fingerstick says how far glucose is from the expected shape *now*. Exploration on development patients
(docs/decisions/2026-10-04-plan-revision.md) showed that carrying that difference forward as a lasting level
makes the estimate worse; letting it fade over about two hours makes it slightly better.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np


class FilterConfig(NamedTuple):
    tau_min: float = 120.0  # how long a deviation seen at a fingerstick persists
    fast_sd: float = 25.0  # stationary spread of the fading deviation, mg/dL
    obs_sd: float = 15.0  # fingerstick against sensor disagreement after the map, mg/dL
    slow: bool = False  # also track a slow level (drift over days)
    slow_sd_per_sqrt_day: float = 8.0
    slow_sd0: float = 20.0


MIN_OWN_PAIRS = 8  # a patient's own slope needs this many calibration pairs ...
MIN_OWN_SPAN = 40.0  # ... spanning at least this many mg/dL
MIN_OFFSET_PAIRS = 3
SLOPE_RANGE = (0.6, 1.2)


def pooled_map(cbg, cgm) -> tuple[float, float]:
    """Sensor = intercept + slope x fingerstick, over development patients' calibration pairs."""
    slope, intercept = np.polyfit(np.asarray(cbg, dtype=float), np.asarray(cgm, dtype=float), 1)
    return float(intercept), float(slope)


def sensor_map(cbg, cgm, pooled: tuple[float, float]) -> tuple[float, float]:
    """This patient's map from calibration-window pairs; the pooled slope, then the pooled map, when pairs are few."""
    cbg, cgm = np.asarray(cbg, dtype=float), np.asarray(cgm, dtype=float)
    if cbg.size >= MIN_OWN_PAIRS and np.ptp(cbg) > MIN_OWN_SPAN:
        slope = float(np.clip(np.polyfit(cbg, cgm, 1)[0], *SLOPE_RANGE))
        return float(np.mean(cgm - slope * cbg)), slope
    if cbg.size >= MIN_OFFSET_PAIRS:
        return float(np.mean(cgm - pooled[1] * cbg)), pooled[1]
    return pooled


def deviation(t_obs, z, t_eval, cfg: FilterConfig = FilterConfig(), smooth: bool = False) -> np.ndarray:
    """Deviation from the daily shape at `t_eval`, from surprises `z` seen at fingerstick times `t_obs`.

    State: a slow level (random walk, optional) and a fast deviation that fades with time constant `tau_min`.
    Live (`smooth=False`): each value uses only fingersticks at or before it. In hindsight (`smooth=True`):
    all fingersticks, for the retrospective report. Fingersticks may be given in any order.
    """
    t_obs, z, t_eval = (np.asarray(a, dtype=float) for a in (t_obs, z, t_eval))
    order = np.argsort(t_obs, kind="stable")
    t_obs, z = t_obs[order], z[order]
    n = t_obs.size
    if n == 0:
        return np.zeros(t_eval.size)
    h = np.array([1.0, 1.0])
    x = np.zeros(2)
    p = np.diag([cfg.slow_sd0**2 if cfg.slow else 0.0, cfg.fast_sd**2])
    q_slow = cfg.slow_sd_per_sqrt_day**2 / 1440.0 if cfg.slow else 0.0
    xs, ps, xps, pps, fs = [], [], [], [], []
    last = t_obs[0]
    for t, y in zip(t_obs, z, strict=True):
        dt = max(t - last, 0.0)
        a = np.exp(-dt / cfg.tau_min)
        f = np.diag([1.0, a])
        xp = f @ x
        pp = f @ p @ f.T + np.diag([q_slow * dt, cfg.fast_sd**2 * (1.0 - a * a)])
        gain = pp @ h / (h @ pp @ h + cfg.obs_sd**2)
        x = xp + gain * (y - h @ xp)
        p = pp - np.outer(gain, h @ pp)
        xs.append(x.copy()), ps.append(p.copy()), xps.append(xp.copy()), pps.append(pp.copy()), fs.append(f)
        last = t
    xs = np.array(xs)
    if smooth:
        for i in range(n - 2, -1, -1):
            c = ps[i] @ fs[i + 1].T @ np.linalg.pinv(pps[i + 1])
            xs[i] = xs[i] + c @ (xs[i + 1] - xps[i + 1])
    idx = np.searchsorted(t_obs, t_eval, side="right") - 1
    j = np.clip(idx, 0, n - 1)
    back = np.where(idx >= 0, xs[j, 0] + xs[j, 1] * np.exp(-(t_eval - t_obs[j]) / cfg.tau_min), 0.0)
    if not smooth:
        return back
    nxt = np.clip(idx + 1, 0, n - 1)
    fwd = xs[nxt, 0] + xs[nxt, 1] * np.exp(-(t_obs[nxt] - t_eval) / cfg.tau_min)
    gap = np.maximum(t_obs[nxt] - t_obs[j], 1.0)
    w = np.clip((t_eval - t_obs[j]) / gap, 0.0, 1.0)
    between = (1.0 - w) * back + w * fwd
    return np.where(idx < 0, fwd, np.where(idx + 1 < n, between, back))
