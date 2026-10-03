"""The hide-and-reveal experiment: calibrate on the first k days, estimate the rest without the sensor."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp
import numpy as np

from chhaya.config import SEED
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline, lodo_average_day, mean_baseline
from chhaya.eval.metrics import rmse, score
from chhaya.twin.clock import meal_clock_offset, shift_meals
from chhaya.twin.fit import TwinFit, draw_ensemble, fit_twin
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import Fixed, simulate_ensemble
from chhaya.twin.priors import Prior, record_prior
from chhaya.units import mmol_to_mgdl


class RevealConfig(NamedTuple):
    """The parts of the estimator added after the first Gate 2 run. Each can be switched off for ablation."""

    meal_clock: bool = True  # estimate the offset between the meal log and the sensor clock
    blend: float = 0.5  # weight on the physiology, the rest on the average day; 1.0 = physiology only
    loss: str = "linear"  # plain least squares; "soft_l1" was tried on dev patients and did not help
    f_scale: float = 1.0  # residual size (mmol/L) beyond which the robust loss takes over


class Reveal(NamedTuple):
    rec_id: str
    k_days: int
    t_test: np.ndarray  # minutes from recording start
    truth: np.ndarray  # hidden sensor, mg/dL
    twin: np.ndarray  # full estimate: physiology blended with the average day, mg/dL
    lo: np.ndarray  # 10th percentile of the predictive band
    hi: np.ndarray  # 90th percentile
    ode: np.ndarray  # physiology alone (MAP member)
    day: np.ndarray  # average-day baseline
    mean: np.ndarray  # mean baseline
    fit: TwinFit
    metrics: dict[str, float]
    cal_t: np.ndarray  # calibration readings, for showing the fit
    cal_truth: np.ndarray
    cal_ode: np.ndarray


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def run_reveal(
    rec: Recording,
    k_days: int,
    prior: Prior | None = None,
    fx: Fixed = Fixed(),
    n_members: int = 200,
    seed: int = SEED,
    min_test_days: float = 1.0,
    cfg: RevealConfig = RevealConfig(),
) -> Reveal | None:
    """Return None when the recording is too short to calibrate on k days and still test on a day.

    Everything learned here (parameters, meal-clock offset, average day, noise scale) comes from
    readings before the split. After it, only meals and activity are read.
    """
    split = k_days * 1440
    offset = 0
    if cfg.meal_clock:
        eaten = rec.meals[rec.meals["carb_g"] > 0]
        offset = meal_clock_offset(rec.cgm["t_min"], rec.cgm["glucose_mgdl"], eaten["t_min"], split)
        rec = shift_meals(rec, offset)
    inp, obs_idx, obs_mmol = build_inputs(rec)
    cal = obs_idx < split
    test = ~cal
    if cal.sum() < 48 or test.sum() < 24 or obs_idx[test].max() - split < min_test_days * 1440:
        return None
    prior = prior if prior is not None else record_prior(rec.static)
    fit = fit_twin(inp, obs_idx[cal], obs_mmol[cal], prior, fx, seed=seed, loss=cfg.loss, f_scale=cfg.f_scale)

    zs = draw_ensemble(fit, n_members, seed)
    ens = mmol_to_mgdl(np.asarray(simulate_ensemble(jnp.asarray(zs), inp, fx).gi)[:, obs_idx])
    obs = mmol_to_mgdl(obs_mmol)
    tod = int(inp.t0_min_of_day) + obs_idx  # clock minutes since midnight of the first day
    w = cfg.blend
    day = average_day_baseline(tod[cal], obs[cal], tod[test])
    mean = mean_baseline(obs[cal], int(test.sum()))
    ode = ens[0, test]
    # The physiology knows what was eaten today; the average day knows the habits the log misses.
    # Their errors are only partly correlated, so the blend beats both.
    twin = w * ode + (1.0 - w) * day
    truth = obs[test]
    # Noise scale from calibration days, with the average day built without the day being predicted.
    seen = lodo_average_day(tod[cal] // 1440, tod[cal], obs[cal]) if w < 1.0 else ens[0, cal]
    sigma = _rms(obs[cal] - (w * ens[0, cal] + (1.0 - w) * seen))
    noise = np.random.default_rng(seed).normal(0.0, sigma, (ens.shape[0], int(test.sum())))
    lo, hi = np.quantile(w * ens[:, test] + (1.0 - w) * day + noise, [0.1, 0.9], axis=0)

    metrics: dict[str, float] = {
        "n_test": float(test.sum()),
        "sigma_res_mgdl": sigma,
        "meal_clock_offset_min": float(offset),
    }
    for name, est in (("twin", twin), ("ode", ode), ("day", day), ("mean", mean)):
        bands = (lo, hi) if name == "twin" else (None, None)
        metrics.update({f"{name}_{k}": v for k, v in score(est, truth, *bands).items()})
    if len(rec.cgm_ref):
        # A second physical sensor: how far apart two real sensors are bounds what any estimate can reach.
        ref = np.interp(obs_idx[test], rec.cgm_ref["t_min"], rec.cgm_ref["glucose_mgdl"])
        metrics["floor_rmse"] = rmse(ref, truth)
        metrics["twin_rmse_vs_ref"] = rmse(twin, ref)
    return Reveal(
        rec_id=rec.rec_id,
        k_days=k_days,
        t_test=obs_idx[test],
        truth=truth,
        twin=twin,
        lo=lo,
        hi=hi,
        ode=ode,
        day=day,
        mean=mean,
        fit=fit,
        metrics=metrics,
        cal_t=obs_idx[cal],
        cal_truth=obs[cal],
        cal_ode=ens[0, cal],
    )
