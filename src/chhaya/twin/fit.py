"""MAP calibration of the twin with a Laplace posterior ensemble."""

from __future__ import annotations

from typing import NamedTuple

import jax
import jax.numpy as jnp
import numpy as np
from scipy.optimize import least_squares

from chhaya.twin.model import Fixed, Inputs, simulate
from chhaya.twin.priors import BOX_SD, Prior

SIGMA_OBS = 1.0  # mmol/L nominal CGM residual scale


class TwinFit(NamedTuple):
    z_map: np.ndarray  # (7,)
    cov: np.ndarray  # (7, 7)
    sigma_res: float  # mmol/L, SD of calibration residuals
    cost: float
    n_obs: int


def _n_eff(r: np.ndarray) -> float:
    """Effective sample size of autocorrelated residuals (AR(1) approximation)."""
    if r.size < 3 or np.std(r) == 0.0:
        return float(r.size)
    rho = float(np.clip(np.corrcoef(r[:-1], r[1:])[0, 1], 0.0, 0.99))
    return r.size * (1.0 - rho) / (1.0 + rho)


def fit_twin(
    inp: Inputs,
    obs_idx: np.ndarray,
    obs_mmol: np.ndarray,
    prior: Prior,
    fx: Fixed = Fixed(),
    n_starts: int = 6,
    seed: int = 0,
) -> TwinFit:
    """Fit z by bounded least squares from several prior draws; keep the lowest-cost solution."""
    if len(obs_idx) < 24:
        raise ValueError(f"need at least 24 CGM readings to calibrate, got {len(obs_idx)}")
    idx = jnp.asarray(obs_idx)
    obs = jnp.asarray(obs_mmol)
    mu = jnp.asarray(prior.mu)
    sd = jnp.asarray(prior.sd)

    def res(z):
        gi = simulate(z, inp, fx).gi
        return jnp.concatenate([(gi[idx] - obs) / SIGMA_OBS, (z - mu) / sd])

    res_j = jax.jit(res)
    jac_j = jax.jit(jax.jacfwd(res))
    rng = np.random.default_rng(seed)
    lo = prior.mu - BOX_SD * prior.sd
    hi = prior.mu + BOX_SD * prior.sd
    draws = [prior.mu + 0.5 * prior.sd * rng.standard_normal(prior.mu.size) for _ in range(n_starts - 1)]
    best = None
    for z0 in [prior.mu, *draws]:
        sol = least_squares(
            lambda z: np.asarray(res_j(z)),
            np.clip(z0, lo + 1e-6, hi - 1e-6),
            jac=lambda z: np.asarray(jac_j(z)),
            bounds=(lo, hi),
            method="trf",
            x_scale="jac",
            max_nfev=80,
        )
        if np.all(np.isfinite(sol.fun)) and (best is None or sol.cost < best.cost):
            best = sol
    if best is None:
        raise RuntimeError("twin calibration diverged from every start")
    n = len(obs_idx)
    r_data = best.fun[:n] * SIGMA_OBS
    sigma_res = float(np.sqrt(np.mean(r_data**2)))
    # Laplace covariance, widened for misfit and for autocorrelated residuals.
    h = best.jac.T @ best.jac
    widen = max(1.0, (sigma_res / SIGMA_OBS) ** 2) * n / max(_n_eff(r_data), 1.0)
    cov = np.linalg.inv(h + 1e-9 * np.eye(h.shape[0])) * widen
    return TwinFit(z_map=best.x, cov=cov, sigma_res=sigma_res, cost=float(best.cost), n_obs=n)


def draw_ensemble(fit: TwinFit, n: int = 200, seed: int = 0) -> np.ndarray:
    """Sample parameter vectors from the Laplace posterior. Member 0 is the MAP."""
    rng = np.random.default_rng(seed)
    zs = rng.multivariate_normal(fit.z_map, fit.cov, size=n, method="eigh")
    zs[0] = fit.z_map
    return zs
