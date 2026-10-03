"""Break test, code stage: pathological inputs for the model, the loaders and the evaluation.

Each attack returns (status, detail). OK = handled sensibly (sane output or a clear error).
BREAK = NaN/inf, silently wrong result, or an unhelpful crash on a plausible input. WEAK = works but
unguarded. Run from the repo root: uv run python fuzz_model.py [fast|fits|shanghai ...]
"""

import dataclasses
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "tests")

import jax.numpy as jnp
import numpy as np
import pandas as pd
from conftest import make_recording

from chhaya.eval import gate2
from chhaya.eval.baselines import average_day_baseline, lodo_average_day
from chhaya.eval.metrics import score, time_in_ranges
from chhaya.eval.reveal import RevealConfig, run_reveal
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import default_z, meal_window, simulate_jit
from chhaya.units import mmol_to_mgdl

RESULTS = []


def attack(name):
    def deco(fn):
        t = time.time()
        try:
            status, detail = fn()
        except Exception as e:  # an uncaught exception on plausible input is a crash
            status, detail = "CRASH", f"{type(e).__name__}: {str(e)[:200]}"
        RESULTS.append((name, status, detail))
        print(f"[{status:5}] {name}: {detail}  ({time.time() - t:.0f}s)", flush=True)
        return fn

    return deco


def sim_mgdl(rec, z=None):
    inp, _, _ = build_inputs(rec)
    return mmol_to_mgdl(np.asarray(simulate_jit(jnp.asarray(default_z() if z is None else z), inp).gi))


def finite_report(g):
    ok = bool(np.isfinite(g).all())
    return ("OK" if ok else "BREAK"), f"finite={ok} min={np.nanmin(g):.0f} max={np.nanmax(g):.0f} mg/dL"


def with_static(rec, **kw):
    return dataclasses.replace(rec, static={**rec.static, **kw})


MODES = set(sys.argv[1:]) or {"fast", "fits", "shanghai"}
REC = make_recording(days=4, seed=11)

if "fast" in MODES:

    @attack("model: body weight 0 kg in the record")
    def _():
        return finite_report(sim_mgdl(with_static(REC, weight_kg=0.0)))

    @attack("model: body weight -70 kg")
    def _():
        return finite_report(sim_mgdl(with_static(REC, weight_kg=-70.0)))

    @attack("model: body weight 5000 kg (pounds or grams entered as kg)")
    def _():
        g = sim_mgdl(with_static(REC, weight_kg=5000.0))
        base = sim_mgdl(REC)
        flat = float(np.ptp(g)) < 0.2 * float(np.ptp(base))
        return (
            "WEAK" if flat else "OK"
        ), f"meal excursion {np.ptp(g):.1f} vs {np.ptp(base):.1f} mg/dL at 70 kg; no plausibility bound"

    @attack("model: fasting insulin 0, negative, NaN, 1e6")
    def _():
        out = [
            finite_report(sim_mgdl(with_static(REC, fasting_insulin_uu_ml=v)))[0]
            for v in (0.0, -5.0, float("nan"), 1e6)
        ]
        return ("OK" if set(out) == {"OK"} else "BREAK"), str(out)

    @attack("model: a single 1000 g carbohydrate meal")
    def _():
        m = REC.meals.copy()
        m.loc[0, "carb_g"] = 1000.0
        return finite_report(sim_mgdl(dataclasses.replace(REC, meals=m)))

    @attack("model: negative and NaN carbohydrate, NaN macros")
    def _():
        m = REC.meals.copy()
        m.loc[0, "carb_g"] = -40.0
        m.loc[1, "carb_g"] = np.nan
        m.loc[2, ["fat_g", "protein_g", "fibre_g"]] = np.nan
        return finite_report(sim_mgdl(dataclasses.replace(REC, meals=m)))

    @attack("model: negative fat/protein/fibre (slow-down factor below 1 or negative)")
    def _():
        m = REC.meals.copy()
        m["fat_g"] = -200.0
        g = sim_mgdl(dataclasses.replace(REC, meals=m))
        return finite_report(g)

    @attack("model: meals at minute 0 and at the last minute")
    def _():
        m = REC.meals.copy()
        m.loc[0, "t_min"] = 0.0
        m.loc[1, "t_min"] = float(REC.n_min - 1)
        return finite_report(sim_mgdl(dataclasses.replace(REC, meals=m)))

    @attack("model: 12 logged items within 2 hours (meal window holds 6)")
    def _():
        base = REC.meals.iloc[:1]
        burst = pd.concat(
            [base.assign(t_min=600.0 + 10.0 * i, carb_g=20.0) for i in range(12)], ignore_index=True
        )
        rec = dataclasses.replace(REC, meals=burst)
        inp, _, _ = build_inputs(rec)
        z = jnp.asarray(default_z())
        narrow = mmol_to_mgdl(np.asarray(simulate_jit(z, inp).gi))
        wide_inp = inp._replace(
            meal_win=jnp.asarray(meal_window(np.asarray(inp.meal_t)[:-1], rec.n_min, width=24))
        )
        wide = mmol_to_mgdl(np.asarray(simulate_jit(z, wide_inp).gi))
        d = float(np.max(np.abs(wide - narrow)))
        return (
            ("BREAK" if d > 1.0 else "OK"),
            f"peak {narrow.max():.0f} with 6-slot window vs {wide.max():.0f} with all 12; max difference {d:.1f} mg/dL",
        )

    @attack("model: activity of 0, 50 and NaN METs")
    def _():
        a = REC.activity.copy()
        a.loc[0:100, "met"] = 0.0
        a.loc[200:300, "met"] = 50.0
        a.loc[400:500, "met"] = np.nan
        return finite_report(sim_mgdl(dataclasses.replace(REC, activity=a)))

    @attack("model: recording that starts at 23:59")
    def _():
        rec = dataclasses.replace(REC, start=pd.Timestamp("2026-01-01 23:59"))
        g = sim_mgdl(rec)
        tod = 23 * 60 + 59 + REC.cgm["t_min"].to_numpy()
        day = average_day_baseline(tod, REC.cgm["glucose_mgdl"].to_numpy(), tod)
        return finite_report(np.concatenate([g, day]))

    @attack("schema: activity reading beyond the end of the recording")
    def _():
        a = pd.concat([REC.activity, pd.DataFrame({"t_min": [REC.n_min + 3.0], "met": [2.0], "hr": [80.0]})])
        try:
            build_inputs(dataclasses.replace(REC, activity=a))
        except ValueError as e:
            return "OK", f"rejected: {e}"
        return "BREAK", "accepted silently"

    @attack("schema: fractional activity timestamps (t_min = 10.7)")
    def _():
        a = REC.activity.copy()
        a["t_min"] = a["t_min"] + 0.7
        a = a[a["t_min"] < REC.n_min]
        inp, _, _ = build_inputs(dataclasses.replace(REC, activity=a))
        return "OK", f"truncated to whole minutes; max MET {float(inp.met.max()):.1f}"

    @attack("baseline: bin size that does not divide a day (bin_min=7)")
    def _():
        tod = np.arange(0, 1440, 5)
        try:
            average_day_baseline(tod, np.full(tod.size, 100.0), tod, bin_min=7)
        except IndexError as e:
            return "WEAK", f"IndexError for readings after 23:55 ({e}); the default 30 is safe"
        return "OK", "handled"

    @attack("baseline: leave-one-day-out when one day holds almost all readings")
    def _():
        t = np.r_[np.arange(0, 1440, 15), 1440 + 30]
        out = lodo_average_day(t // 1440, t, np.full(t.size, 120.0))
        return ("OK" if np.isfinite(out).all() else "BREAK"), f"finite={np.isfinite(out).all()}"

    @attack("metrics: empty input and all-identical input")
    def _():
        try:
            score([], [])
        except ValueError:
            pass
        s = score(np.full(10, 100.0), np.full(10, 100.0))
        t = time_in_ranges(np.array([70.0, 180.0]))
        return (
            "OK" if s["rmse"] == 0.0 and t["tir"] == 100.0 else "BREAK"
        ), f"rmse={s['rmse']} r={s['r']} tir={t['tir']}"

    @attack("gate2: summarise and verdict on an empty frame and an all-failed frame")
    def _():
        e = gate2.verdict(gate2.summarise(pd.DataFrame([])))
        f = pd.DataFrame(
            {"rec_id": ["a", "b"], "patient_id": ["a", "b"], "k_days": [5, 5], "error": ["x", "y"]}
        )
        s = gate2.summarise(f)
        return (
            "OK" if not e["go"] and not gate2.verdict(s)["go"] else "BREAK"
        ), f"empty go={e['go']}; all-failed n_failed={s['n_failed']} go={gate2.verdict(s)['go']}"

    @attack("gate2: half the fits failed at the primary k")
    def _():
        rows = [
            dict(
                rec_id=f"r{i}",
                patient_id=f"p{i}",
                k_days=5,
                error=None,
                twin_rmse=20.0 + i,
                day_rmse=25.0 + i,
                mean_rmse=26.0,
                twin_mard=10.0,
                twin_tir_err=3.0,
                day_tir_err=3.0,
                twin_cov80=0.8,
            )
            for i in range(8)
        ]
        rows += [
            dict(rec_id=f"x{i}", patient_id=f"x{i}", k_days=5, error="twin calibration diverged")
            for i in range(8)
        ]
        s = gate2.summarise(pd.DataFrame(rows))
        v = gate2.verdict(s)
        return (
            ("WEAK" if v["go"] else "OK"),
            f"n_patients={s['n_patients']} n_failed={s['n_failed']} go={v['go']} (GO is granted with half the cohort failed; failures are counted but do not block)",
        )

    @attack("gate2: report for a run that omits the pre-registered k = 5")
    def _():
        rows = [
            dict(
                rec_id=f"r{i}",
                patient_id=f"p{i}",
                k_days=3,
                error=None,
                twin_rmse=20.0 + i,
                day_rmse=25.0 + i,
                mean_rmse=26.0,
                twin_mard=10.0,
                twin_tir_err=3.0,
                day_tir_err=3.0,
                twin_cov80=0.8,
            )
            for i in range(8)
        ]
        with tempfile.TemporaryDirectory() as d:
            res = gate2.write_report(pd.DataFrame(rows), [3], Path(d))
            text = (Path(d) / "report.md").read_text(encoding="utf-8")
        flagged = "primary" in text.lower() or "not the pre-registered" in text.lower()
        return (
            "OK" if flagged or not res["verdict"]["go"] else "WEAK"
        ), f"verdict go={res['verdict']['go']} at k=3; report warns it is not the primary k: {flagged}"


if "fits" in MODES:

    def reveal_ok(out, extra=""):
        m = out.metrics
        bad = [k for k, v in m.items() if not np.isfinite(v) and not k.endswith("_r")]
        fin = np.isfinite(out.twin).all() and np.isfinite(out.lo).all() and np.isfinite(out.hi).all()
        return (
            ("OK" if fin and not bad else "BREAK"),
            f"twin {m['twin_rmse']:.1f} day {m['day_rmse']:.1f} cov {m['twin_cov80']:.2f} non-finite={bad} {extra}",
        )

    @attack("fit: sensor stuck on one value (constant CGM)")
    def _():
        return reveal_ok(
            run_reveal(dataclasses.replace(REC, cgm=REC.cgm.assign(glucose_mgdl=110.0)), 2, n_members=20)
        )

    @attack("fit: a full day of sensor dropout inside the calibration window")
    def _():
        rec = make_recording(days=5, seed=12)
        cgm = rec.cgm[(rec.cgm["t_min"] < 1440) | (rec.cgm["t_min"] >= 2880)]
        return reveal_ok(run_reveal(dataclasses.replace(rec, cgm=cgm), 3, n_members=20))

    @attack("fit: only the first 6 hours of each calibration day have readings")
    def _():
        rec = make_recording(days=5, seed=13)
        keep = (rec.cgm["t_min"] >= 3 * 1440) | (rec.cgm["t_min"] % 1440 < 360)
        out = run_reveal(dataclasses.replace(rec, cgm=rec.cgm[keep]), 3, n_members=20)
        return reveal_ok(out, "(average day must interpolate 18 unseen hours)")

    @attack("fit: one calibration day (k = 1), is the band still honest?")
    def _():
        covs = [
            run_reveal(make_recording(days=4, seed=s), 1, n_members=40).metrics["twin_cov80"]
            for s in (21, 22, 23)
        ]
        m = float(np.mean(covs))
        return (
            "WEAK" if m < 0.65 else "OK"
        ), f"80% band covers {m:.2f} on average over 3 synthetic patients ({[round(c, 2) for c in covs]})"

    @attack("fit: patient who logs no meals at all")
    def _():
        return reveal_ok(run_reveal(dataclasses.replace(REC, meals=REC.meals.iloc[:0]), 2, n_members=20))

    @attack("fit: patient with no band data")
    def _():
        return reveal_ok(
            run_reveal(dataclasses.replace(REC, activity=REC.activity.iloc[:0]), 2, n_members=20)
        )

    @attack("fit: very noisy sensor (SD 54 mg/dL)")
    def _():
        return reveal_ok(run_reveal(make_recording(days=4, seed=14, noise_mmol=3.0), 2, n_members=20))

    @attack("fit: every CGM timestamp duplicated")
    def _():
        cgm = pd.concat([REC.cgm, REC.cgm]).sort_values("t_min", kind="stable").reset_index(drop=True)
        return reveal_ok(run_reveal(dataclasses.replace(REC, cgm=cgm), 2, n_members=20))

    @attack("fit: record claims fasting glucose 400 mg/dL while the sensor reads about 130")
    def _():
        return reveal_ok(
            run_reveal(with_static(REC, fasting_glucose_mgdl=400.0), 2, n_members=20),
            "(prior far from the data)",
        )

    @attack("reveal: blend weight outside 0..1 (1.7)")
    def _():
        out = run_reveal(REC, 2, n_members=20, cfg=RevealConfig(blend=1.7))
        return (
            "WEAK",
            f"accepted without complaint; twin RMSE {out.metrics['twin_rmse']:.1f} (extrapolates away from the average day)",
        )

    @attack("reveal: k_days of 0, negative, fractional and longer than the recording")
    def _():
        got = {k: run_reveal(REC, k, n_members=20) for k in (0, -1, 50)}
        frac = run_reveal(REC, 2.5, n_members=20)
        ok = all(v is None for v in got.values()) and frac is not None
        return (
            "OK" if ok else "BREAK"
        ), f"0/-1/50 -> None: {all(v is None for v in got.values())}; 2.5 days works: {frac is not None}"

    @attack("reveal: ensemble of 1 member and of 0 members")
    def _():
        one = run_reveal(REC, 2, n_members=1)
        try:
            run_reveal(REC, 2, n_members=0)
            zero = "accepted"
        except Exception as e:
            zero = f"{type(e).__name__}: {str(e)[:80]}"
        return (
            "WEAK",
            f"1 member: band width {float(np.mean(one.hi - one.lo)):.1f} mg/dL (two identical quantiles of one draw); 0 members: {zero}",
        )


if "shanghai" in MODES:

    @attack("pipeline: Gate 2 runner on real Shanghai recordings (no macros yet, real fingersticks)")
    def _():
        from chhaya.data.shanghai import load_all

        recs = load_all()[:3]
        df = gate2.run_cohort(recs, [5], n_members=20)
        errs = df["error"].notna().sum() if "error" in df else 0
        s = gate2.summarise(df)
        return (
            ("OK" if errs == 0 else "BREAK"),
            f"{len(df)} rows, {errs} errors, summary n={s['n_patients']}; twin {s.get('twin_rmse', float('nan')):.1f} day {s.get('day_rmse', float('nan')):.1f}",
        )


print()
print("SUMMARY", {s: sum(1 for r in RESULTS if r[1] == s) for s in ("OK", "WEAK", "BREAK", "CRASH")})
for name, status, detail in RESULTS:
    if status != "OK":
        print(f"  {status}: {name} -> {detail}")
