"""THROWAWAY PROBE 3, DEVELOPMENT PATIENTS ONLY. Not a result; nothing here may be quoted.

Probes 1 and 2: reading by reading, fingersticks add little to the patient's own daily shape.
Question now: at the level a doctor reads (the glucose report for the period since the sensor came off:
mean glucose / GMI, time above 180, time in range, fasting level), does shape + fingersticks beat
  (a) the stale sensor report carried forward, and
  (b) the plain average of the fingersticks?
Estimator fixed before running: shrunk daily shape + one level shift = mean fingerstick residual.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm, wilcoxon

from chhaya.config import is_dev_patient
from chhaya.data import shanghai
from chhaya.eval.baselines import average_day_baseline, lodo_average_day

BIN = 30
recs = [r for r in shanghai.load_all() if is_dev_patient(r.patient_id)]


def profile(tod, g):
    return average_day_baseline(tod, g, np.arange(0, 1440, BIN) + BIN // 2, BIN)


def paired(r, lo, hi):
    ft = r.fingersticks["t_min"].to_numpy()
    fg = r.fingersticks["glucose_mgdl"].to_numpy()
    ct = r.cgm["t_min"].to_numpy()
    cg = r.cgm["glucose_mgdl"].to_numpy()
    m = (ft >= lo) & (ft < hi)
    ft, fg = ft[m], fg[m]
    if len(ft) == 0:
        return np.array([]), np.array([]), np.array([])
    j = np.clip(np.searchsorted(ct, ft), 1, len(ct) - 1)
    near = np.where(np.abs(ct[j] - ft) < np.abs(ct[j - 1] - ft), j, j - 1)
    ok = np.abs(ct[near] - ft) <= 10
    return ft[ok], fg[ok], cg[near][ok]


def thin(t_fs, days_fs, rule):
    keep = np.zeros(len(t_fs), dtype=bool)
    if rule == "all":
        keep[:] = True
        return keep
    for d in np.unique(days_fs):
        idx = np.where(days_fs == d)[0]
        if rule == "2/day":
            keep[idx[0]] = keep[idx[-1]] = True
        elif rule == "1/day (first)":
            keep[idx[0]] = True
        elif rule == "3-4/week (first)" and d % 2 == 0:
            keep[idx[0]] = True
    return keep


def metrics_from_trace(g):
    return {"mean": float(np.mean(g)), "tar": float(100 * np.mean(g > 180)), "tir": float(100 * np.mean((g >= 70) & (g <= 180)))}


rows = []
for k in (3, 5):
    split = k * 1440
    pool = [paired(r, 0, split) for r in recs]
    pf = np.concatenate([p[1] for p in pool])
    pc = np.concatenate([p[2] for p in pool])
    pop_b, pop_a = np.polyfit(pf, pc, 1)
    for r in recs:
        days = r.n_min / 1440.0
        ft_all = r.fingersticks["t_min"].to_numpy()
        if days < k + 2 or (ft_all >= split).sum() < 3 or len(ft_all) / days < 1.0:
            continue
        tod0 = r.start.hour * 60 + r.start.minute
        t = r.cgm["t_min"].to_numpy()
        g = r.cgm["glucose_mgdl"].to_numpy()
        cal, test = t < split, t >= split
        if cal.sum() < 96 * k * 0.5 or test.sum() < 96:
            continue
        tod_cal = tod0 + t[cal]
        prof = profile(tod_cal % 1440, g[cal])
        mean_cal = float(g[cal].mean())
        shr = 0.5 * prof + 0.5 * mean_cal
        at = lambda curve, tt: curve[((tod0 + tt) % 1440).astype(int) // BIN]  # noqa: E731
        sigma = float(np.std(g[cal] - (0.5 * lodo_average_day(tod_cal // 1440, tod_cal, g[cal]) + 0.5 * mean_cal)))
        _, cf, cc = paired(r, 0, split)
        if len(cf) >= 8 and np.ptp(cf) > 40:
            b = float(np.clip(np.polyfit(cf, cc, 1)[0], 0.6, 1.2))
            a = float(np.mean(cc - b * cf))
        else:
            b = pop_b
            a = float(np.mean(cc - pop_b * cf)) if len(cf) >= 3 else pop_a
        tt, truth = t[test], g[test]
        true_m = metrics_from_trace(truth)
        stale = metrics_from_trace(g[cal])
        fth_all, fgh_all, _ = paired(r, split, r.n_min + 1)
        days_h = (tod0 + fth_all) // 1440
        for rule in ("all", "2/day", "1/day (first)", "3-4/week (first)"):
            keep = thin(fth_all, days_h, rule)
            fth, fgh = fth_all[keep], fgh_all[keep]
            if len(fth) < 2:
                continue
            fs_sensor = a + b * fgh
            naive = {"mean": float(fs_sensor.mean()), "tar": float(100 * np.mean(fs_sensor > 180)), "tir": float(100 * np.mean((fs_sensor >= 70) & (fs_sensor <= 180)))}
            delta = float(np.mean(fs_sensor - at(shr, fth)))
            est = at(shr, tt) + delta
            p_hi = 1 - norm.cdf((180 - est) / sigma)
            p_lo = norm.cdf((70 - est) / sigma)
            ch = {"mean": float(est.mean()), "tar": float(100 * p_hi.mean()), "tir": float(100 * (1 - p_hi - p_lo).mean())}
            row = {"k": k, "rule": rule, "patient": r.patient_id, "n_fs": len(fth), "true_mean": true_m["mean"], "drift": true_m["mean"] - stale["mean"]}
            for name, m in (("stale", stale), ("naive", naive), ("chhaya", ch)):
                for key in ("mean", "tar", "tir"):
                    row[f"{name}_{key}"] = abs(m[key] - true_m[key])
            rows.append(row)

df = pd.DataFrame(rows)
for (k, rule), grp in df.groupby(["k", "rule"], sort=False):
    per = grp.groupby("patient").mean(numeric_only=True)
    print(f"\nk={k}, fingersticks {rule}: patients {len(per)}, fingersticks in hidden window median {per.n_fs.median():.0f}, |change in mean since calibration| median {per.drift.abs().median():.1f} mg/dL")
    for key, unit in (("mean", "mg/dL"), ("tar", "points"), ("tir", "points")):
        s, n, c = per[f"stale_{key}"], per[f"naive_{key}"], per[f"chhaya_{key}"]
        p1 = wilcoxon(c - s, alternative="less").pvalue
        p2 = wilcoxon(c - n, alternative="less").pvalue
        print(
            f"  abs error in {key:4s} ({unit}): stale report {s.median():5.1f} | fingerstick average {n.median():5.1f} | shape+fingersticks {c.median():5.1f}"
            f"   vs stale: better in {100 * (c < s).mean():3.0f} %, p {p1:.3g}; vs fingerstick average: better in {100 * (c < n).mean():3.0f} %, p {p2:.3g}"
        )
    if key:
        g_err = per["chhaya_mean"].median() * 0.02392
        print(f"  (mean error as GMI: stale {per['stale_mean'].median() * 0.02392:.2f} %, fingerstick average {per['naive_mean'].median() * 0.02392:.2f} %, shape+fingersticks {g_err:.2f} %)")
