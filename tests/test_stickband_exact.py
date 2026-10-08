"""The filter's mean and spread against the exact Gaussian posterior, by plain linear algebra.

Added after the review of 8 Oct: the Monte Carlo check in test_stickband.py would not notice a wrong
covariance between neighbouring smoothed states, or a smoothed variance replaced by the filtered one.
"""

import numpy as np
import pytest

from chhaya.twin.assimilate import FilterConfig
from chhaya.twin.stickband import _posterior

CFG = FilterConfig()


def _exact(t_obs, z, t_eval, mode: str) -> tuple[np.ndarray, np.ndarray]:
    """Condition a stationary Ornstein-Uhlenbeck process on noisy readings, one evaluation time at a time."""
    var0, noise, tau = CFG.fast_sd**2, CFG.obs_sd**2, CFG.tau_min
    mean, sd = np.zeros(t_eval.size), np.full(t_eval.size, CFG.fast_sd)
    for i, t in enumerate(t_eval):
        use = {"hindsight": np.ones(t_obs.size, bool), "strict": t_obs < t, "live": t_obs <= t}[mode]
        if use.any():
            to = t_obs[use]
            cov = var0 * np.exp(-np.abs(to[:, None] - to[None, :]) / tau) + noise * np.eye(to.size)
            k = var0 * np.exp(-np.abs(to - t) / tau)
            w = np.linalg.solve(cov, k)
            mean[i], sd[i] = w @ z[use], np.sqrt(var0 - w @ k)
    return mean, sd


@pytest.mark.parametrize("mode", ["live", "strict", "hindsight"])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_mean_and_spread_are_the_exact_posterior_of_the_filters_own_model(mode, seed):
    rng = np.random.default_rng(seed)
    t_obs = np.sort(np.round(rng.uniform(0, 3000, 14)))
    t_obs[6] = t_obs[5]  # two fingersticks in one minute
    z = rng.normal(0, 30, t_obs.size)
    # before the first, after the last, at a fingerstick and a minute either side of one
    t_eval = np.concatenate([np.arange(-200.0, 3400.0, 37.0), t_obs[:5], t_obs[:5] + 1.0, t_obs[:5] - 1.0])
    mean, sd = _posterior(t_obs, z, t_eval, CFG, mode == "hindsight", mode == "strict")
    want_mean, want_sd = _exact(t_obs, z, t_eval, mode)
    assert np.allclose(mean, want_mean, atol=1e-8)
    assert np.allclose(sd, want_sd, atol=1e-8)


@pytest.mark.parametrize("mode", ["live", "hindsight"])
def test_a_single_fingerstick_is_the_exact_posterior_too(mode):
    t_obs, z = np.array([500.0]), np.array([40.0])
    t_eval = np.array([0.0, 499.0, 500.0, 501.0, 900.0])
    mean, sd = _posterior(t_obs, z, t_eval, CFG, mode == "hindsight", False)
    want_mean, want_sd = _exact(t_obs, z, t_eval, mode)
    assert np.allclose(mean, want_mean, atol=1e-10) and np.allclose(sd, want_sd, atol=1e-10)
