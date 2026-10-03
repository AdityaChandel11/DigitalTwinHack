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

REF_MAX_GAP_MIN = 10  # a reference reading further away than this does not count as simultaneous
MIN_CAL_COVERAGE = 0.5  # share of the calibration window's 15-minute slots that must hold a reading
SLOT_MIN = 15


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
    shrunk: np.ndarray  # half average day, half mean: the physiology-free control
    fit: TwinFit
    metrics: dict[str, float]
    cal_t: np.ndarray  # calibration readings, for showing the fit
    cal_truth: np.ndarray
    cal_ode: np.ndarray


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def _coverage(t_cal: np.ndarray, split: float) -> float:
    """Share of the calibration window's 15-minute slots that hold at least one reading."""
    return float(np.unique(t_cal // SLOT_MIN).size / (split / SLOT_MIN))


def why_skipped(rec: Recording, k_days: float, min_test_days: float = 1.0) -> str | None:
    """Why this recording cannot be run at k_days, or None when it can.

    "k days of calibration" has to mean k days of sensor data: a recording whose calibration window is
    mostly a gap is skipped, and so is one that leaves less than a day to score.
    """
    t = rec.cgm["t_min"].to_numpy()
    split = k_days * 1440
    cal, test = t[t < split], t[t >= split]
    if split <= 0 or cal.size < 48:
        return f"fewer than 48 sensor readings in the first {k_days} days"
    coverage = _coverage(cal, split)
    if coverage < MIN_CAL_COVERAGE:
        return f"calibration window only {100 * coverage:.0f} % covered by the sensor"
    if test.size < 24 or test.max() - split < min_test_days * 1440:
        return "too short to hold out a day after calibration"
    return None


def run_reveal(
    rec: Recording,
    k_days: float,
    prior: Prior | None = None,
    fx: Fixed = Fixed(),
    n_members: int = 200,
    seed: int = SEED,
    min_test_days: float = 1.0,
    cfg: RevealConfig = RevealConfig(),
) -> Reveal | None:
    """Return None when `why_skipped` gives a reason (too little calibration data, or no day left to score).

    Everything learned here (parameters, meal-clock offset, average day, noise scale) comes from
    readings before the split. After it, only meals and activity are read.
    """
    if not 0.0 <= cfg.blend <= 1.0:
        raise ValueError(f"blend must be between 0 and 1, got {cfg.blend}")
    if n_members < 2:
        raise ValueError(f"n_members must be at least 2 to form a band, got {n_members}")
    if why_skipped(rec, k_days, min_test_days) is not None:
        return None
    split = k_days * 1440
    offset = 0
    if cfg.meal_clock:
        eaten = rec.meals[rec.meals["carb_g"] > 0]
        offset = meal_clock_offset(rec.cgm["t_min"], rec.cgm["glucose_mgdl"], eaten["t_min"], split)
        rec = shift_meals(rec, offset)
    inp, obs_idx, obs_mmol = build_inputs(rec)
    cal = obs_idx < split
    test = ~cal
    assert (obs_idx[test] >= split).all(), "a scored reading lies before the calibration split"
    prior = prior if prior is not None else record_prior(rec.static)
    fit = fit_twin(inp, obs_idx[cal], obs_mmol[cal], prior, fx, seed=seed, loss=cfg.loss, f_scale=cfg.f_scale)

    zs = draw_ensemble(fit, n_members, seed)
    ens = mmol_to_mgdl(np.asarray(simulate_ensemble(jnp.asarray(zs), inp, fx).gi)[:, obs_idx])
    obs = mmol_to_mgdl(obs_mmol)
    tod = int(inp.t0_min_of_day) + obs_idx  # clock minutes since midnight of the first day
    w = cfg.blend
    day = average_day_baseline(tod[cal], obs[cal], tod[test])
    mean = mean_baseline(obs[cal], int(test.sum()))
    shrunk = 0.5 * day + 0.5 * mean
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
        "n_cal": float(cal.sum()),
        "cal_coverage": _coverage(obs_idx[cal], split),
        "sigma_res_mgdl": sigma,
        "meal_clock_offset_min": float(offset),
        "fit_nfev": float(fit.nfev),
        "fit_status": float(fit.status),
        "fit_at_bound": float(fit.n_at_bound),
    }
    for name, est in (("twin", twin), ("ode", ode), ("day", day), ("mean", mean), ("shrunk", shrunk)):
        bands = (lo, hi) if name == "twin" else (None, None)
        metrics.update({f"{name}_{k}": v for k, v in score(est, truth, *bands).items()})
    if len(rec.cgm_ref):
        # A second physical sensor: how far apart two real sensors are bounds what any estimate can reach.
        # Only readings both sensors actually took are compared; the reference often stops days earlier,
        # and interpolating past its last reading would compare against a flat line.
        ref_t = rec.cgm_ref["t_min"].to_numpy(dtype=float)
        t = obs_idx[test]
        j = np.searchsorted(ref_t, t)
        last = ref_t.size - 1
        gap = np.minimum(np.abs(ref_t[np.clip(j - 1, 0, last)] - t), np.abs(ref_t[np.clip(j, 0, last)] - t))
        both = gap <= REF_MAX_GAP_MIN
        metrics["floor_n"] = float(both.sum())
        if both.any():
            ref = np.interp(t[both], ref_t, rec.cgm_ref["glucose_mgdl"])
            metrics["floor_rmse"] = rmse(ref, truth[both])
            metrics["twin_rmse_vs_ref"] = rmse(twin[both], ref)
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
        shrunk=shrunk,
        fit=fit,
        metrics=metrics,
        cal_t=obs_idx[cal],
        cal_truth=obs[cal],
        cal_ode=ens[0, cal],
    )
