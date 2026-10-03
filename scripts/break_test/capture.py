"""Break test, compute stage. Runs the committed estimator on real patients and captures everything
needed to attack the Gate 2 claim offline.

Task kinds
  main   : k = 5 reveal for every patient, plus placebo inputs, sample reconstruction, second-sensor data
  shift1 : the same reveal with the first day of the recording dropped (different calibration window)
  leak   : real-data leakage and causality attacks on four patients

Usage: python capture.py out.pkl [workers]
"""

import dataclasses
import pickle
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor

import jax.numpy as jnp
import numpy as np
import pandas as pd

from chhaya.config import SEED, is_dev_patient
from chhaya.data.cgmacros import load_all
from chhaya.eval.reveal import run_reveal
from chhaya.twin.clock import shift_meals
from chhaya.twin.fit import draw_ensemble
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import Fixed, meal_window, simulate_ensemble, simulate_jit
from chhaya.units import mmol_to_mgdl

K = 5
SPLIT = K * 1440
FRAMES = ("cgm", "cgm_ref", "fingersticks", "meals", "activity", "doses")


def crop_start(rec, t0):
    def cut(df):
        d = df[df["t_min"] >= t0].copy()
        d["t_min"] = d["t_min"] - t0
        return d.reset_index(drop=True)

    return dataclasses.replace(
        rec,
        start=rec.start + pd.Timedelta(minutes=t0),
        n_min=rec.n_min - t0,
        **{f: cut(getattr(rec, f)) for f in FRAMES},
    )


def crop_end(rec, n_new):
    return dataclasses.replace(
        rec,
        n_min=n_new,
        **{f: getattr(rec, f)[getattr(rec, f)["t_min"] < n_new].reset_index(drop=True) for f in FRAMES},
    )


def ode_trace(rec, z):
    inp, _, _ = build_inputs(rec)
    return mmol_to_mgdl(np.asarray(simulate_jit(jnp.asarray(z), inp).gi))


def base_info(rec):
    return dict(
        rec=rec.rec_id,
        group=rec.static.get("group"),
        dev=is_dev_patient(rec.patient_id),
        primary_sensor=rec.static.get("primary_sensor"),
        activity_source=rec.static.get("activity_source"),
        amount_unit=rec.static.get("amount_consumed_unit"),
        days=rec.n_min / 1440.0,
    )


def main_task(rec):
    out = run_reveal(rec, K, n_members=200)
    info = dict(kind="main", **base_info(rec))
    if out is None:
        return dict(info, skipped=True)
    off = int(out.metrics["meal_clock_offset_min"])
    rs = shift_meals(rec, off)  # the recording as run_reveal simulated it
    z = out.fit.z_map
    idx = out.t_test
    tod0 = rec.start.hour * 60 + rec.start.minute
    inp_s, _, _ = build_inputs(rs)
    full = ode_trace(rs, z)
    check_ode = float(np.max(np.abs(full[idx] - out.ode)))

    m = rs.meals
    in_test = m["t_min"] >= SPLIT
    # placebo 1: no meal log at all once the sensor is off
    p_none = ode_trace(dataclasses.replace(rs, meals=m[~in_test]), z)[idx]
    # placebo 2: the right meals at the wrong time (6 hours late)
    m2 = m.copy()
    m2.loc[in_test, "t_min"] = m2.loc[in_test, "t_min"] + 360
    m2 = m2[m2["t_min"] < rs.n_min]
    p_late = ode_trace(dataclasses.replace(rs, meals=m2), z)[idx]
    # placebo 3: habitual meals, i.e. each hidden day replays a calibration day of the same patient
    cal_m = m[~in_test]
    parts = [cal_m]
    for d in range(int(np.ceil((rs.n_min - SPLIT) / 1440))):
        s = d % K
        src = cal_m[(cal_m["t_min"] >= s * 1440) & (cal_m["t_min"] < (s + 1) * 1440)]
        parts.append(src.assign(t_min=src["t_min"] + (K + d - s) * 1440))
    m3 = pd.concat(parts, ignore_index=True)
    m3 = m3[m3["t_min"] < rs.n_min]
    p_habit = ode_trace(dataclasses.replace(rs, meals=m3), z)[idx]
    # placebo 4: the band reports rest once the sensor is off
    act = rs.activity.copy()
    act.loc[act["t_min"] >= SPLIT, "met"] = 1.0
    p_rest = ode_trace(dataclasses.replace(rs, activity=act), z)[idx]

    # does the 6-meal window silently drop meals? compare with a window that cannot overflow
    meal_t = np.asarray(inp_s.meal_t)[:-1]
    wide = inp_s._replace(meal_win=jnp.asarray(meal_window(meal_t, rs.n_min, width=24)))
    full_wide = mmol_to_mgdl(np.asarray(simulate_jit(jnp.asarray(z), wide).gi))
    win_diff = float(np.max(np.abs(full_wide - full)))
    srt = np.sort(meal_t)
    max_in_12h = int(
        max((np.searchsorted(srt, t + 720, side="right") - i for i, t in enumerate(srt)), default=0)
    )
    max_in_5h = int(
        max((np.searchsorted(srt, t + 300, side="right") - i for i, t in enumerate(srt)), default=0)
    )

    # rebuild the predictive samples exactly as run_reveal does, to get distribution-based summaries
    zs = draw_ensemble(out.fit, 200, SEED)
    ens = mmol_to_mgdl(np.asarray(simulate_ensemble(jnp.asarray(zs), inp_s, Fixed()).gi)[:, idx])
    sigma = out.metrics["sigma_res_mgdl"]
    noise = np.random.default_rng(SEED).normal(0.0, sigma, (200, idx.size))
    samples = 0.5 * ens + 0.5 * out.day + noise
    lo2, hi2 = np.quantile(samples, [0.1, 0.9], axis=0)
    check_band = float(max(np.abs(lo2 - out.lo).max(), np.abs(hi2 - out.hi).max()))
    pred = dict(
        tir=float(100 * np.mean((samples >= 70) & (samples <= 180))),
        tbr=float(100 * np.mean(samples < 70)),
        tar=float(100 * np.mean(samples > 180)),
        ens_sd=float(np.mean(ens.std(axis=0))),
    )

    ref = None
    if len(rec.cgm_ref):
        rt = rec.cgm_ref["t_min"].to_numpy(dtype=float)
        rg = rec.cgm_ref["glucose_mgdl"].to_numpy(dtype=float)

        def ref_at(t):
            j = np.searchsorted(rt, t)
            near = np.minimum(
                np.abs(rt[np.clip(j - 1, 0, rt.size - 1)] - t), np.abs(rt[np.clip(j, 0, rt.size - 1)] - t)
            )
            return np.interp(t, rt, rg), near <= 10

        ref_test, ok_test = ref_at(idx)
        ref_cal, ok_cal = ref_at(out.cal_t)
        ref = dict(
            test=ref_test,
            ok_test=ok_test,
            cal=ref_cal,
            ok_cal=ok_cal,
            t_first=float(rt[0]),
            t_last=float(rt[-1]),
        )

    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    second = np.abs(g[:-2] - 2 * g[1:-1] + g[2:]) < 1e-6
    run, longest, in_runs = 0, 0, 0
    for flag in second:
        run = run + 1 if flag else 0
        longest = max(longest, run)
        in_runs += run >= 4
    return dict(
        info,
        skipped=False,
        metrics=out.metrics,
        z=z,
        tod0=tod0,
        offset=off,
        sigma=sigma,
        t_test=idx,
        truth=out.truth,
        twin=out.twin,
        ode=out.ode,
        day=out.day,
        mean=out.mean,
        lo=out.lo,
        hi=out.hi,
        cal_t=out.cal_t,
        cal_truth=out.cal_truth,
        cal_ode=out.cal_ode,
        p_none=p_none,
        p_late=p_late,
        p_habit=p_habit,
        p_rest=p_rest,
        meal_t=m["t_min"].to_numpy(dtype=float),
        meal_carb=m["carb_g"].to_numpy(dtype=float),
        check_ode=check_ode,
        check_band=check_band,
        win_diff=win_diff,
        max_in_12h=max_in_12h,
        max_in_5h=max_in_5h,
        pred=pred,
        ref=ref,
        linear_longest=int(longest),
        linear_frac=float(in_runs / max(second.size, 1)),
        cgm_t_last=int(rec.cgm["t_min"].iloc[-1]),
        n_meals=int(len(m)),
    )


def shift_task(rec):
    out = run_reveal(crop_start(rec, 1440), K, n_members=30)
    return dict(kind="shift1", **base_info(rec), metrics=None if out is None else out.metrics)


def leak_task(rec):
    rng = np.random.default_rng(7)
    base = run_reveal(rec, K, n_members=40)
    # (a) scramble every hidden reading of both sensors
    cgm = rec.cgm.copy()
    hid = cgm["t_min"] >= SPLIT
    cgm.loc[hid, "glucose_mgdl"] = rng.uniform(40.0, 400.0, int(hid.sum()))
    ref = rec.cgm_ref.copy()
    if len(ref):
        hr = ref["t_min"] >= SPLIT
        ref.loc[hr, "glucose_mgdl"] = rng.uniform(40.0, 400.0, int(hr.sum()))
    a = run_reveal(dataclasses.replace(rec, cgm=cgm, cgm_ref=ref), K, n_members=40)
    same = {
        f: bool(np.array_equal(getattr(base, f), getattr(a, f)))
        for f in ("twin", "ode", "day", "mean", "lo", "hi")
    }
    same["z_map"] = bool(np.array_equal(base.fit.z_map, a.fit.z_map))
    same["offset"] = base.metrics["meal_clock_offset_min"] == a.metrics["meal_clock_offset_min"]
    same["truth_changed"] = not np.array_equal(base.truth, a.truth)
    # (b) cut the recording 1.5 days after the split: earlier estimates must not move
    n_new = SPLIT + 2160
    b = run_reveal(crop_end(rec, n_new), K, n_members=40)
    common = base.t_test < n_new
    same_len = bool(common.sum() == b.t_test.size)
    trunc = dict(
        n_common=int(common.sum()), same_len=same_len, twin=float("nan"), lo=float("nan"), hi=float("nan")
    )
    if same_len:
        trunc.update(
            twin=float(np.max(np.abs(base.twin[common] - b.twin))),
            lo=float(np.max(np.abs(base.lo[common] - b.lo))),
            hi=float(np.max(np.abs(base.hi[common] - b.hi))),
        )
    # (c) positive control: move one calibration reading and the estimate must move
    cgm2 = rec.cgm.copy()
    i = cgm2.index[cgm2["t_min"] >= SPLIT // 2][0]
    cgm2.loc[i, "glucose_mgdl"] = min(cgm2.loc[i, "glucose_mgdl"] + 80.0, 590.0)
    c = run_reveal(dataclasses.replace(rec, cgm=cgm2), K, n_members=40)
    control = float(np.max(np.abs(base.twin - c.twin)))
    return dict(kind="leak", **base_info(rec), same=same, trunc=trunc, control=control)


TASKS = {"main": main_task, "shift1": shift_task, "leak": leak_task}


def work(task):
    kind, rec = task
    try:
        return TASKS[kind](rec)
    except Exception:  # a crash is itself a finding
        return dict(kind=kind, rec=rec.rec_id, error=traceback.format_exc())


if __name__ == "__main__":
    recs = load_all()
    dev = [r for r in recs if is_dev_patient(r.patient_id)]
    test = [r for r in recs if not is_dev_patient(r.patient_id)]
    tasks = (
        [("leak", r) for r in dev[:2] + test[:2]]
        + [("main", r) for r in recs]
        + [("shift1", r) for r in recs]
    )
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    res = []
    with ProcessPoolExecutor(workers) as pool:
        for n, r in enumerate(pool.map(work, tasks), 1):
            res.append(r)
            print(n, len(tasks), r["kind"], r["rec"], "ERROR" if "error" in r else "ok", flush=True)
            if n % 10 == 0 or n == len(tasks):
                pickle.dump(res, open(sys.argv[1], "wb"))
    print("done", len(res), "errors", sum("error" in r for r in res))
