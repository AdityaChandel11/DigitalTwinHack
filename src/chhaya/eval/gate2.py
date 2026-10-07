"""Gate 2: does the sensor-off twin beat the patient's own average day?

The pass bars are fixed in docs/PREREGISTRATION.md before this is run on real data. Only a full run on
the held-out test split is confirmatory (Amendment 1).
Usage: python -m chhaya.eval.gate2 --dataset cgmacros --split test --k 3 5 7
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import pandas as pd
from scipy.stats import wilcoxon

from chhaya.config import REPO_ROOT, RESULTS_DIR, SEED, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.reveal import RevealConfig, run_reveal, why_skipped
from chhaya.twin.priors import population_prior

PRIMARY_K = 5
TIR_BAR = 10.0  # percentage points
COVERAGE_BAND = (0.70, 0.90)
MAX_FAILED_FRAC = 0.10  # more failed fits than this and the run cannot be GO (Amendment 2)


def _rows_for(rec: Recording, k_list: list[int], n_members: int, prior: str = "record") -> list[dict]:
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
            # None lets the reveal build the record-informed prior, as every Gate 2 run did
            out = run_reveal(
                rec, k, prior=population_prior() if prior == "population" else None, n_members=n_members
            )
        except (RuntimeError, ValueError) as err:
            rows.append({**base, "k_days": k, "error": str(err), "skipped": None})
            print(f"{rec.rec_id} k={k}: FAILED {err}", flush=True)
            continue
        if out is None:
            rows.append({**base, "k_days": k, "error": None, "skipped": why_skipped(rec, k)})
        else:
            rows.append({**base, "k_days": k, "error": None, "skipped": None, **out.metrics})
        shown = "skipped" if out is None else round(out.metrics["twin_rmse"], 1)
        print(f"{rec.rec_id} k={k}: {shown}", flush=True)
    return rows


def run_cohort(
    recs: list[Recording], k_list: list[int], n_members: int = 200, jobs: int = 1, prior: str = "record"
) -> pd.DataFrame:
    """One row per (recording, k). Failed fits keep a row with an `error`, skipped recordings a row with
    the reason in `skipped`, so nothing vanishes silently.

    `jobs` only spreads recordings over processes; every fit is seeded, so the rows do not depend on it.
    """
    work = partial(_rows_for, k_list=k_list, n_members=n_members, prior=prior)
    if jobs > 1:
        with ProcessPoolExecutor(jobs) as pool:
            per_rec = list(pool.map(work, recs))
    else:
        per_rec = [work(rec) for rec in recs]
    return pd.DataFrame([row for rows in per_rec for row in rows])


def _paired_p(diff: pd.Series) -> float:
    """One-sided Wilcoxon signed-rank p that the differences sit below zero; NaN with too few patients."""
    testable = len(diff) >= 6 and bool((diff != 0).any())
    return float(wilcoxon(diff, alternative="less").pvalue) if testable else float("nan")


def summarise(df: pd.DataFrame, k: int = PRIMARY_K) -> dict:
    """Patient-level summary at calibration length k (recordings of one patient are averaged first)."""
    at_k = df[df["k_days"] == k] if "k_days" in df.columns else df.iloc[:0]
    n_skipped = int(at_k["skipped"].notna().sum()) if "skipped" in at_k.columns else 0
    n_failed = int(at_k["error"].notna().sum()) if "error" in at_k.columns else 0
    attempted = len(at_k) - n_skipped
    out = {
        "k_days": k,
        "n_patients": 0,
        "n_failed": n_failed,
        "n_skipped": n_skipped,
        "frac_failed": n_failed / attempted if attempted else 0.0,
    }
    if "twin_rmse" not in df.columns:
        return out
    per = at_k[at_k["twin_rmse"].notna()].groupby("patient_id").mean(numeric_only=True)
    diff = per["twin_rmse"] - per["day_rmse"]
    out.update(
        {
            "n_patients": int(len(per)),
            "twin_rmse": float(per["twin_rmse"].median()),
            "day_rmse": float(per["day_rmse"].median()),
            "mean_rmse": float(per["mean_rmse"].median()),
            "median_diff": float(diff.median()),
            "frac_twin_better": float((diff < 0).mean()),
            "wilcoxon_p": _paired_p(diff),
            "twin_mard": float(per["twin_mard"].median()),
            "twin_tir_err": float(per["twin_tir_err"].median()),
            "day_tir_err": float(per["day_tir_err"].median()),
            "cov80": float(per["twin_cov80"].mean()),
            "cov80_min": float(per["twin_cov80"].min()),
            "cov80_max": float(per["twin_cov80"].max()),
        }
    )
    if "shrunk_rmse" in per.columns:
        # Half average day, half mean: a control with no meals and no model. What Chhaya gains over the raw
        # average day is partly plain smoothing; what it gains over this control is what the physiology adds.
        vs = per["twin_rmse"] - per["shrunk_rmse"]
        out.update(
            {
                "shrunk_rmse": float(per["shrunk_rmse"].median()),
                "median_diff_vs_shrunk": float(vs.median()),
                "frac_better_vs_shrunk": float((vs < 0).mean()),
                "p_vs_shrunk": _paired_p(vs),
            }
        )
    if "floor_rmse" in per.columns:
        out["floor_rmse"] = float(per["floor_rmse"].median())
    return out


def verdict(s: dict) -> dict:
    """Apply the pre-registered bars. GO needs P1 and P2 and few failed fits; P3 is reported."""
    if s["n_patients"] == 0:
        return {
            "p1_beats_average_day": False,
            "p2_tir_within_bar": False,
            "p3_band_calibrated": False,
            "few_failed_fits": False,
            "go": False,
        }
    p1 = s["median_diff"] < 0 and s["wilcoxon_p"] < 0.05
    p2 = s["twin_tir_err"] <= TIR_BAR
    p3 = COVERAGE_BAND[0] <= s["cov80"] <= COVERAGE_BAND[1]
    few = s.get("frac_failed", 0.0) <= MAX_FAILED_FRAC  # failed fits may be the hard patients
    return {
        "p1_beats_average_day": bool(p1),
        "p2_tir_within_bar": bool(p2),
        "p3_band_calibrated": bool(p3),
        "few_failed_fits": bool(few),
        "go": bool(p1 and p2 and few),
    }


def _clean(x):
    """NaN and infinities become null, so the summary file is strict JSON."""
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [_clean(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def write_report(df: pd.DataFrame, k_list: list[int], out_dir: Path, confirmatory: bool = False) -> dict:
    """Write metrics.csv, summary.json and report.md. `confirmatory` is true only for a full test-split run."""
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "metrics.csv", index=False)
    summaries = [summarise(df, k) for k in k_list]
    primary_run = PRIMARY_K in k_list
    primary = next(s for s in summaries if s["k_days"] == PRIMARY_K) if primary_run else summaries[0]
    v = verdict(primary)
    if not primary_run:
        v["go"] = False  # only the pre-registered k can give a verdict
    v["primary_k_run"] = primary_run
    v["confirmatory"] = confirmatory
    result = {"summaries": summaries, "primary": primary, "verdict": v}
    (out_dir / "summary.json").write_text(json.dumps(_clean(result), indent=2, allow_nan=False))

    lines = ["# Gate 2 — sensor-off twin vs the patient's own average day", ""]
    scope = (
        ""
        if confirmatory
        else " (not confirmatory: only a full run on the held-out test split supports a claim)"
    )
    if primary_run:
        lines.append(f"Verdict at k={primary['k_days']} days: **{'GO' if v['go'] else 'NO-GO'}**{scope}")
    else:
        lines.append(
            f"No verdict: the pre-registered primary k = {PRIMARY_K} was not run. "
            f"The figures below (k = {primary['k_days']}) are exploratory{scope}."
        )
    lines += ["", "```json", json.dumps(v, indent=2), "```", ""]
    table = pd.DataFrame(summaries)
    numeric = [
        c for c in table.columns if table[c].dtype.kind == "f" and not c.startswith(("wilcoxon_p", "p_vs"))
    ]
    table[numeric] = table[numeric].round(3)
    for col in ("wilcoxon_p", "p_vs_shrunk"):
        if col in table.columns:
            table[col] = table[col].map(lambda p: f"{p:.2g}")  # rounding would print 3e-05 as 0
    lines.append(table.to_markdown(index=False))
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def results_dir(dataset: str, split: str, limit: int | None, tag: str | None = None) -> Path:
    """Where a run writes. Partial, per-split and tagged runs get their own folder so they cannot overwrite a full run."""
    name = dataset + ("" if split == "all" else f"-{split}") + (f"-limit{limit}" if limit else "")
    return RESULTS_DIR / "gate2" / (name + (f"-{tag}" if tag else ""))


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def provenance(args: argparse.Namespace) -> dict:
    """What produced a results folder: code version, settings and seed. Changes with every commit by design."""
    status = _git("status", "--porcelain", "--", "src")
    return {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes_in_src": None if status is None else bool(status),
        "dataset": args.dataset,
        "split": args.split,
        "limit": args.limit,
        "k": args.k,
        "members": args.members,
        "seed": SEED,
        "prior": args.prior,
        "tag": args.tag,
        "config": RevealConfig()._asdict(),
    }


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
    ap.add_argument("--prior", choices=["record", "population"], default="record")
    ap.add_argument(
        "--tag",
        default=None,
        help="suffix for the results folder; required for any run that is not Gate 2 itself",
    )
    args = ap.parse_args()
    recs = load(args.dataset)
    if args.split != "all":
        recs = [r for r in recs if is_dev_patient(r.patient_id) == (args.split == "dev")]
    recs = recs[: args.limit]
    df = run_cohort(recs, args.k, args.members, args.jobs, args.prior)
    out_dir = results_dir(args.dataset, args.split, args.limit, args.tag)
    confirmatory = args.split == "test" and args.limit is None and args.tag is None and args.prior == "record"
    result = write_report(df, args.k, out_dir, confirmatory=confirmatory)
    (out_dir / "provenance.json").write_text(json.dumps(provenance(args), indent=2))
    print(json.dumps(_clean(result["primary"]), indent=2))
    print(json.dumps(result["verdict"], indent=2))
    p = result["primary"].get("wilcoxon_p")
    if p is None or math.isnan(p):
        print("Too few patients for the signed-rank test; the verdict is NO-GO by construction.")


if __name__ == "__main__":
    main()
