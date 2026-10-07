"""THROWAWAY PROBE 2, DEVELOPMENT PATIENTS ONLY. Not a result; nothing here may be quoted.

Probe 1 found that a random-walk level fed by fingersticks does not beat the fingerstick-free control.
Three follow-up questions, each fixed before running (two filter designs, no grid search):
  1. Headroom: how much could a perfect daily level correction help at all?
  2. Does a better observation model (linear sensor-vs-fingerstick map) and a decaying deviation help?
  3. Against the fingerstick itself (the clinical reference), how far is the estimate, next to a real sensor?
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from chhaya.config import is_dev_patient
from chhaya.data import shanghai
from chhaya.eval.baselines import average_day_baseline

BIN = 30
R_SD = 15.0
TAU = 120.0  # minutes: how long a deviation seen at a fingerstick persists
FAST_SD = 25.0
SLOW_Q = 8.0**2 / 1440.0  # slow level: 8 mg/dL per sqrt(day)

recs = [r for r in shanghai.load_all() if is_dev_patient(r.patient_id)]


def profile(tod, g):
    return average_day_baseline(tod, g, np.arange(0, 1440, BIN) + BIN // 2, BIN)


def paired(r, t_max=None, t_min=None):
    ft = r.fingersticks["t_min"].to_numpy()
    fg = r.fingersticks["glucose_mgdl"].to_numpy()
    ct = r.cgm["t_min"].to_numpy()
    cg = r.cgm["glucose_mgdl"].to_numpy()
    m = np.ones(len(ft), dtype=bool)
    if t_max is not None:
        m &= ft < t_max
    if t_min is not None:
        m &= ft >= t_min
    ft, fg = ft[m], fg[m]
    if len(ft) == 0:
        return np.array([]), np.array([]), np.array([])
    j = np.clip(np.searchsorted(ct, ft), 1, len(ct) - 1)
    near = np.where(np.abs(ct[j] - ft) < np.abs(ct[j - 1] - ft), j, j - 1)
    ok = np.abs(ct[near] - ft) <= 10
    return ft[ok], fg[ok], cg[near][ok]


def two_state(t_obs, z, t_eval, smooth: bool, slow: bool = True):
    """State = [slow level (random walk), fast deviation (OU, time constant TAU)]; observation = sum + noise."""
    n = len(t_obs)
    if n == 0:
        return np.zeros(len(t_eval))
    H = np.array([1.0, 1.0])
    x = np.zeros(2)
    P = np.diag([20.0**2 if slow else 1e-9, FAST_SD**2])
    xs, Ps, xps, Pps, Fs = [], [], [], [], []
    last = t_obs[0]
    for t, y in zip(t_obs, z):
        dt = max(t - last, 0)
        a = np.exp(-dt / TAU)
        F = np.diag([1.0, a])
        Q = np.diag([SLOW_Q * dt if slow else 0.0, FAST_SD**2 * (1 - a * a)])
        xp = F @ x
        Pp = F @ P @ F.T + Q
        S = H @ Pp @ H + R_SD**2
        K = Pp @ H / S
        x = xp + K * (y - H @ xp)
        P = Pp - np.outer(K, H @ Pp)
        xs.append(x.copy()); Ps.append(P.copy()); xps.append(xp.copy()); Pps.append(Pp.copy()); Fs.append(F.copy())
        last = t
    xs = np.array(xs)
    if smooth:
        sm = xs.copy()
        for i in range(n - 2, -1, -1):
            C = Ps[i] @ Fs[i + 1].T @ np.linalg.inv(Pps[i + 1])
            sm[i] = xs[i] + C @ (sm[i + 1] - xps[i + 1])
        xs = sm
    out = np.zeros(len(t_eval))
    idx = np.searchsorted(t_obs, t_eval, side="right") - 1
    for i, (te, j) in enumerate(zip(t_eval, idx)):
        back = xs[j, 0] + xs[j, 1] * np.exp(-(te - t_obs[j]) / TAU) if j >= 0 else 0.0
        if smooth and j + 1 < n:
            fwd = xs[j + 1, 0] + xs[j + 1, 1] * np.exp(-(t_obs[j + 1] - te) / TAU)
            if j >= 0:
                w = (te - t_obs[j]) / max(t_obs[j + 1] - t_obs[j], 1)
                out[i] = (1 - w) * back + w * fwd
            else:
                out[i] = fwd
        else:
            out[i] = back
    return out


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


rows, cap_rows = [], []
for k in (3, 5):
    split = k * 1440
    pool = [paired(r, t_max=split) for r in recs]
    pf = np.concatenate([p[1] for p in pool])
    pc = np.concatenate([p[2] for p in pool])
    pop_b, pop_a = np.polyfit(pf, pc, 1)  # sensor = a + b * fingerstick
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
        prof = profile((tod0 + t[cal]) % 1440, g[cal])
        mean = float(g[cal].mean())
        shr = 0.5 * prof + 0.5 * mean
        at = lambda curve, tt: curve[((tod0 + tt) % 1440).astype(int) // BIN]  # noqa: E731
        _, cf, cc = paired(r, t_max=split)
        if len(cf) >= 8 and np.ptp(cf) > 40:
            b, a = np.polyfit(cf, cc, 1)
            b = float(np.clip(b, 0.6, 1.2))
            a = float(np.mean(cc - b * cf))
        else:
            b, a = pop_b, float(np.mean(cc - pop_b * cf)) if len(cf) >= 3 else pop_a
        tt, truth = t[test], g[test]
        base = at(shr, tt)
        fth, fgh, cgh = paired(r, t_min=split)
        if len(fth) < 3:
            continue
        fs_sensor = a + b * fgh
        z = fs_sensor - at(shr, fth)
        day_idx = (tod0 + tt) // 1440
        oracle = base.copy()
        for d in np.unique(day_idx):
            m = day_idx == d
            oracle[m] += np.mean(truth[m] - base[m])
        row = {
            "k": k,
            "patient": r.patient_id,
            "shrunk": rmse(base, truth),
            "oracle daily level": rmse(oracle, truth),
            "ou causal": rmse(base + two_state(fth, z, tt, False, slow=False), truth),
            "ou smooth": rmse(base + two_state(fth, z, tt, True, slow=False), truth),
            "slow+ou causal": rmse(base + two_state(fth, z, tt, False), truth),
            "slow+ou smooth": rmse(base + two_state(fth, z, tt, True), truth),
        }
        rows.append(row)
        # --- against the fingerstick itself: predict each hidden fingerstick before it is taken
        pred_shape = (at(shr, fth) - a) / b
        lvl = np.zeros(len(fth))
        for i in range(1, len(fth)):
            lvl[i] = two_state(fth[:i], z[:i], fth[i : i + 1], False)[0]
        pred_upd = (at(shr, fth) + lvl - a) / b
        cap_rows.append(
            {
                "k": k,
                "patient": r.patient_id,
                "n": len(fth),
                "sensor MARD": float(np.mean(np.abs(cgh - fgh) / fgh)),
                "shape MARD": float(np.mean(np.abs(pred_shape - fgh) / fgh)),
                "shape+fingersticks MARD": float(np.mean(np.abs(pred_upd - fgh) / fgh)),
                "sensor RMSE": rmse(cgh, fgh),
                "shape RMSE": rmse(pred_shape, fgh),
                "shape+fingersticks RMSE": rmse(pred_upd, fgh),
                "sensor within 15/15": float(np.mean(np.where(fgh < 100, np.abs(cgh - fgh) <= 15, np.abs(cgh - fgh) / fgh <= 0.15))),
                "shape within 15/15": float(np.mean(np.where(fgh < 100, np.abs(pred_shape - fgh) <= 15, np.abs(pred_shape - fgh) / fgh <= 0.15))),
                "shape+fs within 15/15": float(np.mean(np.where(fgh < 100, np.abs(pred_upd - fgh) <= 15, np.abs(pred_upd - fgh) / fgh <= 0.15))),
            }
        )

df = pd.DataFrame(rows)
cap = pd.DataFrame(cap_rows)
for k, grp in df.groupby("k"):
    per = grp.groupby("patient").mean(numeric_only=True).drop(columns="k")
    print(f"\nk={k}: patients {len(per)}  (all real fingersticks; scored against the hidden sensor)")
    print("  median RMSE mg/dL: " + ", ".join(f"{c} {per[c].median():.1f}" for c in per.columns))
    for name in ("oracle daily level", "ou causal", "ou smooth", "slow+ou causal", "slow+ou smooth"):
        d = per[name] - per["shrunk"]
        print(f"    {name} vs shrunk: median diff {d.median():+.1f}, better in {100 * (d < 0).mean():.0f} %, p {wilcoxon(d, alternative='less').pvalue:.3g}")
    c = cap[cap.k == k].groupby("patient").mean(numeric_only=True)
    print(f"  against the fingerstick (clinical reference), {int(c.n.sum())} hidden fingersticks, medians over patients:")
    print(f"    MARD: real sensor {100 * c['sensor MARD'].median():.1f} %, shape only {100 * c['shape MARD'].median():.1f} %, shape + earlier fingersticks {100 * c['shape+fingersticks MARD'].median():.1f} %")
    print(f"    RMSE: real sensor {c['sensor RMSE'].median():.1f}, shape only {c['shape RMSE'].median():.1f}, shape + earlier fingersticks {c['shape+fingersticks RMSE'].median():.1f}")
    print(f"    within 15 mg/dL or 15 %: real sensor {100 * c['sensor within 15/15'].median():.0f} %, shape only {100 * c['shape within 15/15'].median():.0f} %, shape + earlier fingersticks {100 * c['shape+fs within 15/15'].median():.0f} %")
    d = c["shape+fingersticks MARD"] - c["shape MARD"]
    print(f"    shape+fingersticks vs shape only (MARD): median diff {100 * d.median():+.1f} points, better in {100 * (d < 0).mean():.0f} %, p {wilcoxon(d, alternative='less').pvalue:.3g}")
