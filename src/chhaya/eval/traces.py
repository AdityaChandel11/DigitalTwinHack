"""Reveal traces: the hidden readings beside the estimate and its band, one file per recording and k.

Expiry by day and the band recalibration need every hidden reading; the Gate 2 results folder keeps one row
per recording. Per-reading arrays are patient data, not aggregates (rule 6), so they are written under
DATA_DIR/derived/traces, which git ignores, and never under results/. Development and test patients go to
separate folders and a reader names the split it wants, so a development run cannot open a test file.

The estimator is `run_reveal` with its defaults, exactly as Gate 2 ran it. `gate2_differences` checks that:
a trace must give back the error and the coverage the Gate 2 results folder holds for that recording.

Tracing test patients runs the estimator on them, so it needs --confirm, committed code and the registered
settings, and it stops with an error unless the traces give back the Gate 2 run. It may be repeated: the
traces are a cache of numbers that are already committed, and every later pass checks them again.

Usage: python -m chhaya.eval.traces --split dev --jobs 6
       python -m chhaya.eval.traces --split test --confirm --jobs 6
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import DATA_DIR, RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import check_committed, differences, provenance
from chhaya.eval.gate2 import _git, load
from chhaya.eval.metrics import coverage, rmse
from chhaya.eval.reveal import Reveal, run_reveal, why_skipped

TRACE_DIR = DATA_DIR / "derived" / "traces"
GATE2_TEST = RESULTS_DIR / "gate2" / "cgmacros-test" / "metrics.csv"
INDEX_COLS = ["rec_id", "patient_id", "k_days", "error", "skipped", "twin_rmse", "twin_cov80"]
REGISTERED_K = [3.0, 5.0]  # the calibration lengths the descriptive outputs are registered at
REGISTERED_MEMBERS = 200  # the ensemble size of every Gate 2 run
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


def trace_file(root: Path, dataset: str, patient_id: str, rec_id: str, k_days: float) -> Path:
    return root / dataset / split_of(patient_id) / f"{rec_id}-k{k_days:g}.npz"


def trace_path(trace: dict, root: Path = TRACE_DIR) -> Path:
    return trace_file(root, trace["dataset"], trace["patient_id"], trace["rec_id"], trace["k_days"])


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


def gate2_differences(
    traces: list[dict], metrics: pd.DataFrame, ks: list[float] | None = None, tol: float = 1e-6
) -> list[str]:
    """Where these traces and a Gate 2 metrics table disagree. Empty: the traces are the estimator Gate 2 scored.

    Checked per recording and k: the estimate's RMSE and the coverage of its 80 % band. A recording Gate 2
    scored at one of the calibration lengths `ks` and that has no trace is a difference too. Name `ks` whenever
    a k could have no trace at all; left out, only the calibration lengths of the traces given are asked for.
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
    asked = {float(k) for k in ks} if ks is not None else {float(tr["k_days"]) for tr in traces}
    out += [
        f"{r} k={k:g}: scored by the Gate 2 run, no trace"
        for r, k in want
        if k in asked and (r, k) not in seen
    ]
    return out


def require_gate2(traces: list[dict], k_days: float, metrics_path: Path = GATE2_TEST) -> None:
    """Stop unless the traces at `k_days` are the estimator the confirmatory Gate 2 run scored: every recording
    it scored at that k has a trace, and each trace gives back its error and its coverage."""
    if not metrics_path.exists():
        raise SystemExit(f"{metrics_path} is missing: the traces cannot be checked against the Gate 2 run")
    metrics = pd.read_csv(metrics_path)
    if not ((metrics["k_days"] == k_days) & metrics["twin_rmse"].notna()).any():
        raise SystemExit(
            f"the Gate 2 run did not score k = {k_days:g}: there is nothing to check the traces against"
        )
    bad = gate2_differences(traces, metrics, ks=[k_days])
    if bad:
        raise SystemExit(
            "the traces do not reproduce the Gate 2 run, so they are not the estimator it scored:\n"
            + "\n".join(bad)
        )


def check_test_build(confirm: bool, src_status: str | None, k: list[float], members: int) -> None:
    """Tracing test patients runs the estimator on them: only on request, on committed code, as registered."""
    if not confirm:
        raise SystemExit("tracing test patients runs the estimator on them: pass --confirm")
    check_committed(src_status)
    if [float(x) for x in k] != REGISTERED_K or members != REGISTERED_MEMBERS:
        raise SystemExit(
            f"test patients are traced at the registered settings, k = {REGISTERED_K} and {REGISTERED_MEMBERS} "
            "members; remove --k and --members"
        )


def trace_provenance(dataset: str, split: str, root: Path = TRACE_DIR) -> dict | None:
    """What built the cached traces of one split (commit, settings), for the passes that read them."""
    path = root / dataset / f"build-{split}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


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
        # a recording this build cannot trace must not keep the trace of an earlier build
        old = trace_file(root, rec.dataset, rec.patient_id, rec.rec_id, k)
        try:
            out = run_reveal(rec, k, n_members=n_members)
        except (RuntimeError, ValueError) as err:
            old.unlink(missing_ok=True)
            rows.append({**base, "error": str(err)})  # a failed fit keeps its row (rule 4)
            continue
        if out is None:
            old.unlink(missing_ok=True)
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
    ap.add_argument("--k", type=float, nargs="+", default=REGISTERED_K)
    ap.add_argument("--members", type=int, default=REGISTERED_MEMBERS)
    ap.add_argument("--jobs", type=int, default=1, help="worker processes; results do not depend on it")
    ap.add_argument("--confirm", action="store_true", help="needed to trace the test patients")
    args = ap.parse_args()
    test = args.split == "test"
    if test:
        check_test_build(args.confirm, _git("status", "--porcelain", "--", "src"), args.k, args.members)
    recs = [r for r in load(args.dataset) if split_of(r.patient_id) == args.split]
    index = build(recs, args.k, args.members, args.jobs, TRACE_DIR).reindex(columns=INDEX_COLS)
    folder = TRACE_DIR / args.dataset
    folder.mkdir(parents=True, exist_ok=True)
    index.to_csv(folder / f"index-{args.split}.csv", index=False)
    n_traces = int(index["twin_rmse"].notna().sum())
    prov = provenance(
        test, dataset=args.dataset, split=args.split, k=args.k, members=args.members, n_traces=n_traces
    )
    (folder / f"build-{args.split}.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print(
        f"{n_traces} traces written under {folder / args.split}; "
        f"{int(index['skipped'].notna().sum())} skipped, {int(index['error'].notna().sum())} failed"
    )
    if test and args.dataset == "cgmacros":
        for k in args.k:
            require_gate2(load_traces("cgmacros", "test", k, TRACE_DIR), k, GATE2_TEST)
        print("Reproduces the Gate 2 run.")


if __name__ == "__main__":
    main()
