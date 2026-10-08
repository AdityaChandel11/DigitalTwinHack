"""The meal what-if: the same twin, one logged meal resized, labelled simulation.

It reruns the reveal's own steps (meal-clock shift, the fitted ensemble, the blend with the average day, the
band from the calibration residual) with one meal's carbohydrate changed. At the logged amount it gives back the
reveal's estimate exactly, which a test checks. It changes a meal only: no dose, drug or activity, and it is not
a prediction for this patient. Never read: any hidden sensor value.
"""

from __future__ import annotations

import jax.numpy as jnp
import numpy as np

from chhaya.config import SEED
from chhaya.data.schema import Recording
from chhaya.eval.reveal import Reveal, RevealConfig
from chhaya.twin.clock import shift_meals
from chhaya.twin.fit import draw_ensemble
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import Fixed, simulate_ensemble
from chhaya.units import mmol_to_mgdl

AMOUNTS = [20, 30, 40, 50, 60, 70, 80, 90, 100]  # grams of carbohydrate offered
BEFORE_MIN, AFTER_MIN = 60, 360  # the window drawn around the meal


def simulate_meal(
    rec: Recording, out: Reveal, k_days: float, meal_t: float, carbs: float, n_members: int = 200
) -> dict[str, np.ndarray]:
    """The reveal's estimate and band with the meal logged at `meal_t` (minutes since the start) set to `carbs` g."""
    cfg = RevealConfig()
    meals = rec.meals.copy()
    at = (meals["t_min"] - meal_t).abs().idxmin()
    meals.loc[at, "carb_g"] = float(carbs)
    changed = rec.__class__(**{**rec.__dict__, "meals": meals})
    shifted = shift_meals(changed, int(out.metrics["meal_clock_offset_min"]))
    inp, obs_idx, _ = build_inputs(shifted)
    test = obs_idx >= k_days * 1440
    ens = mmol_to_mgdl(
        np.asarray(simulate_ensemble(jnp.asarray(draw_ensemble(out.fit, n_members, SEED)), inp, Fixed()).gi)[
            :, obs_idx
        ]
    )
    w = cfg.blend
    noise = np.random.default_rng(SEED).normal(
        0.0, out.metrics["sigma_res_mgdl"], (ens.shape[0], int(test.sum()))
    )
    est = w * ens[0, test] + (1.0 - w) * out.day
    lo, hi = np.quantile(w * ens[:, test] + (1.0 - w) * out.day + noise, [0.1, 0.9], axis=0)
    return {"t": obs_idx[test], "est": est, "lo": lo, "hi": hi}


def meal_whatif(rec: Recording, out: Reveal, k_days: float) -> dict:
    """The largest logged meal of the last day, at each offered amount, over the hours around it."""
    day_start = k_days * 1440.0 + (int(out.t_test.max() - k_days * 1440.0) // 1440) * 1440.0
    meals = rec.meals[(rec.meals["t_min"] >= day_start) & (rec.meals["t_min"] < day_start + 1440.0)]
    big = meals.loc[meals["carb_g"].idxmax()]
    window = (out.t_test >= big["t_min"] - BEFORE_MIN) & (out.t_test <= big["t_min"] + AFTER_MIN)
    series = {}
    for amount in AMOUNTS:
        s = simulate_meal(rec, out, k_days, big["t_min"], amount)
        series[str(amount)] = {k: [round(float(v), 1) for v in s[k][window]] for k in ("est", "lo", "hi")}
    return {
        "label": "simulation",
        "meal": {"t": float(big["t_min"] - day_start), "t_abs": float(big["t_min"]), "carbs": float(big["carb_g"]), "label": str(big["label"])},
        "day_meals": [{"t": float(r["t_min"] - day_start), "carbs": float(r["carb_g"]), "label": str(r["label"])} for _, r in meals.iterrows()],
        "amounts": AMOUNTS,
        "t": [float(t - day_start) for t in out.t_test[window]],
        "series": series,
    }  # fmt: skip
