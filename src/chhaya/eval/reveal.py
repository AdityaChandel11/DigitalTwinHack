"""The hide-and-reveal experiment: calibrate on the first k days, estimate the rest without the sensor."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp
import numpy as np

from chhaya.config import SEED
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline, mean_baseline
from chhaya.eval.metrics import rmse, score
from chhaya.twin.fit import TwinFit, draw_ensemble, fit_twin
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import Fixed, simulate_ensemble
from chhaya.twin.priors import Prior, record_prior
from chhaya.units import mmol_to_mgdl


class Reveal(NamedTuple):
    rec_id: str
    k_days: int
    t_test: np.ndarray  # minutes from recording start
    truth: np.ndarray  # hidden sensor, mg/dL
    twin: np.ndarray  # twin estimate (MAP member), mg/dL
    lo: np.ndarray  # 10th percentile of the predictive band
    hi: np.ndarray  # 90th percentile
    day: np.ndarray  # average-day baseline
    mean: np.ndarray  # mean baseline
    fit: TwinFit
    metrics: dict[str, float]


def run_reveal(
    rec: Recording,
    k_days: int,
    prior: Prior | None = None,
    fx: Fixed = Fixed(),
    n_members: int = 200,
    seed: int = SEED,
    min_test_days: float = 1.0,
) -> Reveal | None:
    """Return None when the recording is too short to calibrate on k days and still test on a day."""
    inp, obs_idx, obs_mmol = build_inputs(rec)
    split = k_days * 1440
    cal = obs_idx < split
    test = ~cal
    if cal.sum() < 48 or test.sum() < 24 or obs_idx[test].max() - split < min_test_days * 1440:
        return None
    prior = prior if prior is not None else record_prior(rec.static)
    fit = fit_twin(inp, obs_idx[cal], obs_mmol[cal], prior, fx, seed=seed)

    zs = draw_ensemble(fit, n_members, seed)
    ens = np.asarray(simulate_ensemble(jnp.asarray(zs), inp, fx).gi)[:, obs_idx[test]]
    noise = np.random.default_rng(seed).normal(0.0, fit.sigma_res, ens.shape)
    lo, hi = mmol_to_mgdl(np.quantile(ens + noise, [0.1, 0.9], axis=0))
    twin = mmol_to_mgdl(ens[0])
    truth = mmol_to_mgdl(obs_mmol[test])

    tod0 = int(inp.t0_min_of_day)
    cal_g = mmol_to_mgdl(obs_mmol[cal])
    day = average_day_baseline(tod0 + obs_idx[cal], cal_g, tod0 + obs_idx[test])
    mean = mean_baseline(cal_g, int(test.sum()))

    metrics: dict[str, float] = {"n_test": float(test.sum()), "sigma_res_mgdl": mmol_to_mgdl(fit.sigma_res)}
    for name, est in (("twin", twin), ("day", day), ("mean", mean)):
        bands = (lo, hi) if name == "twin" else (None, None)
        metrics.update({f"{name}_{k}": v for k, v in score(est, truth, *bands).items()})
    if len(rec.cgm_ref):
        # A second physical sensor: how far apart two real sensors are bounds what any estimate can reach.
        ref = np.interp(obs_idx[test], rec.cgm_ref["t_min"], rec.cgm_ref["glucose_mgdl"])
        metrics["floor_rmse"] = rmse(ref, truth)
        metrics["twin_rmse_vs_ref"] = rmse(twin, ref)
    return Reveal(rec.rec_id, k_days, obs_idx[test], truth, twin, lo, hi, day, mean, fit, metrics)
