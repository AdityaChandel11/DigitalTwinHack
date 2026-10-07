"""Feasibility counts on ShanghaiT2DM. Labels and availability only: no predictor-outcome association.

Throwaway research script (scratchpad). Definitions were fixed before this was run:
  event night  = a run of >= 2 consecutive sensor readings below 70 mg/dL that starts between 00:00 and 06:00
  prediction   = made at 22:00 the evening before
"""

from __future__ import annotations

import re
from collections import Counter

import numpy as np
import pandas as pd

from chhaya.config import RAW_DIR, is_dev_patient
from chhaya.data import shanghai
from chhaya.data.audit import low_events

pd.set_option("display.width", 200)
recs = shanghai.load_all()
print(f"recordings {len(recs)}, patients {len({r.patient_id for r in recs})}")

# ---------------------------------------------------------------- summary-sheet headers
summ = shanghai.load_summary(RAW_DIR / "shanghai")
print("\nSUMMARY SHEET COLUMNS")
for c in summ.columns:
    print("  ", repr(str(c))[:110], "| non-null", int(summ[c].notna().sum()))

# ---------------------------------------------------------------- nights
NIGHT_END = 360  # 06:00
rows = []
for r in recs:
    t = r.cgm["t_min"].to_numpy()
    g = r.cgm["glucose_mgdl"].to_numpy()
    tod0 = r.start.hour * 60 + r.start.minute
    clock = tod0 + t
    fs_clock = tod0 + r.fingersticks["t_min"].to_numpy()
    lows70 = [tod0 + s for s in low_events(t, g, 70.0, 2)]
    lows54 = [tod0 + s for s in low_events(t, g, 54.0, 2)]
    last_day = int(clock.max() // 1440)
    for d in range(1, last_day + 1):
        w0, w1 = d * 1440, d * 1440 + NIGHT_END
        n_night = int(((clock >= w0) & (clock < w1)).sum())
        eve0, eve1 = (d - 1) * 1440 + 18 * 60, (d - 1) * 1440 + 22 * 60
        n_eve = int(((clock >= eve0) & (clock < eve1)).sum())
        day0, day1 = (d - 1) * 1440 + 6 * 60, (d - 1) * 1440 + 22 * 60
        n_day = int(((clock >= day0) & (clock < day1)).sum())
        rows.append(
            {
                "rec_id": r.rec_id,
                "patient_id": r.patient_id,
                "dev": is_dev_patient(r.patient_id),
                "night": d,
                "n_night": n_night,
                "n_eve": n_eve,
                "n_day": n_day,
                "low70": any(w0 <= s < w1 for s in lows70),
                "low54": any(w0 <= s < w1 for s in lows54),
                "fs_day": int(((fs_clock >= day0) & (fs_clock < day1)).sum()),
                "fs_eve": int(((fs_clock >= (d - 1) * 1440 + 20 * 60) & (fs_clock < (d - 1) * 1440 + 23 * 60)).sum()),
                "days_before": (w0 - tod0) / 1440.0,
            }
        )
nights = pd.DataFrame(rows)
print(f"\nNIGHTS (all, any coverage): {len(nights)}; with low<70: {int(nights.low70.sum())}; low<54: {int(nights.low54.sum())}")

# eligibility: >= 18 of 24 night slots read, >= 12 of 16 evening slots read (18:00-22:00)
elig = nights[(nights.n_night >= 18) & (nights.n_eve >= 12)].copy()
print(f"ELIGIBLE nights (night >=75 % covered, evening 18-22h >=75 % covered): {len(elig)}")


def block(df: pd.DataFrame, name: str) -> None:
    per = df.groupby("patient_id").agg(n=("low70", "size"), ev70=("low70", "sum"), ev54=("low54", "sum"))
    ev = per.ev70.sort_values(ascending=False)
    tot = int(ev.sum())
    print(
        f"  {name}: patients {len(per)}, nights {len(df)}, event nights<70 {tot} ({100 * tot / max(len(df), 1):.1f} %), "
        f"patients with >=1 event {int((per.ev70 > 0).sum())}, with >=2 {int((per.ev70 > 1).sum())}; "
        f"event nights<54 {int(per.ev54.sum())} in {int((per.ev54 > 0).sum())} patients"
    )
    if tot:
        print(
            f"     share of event nights in top 5 patients {100 * ev.head(5).sum() / tot:.0f} %, top 10 {100 * ev.head(10).sum() / tot:.0f} %; "
            f"per-patient event-night counts (sorted, non-zero): {ev[ev > 0].astype(int).tolist()}"
        )


print("\nEVENT CONCENTRATION (eligible nights)")
block(elig, "ALL ")
block(elig[elig.dev], "DEV ")
block(elig[~elig.dev], "TEST")

print("\nSENSOR-OFF VARIANT: eligible nights at least k days after recording start (personal baseline from the first k days)")
for k in (2, 3, 5):
    sub = elig[elig.days_before >= k]
    block(sub, f"k>={k} ALL ")
    block(sub[~sub.dev], f"k>={k} TEST")
    with_fs = sub[sub.fs_eve > 0]
    print(f"     of these, nights with a fingerstick 20:00-23:00: {len(with_fs)} ({int(with_fs.low70.sum())} events); with any fingerstick 06-22h: {int((sub.fs_day > 0).sum())}")

# ---------------------------------------------------------------- recording lengths
days = pd.Series({r.rec_id: r.n_min / 1440.0 for r in recs})
print("\nRECORDING LENGTH (days): ", {f">={d}": int((days >= d).sum()) for d in (3, 6, 7, 8, 10, 13)}, "median", round(float(days.median()), 1))
pat_days = pd.Series({r.rec_id: is_dev_patient(r.patient_id) for r in recs})
print("  test-split recordings with >=8 days:", int(((days >= 8) & ~pat_days).sum()), "| dev:", int(((days >= 8) & pat_days).sum()))

# ---------------------------------------------------------------- fingersticks
hours = Counter()
n_fs = 0
pairs = []
for r in recs:
    tod0 = r.start.hour * 60 + r.start.minute
    ft = r.fingersticks["t_min"].to_numpy()
    fg = r.fingersticks["glucose_mgdl"].to_numpy()
    n_fs += len(ft)
    for x in ft:
        hours[int(((tod0 + x) % 1440) // 60)] += 1
    ct = r.cgm["t_min"].to_numpy()
    cg = r.cgm["glucose_mgdl"].to_numpy()
    if len(ft) == 0:
        continue
    j = np.clip(np.searchsorted(ct, ft), 1, len(ct) - 1)
    near = np.where(np.abs(ct[j] - ft) < np.abs(ct[j - 1] - ft), j, j - 1)
    ok = np.abs(ct[near] - ft) <= 10
    for a, b, c in zip(cg[near][ok], fg[ok], ((tod0 + ft[ok]) % 1440) // 60):
        pairs.append((a, b, int(c)))
print(f"\nFINGERSTICKS: {n_fs} total; by clock hour: {dict(sorted(hours.items()))}")
p = pd.DataFrame(pairs, columns=["cgm", "cbg", "hour"])
print(f"PAIRED sensor vs fingerstick (within 10 min): n {len(p)}")
if len(p):
    ard = (p.cgm - p.cbg).abs() / p.cbg
    print(f"  MARD {100 * ard.mean():.1f} %, bias (sensor - fingerstick) mean {np.mean(p.cgm - p.cbg):.1f} mg/dL, median {np.median(p.cgm - p.cbg):.1f}")
    lo = p[p.cgm < 70]
    print(
        f"  when the SENSOR reads < 70: n {len(lo)}, fingerstick median {lo.cbg.median() if len(lo) else float('nan'):.0f} mg/dL, "
        f"fingerstick also < 70 in {100 * (lo.cbg < 70).mean() if len(lo) else float('nan'):.0f} %, fingerstick < 80 in {100 * (lo.cbg < 80).mean() if len(lo) else float('nan'):.0f} %"
    )
    lo2 = p[p.cbg < 70]
    print(f"  when the FINGERSTICK reads < 70: n {len(lo2)}, sensor also < 70 in {100 * (lo2.cgm < 70).mean() if len(lo2) else float('nan'):.0f} %")
    print(f"  paired readings taken 00:00-06:00: {int((p.hour < 6).sum())}")

# ---------------------------------------------------------------- record completeness and drug vocabulary
st = pd.DataFrame([r.static for r in recs])
print("\nRECORD FIELDS, share non-missing over recordings:")
for c in st.columns:
    col = st[c]
    if col.dtype.kind == "f":
        print(f"  {c}: {100 * col.notna().mean():.0f} %  (median {col.median():.1f})")
    else:
        print(f"  {c}: {100 * col.notna().mean():.0f} %  e.g. {col.dropna().astype(str).head(3).tolist()}")

tok = Counter()
for s in st["agents"].dropna().astype(str):
    for part in re.split(r"[,;，；\n]+", s):
        part = part.strip().lower()
        if part and part != "nan":
            tok[part] += 1
print("\nSUMMARY-SHEET AGENTS vocabulary (top 40):", tok.most_common(40))

by_route = {}
for r in recs:
    if len(r.doses):
        for route, drug in zip(r.doses["route"], r.doses["drug"]):
            by_route.setdefault(route, Counter())[re.sub(r"[\d\.]+", "#", str(drug)).strip().lower()[:60]] += 1
for route, c in by_route.items():
    print(f"\nDOSE TEXT route={route}: {sum(c.values())} rows, {len(c)} patterns; top 15: {c.most_common(15)}")

rec_routes = Counter()
for r in recs:
    routes = set(r.doses["route"]) if len(r.doses) else set()
    rec_routes[tuple(sorted(routes))] += 1
print("\nRECORDINGS BY DOSE ROUTES:", dict(rec_routes))
