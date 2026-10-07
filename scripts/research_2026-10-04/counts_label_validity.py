"""Second feasibility pass on ShanghaiT2DM: label validity against fingersticks, fingerstick density,
repeat recordings. Availability and agreement only: no predictor-outcome association, no estimator run.

Throwaway research script (scratchpad).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from chhaya.config import is_dev_patient
from chhaya.data import shanghai

recs = shanghai.load_all()

pairs = []
per_rec = []
for r in recs:
    tod0 = r.start.hour * 60 + r.start.minute
    ft = r.fingersticks["t_min"].to_numpy()
    fg = r.fingersticks["glucose_mgdl"].to_numpy()
    ct = r.cgm["t_min"].to_numpy()
    cg = r.cgm["glucose_mgdl"].to_numpy()
    days = r.n_min / 1440.0
    routes = set(r.doses["route"]) if len(r.doses) else set()
    per_rec.append(
        {
            "rec_id": r.rec_id,
            "patient_id": r.patient_id,
            "dev": is_dev_patient(r.patient_id),
            "start": r.start,
            "days": days,
            "fs_per_day": len(ft) / days,
            "meals_per_day": len(r.meals) / days,
            "insulin": bool(routes & {"sc", "iv", "csii"}),
            "csii": "csii" in routes,
            "cgm_mean": float(np.mean(cg)),
        }
    )
    if len(ft) == 0:
        continue
    j = np.clip(np.searchsorted(ct, ft), 1, len(ct) - 1)
    near = np.where(np.abs(ct[j] - ft) < np.abs(ct[j - 1] - ft), j, j - 1)
    ok = np.abs(ct[near] - ft) <= 10
    # slope of the sensor around the pair (mg/dL per 15 min), to separate lag from bias
    slope = np.full(len(ft), np.nan)
    inner = (near > 0) & (near < len(ct) - 1)
    slope[inner] = (cg[np.clip(near + 1, 0, len(ct) - 1)][inner] - cg[np.clip(near - 1, 0, len(ct) - 1)][inner]) / 2.0
    for a, b, c, s in zip(cg[near][ok], fg[ok], ((tod0 + ft[ok]) % 1440) // 60, slope[ok]):
        pairs.append((r.patient_id, a, b, int(c), s))

p = pd.DataFrame(pairs, columns=["patient_id", "cgm", "cbg", "hour", "slope"])
R = pd.DataFrame(per_rec)
print(f"pairs {len(p)} from {p.patient_id.nunique()} patients")

print("\nAGREEMENT BY FINGERSTICK RANGE (reference = fingerstick)")
bins = [(0, 70), (70, 100), (100, 180), (180, 250), (250, 600)]
for lo, hi in bins:
    s = p[(p.cbg >= lo) & (p.cbg < hi)]
    if len(s):
        d = s.cgm - s.cbg
        print(f"  fingerstick {lo:3d}-{hi:3d}: n {len(s):4d}, sensor bias mean {d.mean():6.1f}, MARD {100 * (d.abs() / s.cbg).mean():5.1f} %")

print("\nLABEL VALIDITY (how often the sensor threshold agrees with the fingerstick at the same moment)")
for name, thr, low in (("< 70", 70, True), ("< 54", 54, True), ("> 180", 180, False), ("> 250", 250, False)):
    s_flag = p.cgm < thr if low else p.cgm > thr
    f_flag = p.cbg < thr if low else p.cbg > thr
    tp = int((s_flag & f_flag).sum())
    ppv = tp / max(int(s_flag.sum()), 1)
    sens = tp / max(int(f_flag.sum()), 1)
    print(f"  {name:6s}: sensor flags {int(s_flag.sum()):4d}, fingerstick flags {int(f_flag.sum()):4d}, both {tp:4d} -> PPV {100 * ppv:4.0f} %, sensitivity {100 * sens:4.0f} %")

lo = p[p.cgm < 70]
print(f"\nSENSOR < 70 pairs: n {len(lo)} in {lo.patient_id.nunique()} patients; night (00-06h) {int((lo.hour < 6).sum())}; fingerstick quartiles {np.percentile(lo.cbg, [25, 50, 75]).round(0).tolist()}")
stable = lo[lo.slope.abs() <= 5]
print(f"  of these with a flat sensor trace (|slope| <= 5 mg/dL per 15 min): n {len(stable)}, fingerstick median {stable.cbg.median():.0f}, fingerstick < 70 in {100 * (stable.cbg < 70).mean():.0f} %")
night = lo[lo.hour < 6]
if len(night):
    print(f"  night pairs: fingerstick median {night.cbg.median():.0f}, fingerstick < 70 in {100 * (night.cbg < 70).mean():.0f} %")

print("\nPER-PATIENT sensor - fingerstick offset (patients with >= 10 pairs)")
g = p.assign(d=p.cgm - p.cbg).groupby("patient_id").d.agg(["size", "mean", "std"])
g = g[g["size"] >= 10]
print(f"  patients {len(g)}; offset mean of means {g['mean'].mean():.1f}, SD across patients {g['mean'].std():.1f}, range {g['mean'].min():.1f} to {g['mean'].max():.1f}; within-patient SD median {g['std'].median():.1f}")

print("\nFINGERSTICKS PER DAY per recording:", R.fs_per_day.describe().round(2).to_dict())
print("  recordings with >= 1/day:", int((R.fs_per_day >= 1).sum()), "| >= 2/day:", int((R.fs_per_day >= 2).sum()), "| >= 4/day:", int((R.fs_per_day >= 4).sum()), "| none:", int((R.fs_per_day == 0).sum()))
print("MEALS PER DAY per recording:", R.meals_per_day.describe().round(2).to_dict())

print("\nSENSOR-OFF COHORT SIZES (recording has >= k+2 days and >= 1 fingerstick a day)")
for k in (3, 5, 7):
    ok = R[(R.days >= k + 2) & (R.fs_per_day >= 1)]
    print(
        f"  k={k}: recordings {len(ok)} (patients {ok.patient_id.nunique()}); dev {int(ok.dev.sum())}, test {int((~ok.dev).sum())}; "
        f"not on insulin {int((~ok.insulin).sum())} (test {int((~ok.insulin & ~ok.dev).sum())}); hidden days median {float((ok.days - k).median()):.1f}"
    )

print("\nREPEAT RECORDINGS (same patient, more than one recording)")
rep = R[R.patient_id.duplicated(keep=False)].sort_values(["patient_id", "start"])
for pid, grp in rep.groupby("patient_id"):
    starts = grp.start.tolist()
    gaps = [(b - a).days for a, b in zip(starts[:-1], starts[1:])]
    print(f"  {pid} dev={bool(grp.dev.iloc[0])}: {len(grp)} recordings, days {grp.days.round(1).tolist()}, gap between starts (days) {gaps}, fs/day {grp.fs_per_day.round(1).tolist()}, insulin {grp.insulin.tolist()}")

print("\nDRIFT WITHIN A RECORDING (sensor mean of the last 3 days minus the first 3 days, recordings >= 8 days)")
drift = []
for r in recs:
    if r.n_min / 1440.0 < 8:
        continue
    t = r.cgm["t_min"].to_numpy()
    g_ = r.cgm["glucose_mgdl"].to_numpy()
    first = g_[t < 3 * 1440]
    last = g_[t >= r.n_min - 3 * 1440]
    if len(first) > 100 and len(last) > 100:
        drift.append(last.mean() - first.mean())
drift = np.array(drift)
print(f"  n {len(drift)}; median change {np.median(drift):.1f} mg/dL; quartiles {np.percentile(drift, [10, 25, 75, 90]).round(1).tolist()}; share falling by more than 20: {100 * (drift < -20).mean():.0f} %, rising by more than 20: {100 * (drift > 20).mean():.0f} %")
