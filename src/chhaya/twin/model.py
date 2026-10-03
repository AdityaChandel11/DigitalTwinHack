"""T2D glucose-insulin twin core.

Structure follows E-DES (Maas et al. 2015; CGM form of Erdos et al. 2023): gut, plasma glucose,
plasma insulin with glucose-driven endogenous secretion, interstitial glucose. Added here: a
circadian term on hepatic output and an exercise term on insulin-dependent uptake.

Units: time min, glucose mmol/L, insulin mU/L, gut glucose mg.
"""

from __future__ import annotations

from typing import NamedTuple

import jax
import jax.numpy as jnp
import numpy as np

jax.config.update("jax_enable_x64", True)

N_THETA = 7
THETA_NAMES = ("log_k1", "logit_fit", "log_k6", "log_gb", "logit_dawn", "log_kex", "log_bmeal")


class Fixed(NamedTuple):
    """Population constants. Values follow the published E-DES reference implementation."""

    k2: float = 0.633  # 1/min, gut -> plasma
    k3: float = 5.0e-5  # 1/min, hepatic response to glucose deviation
    k4: float = 1.0e-3  # hepatic response to insulin deviation
    k7: float = 1.15  # basal secretion gain
    k8: float = 4.71  # derivative secretion gain
    k9: float = 1.08e-2  # 1/min, insulin loss to interstitium
    sigma: float = 1.35  # Weibull shape of meal appearance
    km: float = 0.63  # mmol/L, Michaelis constant of glucose uptake
    f: float = 0.005551  # mmol per mg glucose
    vg: float = 17.0 / 70.0  # L/kg glucose distribution volume
    gbliv: float = 0.043  # mmol/L/min basal hepatic output
    beta: float = 1.0
    tau_i: float = 31.0  # min
    tau_d: float = 3.0  # min
    g_th: float = 10.0  # mmol/L renal threshold
    c1: float = 0.1  # renal clearance constant
    tau_g: float = 10.0  # min, plasma -> interstitial (CGM) lag
    tau_ex: float = 45.0  # min, exercise effect time constant
    met_rest: float = 1.5  # METs below this count as rest
    dawn_peak_min: float = 300.0  # minute of day of peak hepatic output (05:00)
    dawn_max: float = 0.5  # upper bound of dawn amplitude


class Inputs(NamedTuple):
    meal_t: jnp.ndarray  # (M+1,) minutes from t=0; last entry is a zero-carb dummy
    meal_carb_mg: jnp.ndarray  # (M+1,) carbohydrate as mg glucose
    meal_slow: jnp.ndarray  # (M+1,) >=1, divisor on k1 from fat/protein/fibre
    meal_win: jnp.ndarray  # (T, W) int, indices of meals that can still be absorbing at minute t
    met: jnp.ndarray  # (T,) METs per minute (1.0 = rest)
    t0_min_of_day: float  # clock minute at t=0
    body_mass: float  # kg
    ib: float  # mU/L fasting insulin
    g0: float  # mmol/L glucose at t=0


class Params(NamedTuple):
    k1: jnp.ndarray
    k5: jnp.ndarray
    k6: jnp.ndarray
    gb: jnp.ndarray
    dawn: jnp.ndarray
    kex: jnp.ndarray
    bmeal: jnp.ndarray
    fit: jnp.ndarray  # insulin-mediated fraction of basal glucose disposal


class Trajectory(NamedTuple):
    g: jnp.ndarray  # (T,) plasma glucose mmol/L
    gi: jnp.ndarray  # (T,) interstitial (CGM) glucose mmol/L
    ins: jnp.ndarray  # (T,) plasma insulin mU/L


def unpack(z: jnp.ndarray, ib: float, fx: Fixed = Fixed()) -> Params:
    """Map the unconstrained vector z to physical parameters.

    k5 is expressed as a fraction of its largest admissible value so that the
    insulin-independent uptake constant c11 can never go negative.
    """
    gb = jnp.exp(z[3])
    fit = jax.nn.sigmoid(z[1])
    k5_max = fx.gbliv * (fx.km + gb) / (gb * fx.beta * ib)
    return Params(
        k1=jnp.exp(z[0]),
        k5=fit * k5_max,
        k6=jnp.exp(z[2]),
        gb=gb,
        dawn=fx.dawn_max * jax.nn.sigmoid(z[4]),
        kex=jnp.exp(z[5]),
        bmeal=jnp.exp(z[6]),
        fit=fit,
    )


def default_z() -> np.ndarray:
    """Reference adult with T2D-leaning values: the population prior mean until one is learned."""
    return np.array([np.log(0.012), 0.0, np.log(0.25), np.log(7.0), -1.4, np.log(0.15), 0.0])


def meal_window(meal_t, n_steps: int, width: int = 6, horizon_min: float = 720.0) -> np.ndarray:
    """For each minute, indices of up to `width` most recent meals started within `horizon_min`.

    Unused slots hold len(meal_t), the index of the zero-carb dummy the caller appends.
    """
    meal_t = np.asarray(meal_t, dtype=float)
    dummy = meal_t.size
    win = np.full((n_steps, width), dummy, dtype=np.int32)
    if dummy == 0:
        return win
    order = np.argsort(meal_t, kind="stable")
    t_end = np.arange(n_steps) + 1.0
    hi = np.searchsorted(meal_t[order], t_end, side="left")  # meals with meal_t < t + 1
    for j in range(width):
        k = hi - 1 - j
        idx = order[np.clip(k, 0, dummy - 1)]
        recent = (k >= 0) & (t_end - meal_t[idx] <= horizon_min)
        win[:, j] = np.where(recent, idx, dummy)
    return win


def _weibull(tau, k1, sigma):
    pos = tau > 0.0
    ts = jnp.where(pos, tau, 1.0)
    w = sigma * k1**sigma * ts ** (sigma - 1.0) * jnp.exp(-((k1 * ts) ** sigma))
    return jnp.where(pos, w, 0.0)


def _derivs(x, t, met, win, p: Params, inp: Inputs, fx: Fixed):
    mg, g, ins, gi, ex = x
    k1_m = p.k1 / inp.meal_slow[win]
    mgmeal = p.bmeal * jnp.sum(_weibull(t - inp.meal_t[win], k1_m, fx.sigma) * inp.meal_carb_mg[win])
    d_mg = mgmeal - fx.k2 * mg

    tod = inp.t0_min_of_day + t
    circ = 1.0 + p.dawn * jnp.cos(2.0 * jnp.pi * (tod - fx.dawn_peak_min) / 1440.0)
    gliv = jnp.maximum(fx.gbliv * circ - fx.k3 * (g - p.gb) - fx.k4 * fx.beta * (ins - inp.ib), 0.0)
    ggut = fx.k2 * fx.f / (fx.vg * inp.body_mass) * mg
    sat = g / (fx.km + g)
    c11 = fx.gbliv * (fx.km + p.gb) / p.gb - p.k5 * fx.beta * inp.ib
    gnonit = c11 * sat
    git = p.k5 * fx.beta * ins * sat * (1.0 + p.kex * ex)
    gren = fx.c1 / (fx.vg * inp.body_mass) * jnp.maximum(g - fx.g_th, 0.0)
    d_g = gliv + ggut - gnonit - git - gren

    ipnc = jnp.maximum(
        (p.k6 * (g - p.gb) + (fx.k7 / fx.tau_i) * p.gb + fx.k8 * fx.tau_d * d_g) / fx.beta, 0.0
    )
    iliv = fx.k7 * p.gb / (fx.beta * fx.tau_i * inp.ib) * ins
    iif = fx.k9 * (ins - inp.ib)
    d_ins = ipnc - iliv - iif

    d_gi = (g - gi) / fx.tau_g
    d_ex = (jnp.maximum(met - fx.met_rest, 0.0) - ex) / fx.tau_ex
    return jnp.stack([d_mg, d_g, d_ins, d_gi, d_ex])


_FLOOR = jnp.array([0.0, 0.5, 0.0, 0.5, 0.0])


def simulate(z: jnp.ndarray, inp: Inputs, fx: Fixed = Fixed()) -> Trajectory:
    """Integrate the twin on a 1-minute grid with RK4. Output index i is the state at minute i."""
    p = unpack(z, inp.ib, fx)
    x0 = jnp.array([0.0, inp.g0, inp.ib, inp.g0, 0.0])

    def step(x, tm):
        t, met, win = tm
        a = _derivs(x, t, met, win, p, inp, fx)
        b = _derivs(x + 0.5 * a, t + 0.5, met, win, p, inp, fx)
        c = _derivs(x + 0.5 * b, t + 0.5, met, win, p, inp, fx)
        d = _derivs(x + c, t + 1.0, met, win, p, inp, fx)
        x_new = jnp.maximum(x + (a + 2.0 * b + 2.0 * c + d) / 6.0, _FLOOR)
        return x_new, x

    ts = jnp.arange(inp.met.shape[0], dtype=jnp.float64)
    _, xs = jax.lax.scan(step, x0, (ts, inp.met, inp.meal_win))
    return Trajectory(g=xs[:, 1], gi=xs[:, 3], ins=xs[:, 2])


simulate_jit = jax.jit(simulate)
simulate_ensemble = jax.jit(jax.vmap(simulate, in_axes=(0, None, None)))
