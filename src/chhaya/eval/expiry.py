"""Expiry: how fast one sensor wear stops describing the patient (Amendment 3, "Descriptive, no bar").

Three outputs, none with a bar. How each is computed is fixed in the note on the descriptive outputs in
docs/PREREGISTRATION.md.

  shanghai   the daily shape from the first k days against each later day: the profile alone, no fingersticks,
             every recording that can be run (wider than the cohort of section F)
  cgmacros   the same by day for the twin, its control and its band, from cached reveal traces
  cases      the Shanghai patients recorded again weeks later: the first wear's profile on the later wear

Day 0 in every by-day table is "inside the wear": one day of the calibration window against its other days.
It is built from k - 1 days where a later day is read against k, so it slightly overstates how wrong an unaged
report is. For the report's mean that is a few percent and each later day is compared with it; for the point
error of the shape it is larger, so there the slope inside each patient is the measure and day 0 is context.

Usage: python -m chhaya.eval.expiry {shanghai,cgmacros,cases} [--confirm]
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline
from chhaya.eval.descriptive import (
    aging,
    check_committed,
    daily_rows,
    day_index,
    day_report,
    excess_over_day_zero,
    glucose_report,
    inside_the_wear,
    profile_sigma,
    provenance,
    slope_per_day,
    summarise_days,
    table,
    write_outputs,
)
from chhaya.eval.events import drug_flags
from chhaya.eval.gate2 import _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.eval.metrics import rmse
from chhaya.eval.reveal import why_skipped
from chhaya.eval.traces import load_traces, require_gate2, trace_provenance

BIN = 30
K_LIST = (3.0, 5.0)
FOLDER = RESULTS_DIR / "expiry"
INSULIN_ROUTES = {"sc", "iv", "csii"}
PROFILE_COLS = [
    "patient_id",
    "rec_id",
    "day",
    "control_rmse",
    "abs_dmean",
    "dmean",
    "moved",
    "abs_dtar",
    "abs_dtir",
]
TWIN_COLS = [
    "patient_id",
    "rec_id",
    "day",
    "twin_rmse",
    "control_rmse",
    "avgday_rmse",
    "cov80",
    "twin_mean_err",
    "abs_dmean",
    "dmean",
    "moved",
    "abs_dtar",
]
# the columns of a by-day table in report.md; summary.json holds every column
SHANGHAI_SHOWN = [
    "day",
    "n_patients",
    "share_of_cohort",
    "control_rmse",
    "abs_dmean",
    "dmean",
    "share_moved",
    "abs_dtar",
]
TWIN_SHOWN = [
    "day",
    "n_patients",
    "share_of_cohort",
    "twin_rmse",
    "control_rmse",
    "avgday_rmse",
    "cov80",
    "abs_dmean",
    "share_moved",
]
TWIN_PAIRS = (("twin_rmse", "control_rmse"), ("twin_rmse", "avgday_rmse"), ("twin_mean_err", "abs_dmean"))


def _clock0(rec: Recording) -> int:
    return rec.start.hour * 60 + rec.start.minute


def daily_shape(rec: Recording, until: float | None = None) -> np.ndarray:
    """Half the patient's average day, half their mean, in 48 half-hour bins of clock time.

    Built from sensor readings before minute `until` (all of them when None). This is the control of section F.
    """
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    m = np.ones(t.size, dtype=bool) if until is None else t < until
    if not m.any():
        raise ValueError(f"{rec.rec_id}: no sensor reading before minute {until}")
    centres = np.arange(0, 1440, BIN) + BIN // 2
    return 0.5 * average_day_baseline((_clock0(rec) + t[m]) % 1440, g[m], centres, BIN) + 0.5 * float(
        g[m].mean()
    )


def shape_at(shape: np.ndarray, rec: Recording, t) -> np.ndarray:
    """A daily shape read at minutes `t` of recording `rec`, by that recording's own clock."""
    return shape[((_clock0(rec) + np.asarray(t, dtype=float)) % 1440).astype(int) // BIN]


def profile_rows(rec: Recording, k_days: float) -> list[dict] | None:
    """By-day rows of one recording for the profile alone; None when it cannot be run at k (Gate 2 rule).

    Day 0 is inside the wear. From day 1 on only the hidden readings are scored, against a shape and a report
    that were built before the split.
    """
    if why_skipped(rec, k_days) is not None:
        return None
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    stale = glucose_report(g[cal])
    control = shape_at(daily_shape(rec, split), rec, t[~cal])
    ids = {"rec_id": rec.rec_id, "patient_id": rec.patient_id, "k_days": k_days}
    rows = []
    floor = inside_the_wear(t[cal], g[cal])
    if floor is not None:
        rows.append({**ids, "day": 0, "control_rmse": profile_sigma(_clock0(rec) + t[cal], g[cal]), **floor})
    for d in daily_rows(t[~cal], split, g[~cal], {"control": control}):
        rows.append(
            {**ids, "day": d["day"], "control_rmse": d["control_rmse"], **aging(day_report(d), stale)}
        )
    return rows


def trace_rows(tr: dict) -> list[dict]:
    """By-day rows of one cached reveal trace: the twin, its control, the average day and the band."""
    split = float(tr["k_days"]) * 1440.0
    stale = glucose_report(tr["cal_truth"])
    ids = {
        "rec_id": tr["rec_id"],
        "patient_id": tr["patient_id"],
        "k_days": float(tr["k_days"]),
        "group": tr["group"],
    }
    rows = []
    floor = inside_the_wear(tr["cal_t"], tr["cal_truth"])
    if floor is not None:
        rows.append({**ids, "day": 0, **floor})
    day = day_index(tr["t"], split)
    inside = (tr["truth"] >= tr["lo"]) & (tr["truth"] <= tr["hi"])
    shown = {"twin": tr["twin"], "control": tr["shrunk"], "avgday": tr["day"]}
    for d in daily_rows(tr["t"], split, tr["truth"], shown):
        rows.append(
            {
                **ids,
                "day": d["day"],
                **{f"{name}_rmse": d[f"{name}_rmse"] for name in shown},
                "cov80": float(inside[day == d["day"]].mean()),
                "twin_mean_err": abs(d["twin_mean"] - d["day_mean"]),
                **aging(day_report(d), stale),
            }
        )
    return rows


def day_block(
    days: pd.DataFrame,
    k_days: float,
    cols: list[str],
    pairs: tuple = (),
    slopes: tuple = (),
    zero: tuple = (),
) -> dict:
    """Everything reported by day at one k: the table, the slope inside each patient, each day against day 0."""
    if days.empty:
        return {"k_days": k_days, "n_patients": 0}
    days = days.reindex(columns=[*cols, *(c for c in days.columns if c not in cols)])
    return {
        "k_days": k_days,
        "n_patients": int(days["patient_id"].nunique()),
        "recordings": int(days["rec_id"].nunique()),
        "by_day": summarise_days(days[cols], pairs),
        "slopes": [slope_per_day(days, c) for c in slopes],
        "against_day_zero": [row for c in zero for row in excess_over_day_zero(days, c)],
    }


def shanghai_block(recs: list[Recording], k_days: float) -> dict:
    skipped = Counter(w for w in (why_skipped(r, k_days) for r in recs) if w)
    rows = [row for r in recs for row in (profile_rows(r, k_days) or [])]
    slopes = ("control_rmse", "abs_dmean")
    block = day_block(pd.DataFrame(rows), k_days, PROFILE_COLS, (), slopes, ("abs_dmean",))
    return {**block, "skipped": dict(skipped)}


def cgmacros_block(traces: list[dict], k_days: float) -> dict:
    days = pd.DataFrame([row for tr in traces for row in trace_rows(tr)])
    slopes = ("twin_rmse", "control_rmse", "cov80", "abs_dmean")
    block = day_block(days, k_days, TWIN_COLS, TWIN_PAIRS, slopes, ("abs_dmean",))
    if len(days):
        t2d = days[days["group"] == "t2d"]
        block["groups"] = {str(g): int(n) for g, n in days.groupby("group")["patient_id"].nunique().items()}
        block["by_day_t2d"] = summarise_days(t2d.reindex(columns=TWIN_COLS), TWIN_PAIRS) if len(t2d) else []
    return block


def treatment(rec: Recording) -> dict:
    """What the files say about treatment during one wear. Compared across wears, never used as a predictor."""
    routes = set(rec.doses["route"]) if len(rec.doses) else set()
    listed = drug_flags(rec.static.get("agents"))["r_insulin"] == 1.0
    return {"insulin": bool(listed or routes & INSULIN_ROUTES), "pump": "csii" in routes}


def repeat_cases(recs: list[Recording]) -> list[dict]:
    """One row per later wear of a patient recorded more than once: the first wear's profile on the later wear.

    `old_profile_rmse` is the first wear's daily shape against the later wear's readings. Two yardsticks sit
    beside it: `fresh_profile_rmse`, the later wear's own shape built without the day being scored (what a new
    sensor wear would give), and `first_wear_rmse`, the same inside the first wear. A case series: no test.
    """
    by_patient: dict[str, list[Recording]] = {}
    for r in recs:
        by_patient.setdefault(r.patient_id, []).append(r)
    rows = []
    for pid, wears in sorted(by_patient.items()):
        if len(wears) < 2:
            continue
        first, *later = sorted(wears, key=lambda r: r.start)
        t1 = first.cgm["t_min"].to_numpy(dtype=float)
        g1 = first.cgm["glucose_mgdl"].to_numpy(dtype=float)
        shape, report = daily_shape(first), glucose_report(g1)
        before = treatment(first)
        agents = str(first.static.get("agents") or "").strip().lower()
        for rec in later:
            t = rec.cgm["t_min"].to_numpy(dtype=float)
            g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
            now = treatment(rec)
            between = (rec.start - first.start) / pd.Timedelta(days=1)
            rows.append(
                {
                    "patient_id": pid,
                    "dev": is_dev_patient(pid),
                    "later_rec": rec.rec_id,
                    "days_between_starts": float(between),
                    "days_since_first_sensor": float(between - first.n_min / 1440.0),
                    "first_wear_days": first.n_min / 1440.0,
                    "later_wear_days": rec.n_min / 1440.0,
                    "old_profile_rmse": rmse(shape_at(shape, rec, t), g),
                    "fresh_profile_rmse": profile_sigma(_clock0(rec) + t, g),
                    "first_wear_rmse": profile_sigma(_clock0(first) + t1, g1),
                    **aging(glucose_report(g), report),
                    "insulin_first": before["insulin"],
                    "insulin_later": now["insulin"],
                    "pump_first": before["pump"],
                    "pump_later": now["pump"],
                    "agents_changed": agents != str(rec.static.get("agents") or "").strip().lower(),
                }
            )
    return rows


def cases_block(recs: list[Recording]) -> dict:
    rows = repeat_cases(recs)
    if not rows:
        return {"n_patients": 0, "n_cases": 0, "cases": []}
    df = pd.DataFrame(rows)
    changed = (
        df["agents_changed"]
        | (df["insulin_first"] != df["insulin_later"])
        | (df["pump_first"] != df["pump_later"])
    )
    return {
        "n_patients": int(df["patient_id"].nunique()),
        "n_cases": int(len(df)),
        "unit": "later wear",  # the medians and counts below are over later wears, not patients
        "old_profile_rmse": float(df["old_profile_rmse"].median()),
        "fresh_profile_rmse": float(df["fresh_profile_rmse"].median()),
        "first_wear_rmse": float(df["first_wear_rmse"].median()),
        "abs_dmean": float(df["abs_dmean"].median()),
        "n_moved": int(df["moved"].sum()),
        "n_treatment_changed": int(changed.sum()),
        "cases": rows,
    }


def _by_day_report(title: str, note: str, result: dict, columns: list[str]) -> str:
    lines = [f"# {title}", "", note, ""]
    lines.append(
        "Test patients. Descriptive: no bar."
        if result["confirmatory"]
        else "Development patients. Not confirmatory."
    )
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days", ""]
        if not block["n_patients"]:
            lines.append("No recording could be run.")
            continue
        lines += [f"{block['n_patients']} patients, {block['recordings']} recordings.", ""]
        lines += [table(block["by_day"], columns, digits=2), "", "Change per day inside each patient:", ""]
        lines += [table(block["slopes"], digits=2), "", "Each day against the same patient's day 0:", ""]
        lines.append(table(block["against_day_zero"], digits=3))
        if block.get("skipped"):
            lines += ["", "Not run: " + "; ".join(f"{v} ({k})" for k, v in block["skipped"].items())]
    return "\n".join(lines) + "\n"


def _cases_report(result: dict) -> str:
    lines = [
        "# Expiry: patients recorded again (case series)",
        "",
        "The first wear's daily shape against the later wear. `fresh_profile_rmse` is what a new wear's own shape "
        "gives. A case series of a handful of patients under changing treatment: no test, no interval.",
        "",
        "All re-recorded patients."
        if result["confirmatory"]
        else "Development patients only. Not confirmatory.",
        "",
        f"{result['n_cases']} later wears of {result['n_patients']} patients. The table has one row per later "
        "wear, and the counts and medians in the summary are over wears: a patient recorded three times has two.",
        "",
    ]
    lines.append(table(result["cases"]))
    return "\n".join(lines) + "\n"


def run(what: str, confirm: bool, out_dir: Path) -> dict:
    """Load what the output needs, compute, write. Test patients are scored only with `confirm`.

    The Shanghai loader reads every workbook; the split is applied here, before anything is computed. CGMacros
    traces are read from one split's folder only.
    """
    split = "test" if confirm else "dev"
    if what == "cgmacros":
        result = {"confirmatory": confirm, "by_k": []}
        for k in K_LIST:
            traces = load_traces("cgmacros", split, k)
            if not traces:
                raise SystemExit(
                    f"no {split} traces at k = {k:g}: run python -m chhaya.eval.traces --split {split}"
                )
            if confirm:
                require_gate2(traces, k)
            result["by_k"].append(cgmacros_block(traces, k))
        note = "The twin (`twin`), its control with no meals (`control`) and the raw average day, by day since the sensor."
        report = _by_day_report("Expiry by day: CGMacros", note, result, TWIN_SHOWN)
    else:
        from chhaya.data.shanghai import load_all

        recs = load_all()
        if what == "shanghai":
            recs = [r for r in recs if is_dev_patient(r.patient_id) != confirm]
            result = {"confirmatory": confirm, "by_k": [shanghai_block(recs, k) for k in K_LIST]}
            note = "The daily shape of the first k days against each later day; no fingersticks are read."
            report = _by_day_report("Expiry by day: ShanghaiT2DM", note, result, SHANGHAI_SHOWN)
        else:
            # nothing is fitted across patients here, so the registered case series uses all of them
            recs = recs if confirm else [r for r in recs if is_dev_patient(r.patient_id)]
            result = {"confirmatory": confirm, **cases_block(recs)}
            report = _cases_report(result)
    built = trace_provenance("cgmacros", split) if what == "cgmacros" else None
    write_outputs(out_dir, result, report, provenance(confirm, output=what, k=list(K_LIST), traces=built))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["shanghai", "cgmacros", "cases"])
    ap.add_argument(
        "--confirm", action="store_true", help="read the test patients; this is done once per output"
    )
    args = ap.parse_args()
    out_dir = FOLDER / (args.what if args.confirm else f"{args.what}-dev")
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        refuse_second_run(out_dir)
    run(args.what, args.confirm, out_dir)
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
