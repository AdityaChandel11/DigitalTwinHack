"""The spread the frozen fingerstick filter assigns to its own deviation: the band of section F's estimates.

`chhaya.twin.assimilate.deviation` returns the mean of a fading deviation given fingerstick surprises. This
module runs the same recursion and keeps the variance, which that function computes and throws away. It adds
no constant and fits nothing (docs/PREREGISTRATION.md, note to Amendment 3 of 8 Oct 2026 on the band). The
filter is registered without a slow level, so the state is one number.
"""

from __future__ import annotations

import numpy as np

from chhaya.twin.assimilate import FilterConfig

Z80 = 1.2815515655446004  # 90th percentile of the standard normal: half-width of a central 80 % interval


def _posterior(
    t_obs, z, t_eval, cfg: FilterConfig, smooth: bool, strictly_before: bool
) -> tuple[np.ndarray, np.ndarray]:
    """Mean and spread of the fading deviation at `t_eval`. The mean is what `deviation` returns.

    Live: fingersticks at or before each time (strictly before it when asked). In hindsight (`smooth`): all
    of them. Between two fingersticks the smoothed state is an Ornstein-Uhlenbeck bridge between its two
    smoothed ends, so its variance is the bridge's own plus what the uncertain ends pass on.
    """
    if cfg.slow:
        raise ValueError("the band is registered for the filter without a slow level")
    t_obs, z, t_eval = (np.asarray(a, dtype=float) for a in (t_obs, z, t_eval))
    order = np.argsort(t_obs, kind="stable")
    t_obs, z = t_obs[order], z[order]
    n = t_obs.size
    var0, noise, tau = cfg.fast_sd**2, cfg.obs_sd**2, cfg.tau_min
    if n == 0:
        return np.zeros(t_eval.shape), np.full(t_eval.shape, cfg.fast_sd)

    m, p, mp, pp, step = (np.empty(n) for _ in range(5))  # filtered, predicted, and each step's decay
    x, v, last = 0.0, var0, t_obs[0]
    for i in range(n):
        a = np.exp(-max(t_obs[i] - last, 0.0) / tau)
        xp, vp = a * x, a * a * v + var0 * (1.0 - a * a)
        gain = vp / (vp + noise)
        x, v = xp + gain * (z[i] - xp), (1.0 - gain) * vp
        m[i], p[i], mp[i], pp[i], step[i] = x, v, xp, vp, a
        last = t_obs[i]

    idx = np.searchsorted(t_obs, t_eval, side="left" if strictly_before and not smooth else "right") - 1
    j = np.clip(idx, 0, n - 1)
    seen = idx >= 0
    a = np.exp(-np.where(seen, t_eval - t_obs[j], 0.0) / tau)
    if not smooth:
        mean = np.where(seen, m[j] * a, 0.0)
        var = np.where(seen, a * a * p[j] + var0 * (1.0 - a * a), var0)
        return mean, np.sqrt(var)

    ms, ps, lag = m.copy(), p.copy(), np.zeros(n)  # smoothed mean and variance; covariance with the next
    for i in range(n - 2, -1, -1):
        c = p[i] * step[i + 1] / pp[i + 1]
        ms[i] = m[i] + c * (ms[i + 1] - mp[i + 1])
        ps[i] = p[i] + c * c * (ps[i + 1] - pp[i + 1])
        lag[i] = c * ps[i + 1]

    after_mean, after_var = ms[j] * a, a * a * ps[j] + var0 * (1.0 - a * a)
    b = np.exp(-np.where(seen, 0.0, t_obs[0] - t_eval) / tau)
    before_mean, before_var = ms[0] * b, b * b * ps[0] + var0 * (1.0 - b * b)
    nxt = np.clip(idx + 1, 0, n - 1)
    gap = np.maximum(t_obs[nxt] - t_obs[j], 1e-9)
    u = np.clip(t_eval - t_obs[j], 0.0, gap) / tau
    w = np.clip(t_obs[nxt] - t_eval, 0.0, gap) / tau
    den = -np.expm1(-2.0 * gap / tau)
    wj = np.exp(-u) * -np.expm1(-2.0 * w) / den
    wn = np.exp(-w) * -np.expm1(-2.0 * u) / den
    between_mean = wj * ms[j] + wn * ms[nxt]
    between_var = (
        var0 * np.expm1(-2.0 * u) * np.expm1(-2.0 * w) / den
        + wj * wj * ps[j]
        + wn * wn * ps[nxt]
        + 2.0 * wj * wn * lag[j]
    )
    inside = seen & (idx + 1 < n)
    mean = np.where(~seen, before_mean, np.where(inside, between_mean, after_mean))
    var = np.where(~seen, before_var, np.where(inside, between_var, after_var))
    return mean, np.sqrt(np.maximum(var, 0.0))


def deviation_sd(
    t_obs, t_eval, cfg: FilterConfig = FilterConfig(), smooth: bool = False, strictly_before: bool = False
) -> np.ndarray:
    """Spread (mg/dL) of the fading deviation at `t_eval`, given fingersticks at `t_obs`.

    It takes no readings: the variance of this filter depends on when fingersticks were taken, not on what
    they read. So it cannot leak a hidden value, and it is the same before and after the reveal.
    """
    t_obs = np.asarray(t_obs, dtype=float)
    return _posterior(t_obs, np.zeros(t_obs.shape), t_eval, cfg, smooth, strictly_before)[1]


def band(est, sd, scale: float = 1.0, z: float = Z80) -> tuple[np.ndarray, np.ndarray]:
    """Low and high edge of a symmetric band: `est` minus and plus `z * scale * sd`."""
    if not scale > 0.0:
        raise ValueError(f"scale must be positive, got {scale}")
    est = np.asarray(est, dtype=float)
    half = z * scale * np.asarray(sd, dtype=float)
    return est - half, est + half
