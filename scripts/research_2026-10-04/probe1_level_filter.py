"""THROWAWAY PROBE, DEVELOPMENT PATIENTS ONLY. Not a result; nothing here may be quoted.

Question: after the sensor comes off, do real fingersticks rescue the estimate, and does the patient's own
sensor-derived daily shape add anything to the fingersticks (or the fingersticks to the shape)?

Shanghai test-split patients are never loaded into any estimator or score here.
Fixed before running: random-walk level, r = 18 mg/dL (within-patient sensor-fingerstick SD from the audit),
q = 15 mg/dL per sqrt(day). No tuning.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from chhaya.config import is_dev_patient
from chhaya.data import shanghai
from chhaya.eval.baselines import average_day_baseline

R_SD = 18.0
Q_PER_MIN = 15.0**2 / 1440.0
BIN = 30

recs = [r for r in shanghai.load_all() if is_dev_patient(r.patient_id)]
print(f"development recordings {len(recs)}, patients {len({r.patient_id for r in recs})}")


def profile(tod, g):
    """Average day as a 48-bin curve."""
    return average_day_baseline(tod, g, np.arange(0, 1440, BIN) + BIN // 2, BIN)


# population shape per patient, leaving that patient out (mean-centred daily shape of the other dev patients)
shapes = {}
for r in recs:
    tod = (r.start.hour * 60 + r.start.minute + r.cgm["t_min"].to_numpy()) % 1440
    g = r.cgm["glucose_mgdl"].to_numpy()
    p = profile(tod, g)
    shapes.setdefault(r.patient_id, []).append(p - p.mean())
pat_shape = {k: np.mean(v, axis=0) for k, v in shapes.items()}


def pop_shape(exclude: str) -> np.ndarray:
    return np.mean([v for k, v in pat_shape.items() if k != exclude], axis=0)


def kalman(t_obs, z, t_eval, smooth: bool):
    """Random-walk level observed at t_obs with noise R_SD; returns the level at t_eval.

    Causal: the filtered level at the last observation at or before each t_eval (0 before the first).
    Smoothed: RTS over the observations, linear between them, held flat outside.
    """
    if len(t_obs) == 0:
        return np.zeros(len(t_eval))
    m, P = 0.0, 30.0**2
    ms, Ps, mp, Pp = [], [], [], []
    last = t_obs[0]
    for t, y in zip(t_obs, z):
        P_pred = P + Q_PER_MIN * max(t - last, 0)
        K = P_pred / (P_pred + R_SD**2)
        mp.append(m)
        Pp.append(P_pred)
        m = m + K * (y - m)
        P = (1 - K) * P_pred
        ms.append(m)
        Ps.append(P)
        last = t
    ms, Ps, mp, Pp = map(np.array, (ms, Ps, mp, Pp))
    if not smooth:
        idx = np.searchsorted(t_obs, t_eval, side="right") - 1
        return np.where(idx >= 0, ms[np.clip(idx, 0, len(ms) - 1)], 0.0)
    sm = ms.copy()
    for i in range(len(ms) - 2, -1, -1):
        C = Ps[i] / Pp[i + 1]
        sm[i] = ms[i] + C * (sm[i + 1] - mp[i + 1])
    return np.interp(t_eval, t_obs, sm)


def thin(t_fs, days_fs, rule: str) -> np.ndarray:
    keep = np.zeros(len(t_fs), dtype=bool)
    if rule == "all":
        keep[:] = True
    else:
        for d in np.unique(days_fs):
            idx = np.where(days_fs == d)[0]
            if rule == "2/day":
                keep[idx[0]] = keep[idx[-1]] = True
            elif rule == "1/day":
                keep[idx[0]] = True
            elif rule == "3-4/week" and d % 2 == 0:
                keep[idx[0]] = True
    return keep


def rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


# development-wide sensor-minus-fingerstick offset from calibration-window pairs (fallback for a patient with few pairs)
def pairs(r, t_max=None):
    ft = r.fingersticks["t_min"].to_numpy()
    fg = r.fingersticks["glucose_mgdl"].to_numpy()
    ct = r.cgm["t_min"].to_numpy()
    cg = r.cgm["glucose_mgdl"].to_numpy()
    if t_max is not None:
        m = ft < t_max
        ft, fg = ft[m], fg[m]
    if len(ft) == 0:
        return np.array([])
    j = np.clip(np.searchsorted(ct, ft), 1, len(ct) - 1)
    near = np.where(np.abs(ct[j] - ft) < np.abs(ct[j - 1] - ft), j, j - 1)
    ok = np.abs(ct[near] - ft) <= 10
    return cg[near][ok] - fg[ok]


rows = []
for k in (3, 5):
    split = k * 1440
    pop_off = float(np.mean(np.concatenate([pairs(r, split) for r in recs] + [np.array([])])))
    for r in recs:
        days = r.n_min / 1440.0
        ft_all = r.fingersticks["t_min"].to_numpy()
        fg_all = r.fingersticks["glucose_mgdl"].to_numpy()
        hid = ft_all >= split
        if days < k + 2 or hid.sum() < 3 or len(ft_all) / days < 1.0:
            continue
        tod0 = r.start.hour * 60 + r.start.minute
        t = r.cgm["t_min"].to_numpy()
        g = r.cgm["glucose_mgdl"].to_numpy()
        cal, test = t < split, t >= split
        if cal.sum() < 96 * k * 0.5 or test.sum() < 96:
            continue
        prof = profile((tod0 + t[cal]) % 1440, g[cal])
        mean = float(g[cal].mean())
        shr = 0.5 * prof + 0.5 * mean
        at = lambda curve, tt: curve[((tod0 + tt) % 1440).astype(int) // BIN]  # noqa: E731
        d_cal = pairs(r, split)
        off = float(d_cal.mean()) if len(d_cal) >= 3 else pop_off
        truth = g[test]
        tt = t[test]
        base = {"day": at(prof, tt), "shrunk": at(shr, tt), "mean": np.full(test.sum(), mean)}
        # the never-wore-a-sensor variant: population shape, level from fingersticks alone (from day 0)
        pshape = pop_shape(r.patient_id)
        for rule in ("all", "2/day", "1/day", "3-4/week"):
            keep = thin(ft_all, (tod0 + ft_all) // 1440, rule)
            fth, fgh = ft_all[keep & hid], fg_all[keep & hid]
            if len(fth) < 2:
                continue
            fs_sensor = fgh + off
            est = dict(base)
            idx = np.searchsorted(fth, tt, side="right") - 1
            est["locf"] = np.where(idx >= 0, fs_sensor[np.clip(idx, 0, len(fth) - 1)], base["shrunk"])
            est["interp"] = np.interp(tt, fth, fs_sensor)
            z = fs_sensor - at(shr, fth)
            est["shape+kf"] = base["shrunk"] + kalman(fth, z, tt, smooth=False)
            est["shape+rts"] = base["shrunk"] + kalman(fth, z, tt, smooth=True)
            zm = fs_sensor - mean
            est["mean+kf"] = mean + kalman(fth, zm, tt, smooth=False)
            # no sensor ever: fingersticks from the whole recording, population offset and shape
            fta, fga = ft_all[keep], fg_all[keep] + pop_off
            lvl0 = float(np.mean(fga[fta < split])) if (fta < split).sum() else float(np.mean(fga))
            zp = fga - (lvl0 + at(pshape, fta))
            est["popshape+kf(no sensor)"] = lvl0 + at(pshape, tt) + kalman(fta, zp, tt, smooth=False)
            est["popshape+rts(no sensor)"] = lvl0 + at(pshape, tt) + kalman(fta, zp, tt, smooth=True)
            row = {"k": k, "rule": rule, "rec": r.rec_id, "patient": r.patient_id, "n_fs_hidden": len(fth), "hidden_days": (tt.max() - split) / 1440.0}
            row.update({name: rmse(e, truth) for name, e in est.items()})
            rows.append(row)

df = pd.DataFrame(rows)
names = ["mean", "day", "shrunk", "locf", "interp", "mean+kf", "shape+kf", "shape+rts", "popshape+kf(no sensor)", "popshape+rts(no sensor)"]
for (k, rule), grp in df.groupby(["k", "rule"], sort=False):
    per = grp.groupby("patient")[names + ["n_fs_hidden", "hidden_days"]].mean()
    print(f"\nk={k} fingersticks={rule}: patients {len(per)}, fingersticks per hidden day {float((per.n_fs_hidden / per.hidden_days).median()):.1f}")
    print("  median RMSE mg/dL: " + ", ".join(f"{n} {per[n].median():.1f}" for n in names))
    for a, b in (("shape+kf", "shrunk"), ("shape+kf", "locf"), ("shape+kf", "mean+kf"), ("shape+rts", "interp"), ("shape+kf", "popshape+kf(no sensor)")):
        d = per[a] - per[b]
        p = wilcoxon(d, alternative="less").pvalue if len(d) >= 6 and (d != 0).any() else float("nan")
        print(f"    {a} vs {b}: median diff {d.median():+.1f}, better in {100 * (d < 0).mean():.0f} %, one-sided p {p:.3g}")
