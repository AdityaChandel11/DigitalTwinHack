"""Break test, analysis stage: attack the Gate 2 claim with the arrays captured by capture.py.

Usage: python analyse.py capture.pkl <repo root with committed results> [results folder suffix]
"""

import pickle
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import binomtest, norm, wilcoxon

from chhaya.eval.baselines import average_day_baseline, lodo_average_day
from chhaya.eval.metrics import time_in_ranges
from chhaya.units import gmi_percent

warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
K, SPLIT = 5, 5 * 1440
res = pickle.load(open(sys.argv[1], "rb"))
repo = sys.argv[2]
suffix = sys.argv[3] if len(sys.argv) > 3 else ""  # e.g. "-registered" for the run of commit a57227f
errors = [r for r in res if "error" in r]
main = [r for r in res if r["kind"] == "main" and "error" not in r and not r.get("skipped")]
shift = [r for r in res if r["kind"] == "shift1" and "error" not in r]
leak = [r for r in res if r["kind"] == "leak" and "error" not in r]
TEST = [r for r in main if not r["dev"]]
DEV = [r for r in main if r["dev"]]


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def section(title):
    print("\n" + "=" * 100 + "\n" + title + "\n" + "=" * 100)


def wil(d, alt="two-sided"):
    d = np.asarray(d, dtype=float)
    return float(wilcoxon(d, alternative=alt).pvalue) if d.size >= 6 and np.any(d != 0) else float("nan")


section(
    f"0. RUN HEALTH: {len(res)} tasks, {len(errors)} crashed; main {len(main)}, shifted-window {len(shift)}, leak {len(leak)}"
)
for r in errors:
    print("CRASH", r["kind"], r["rec"], "|", r["error"].strip().splitlines()[-1][:200])

section("1. DETERMINISM: does a separate run reproduce the committed per-patient metrics exactly?")
committed = pd.concat(
    [
        pd.read_csv(f"{repo}/results/gate2/cgmacros-{s}{suffix}/metrics.csv", float_precision="round_trip")
        for s in ("dev", "test")
    ]
)
committed = committed[committed.k_days == K].set_index("rec_id")
cols = [
    "twin_rmse",
    "ode_rmse",
    "day_rmse",
    "mean_rmse",
    "twin_tir_err",
    "twin_cov80",
    "sigma_res_mgdl",
    "meal_clock_offset_min",
]
worst = 0.0
for r in main:
    for c in cols:
        worst = max(worst, abs(r["metrics"][c] - committed.loc[r["rec"], c]))
print(
    f"largest absolute difference across {len(main)} patients x {len(cols)} metrics: {worst:.3g}  ->",
    "IDENTICAL" if worst == 0 else "DIFFERS",
)
print(
    f"my re-simulation of the physiology vs the pipeline's: max {max(r['check_ode'] for r in main):.2g} mg/dL; band rebuilt from samples: max {max(r['check_band'] for r in main):.2g} mg/dL"
)

section("2. LEAKAGE AND CAUSALITY ON REAL PATIENTS")
for r in leak:
    s, t = r["same"], r["trunc"]
    unchanged = all(s[k] for k in ("twin", "ode", "day", "mean", "lo", "hi", "z_map", "offset"))
    print(
        f"{r['rec']} ({'dev' if r['dev'] else 'test'}): hidden readings of both sensors scrambled -> estimate, band, fit, clock offset unchanged: {unchanged}"
        f" (scramble reached the scored truth: {s['truth_changed']}); recording cut 1.5 days after the split -> estimate moves {t['twin']:.2g} mg/dL,"
        f" band moves up to {max(t['lo'], t['hi']):.2f} mg/dL; control (one calibration reading +80) moves the estimate {r['control']:.2f} mg/dL"
    )

section("3. MEAL WINDOW: does the 6-slot window drop meals in real patients?")
w = pd.DataFrame(
    [
        dict(
            rec=r["rec"][-3:],
            split="dev" if r["dev"] else "test",
            group=r["group"],
            meals=r["n_meals"],
            max_12h=r["max_in_12h"],
            max_5h=r["max_in_5h"],
            max_effect_mgdl=round(r["win_diff"], 2),
        )
        for r in main
    ]
)
print(w[w.max_effect_mgdl > 0].sort_values("max_effect_mgdl", ascending=False).to_string(index=False))
print(
    "patients affected:",
    int((w.max_effect_mgdl > 0).sum()),
    "| on the test side:",
    int(((w.max_effect_mgdl > 0) & (w.split == "test")).sum()),
)

section("4. THE TWO PHYSICAL SENSORS: how far apart are they where BOTH actually recorded?")
rows = []
for r in main:
    f = r["ref"]
    ok = f["ok_test"]
    d = r["truth"][ok] - f["test"][ok]
    rows.append(
        dict(
            rec=r["rec"][-3:],
            group=r["group"],
            frac_overlap=ok.mean(),
            bias=d.mean() if ok.any() else np.nan,
            sd=d.std() if ok.any() else np.nan,
            floor_matched=rmse(r["truth"][ok], f["test"][ok]) if ok.any() else np.nan,
            floor_committed=r["metrics"].get("floor_rmse", np.nan),
        )
    )
fl = pd.DataFrame(rows)
print(
    fl.groupby("group")[["frac_overlap", "bias", "sd", "floor_matched", "floor_committed"]]
    .median()
    .round(1)
    .to_string()
)
print(
    f"all patients, median: overlap {100 * fl.frac_overlap.median():.0f}% | Libre minus Dexcom {fl.bias.median():.1f} mg/dL | SD of difference {fl.sd.median():.1f} | RMSE where both recorded {fl.floor_matched.median():.1f} | figure in the committed results {fl.floor_committed.median():.1f}"
)
print(
    "patients whose second sensor covers less than 90%% of the hidden window: %d of %d"
    % ((fl.frac_overlap < 0.9).sum(), len(fl))
)


def profile(tod_cal, g, tod_test, bin_min=30, stat="mean", smooth=False):
    n = 1440 // bin_min
    b = (np.asarray(tod_cal, dtype=int) % 1440) // bin_min
    s = pd.Series(g).groupby(b).agg(stat).reindex(range(n))
    have = s.notna().to_numpy()
    p = np.interp(np.arange(n), np.arange(n)[have], s.to_numpy()[have], period=n)
    if smooth:
        p = 0.5 * p + 0.25 * (np.roll(p, 1) + np.roll(p, -1))
    return p[(np.asarray(tod_test, dtype=int) % 1440) // bin_min]


def estimators(r):
    tc, tt = r["tod0"] + r["cal_t"], r["tod0"] + r["t_test"]
    g = r["cal_truth"]
    day, mean, ode = r["day"], r["mean"], r["ode"]
    last = r["cal_t"] >= SPLIT - 1440
    sm = profile(tc, g, tt, 30, "mean", True)
    e = {
        "average day (30 min, as registered)": day,
        "average day, 15-min bins": average_day_baseline(tc, g, tt, 15),
        "average day, 60-min bins": average_day_baseline(tc, g, tt, 60),
        "average day, 120-min bins": average_day_baseline(tc, g, tt, 120),
        "median day": profile(tc, g, tt, 30, "median"),
        "smoothed average day": sm,
        "yesterday only": average_day_baseline(tc[last], g[last], tt, 30),
        "mean": mean,
        "shrunk day 0.75 day + 0.25 mean": 0.75 * day + 0.25 * mean,
        "shrunk day 0.5 day + 0.5 mean": 0.5 * day + 0.5 * mean,
        "shrunk day 0.25 day + 0.75 mean": 0.25 * day + 0.75 * mean,
        "shrunk smoothed day 0.5 + 0.5 mean": 0.5 * sm + 0.5 * mean,
        "physiology alone": ode,
        "CHHAYA (0.5 physiology + 0.5 day)": r["twin"],
        "0.25 physiology + 0.75 day": 0.25 * ode + 0.75 * day,
        "0.75 physiology + 0.25 day": 0.75 * ode + 0.25 * day,
        "three-way: physiology, day, mean": (ode + day + mean) / 3.0,
        "PLACEBO no meal log + day": 0.5 * r["p_none"] + 0.5 * day,
        "PLACEBO meals 6 h late + day": 0.5 * r["p_late"] + 0.5 * day,
        "habitual meals (replayed) + day": 0.5 * r["p_habit"] + 0.5 * day,
        "PLACEBO band at rest + day": 0.5 * r["p_rest"] + 0.5 * day,
    }
    return e


def table(group, label):
    errs = {}
    for r in group:
        for name, est in estimators(r).items():
            errs.setdefault(name, []).append(rmse(est, r["truth"]))
    errs = {k: np.array(v) for k, v in errs.items()}
    ours, day = errs["CHHAYA (0.5 physiology + 0.5 day)"], errs["average day (30 min, as registered)"]
    rows = []
    for name, e in errs.items():
        rows.append(
            dict(
                estimator=name,
                median=np.median(e),
                mean=e.mean(),
                vs_day_better=np.mean(e < day),
                minus_chhaya=np.median(e - ours),
                chhaya_better_in=np.mean(ours < e),
                p_two_sided=wil(e - ours),
            )
        )
    print(f"\n{label}: n = {len(group)}   (RMSE mg/dL; minus_chhaya > 0 means worse than Chhaya)")
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    return errs


section(
    "5. IS THE BASELINE FAIR, AND DOES THE MEAL LOG MATTER?  Stronger baselines and placebo inputs, k = 5"
)
E_test = table(TEST, "HELD-OUT TEST PATIENTS")
E_dev = table(DEV, "DEVELOPMENT PATIENTS")

section("6. BLEND WEIGHT: is 0.5 a knife edge?  (test patients; chosen on dev)")
for grp, lab in ((TEST, "test"), (DEV, "dev")):
    out = []
    for wgt in np.linspace(0, 1, 9):
        e = np.array([rmse(wgt * r["ode"] + (1 - wgt) * r["day"], r["truth"]) for r in grp])
        d = np.array([rmse(r["day"], r["truth"]) for r in grp])
        out.append(f"w={wgt:.3f}: {np.median(e):.2f} ({100 * np.mean(e < d):.0f}%)")
    print(lab, " | ".join(out))

section("7. JUDGED BY THE OTHER SENSOR: scored against the Dexcom, never used for calibration")
for grp, lab in ((TEST, "test"), (DEV, "dev")):
    rows = []
    for r in grp:
        f = r["ref"]
        ok, okc = f["ok_test"], f["ok_cal"]
        if ok.sum() < 48 or okc.sum() < 48:
            continue
        off = float(
            np.mean(r["cal_truth"][okc] - f["cal"][okc])
        )  # Libre minus Dexcom, learned before the split
        ref = f["test"][ok] + off
        rows.append(
            dict(
                rec=r["rec"],
                twin=rmse(r["twin"][ok], ref),
                day=rmse(r["day"][ok], ref),
                ode=rmse(r["ode"][ok], ref),
                mean=rmse(r["mean"][ok], ref),
                r_twin=np.corrcoef(r["twin"][ok], ref)[0, 1],
                r_day=np.corrcoef(r["day"][ok], ref)[0, 1],
            )
        )
    d = pd.DataFrame(rows)
    diff = d.twin - d.day
    print(
        f"{lab}: n={len(d)} | Chhaya {d.twin.median():.1f} vs average day {d.day.median():.1f} vs mean {d['mean'].median():.1f} (physiology alone {d.ode.median():.1f}) |"
        f" Chhaya better in {100 * (diff < 0).mean():.0f}% | one-sided p = {wil(diff, 'less'):.2g} | correlation with Dexcom: Chhaya {d.r_twin.median():.2f}, day {d.r_day.median():.2f}"
    )

section("8. ROBUSTNESS OF P1 ON TEST PATIENTS: subsets, other statistics, uncertainty")
T = pd.DataFrame(
    [
        dict(
            rec=r["rec"][-3:],
            group=r["group"],
            twin=r["metrics"]["twin_rmse"],
            day=r["metrics"]["day_rmse"],
            twin_mae=r["metrics"]["twin_mae"],
            day_mae=r["metrics"]["day_mae"],
            offset=r["offset"],
            unit=r["amount_unit"],
            act=r["activity_source"],
            days=r["days"],
        )
        for r in TEST
    ]
)
T["diff"] = T.twin - T.day


def p1(d, label):
    x = d["diff"].to_numpy()
    print(
        f"  {label:58s} n={len(d):2d} median diff {np.median(x):+.2f}  better in {100 * np.mean(x < 0):3.0f}%  Wilcoxon p={wil(x, 'less'):.2g}  sign-test p={binomtest(int((x < 0).sum()), len(x), 0.5, alternative='greater').pvalue:.2g}"
    )


p1(T, "all test patients")
p1(T[T.offset.abs() < 45], "excluding patients whose meal clock was moved 45+ min")
p1(T[T.unit != "fraction"], "excluding files with the fraction convention")
p1(T[T.act == "mets"], "excluding files with derived METs")
for g in ("healthy", "prediabetes", "t2d"):
    p1(T[T.group != g], f"leaving out the {g} group")
    p1(T[T.group == g], f"only the {g} group")
loo = [wil(T.drop(i)["diff"].to_numpy(), "less") for i in T.index]
print(f"  leave-one-patient-out: worst one-sided p = {max(loo):.2g}")
x = (T.twin_mae - T.day_mae).to_numpy()
print(
    f"  same test on MAE instead of RMSE: median diff {np.median(x):+.2f}, better in {100 * np.mean(x < 0):.0f}%, p = {wil(x, 'less'):.2g}"
)
rng = np.random.default_rng(0)
boot = np.array([np.median(rng.choice(T["diff"].to_numpy(), len(T))) for _ in range(10000)])
rel = (T.twin / T.day - 1).to_numpy()
bootr = np.array([np.mean(rng.choice(rel, len(rel))) for _ in range(10000)])
print(
    f"  median difference {np.median(T['diff']):+.2f} mg/dL, 95% bootstrap CI [{np.percentile(boot, 2.5):+.2f}, {np.percentile(boot, 97.5):+.2f}]"
)
print(
    f"  mean relative change in RMSE {100 * rel.mean():+.1f}%, 95% bootstrap CI [{100 * np.percentile(bootr, 2.5):+.1f}%, {100 * np.percentile(bootr, 97.5):+.1f}%]"
)
print(
    f"  RMSE as a fraction of the SD of the hidden glucose (test, median): Chhaya {np.median([rmse(r['twin'], r['truth']) / np.std(r['truth']) for r in TEST]):.2f},"
    f" average day {np.median([rmse(r['day'], r['truth']) / np.std(r['truth']) for r in TEST]):.2f}, mean {np.median([rmse(r['mean'], r['truth']) / np.std(r['truth']) for r in TEST]):.2f}"
)

section(
    "9. DOES THE ADVANTAGE LAST?  Chhaya minus average-day RMSE by day since the sensor came off (all 45)"
)
rows = []
for r in main:
    d = (r["t_test"] - SPLIT) // 1440
    for k in np.unique(d):
        m = d == k
        if m.sum() >= 48:
            rows.append(
                dict(
                    rec=r["rec"],
                    day=int(k),
                    twin=rmse(r["twin"][m], r["truth"][m]),
                    base=rmse(r["day"][m], r["truth"][m]),
                    mean=rmse(r["mean"][m], r["truth"][m]),
                )
            )
D = pd.DataFrame(rows)
D["diff"] = D.twin - D.base
print(
    D.groupby("day")
    .agg(
        patients=("rec", "nunique"),
        chhaya=("twin", "median"),
        average_day=("base", "median"),
        mean_baseline=("mean", "median"),
        median_diff=("diff", "median"),
        better=("diff", lambda s: (s < 0).mean()),
    )
    .round(2)
    .to_string()
)

section(
    "10. DOES IT RESPOND TO WHAT WAS EATEN?  Advantage on hidden days by how unusual the day's carbohydrate was"
)
rows = []
for r in main:
    mt, mc = r["meal_t"], np.nan_to_num(r["meal_carb"])
    cal_daily = np.array([mc[(mt >= d * 1440) & (mt < (d + 1) * 1440)].sum() for d in range(K)])
    if cal_daily.mean() <= 0:
        continue
    d = (r["t_test"] - SPLIT) // 1440
    for k in np.unique(d):
        m = d == k
        if m.sum() < 48:
            continue
        carbs = mc[(mt >= (K + k) * 1440) & (mt < (K + k + 1) * 1440)].sum()
        rows.append(
            dict(
                rec=r["rec"],
                atyp=abs(carbs - cal_daily.mean()) / cal_daily.mean(),
                carbs=carbs,
                adv_twin=rmse(r["day"][m], r["truth"][m]) - rmse(r["twin"][m], r["truth"][m]),
                adv_ode=rmse(r["day"][m], r["truth"][m]) - rmse(r["ode"][m], r["truth"][m]),
            )
        )
A = pd.DataFrame(rows)
A["tercile"] = pd.qcut(A.atyp, 3, labels=["typical day", "middle", "unusual day"])
print(
    A.groupby("tercile", observed=True)
    .agg(
        days=("rec", "size"),
        atypicality=("atyp", "median"),
        chhaya_gain=("adv_twin", "mean"),
        physiology_gain=("adv_ode", "mean"),
    )
    .round(2)
    .to_string()
)
print(
    "correlation between how unusual the day was and Chhaya's gain over the average day: r = %.2f (n = %d patient-days)"
    % (A.atyp.corr(A.adv_twin), len(A))
)

section("10b. HIDDEN DAYS WITH AND WITHOUT A MEAL LOG: the study protocol ended before some sensors did")
rows = []
for r in main:
    mt, mc = r["meal_t"], np.nan_to_num(r["meal_carb"])
    d = (r["t_test"] - SPLIT) // 1440
    shrunk = 0.5 * r["day"] + 0.5 * r["mean"]
    for k in np.unique(d):
        m = d == k
        if m.sum() < 48:
            continue
        n_meals = int(((mt >= (K + k) * 1440) & (mt < (K + k + 1) * 1440) & (mc > 0)).sum())
        rows.append(
            dict(
                rec=r["rec"],
                dev=r["dev"],
                logged="no meals logged" if n_meals == 0 else "1-2 meals" if n_meals <= 2 else "3+ meals",
                chhaya=rmse(r["twin"][m], r["truth"][m]),
                ode=rmse(r["ode"][m], r["truth"][m]),
                day=rmse(r["day"][m], r["truth"][m]),
                shrunk=rmse(shrunk[m], r["truth"][m]),
                mean=rmse(r["mean"][m], r["truth"][m]),
            )
        )
B = pd.DataFrame(rows)
B["vs_day"] = B.chhaya - B.day
B["vs_shrunk"] = B.chhaya - B.shrunk
B["ode_vs_shrunk"] = B.ode - B.shrunk
for flag, lab in ((False, "test"), (True, "dev")):
    g = (
        B[B.dev == flag]
        .groupby("logged")
        .agg(
            patient_days=("rec", "size"),
            patients=("rec", "nunique"),
            chhaya=("chhaya", "median"),
            physiology=("ode", "median"),
            shrunk_control=("shrunk", "median"),
            average_day=("day", "median"),
            vs_day=("vs_day", "median"),
            vs_shrunk=("vs_shrunk", "median"),
            better_than_shrunk=("vs_shrunk", lambda x: (x < 0).mean()),
            physiology_vs_shrunk=("ode_vs_shrunk", "median"),
        )
    )
    print(lab)
    print(g.round(2).to_string())
# patient-level test restricted to hidden days that have a meal log
for flag, lab in ((False, "test"), (True, "dev")):
    out = []
    for r in (x for x in main if x["dev"] == flag):
        mt, mc = r["meal_t"], np.nan_to_num(r["meal_carb"])
        d = (r["t_test"] - SPLIT) // 1440
        keep = np.zeros(d.size, dtype=bool)
        for k in np.unique(d):
            if ((mt >= (K + k) * 1440) & (mt < (K + k + 1) * 1440) & (mc > 0)).sum() >= 2:
                keep |= d == k
        if keep.sum() >= 48:
            shrunk = 0.5 * r["day"] + 0.5 * r["mean"]
            out.append(
                (
                    rmse(r["twin"][keep], r["truth"][keep]),
                    rmse(shrunk[keep], r["truth"][keep]),
                    rmse(r["day"][keep], r["truth"][keep]),
                    rmse(r["ode"][keep], r["truth"][keep]),
                )
            )
    o = np.array(out)
    print(
        f"{lab}, only hidden days with 2+ logged meals: n={len(o)} patients | Chhaya {np.median(o[:, 0]):.1f}, shrunk control {np.median(o[:, 1]):.1f}, average day {np.median(o[:, 2]):.1f}, physiology {np.median(o[:, 3]):.1f}"
        f" | Chhaya vs control: median {np.median(o[:, 0] - o[:, 1]):+.2f}, better in {100 * np.mean(o[:, 0] < o[:, 1]):.0f}%, one-sided p = {wil(o[:, 0] - o[:, 1], 'less'):.2g}"
        f" | physiology alone vs control: median {np.median(o[:, 3] - o[:, 1]):+.2f}, p = {wil(o[:, 3] - o[:, 1], 'less'):.2g}"
    )

section("11. MEAL BY MEAL: does the predicted 2-hour rise track the observed rise in the hidden window?")


def rises(r, key):
    t, x = r["t_test"], r[key] if isinstance(key, str) else key
    obs, pred = [], []
    for tm, c in zip(r["meal_t"], np.nan_to_num(r["meal_carb"]), strict=False):
        if c < 10 or tm < SPLIT or tm + 120 > t[-1]:
            continue
        m = (t >= tm) & (t <= tm + 120)
        if m.sum() < 5:
            continue
        obs.append(r["truth"][m].max() - np.interp(tm, t, r["truth"]))
        pred.append(x[m].max() - np.interp(tm, t, x))
    return np.array(obs), np.array(pred)


for grp, lab in ((TEST, "test"), (DEV, "dev")):
    out = {}
    for key, name in (
        ("ode", "physiology"),
        ("twin", "Chhaya"),
        ("day", "average day"),
        ("p_none", "placebo: no meal log"),
    ):
        per, po, pp = [], [], []
        for r in grp:
            o, p = rises(r, key)
            if o.size >= 5 and np.std(p) > 0:
                per.append(np.corrcoef(o, p)[0, 1])
            po += list(o)
            pp += list(p)
        out[name] = (np.median(per), len(per), np.corrcoef(po, pp)[0, 1], len(po))
    print(
        lab,
        " | ".join(
            f"{n}: per-patient r {v[0]:.2f} (n={v[1]}), pooled r {v[2]:.2f} ({v[3]} meals)"
            for n, v in out.items()
        ),
    )

section(
    "12. THE CLINICAL SUMMARY: can it estimate time in range, and does it beat 'same as the sensor fortnight'?"
)
rows = []
for r in main:
    tr = time_in_ranges(r["truth"])
    tc = r["tod0"] + r["cal_t"]
    sig_day = float(
        np.sqrt(np.mean((r["cal_truth"] - lodo_average_day(tc // 1440, tc, r["cal_truth"])) ** 2))
    )
    day_tir = float(100 * np.mean(norm.cdf((180 - r["day"]) / sig_day) - norm.cdf((70 - r["day"]) / sig_day)))
    carry = time_in_ranges(r["cal_truth"])
    rows.append(
        dict(
            rec=r["rec"],
            dev=r["dev"],
            group=r["group"],
            tir_true=tr["tir"],
            point=abs(time_in_ranges(r["twin"])["tir"] - tr["tir"]),
            predictive=abs(r["pred"]["tir"] - tr["tir"]),
            day_point=abs(time_in_ranges(r["day"])["tir"] - tr["tir"]),
            day_predictive=abs(day_tir - tr["tir"]),
            carry_forward=abs(carry["tir"] - tr["tir"]),
            tbr_pred=abs(r["pred"]["tbr"] - tr["tbr"]),
            tbr_carry=abs(carry["tbr"] - tr["tbr"]),
            tar_pred=abs(r["pred"]["tar"] - tr["tar"]),
            tar_carry=abs(carry["tar"] - tr["tar"]),
            gmi_twin=abs(gmi_percent(r["twin"].mean()) - gmi_percent(r["truth"].mean())),
            gmi_carry=abs(gmi_percent(r["cal_truth"].mean()) - gmi_percent(r["truth"].mean())),
        )
    )
C = pd.DataFrame(rows)
cols = [
    "point",
    "predictive",
    "day_point",
    "day_predictive",
    "carry_forward",
    "tbr_pred",
    "tbr_carry",
    "tar_pred",
    "tar_carry",
    "gmi_twin",
    "gmi_carry",
]
print("median absolute error (TIR/TBR/TAR in percentage points, GMI in % units):")
print(C.groupby("dev")[cols].median().round(2).rename(index={True: "dev", False: "test"}).to_string())
print("by group, all patients:")
print(C.groupby("group")[["tir_true"] + cols[:5]].median().round(1).to_string())
ct = C[~C.dev]
print(
    f"test patients: Chhaya predictive TIR better than carry-forward in {100 * np.mean(ct.predictive < ct.carry_forward):.0f}% (p = {wil(ct.predictive - ct.carry_forward):.2g}, two-sided)"
)

section(
    "13. A DIFFERENT CALIBRATION WINDOW: drop day 1 of every recording, then calibrate on the next 5 days"
)
S = pd.DataFrame(
    [
        dict(
            rec=r["rec"],
            dev=r["dev"],
            group=r["group"],
            twin=r["metrics"]["twin_rmse"],
            day=r["metrics"]["day_rmse"],
            ode=r["metrics"]["ode_rmse"],
            tir=r["metrics"]["twin_tir_err"],
            cov=r["metrics"]["twin_cov80"],
        )
        for r in shift
        if r["metrics"] is not None
    ]
)
print("usable recordings:", len(S), "of", len(shift))
for flag, lab in ((False, "test"), (True, "dev")):
    d = S[S.dev == flag]
    x = (d.twin - d.day).to_numpy()
    print(
        f"  {lab}: n={len(d)} Chhaya {d.twin.median():.1f} vs average day {d.day.median():.1f} | median diff {np.median(x):+.2f} | better in {100 * np.mean(x < 0):.0f}% | one-sided p = {wil(x, 'less'):.2g} | TIR error {d.tir.median():.1f} | band covers {100 * d['cov'].mean():.0f}%"
    )

section(
    "14. IS THE HIDDEN 'TRUTH' REAL DATA?  Straight-line stretches in the Libre trace (a sign of filled-in gaps)"
)
L = pd.DataFrame(
    [
        dict(rec=r["rec"][-3:], longest_h=r["linear_longest"] * 15 / 60, pct=100 * r["linear_frac"])
        for r in main
    ]
)
print(
    "patients with a perfectly straight stretch of 2 h or more: %d of %d; worst: %s"
    % (
        (L.longest_h >= 2).sum(),
        len(L),
        L.sort_values("longest_h", ascending=False).head(4).round(1).to_dict("records"),
    )
)
print(f"median share of readings inside straight stretches: {L.pct.median():.2f}%")
