import dataclasses

import jax.numpy as jnp
import numpy as np
import pytest

from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import default_z, simulate_jit
from chhaya.units import mgdl_to_mmol


def test_shapes_and_observations(rec):
    inp, obs_idx, obs_mmol = build_inputs(rec)
    assert inp.met.shape == (rec.n_min,)
    assert inp.meal_win.shape[0] == rec.n_min
    assert inp.meal_t.shape[0] == len(rec.meals) + 1  # the zero-carb dummy
    assert float(inp.meal_carb_mg[-1]) == 0.0
    assert (np.asarray(inp.meal_slow) >= 1.0).all()
    assert obs_idx.shape == obs_mmol.shape == (len(rec.cgm),)
    assert obs_mmol[0] == mgdl_to_mmol(rec.cgm["glucose_mgdl"].iloc[0]) == inp.g0


def test_missing_weight_and_insulin_fall_back_to_reference_adult(rec):
    bare = dataclasses.replace(rec, static={"weight_kg": float("nan"), "fasting_insulin_uu_ml": None})
    inp, _, _ = build_inputs(bare)
    assert inp.body_mass == 70.0 and inp.ib == 10.0


def test_implausible_fasting_insulin_is_clipped(rec):
    inp, _, _ = build_inputs(dataclasses.replace(rec, static={**rec.static, "fasting_insulin_uu_ml": 400.0}))
    assert inp.ib == 60.0


def test_meals_without_carbohydrate_values_are_ignored(rec):
    text_only = rec.meals.assign(carb_g=np.nan)
    inp, _, _ = build_inputs(dataclasses.replace(rec, meals=text_only))
    assert inp.meal_t.shape[0] == 1
    assert np.isfinite(np.asarray(simulate_jit(jnp.asarray(default_z()), inp).gi)).all()


def test_gaps_in_the_band_count_as_rest(rec):
    half = rec.activity[rec.activity["t_min"] < rec.n_min // 2]
    inp, _, _ = build_inputs(dataclasses.replace(rec, activity=half))
    assert (np.asarray(inp.met)[rec.n_min // 2 :] == 1.0).all()


@pytest.mark.parametrize("weight", [0.0, -70.0, 12.0, 5000.0])
def test_implausible_body_weight_falls_back_to_reference_adult(rec, weight):
    inp, _, _ = build_inputs(dataclasses.replace(rec, static={**rec.static, "weight_kg": weight}))
    assert inp.body_mass == 70.0
    assert np.isfinite(np.asarray(simulate_jit(jnp.asarray(default_z()), inp).gi)).all()


def test_plausible_extremes_of_body_weight_are_kept(rec):
    for weight in (35.0, 180.0):
        inp, _, _ = build_inputs(dataclasses.replace(rec, static={**rec.static, "weight_kg": weight}))
        assert inp.body_mass == weight


def test_negative_macros_cannot_speed_up_or_break_absorption(rec):
    bad = rec.meals.assign(fat_g=-200.0, protein_g=-50.0, fibre_g=-10.0)
    inp, _, _ = build_inputs(dataclasses.replace(rec, meals=bad))
    assert (np.asarray(inp.meal_slow) == 1.0).all()
    assert np.isfinite(np.asarray(simulate_jit(jnp.asarray(default_z()), inp).gi)).all()
