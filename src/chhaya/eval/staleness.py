"""The staleness alarm on real drift (Amendment 3, "Staleness alarm" and the note on the descriptive outputs).

A recording has drifted when its hidden-window sensor mean differs from its calibration mean by more than
20 mg/dL. The alarm reads fingersticks only. Its threshold is set on development recordings so that at most
10 % of those that did not drift would alarm; test recordings then report AUROC, sensitivity, false alarms and
days to alarm. Beside it, the plainest thing a doctor could do: the fingerstick average against the report's
mean, with a threshold set the same way. Descriptive: no bar.

Usage: python -m chhaya.eval.staleness             (development recordings; the threshold is in-sample)
       python -m chhaya.eval.staleness --confirm   (test recordings, once)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from chhaya.config import RESULTS_DIR, SEED, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import (
    MOVED_MGDL,
    check_committed,
    pooled_line,
    profile_sigma,
    provenance,
    table,
    write_outputs,
)
from chhaya.eval.fingersticks import REGISTERED_K, estimates, why_not
from chhaya.eval.gate2 import _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.twin.assimilate import FilterConfig
from chhaya.twin.staleness import cusum, first_alarm, surprise_scale

FALSE_ALARMS = 0.10
N_BOOT = 2000
SCORES = ("score", "plain")  # the cumulative sum, and the fingerstick average against the report's mean
FOLDER = RESULTS_DIR / "staleness"


def score_recording(rec: Recording, k_days: float, pooled: tuple[float, float]) -> dict | None:
    """Drift label and alarm statistics of one recording in the cohort of section F; None outside it.

    The label reads the hidden sensor. Nothing else does: the surprises come from `estimates` as committed,
    and their scale and the report's mean from the calibration window.
    """
    if why_not(rec, k_days) is not None:
        return None
    e = estimates(rec, k_days, FilterConfig(), pooled)
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    scale = surprise_scale(
        profile_sigma(rec.start.hour * 60 + rec.start.minute + t[cal], g[cal]), FilterConfig().obs_sd
    )
    stat = cusum(e["z"] / scale)
    a, b = e["map"]
    drift = float(g[~cal].mean() - g[cal].mean())
    return {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "drift": drift,
        "drifted": bool(abs(drift) > MOVED_MGDL),
        "score": float(stat.max()) if stat.size else 0.0,
        "plain": abs(float(np.mean(a + b * e["cbg"])) - float(g[cal].mean())) if e["cbg"].size else 0.0,
        "n_sticks": int(e["ft"].size),
        "days": (e["ft"] - split) / 1440.0,  # when each fingerstick was taken, in days since the sensor
        "stat": stat,
    }


def threshold(scores, drifted, rate: float = FALSE_ALARMS) -> float:
    """The smallest observed score that at most `rate` of the recordings without drift lie above."""
    quiet = np.asarray(scores, dtype=float)[~np.asarray(drifted, dtype=bool)]
    if quiet.size == 0:
        raise ValueError("no recording without drift: a false-alarm rate cannot be set")
    return float(np.quantile(quiet, 1.0 - rate, method="higher"))


def _auroc(y, s) -> float:
    y = np.asarray(y, dtype=int)
    return float(roc_auc_score(y, s)) if 0 < y.sum() < y.size else float("nan")


def boot_auroc(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """AUROC of both scores and of their difference, with 95 % intervals from resampling patients.

    A resample in which every recording drifted, or none did, has no AUROC and is left out; the number of
    resamples used is returned.
    """
    y = df["drifted"].to_numpy(dtype=int)
    s = {name: df[name].to_numpy(dtype=float) for name in SCORES}
    patient = df["patient_id"].to_numpy()
    groups = [np.flatnonzero(patient == u) for u in pd.unique(patient)]
    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {"score": [], "plain": [], "diff": []}
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        if 0 < y[idx].sum() < idx.size:
            a, b = _auroc(y[idx], s["score"][idx]), _auroc(y[idx], s["plain"][idx])
            draws["score"].append(a), draws["plain"].append(b), draws["diff"].append(a - b)
    point = {name: _auroc(y, s[name]) for name in SCORES}
    point["diff"] = point["score"] - point["plain"]
    out: dict = {"n_resamples_used": len(draws["diff"])}
    for name, values in draws.items():
        lo, hi = np.percentile(values, [2.5, 97.5]) if values else (float("nan"), float("nan"))
        out[name] = {
            "auroc" if name != "diff" else "difference": point[name],
            "lo": float(lo),
            "hi": float(hi),
        }
    return out


def alarms(rows: list[dict], name: str, h: float) -> dict:
    """What a threshold does on a set of recordings: who alarms, and for the cumulative sum, when."""
    y = np.array([r["drifted"] for r in rows], dtype=bool)
    fired = np.array([r[name] > h for r in rows], dtype=bool)
    out = {
        "threshold": h,
        "sensitivity": float(fired[y].mean()) if y.any() else float("nan"),
        "false_alarm_rate": float(fired[~y].mean()) if (~y).any() else float("nan"),
        "n_alarms": int(fired.sum()),
    }
    if name == "score":
        when = [first_alarm(r["days"], r["stat"], h) for r, yes in zip(rows, y & fired, strict=True) if yes]
        out["median_days_to_alarm"] = float(np.median(when)) if when else float("nan")
    return out


def block_for(rows: list[dict], thresholds: dict[str, float], k_days: float, n_boot: int = N_BOOT) -> dict:
    """Everything reported at one k for one set of scored recordings."""
    if not rows:
        return {"k_days": k_days, "n_recordings": 0}
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("days", "stat")} for r in rows])
    return {
        "k_days": k_days,
        "n_recordings": int(len(df)),
        "n_patients": int(df["patient_id"].nunique()),
        "n_drifted": int(df["drifted"].sum()),
        "n_drifted_down": int((df["drift"] < -MOVED_MGDL).sum()),
        "median_abs_drift": float(df["drift"].abs().median()),
        "auroc": boot_auroc(df, n_boot),
        # a sum over more fingersticks can only grow: how much of the separation is just more testing?
        "auroc_of_fingerstick_count": _auroc(df["drifted"], df["n_sticks"]),
        **{name: alarms(rows, name, thresholds[name]) for name in SCORES},
    }


def run(
    scored: list[Recording],
    dev_recs: list[Recording],
    k_list: list[float],
    confirmatory: bool,
    n_boot: int = N_BOOT,
) -> dict:
    """Thresholds from development recordings, then `scored` under them. The pooled map is the development one."""
    result = {"confirmatory": confirmatory, "false_alarm_target": FALSE_ALARMS, "by_k": []}
    for k in k_list:
        pooled = pooled_line(dev_recs, k)
        dev = [row for row in (score_recording(r, k, pooled) for r in dev_recs) if row]
        if not dev:
            result["by_k"].append({"k_days": k, "n_recordings": 0})
            continue
        drifted = [r["drifted"] for r in dev]
        thresholds = {name: threshold([r[name] for r in dev], drifted) for name in SCORES}
        rows = [row for row in (score_recording(r, k, pooled) for r in scored) if row]
        block = block_for(rows, thresholds, k, n_boot)
        block["development"] = {"n_recordings": len(dev), "n_without_drift": int(len(dev) - sum(drifted))}
        result["by_k"].append(block)
    return result


def _report(result: dict) -> str:
    lines = ["# Staleness alarm on real drift", ""]
    lines.append(
        "Test recordings; thresholds were set on development recordings. Descriptive: no bar."
        if result["confirmatory"]
        else "Development recordings: the thresholds are set on these same recordings, so this is in-sample."
    )
    lines += [
        "",
        "`score` is the cumulative sum of fingerstick surprises against the frozen profile; `plain` is the "
        "fingerstick average against the report's mean. Drift: the hidden sensor mean more than 20 mg/dL from the "
        "calibration mean.",
    ]
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days", ""]
        if not block["n_recordings"]:
            lines.append("No recording in the cohort.")
            continue
        au = block["auroc"]
        lines += [
            f"{block['n_recordings']} recordings of {block['n_patients']} patients; {block['n_drifted']} drifted "
            f"({block['n_drifted_down']} downwards). Thresholds from {block['development']['n_without_drift']} "
            "development recordings without drift.",
            "",
            table(
                [
                    {
                        "alarm": name,
                        "auroc": au[name]["auroc"],
                        "lo": au[name]["lo"],
                        "hi": au[name]["hi"],
                        **block[name],
                    }
                    for name in SCORES
                ],
                digits=3,
            ),
            "",
            f"AUROC difference, cumulative sum minus plain: {au['diff']['difference']:.3f} "
            f"({au['diff']['lo']:.3f} to {au['diff']['hi']:.3f}); {au['n_resamples_used']} resamples used. "
            f"AUROC of the number of fingersticks alone: {block['auroc_of_fingerstick_count']:.3f}.",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test recordings; this is done once")
    args = ap.parse_args()
    out_dir: Path = FOLDER / ("shanghai" if args.confirm else "shanghai-dev")
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        refuse_second_run(out_dir)
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    result = run(scored, dev_recs, list(REGISTERED_K), args.confirm)
    write_outputs(out_dir, result, _report(result), provenance(args.confirm, k=list(REGISTERED_K)))
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
