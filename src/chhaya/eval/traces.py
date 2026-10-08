"""Reveal traces: the hidden readings beside the estimate and its band, one file per recording and k.

Expiry by day and the band recalibration need every hidden reading; the Gate 2 results folder keeps one row
per recording. Per-reading arrays are patient data, not aggregates (rule 6), so they are written under
DATA_DIR/derived/traces, which git ignores, and never under results/. Development and test patients go to
separate folders and a reader names the split it wants, so a development run cannot open a test file.

The estimator is `run_reveal` with its defaults, exactly as Gate 2 ran it. `gate2_differences` checks that:
a trace must give back the error and the coverage the Gate 2 results folder holds for that recording.

Usage: python -m chhaya.eval.traces --dataset cgmacros --split dev --k 3 5 --jobs 6
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import DATA_DIR, RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import differences
from chhaya.eval.gate2 import load
from chhaya.eval.metrics import coverage, rmse
from chhaya.eval.reveal import Reveal, run_reveal, why_skipped

TRACE_DIR = DATA_DIR / "derived" / "traces"
GATE2_TEST = RESULTS_DIR / "gate2" / "cgmacros-test" / "metrics.csv"
ARRAYS = ("t", "truth", "twin", "lo", "hi", "shrunk", "day", "cal_t", "cal_truth")
SPLITS = ("dev", "test")


def split_of(patient_id: str) -> str:
    return "dev" if is_dev_patient(patient_id) else "test"


def trace_of(rec: Recording, out: Reveal) -> dict:
    """What later passes need from one reveal. `day` is the average-day baseline, `shrunk` the control."""
    return {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "dataset": rec.dataset,
        "group": str(rec.static.get("group")),
        "k_days": float(out.k_days),
        "t": np.asarray(out.t_test, dtype=float),
        "truth": out.truth,
        "twin": out.twin,
        "lo": out.lo,
        "hi": out.hi,
        "shrunk": out.shrunk,
        "day": out.day,
        "cal_t": np.asarray(out.cal_t, dtype=float),
        "cal_truth": out.cal_truth,
    }


def trace_path(trace: dict, root: Path = TRACE_DIR) -> Path:
    name = f"{trace['rec_id']}-k{trace['k_days']:g}.npz"
    return root / trace["dataset"] / split_of(trace["patient_id"]) / name


def save_trace(trace: dict, root: Path = TRACE_DIR) -> Path:
    path = trace_path(trace, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **trace)
    return path


def load_traces(dataset: str, split: str, k_days: float, root: Path = TRACE_DIR) -> list[dict]:
    """Every cached trace of one split at one k. Only that split's folder is opened."""
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")
    out = []
    for path in sorted((root / dataset / split).glob(f"*-k{k_days:g}.npz")):
        with np.load(path, allow_pickle=False) as z:
            tr = {k: (z[k].item() if z[k].ndim == 0 else z[k]) for k in z.files}
        if split_of(tr["patient_id"]) != split:
            raise ValueError(f"{path} holds a patient of the other split")
        out.append(tr)
    return out


def gate2_differences(traces: list[dict], metrics: pd.DataFrame, tol: float = 1e-6) -> list[str]:
    """Where these traces and a Gate 2 metrics table disagree. Empty: the traces are the estimator Gate 2 scored.

    Checked per recording and k: the estimate's RMSE and the coverage of its 80 % band. A recording Gate 2
    scored at one of these k and that has no trace is a difference too.
    """
    scored = metrics[metrics["twin_rmse"].notna()]
    want = {(r.rec_id, float(r.k_days)): r for r in scored.itertuples()}
    out, seen = [], set()
    for tr in traces:
        key = (tr["rec_id"], float(tr["k_days"]))
        if key not in want:
            out.append(f"{key[0]} k={key[1]:g}: not scored by the Gate 2 run")
            continue
        seen.add(key)
        found = {
            "twin_rmse": rmse(tr["twin"], tr["truth"]),
            "twin_cov80": coverage(tr["truth"], tr["lo"], tr["hi"]),
        }
        committed = {c: getattr(want[key], c) for c in found}
        out += [f"{key[0]} k={key[1]:g} {d}" for d in differences(found, committed, tol)]
    ks = {float(tr["k_days"]) for tr in traces}
    out += [
        f"{r} k={k:g}: scored by the Gate 2 run, no trace" for r, k in want if k in ks and (r, k) not in seen
    ]
    return out


def require_gate2(traces: list[dict], metrics_path: Path = GATE2_TEST) -> None:
    """Stop a pass over test patients whose traces are not the estimator the confirmatory Gate 2 run scored."""
    if not metrics_path.exists():
        raise SystemExit(f"{metrics_path} is missing: the traces cannot be checked against the Gate 2 run")
    bad = gate2_differences(traces, pd.read_csv(metrics_path))
    if bad:
        raise SystemExit(
            "the traces do not reproduce the Gate 2 run; nothing was written:\n" + "\n".join(bad)
        )


def _work(rec: Recording, k_list: list[float], n_members: int, root: Path) -> list[dict]:
    """All (recording, k) index rows for one recording. Top-level so worker processes can import it."""
    rows = []
    for k in k_list:
        base = {
            "rec_id": rec.rec_id,
            "patient_id": rec.patient_id,
            "k_days": k,
            "error": None,
            "skipped": None,
        }
        try:
            out = run_reveal(rec, k, n_members=n_members)
        except (RuntimeError, ValueError) as err:
            rows.append({**base, "error": str(err)})  # a failed fit keeps its row (rule 4)
            continue
        if out is None:
            rows.append({**base, "skipped": why_skipped(rec, k)})
            continue
        save_trace(trace_of(rec, out), root)
        rows.append({**base, "twin_rmse": out.metrics["twin_rmse"], "twin_cov80": out.metrics["twin_cov80"]})
    return rows


def build(
    recs: list[Recording], k_list: list[float], n_members: int = 200, jobs: int = 1, root: Path = TRACE_DIR
) -> pd.DataFrame:
    """Run the reveal for every recording and k, save the traces, return one index row each."""
    work = partial(_work, k_list=k_list, n_members=n_members, root=root)
    if jobs > 1:
        with ProcessPoolExecutor(jobs) as pool:
            per_rec = list(pool.map(work, recs))
    else:
        per_rec = [work(rec) for rec in recs]
    return pd.DataFrame([row for rows in per_rec for row in rows])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="cgmacros")
    ap.add_argument("--split", choices=SPLITS, required=True)
    ap.add_argument("--k", type=float, nargs="+", default=[3.0, 5.0])
    ap.add_argument("--members", type=int, default=200)
    ap.add_argument("--jobs", type=int, default=1, help="worker processes; results do not depend on it")
    args = ap.parse_args()
    recs = [r for r in load(args.dataset) if split_of(r.patient_id) == args.split]
    index = build(recs, args.k, args.members, args.jobs)
    folder = TRACE_DIR / args.dataset
    folder.mkdir(parents=True, exist_ok=True)
    index.to_csv(folder / f"index-{args.split}.csv", index=False)
    done = index["twin_rmse"].notna() if "twin_rmse" in index.columns else pd.Series(False, index=index.index)
    print(
        f"{int(done.sum())} traces written under {folder / args.split}; "
        f"{int(index['skipped'].notna().sum())} skipped, {int(index['error'].notna().sum())} failed"
    )
    if args.dataset == "cgmacros" and args.split == "test" and GATE2_TEST.exists():
        metrics = pd.read_csv(GATE2_TEST)
        bad = [d for k in args.k for d in gate2_differences(load_traces("cgmacros", "test", k), metrics)]
        print(
            "Reproduces the Gate 2 run."
            if not bad
            else "DOES NOT reproduce the Gate 2 run:\n" + "\n".join(bad)
        )


if __name__ == "__main__":
    main()
