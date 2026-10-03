import dataclasses

import jax.numpy as jnp
import numpy as np
import pandas as pd

from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import Fixed, default_z, meal_window, simulate_ensemble, simulate_jit, unpack
from chhaya.twin.priors import BOX_SD, population_prior


def _sim(rec, z=None):
    inp, _, _ = build_inputs(rec)
    return inp, simulate_jit(jnp.asarray(default_z() if z is None else z), inp)


def test_fasting_rest_is_a_steady_state(rec):
    inp, _, _ = build_inputs(
        dataclasses.replace(rec, meals=rec.meals.iloc[:0], activity=rec.activity.iloc[:0])
    )
    z = default_z()
    z[4] = -30.0  # no dawn effect
    inp = inp._replace(g0=float(np.exp(z[3])))
    tr = simulate_jit(jnp.asarray(z), inp)
    assert np.allclose(np.asarray(tr.g), np.exp(z[3]), atol=1e-6)
    assert np.allclose(np.asarray(tr.ins), inp.ib, atol=1e-6)


def test_a_meal_raises_glucose_and_it_comes_back(rec):
    _, tr = _sim(rec)
    day2 = np.asarray(tr.gi)[1440:2880]
    assert day2.max() - day2.min() > 2.0  # mmol/L excursion from three meals
    assert day2[7 * 60] < day2.max() - 1.5  # by 07:00 the overnight fast has brought it down


def test_more_carbohydrate_gives_a_higher_peak(rec):
    _, base = _sim(rec)
    bigger = dataclasses.replace(rec, meals=rec.meals.assign(carb_g=rec.meals["carb_g"] * 1.5))
    _, more = _sim(bigger)
    assert float(more.gi.max()) > float(base.gi.max()) + 0.5


def test_exercise_lowers_glucose(rec):
    _, active = _sim(rec)
    _, resting = _sim(dataclasses.replace(rec, activity=rec.activity.assign(met=1.0)))
    assert float(active.gi.mean()) < float(resting.gi.mean())


def test_insulin_independent_uptake_never_negative():
    fx = Fixed()
    for ib in (2.0, 12.0, 60.0):
        for z1 in (-6.0, 0.0, 6.0):
            z = default_z()
            z[1] = z1
            p = unpack(jnp.asarray(z), ib, fx)
            c11 = fx.gbliv * (fx.km + p.gb) / p.gb - p.k5 * fx.beta * ib
            assert float(c11) >= 0.0


def test_stays_finite_everywhere_the_optimiser_may_go(rec):
    inp, _, _ = build_inputs(rec)
    prior = population_prior()
    rng = np.random.default_rng(0)
    zs = prior.mu + prior.sd * rng.uniform(-BOX_SD, BOX_SD, (128, prior.mu.size))
    gi = np.asarray(simulate_ensemble(jnp.asarray(zs), inp, Fixed()).gi)
    assert np.isfinite(gi).all()
    assert gi.min() >= 0.5 and gi.max() < 100.0  # mmol/L: absurd corners stay bounded, never NaN


def test_meal_window_lists_recent_meals_only():
    win = meal_window([100.0, 400.0], n_steps=1500, width=3, horizon_min=720.0)
    assert set(win[50]) == {2}  # nothing eaten yet: only the dummy index
    assert set(win[100]) == {0, 2}  # the meal at minute 100 starts inside step 100
    assert set(win[500]) == {0, 1, 2}
    assert set(win[900]) == {1, 2}  # the first meal is more than 12 h old
    assert set(win[1400]) == {2}


def test_meal_window_with_no_meals():
    win = meal_window([], n_steps=10)
    assert win.shape == (10, 6) and (win == 0).all()


def test_meal_window_grows_so_that_no_recent_meal_is_dropped():
    burst = [600.0 + 10.0 * i for i in range(12)]  # twelve items logged within two hours
    win = meal_window(burst, n_steps=1500)
    assert win.shape[1] >= 12
    assert set(range(12)) <= set(win[800].tolist())  # all twelve are still being absorbed at minute 800
    assert meal_window([100.0, 400.0], n_steps=1500).shape[1] == 6  # an ordinary log keeps the small window


def test_every_item_of_a_busy_meal_log_reaches_the_simulation(rec):
    burst = pd.concat(
        [rec.meals.iloc[:1].assign(t_min=600.0 + 10.0 * i, carb_g=20.0) for i in range(12)], ignore_index=True
    )
    inp, _, _ = build_inputs(dataclasses.replace(rec, meals=burst))
    z = jnp.asarray(default_z())
    exhaustive = inp._replace(
        meal_win=jnp.asarray(meal_window(np.asarray(inp.meal_t)[:-1], rec.n_min, width=24))
    )
    assert np.allclose(np.asarray(simulate_jit(z, inp).gi), np.asarray(simulate_jit(z, exhaustive).gi))
