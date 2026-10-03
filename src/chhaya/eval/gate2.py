"""Gate 2: does the sensor-off twin beat the patient's own average day?

The pass bars are fixed in docs/PREREGISTRATION.md before this is run on real data.
Usage: python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.reveal import run_reveal

PRIMARY_K = 5
TIR_BAR = 10.0  # percentage points
COVERAGE_BAND = (0.70, 0.90)


def _rows_for(rec: Recording, k_list: list[int], n_members: int) -> list[dict]:
    """All (recording, k) rows for one recording. Top-level so worker processes can import it."""
    base = {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "dataset": rec.dataset,
        "group": rec.static.get("group"),
        "dev": is_dev_patient(rec.patient_id),
    }
    rows = []
    for k in k_list:
        try:
            out = run_reveal(rec, k, n_members=n_members)
        except (RuntimeError, ValueError) as err:
            rows.append({**base, "k_days": k, "error": str(err)})
            continue
        if out is not None:
            rows.append({**base, "k_days": k, "error": None, **out.metrics})
        shown = "skipped" if out is None else round(out.metrics["twin_rmse"], 1)
        print(f"{rec.rec_id} k={k}: {shown}", flush=True)
    return rows


def run_cohort(recs: list[Recording], k_list: list[int], n_members: int = 200, jobs: int = 1) -> pd.DataFrame:
    """One row per (recording, k). Failed fits are kept as rows with an `error` so nothing vanishes silently.

    `jobs` only spreads recordings over processes; every fit is seeded, so the rows do not depend on it.
    """
    work = partial(_rows_for, k_list=k_list, n_members=n_members)
    if jobs > 1:
        with ProcessPoolExecutor(jobs) as pool:
            per_rec = list(pool.map(work, recs))
    else:
        per_rec = [work(rec) for rec in recs]
    return pd.DataFrame([row for rows in per_rec for row in rows])


def summarise(df: pd.DataFrame, k: int = PRIMARY_K) -> dict:
    """Patient-level summary at calibration length k (recordings of one patient are averaged first)."""
    if "twin_rmse" not in df.columns:
        return {"k_days": k, "n_patients": 0, "n_failed": int(len(df))}
    ok = df[(df["k_days"] == k) & df["twin_rmse"].notna()]
    per = ok.groupby("patient_id").mean(numeric_only=True)
    diff = per["twin_rmse"] - per["day_rmse"]
    testable = len(per) >= 6 and bool((diff != 0).any())
    out = {
        "k_days": k,
        "n_patients": int(len(per)),
        "n_failed": int(((df["k_days"] == k) & df["error"].notna()).sum()),
        "twin_rmse": float(per["twin_rmse"].median()),
        "day_rmse": float(per["day_rmse"].median()),
        "mean_rmse": float(per["mean_rmse"].median()),
        "median_diff": float(diff.median()),
        "frac_twin_better": float((diff < 0).mean()),
        "wilcoxon_p": float(wilcoxon(diff, alternative="less").pvalue) if testable else float("nan"),
        "twin_mard": float(per["twin_mard"].median()),
        "twin_tir_err": float(per["twin_tir_err"].median()),
        "day_tir_err": float(per["day_tir_err"].median()),
        "cov80": float(per["twin_cov80"].mean()),
    }
    if "floor_rmse" in per.columns:
        out["floor_rmse"] = float(per["floor_rmse"].median())
    return out


def verdict(s: dict) -> dict:
    """Apply the pre-registered bars. GO needs P1 and P2; P3 is reported and fixed later if it fails."""
    if s["n_patients"] == 0:
        return {
            "p1_beats_average_day": False,
            "p2_tir_within_bar": False,
            "p3_band_calibrated": False,
            "go": False,
        }
    p1 = s["median_diff"] < 0 and s["wilcoxon_p"] < 0.05
    p2 = s["twin_tir_err"] <= TIR_BAR
    p3 = COVERAGE_BAND[0] <= s["cov80"] <= COVERAGE_BAND[1]
    return {
        "p1_beats_average_day": bool(p1),
        "p2_tir_within_bar": bool(p2),
        "p3_band_calibrated": bool(p3),
        "go": bool(p1 and p2),
    }


def write_report(df: pd.DataFrame, k_list: list[int], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "metrics.csv", index=False)
    summaries = [summarise(df, k) for k in k_list]
    primary = next((s for s in summaries if s["k_days"] == PRIMARY_K), summaries[0])
    result = {"summaries": summaries, "primary": primary, "verdict": verdict(primary)}
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    lines = ["# Gate 2 — sensor-off twin vs the patient's own average day", ""]
    lines.append(f"Verdict at k={primary['k_days']} days: **{'GO' if result['verdict']['go'] else 'NO-GO'}**")
    lines += ["", "```json", json.dumps(result["verdict"], indent=2), "```", ""]
    lines.append(pd.DataFrame(summaries).round(3).to_markdown(index=False))
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def load(dataset: str) -> list[Recording]:
    if dataset == "cgmacros":
        from chhaya.data.cgmacros import load_all
    elif dataset == "shanghai":
        from chhaya.data.shanghai import load_all
    else:
        raise ValueError(f"unknown dataset {dataset!r}")
    return load_all()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="cgmacros")
    ap.add_argument("--k", type=int, nargs="+", default=[3, 5, 7])
    ap.add_argument("--limit", type=int, default=None, help="only the first N recordings (smoke run)")
    ap.add_argument("--members", type=int, default=200)
    ap.add_argument("--split", choices=["all", "dev", "test"], default="all", help="which patients")
    ap.add_argument("--jobs", type=int, default=1, help="worker processes; results do not depend on it")
    args = ap.parse_args()
    recs = load(args.dataset)
    if args.split != "all":
        recs = [r for r in recs if is_dev_patient(r.patient_id) == (args.split == "dev")]
    recs = recs[: args.limit]
    df = run_cohort(recs, args.k, args.members, args.jobs)
    suffix = "" if args.split == "all" else f"-{args.split}"
    result = write_report(df, args.k, RESULTS_DIR / "gate2" / f"{args.dataset}{suffix}")
    print(json.dumps(result["primary"], indent=2))
    print(json.dumps(result["verdict"], indent=2))
    if np.isnan(result["primary"].get("wilcoxon_p", np.nan)):
        print("Too few patients for the signed-rank test; the verdict is NO-GO by construction.")


if __name__ == "__main__":
    main()
