"""Experiment F, second pass: what the frozen fingerstick estimator says at the level a doctor reads.

Amendment 3, section F lists, besides F1 and F2: error in mean glucose, time above 180 and time in range over
the hidden window against the stale sensor report and the plain fingerstick average, and error by day since the
sensor came off. The confirmatory run deferred them and said so (note of 8 Oct); how each is computed is fixed
in the note on the descriptive outputs. Descriptive: no bar, no verdict.

`estimates` and `FilterConfig` are used exactly as committed for the confirmatory run. Before anything is
written, this pass must reproduce that run's cohort size, control error and both paired differences.

Usage: python -m chhaya.eval.fingersticks_report             (development patients)
       python -m chhaya.eval.fingersticks_report --confirm   (test patients, once)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import (
    MIN_DAY_PATIENTS,
    REPORT_KEYS,
    aging,
    check_committed,
    daily_rows,
    day_report,
    differences,
    estimated_report,
    glucose_report,
    paired_summary,
    pooled_line,
    profile_sigma,
    provenance,
    slope_per_day,
    summarise_days,
    table,
    write_outputs,
)
from chhaya.eval.fingersticks import (
    REGISTERED_FILTER,
    REGISTERED_K,
    estimates,
    why_not,
)
from chhaya.eval.gate2 import _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.eval.metrics import rmse
from chhaya.twin.assimilate import FilterConfig

# who states the report of the hidden window: the old sensor report, the fingersticks alone, the estimates
SOURCES = ("stale", "sticks", "sticks_raw", "shape", "live", "hindsight", "hindsight_count")
COMPARISONS = (
    ("hindsight", "stale"),
    ("hindsight", "sticks"),
    ("hindsight", "shape"),
    ("live", "stale"),
    ("sticks", "stale"),
)
DAY_COLS = [
    "patient_id",
    "day",
    "control_rmse",
    "live_rmse",
    "hindsight_rmse",
    "abs_dmean",
    "dmean",
    "moved",
    "abs_dtar",
    "hindsight_mean_err",
]
DAY_PAIRS = (
    ("live_rmse", "control_rmse"),
    ("hindsight_rmse", "control_rmse"),
    ("hindsight_mean_err", "abs_dmean"),
)
CHECKED = ("n_patients", "control_rmse", "live_median_diff", "hindsight_median_diff")
FOLDER = RESULTS_DIR / "fingersticks"
# the runs this pass must reproduce: the confirmatory one, and the frozen design on development patients
COMMITTED = {
    True: FOLDER / "shanghai" / "summary.json",
    False: FOLDER / "shanghai-dev-tau120" / "summary.json",
}


def stated(rec: Recording, k_days: float, pooled: tuple[float, float]) -> tuple[dict, dict]:
    """The report of the hidden window as each source states it, and the estimates behind the last four.

    No hidden sensor reading is used: the stale report and the spread come from the calibration window, the
    fingerstick averages from the fingersticks, the estimates from `estimates` as committed.
    """
    e = estimates(rec, k_days, FilterConfig(), pooled)
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    assert (e["t"] >= split).all() and (e["ft"] >= split).all(), "something from before the split is scored"
    sigma = profile_sigma(rec.start.hour * 60 + rec.start.minute + t[cal], g[cal])
    a, b = e["map"]
    reports = {
        "stale": glucose_report(g[cal]),
        "sticks": glucose_report(a + b * e["cbg"]),  # on the sensor's scale, by the line the estimator uses
        "sticks_raw": glucose_report(e["cbg"]),  # as a logbook would average them
        "shape": estimated_report(e["control"], sigma),
        "live": estimated_report(e["live"], sigma),
        "hindsight": estimated_report(e["hindsight"], sigma),
        "hindsight_count": glucose_report(e["hindsight"]),  # no spread: the plain count, for comparison
    }
    return reports, {**e, "sigma": sigma}


def recording_rows(
    rec: Recording, k_days: float, pooled: tuple[float, float]
) -> tuple[dict, list[dict]] | None:
    """The report-level row and the by-day rows of a recording in the cohort of section F; None outside it."""
    if why_not(rec, k_days) is not None:
        return None
    reports, e = stated(rec, k_days, pooled)
    split = k_days * 1440.0
    truth = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)[rec.cgm["t_min"].to_numpy(dtype=float) >= split]
    true, stale = glucose_report(truth), reports["stale"]
    ids = {"rec_id": rec.rec_id, "patient_id": rec.patient_id, "k_days": k_days}
    row = {
        **ids,
        "n_sticks": len(e["ft"]),
        "sticks_per_day": len(rec.fingersticks) / (rec.n_min / 1440.0),
        "sticks_per_day_hidden": len(e["ft"]) / ((rec.n_min - split) / 1440.0),
        "sigma": e["sigma"],
        "control_rmse": rmse(e["control"], truth),
        "live_rmse": rmse(e["live"], truth),
        "hindsight_rmse": rmse(e["hindsight"], truth),
        **aging(true, stale),
    }
    for name, r in reports.items():
        row.update({f"{name}_{key}_err": abs(r[key] - true[key]) for key in REPORT_KEYS})
    days = []
    shown = {name: e[name] for name in ("control", "live", "hindsight")}
    for d in daily_rows(e["t"], split, truth, shown):
        err = abs(d["hindsight_mean"] - d["day_mean"])
        days.append({**ids, **d, **aging(day_report(d), stale), "hindsight_mean_err": err})
    return row, days


def density(per: pd.DataFrame) -> dict:
    """How often the cohort tests, and whether the patients who test more gain more from the live estimate."""
    out: dict = {}
    for col in ("sticks_per_day", "sticks_per_day_hidden"):
        q = per[col].quantile([0.0, 0.25, 0.5, 0.75, 1.0]).to_numpy()
        out[col] = dict(zip(("min", "q25", "median", "q75", "max"), (float(v) for v in q), strict=True))
    gain = per["live_rmse"] - per["control_rmse"]
    testable = len(per) >= MIN_DAY_PATIENTS and np.ptp(per["sticks_per_day_hidden"]) > 0 and np.ptp(gain) > 0
    rho = spearmanr(per["sticks_per_day_hidden"], gain) if testable else None
    out["spearman_density_vs_live_gain"] = float(rho.statistic) if rho else float("nan")
    out["spearman_p"] = float(rho.pvalue) if rho else float("nan")
    return out


def summarise(df: pd.DataFrame) -> dict:
    """Patient-level medians (recordings of one patient are averaged first) and paired comparisons."""
    per = df.groupby("patient_id").mean(numeric_only=True)
    out: dict = {
        "n_patients": int(len(per)),
        "recordings": int(df["rec_id"].nunique()),
        "control_rmse": float(per["control_rmse"].median()),
        "live_median_diff": float((per["live_rmse"] - per["control_rmse"]).median()),
        "hindsight_median_diff": float((per["hindsight_rmse"] - per["control_rmse"]).median()),
        "aged": {
            "abs_dmean": float(per["abs_dmean"].median()),
            "dmean": float(per["dmean"].median()),
            "share_moved": float(per["moved"].mean()),
            "abs_dtar": float(per["abs_dtar"].median()),
            "abs_dtir": float(per["abs_dtir"].median()),
        },
        "density": density(per),
    }
    for key in REPORT_KEYS:
        block: dict = {"errors": {name: float(per[f"{name}_{key}_err"].median()) for name in SOURCES}}
        for a, b in COMPARISONS:
            block[f"{a}_vs_{b}"] = paired_summary(per, f"{a}_{key}_err", f"{b}_{key}_err")
        out[key] = block
    return out


def block_for(recs: list[Recording], k_days: float, pooled: tuple[float, float]) -> dict:
    """Everything reported at one k for one set of recordings."""
    got = [x for x in (recording_rows(r, k_days, pooled) for r in recs) if x is not None]
    if not got:
        return {"k_days": k_days, "n_patients": 0}
    df = pd.DataFrame([row for row, _ in got])
    days = pd.DataFrame([d for _, ds in got for d in ds])
    block = {"k_days": k_days, **summarise(df), "by_day": [], "slopes": []}
    if len(days):
        block["by_day"] = summarise_days(days[DAY_COLS], DAY_PAIRS)
        block["slopes"] = [slope_per_day(days, c) for c in ("control_rmse", "hindsight_rmse", "abs_dmean")]
    return block


def _report(result: dict) -> str:
    lines = ["# Fingersticks, second pass: the report a doctor reads", ""]
    lines.append(
        "Test patients, read a second time after F1 and F2 were known. Descriptive: no bar."
        if result["confirmatory"]
        else "Development patients. Not confirmatory."
    )
    lines += [
        "",
        f"Filter: `{result['filter']}` (frozen). Errors are absolute, medians over patients: mean glucose in "
        "mg/dL, time above 180 and time in range in percentage points. `stale` is the report of the calibration "
        "days; `sticks` the average of the hidden fingersticks on the sensor's scale and `sticks_raw` as read; "
        "`shape` the daily shape alone; `hindsight_count` counts crossings of the estimate with no spread.",
    ]
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days", ""]
        if not block["n_patients"]:
            lines.append("No recording in the cohort.")
            continue
        aged, dens = block["aged"], block["density"]
        lines += [
            f"{block['n_patients']} patients, {block['recordings']} recordings. Since the calibration days the "
            f"mean moved by a median of {aged['abs_dmean']:.1f} mg/dL (signed {aged['dmean']:+.1f}); "
            f"{100 * aged['share_moved']:.0f} % of patients moved more than 20.",
            "",
            f"Fingersticks per day: {dens['sticks_per_day']['median']:.1f} over the recording "
            f"(quartiles {dens['sticks_per_day']['q25']:.1f} to {dens['sticks_per_day']['q75']:.1f}), "
            f"{dens['sticks_per_day_hidden']['median']:.1f} in the hidden window.",
            "",
            table([{"source": s, **{k: block[k]["errors"][s] for k in REPORT_KEYS}} for s in SOURCES], digits=2),
            "",
            table(
                [
                    {"what": key, **block[key][f"{a}_vs_{b}"]}
                    for key in REPORT_KEYS
                    for a, b in COMPARISONS
                    if block[key][f"{a}_vs_{b}"]["n_patients"]
                ],
                digits=3,
            ),
            "",
            "By day since the sensor came off (RMSE against the hidden sensor, mg/dL):",
            "",
            table(block["by_day"], ["day", "n_patients", "control_rmse", "live_rmse", "hindsight_rmse", "abs_dmean",
                                    "share_moved", "hindsight_mean_err"], digits=2),
        ]  # fmt: skip
    return "\n".join(lines) + "\n"


def run(
    scored: list[Recording],
    dev_recs: list[Recording],
    k_list: list[float],
    out_dir: Path,
    confirmatory: bool,
    committed: dict | None = None,
) -> dict:
    """Score `scored` at each k; the pooled line of the sensor map always comes from `dev_recs`.

    With `committed` (the summary of the run this pass repeats), nothing is written unless the cohort size,
    the control error and both paired differences come out the same at every k.
    """
    result = {"confirmatory": confirmatory, "filter": FilterConfig()._asdict(), "by_k": []}
    for i, k in enumerate(k_list):
        pooled = pooled_line(dev_recs, k)
        block = block_for(scored, k, pooled)
        if committed is not None:
            want = committed["by_k"][i]
            if want["k_days"] != k:
                raise SystemExit(f"the committed run has k = {want['k_days']:g} where this pass has {k:g}")
            bad = differences(block, {key: want["rules"]["all"][key] for key in CHECKED})
            if bad:
                raise SystemExit(
                    f"this pass does not reproduce the committed run at k = {k:g}, so it is not the frozen "
                    "estimator and nothing was written: " + "; ".join(bad)
                )
        if confirmatory and block["n_patients"]:
            block["density_dev"] = block_for(dev_recs, k, pooled).get("density")
        result["by_k"].append(block)
    write_outputs(out_dir, result, _report(result))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="read the test patients; this is done once")
    args = ap.parse_args()
    out_dir = FOLDER / ("shanghai-report" if args.confirm else "shanghai-dev-report")
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        cfg = FilterConfig()
        if (cfg.tau_min, cfg.slow) != REGISTERED_FILTER:
            raise SystemExit(f"the code defaults are not the frozen design {REGISTERED_FILTER}")
        refuse_second_run(out_dir)
    path = COMMITTED[args.confirm]
    if args.confirm and not path.exists():
        raise SystemExit(f"{path} is missing: the confirmatory run this pass repeats cannot be checked")
    committed = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    assert args.confirm or all(is_dev_patient(r.patient_id) for r in scored)
    run(scored, dev_recs, list(REGISTERED_K), out_dir, args.confirm, committed)
    prov = provenance(args.confirm, k=list(REGISTERED_K), reproduces=str(path) if committed else None)
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
