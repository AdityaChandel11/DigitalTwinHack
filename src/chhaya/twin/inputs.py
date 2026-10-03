"""Turn a Recording into the arrays the twin integrates."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp
import numpy as np

from chhaya.data.schema import Recording
from chhaya.twin.model import Inputs, meal_window
from chhaya.units import mgdl_to_mmol


class SlowCoef(NamedTuple):
    """How much each gram of fat, protein and fibre slows carbohydrate appearance (population-level)."""

    fat: float = 0.010
    protein: float = 0.005
    fibre: float = 0.020


def _ok(v) -> bool:
    return v is not None and np.isfinite(v)


def build_inputs(rec: Recording, slow: SlowCoef = SlowCoef()) -> tuple[Inputs, np.ndarray, np.ndarray]:
    """Return (inputs, obs_idx, obs_mmol): model inputs plus the CGM minutes and values to fit against."""
    rec.validate()
    meals = rec.meals[rec.meals["carb_g"].notna() & (rec.meals["carb_g"] > 0)].sort_values("t_min")
    meal_t = meals["t_min"].to_numpy(dtype=float)
    macros = meals[["fat_g", "protein_g", "fibre_g"]].astype(float).fillna(0.0).to_numpy()
    meal_slow = 1.0 + macros @ np.array([slow.fat, slow.protein, slow.fibre])

    met = np.ones(rec.n_min)
    act = rec.activity[rec.activity["met"].notna()]
    if len(act):
        met[act["t_min"].to_numpy(dtype=int)] = np.clip(act["met"].to_numpy(dtype=float), 0.9, 18.0)

    weight = rec.static.get("weight_kg")
    ib = rec.static.get("fasting_insulin_uu_ml")
    obs_idx = rec.cgm["t_min"].to_numpy(dtype=int)
    obs_mmol = mgdl_to_mmol(rec.cgm["glucose_mgdl"].to_numpy(dtype=float))
    inp = Inputs(
        meal_t=jnp.asarray(np.append(meal_t, 0.0)),
        meal_carb_mg=jnp.asarray(np.append(meals["carb_g"].to_numpy(dtype=float) * 1000.0, 0.0)),
        meal_slow=jnp.asarray(np.append(meal_slow, 1.0)),
        meal_win=jnp.asarray(meal_window(meal_t, rec.n_min)),
        met=jnp.asarray(met),
        t0_min_of_day=float(rec.start.hour * 60 + rec.start.minute),
        body_mass=float(weight) if _ok(weight) else 70.0,
        ib=float(np.clip(ib, 2.0, 60.0)) if _ok(ib) else 10.0,
        g0=float(obs_mmol[0]),
    )
    return inp, obs_idx, obs_mmol
