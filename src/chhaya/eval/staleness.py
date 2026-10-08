"""The staleness alarm on real drift (Amendment 3, "Staleness alarm" and the note on the descriptive outputs).

A recording has drifted when its hidden-window sensor mean differs from its calibration mean by more than
20 mg/dL. The alarm reads fingersticks only. Its threshold is set on development recordings so that at most
10 % of those that did not drift would alarm; test recordings then report AUROC, sensitivity, false alarms and
days to alarm. Descriptive: no bar.

Three things are reported beside it, because a cumulative sum over more fingersticks can only grow: the same
sum over the first two days only, which every recording in the cohort has (`early`); the plainest thing a
doctor could do, the fingerstick average against the report's mean (`plain`); and how well the number of
fingersticks alone separates drifted recordings.

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
    refuse_second_pass,
    table,
    write_outputs,
)
from chhaya.eval.fingersticks import REGISTERED_FILTER, REGISTERED_K, estimates, why_not
from chhaya.eval.gate2 import _git
from chhaya.twin.assimilate import FilterConfig
from chhaya.twin.staleness import cusum, first_alarm, surprise_scale

FALSE_ALARMS = 0.10
N_BOOT = 2000
EARLY_DAYS = 2.0  # every recording in the cohort has two hidden days, so this window is the same for all
REGISTERED_OBS_SD = 15.0  # the filter's fingerstick spread, part of the registered scale of a surprise
# the cumulative sum; the same sum over the first two days; the fingerstick average against the report's mean
SCORES = ("score", "early", "plain")
COUNT = "n_sticks"  # not a score: how well the number of fingersticks alone separates drifted recordings
FOLDER = RESULTS_DIR / "staleness"


def score_recording(rec: Recording, k_days: float, pooled: tuple[float, float]) -> dict | None:
    """Drift label and alarm statistics of one recording in the cohort of section F; None outside it.

    The label reads the hidden sensor. Nothing else does: the surprises come from `estimates` as committed,
    and their scale and the report's mean from the calibration window.
    """
    if why_not(rec, k_days) is not None:
        return None
    cfg = FilterConfig()
    e = estimates(rec, k_days, cfg, pooled)
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    scale = surprise_scale(profile_sigma(rec.start.hour * 60 + rec.start.minute + t[cal], g[cal]), cfg.obs_sd)
    stat = cusum(e["z"] / scale)
    days = (e["ft"] - split) / 1440.0  # when each fingerstick was taken, in days since the sensor
    first = stat[days < EARLY_DAYS]
    a, b = e["map"]
    drift = float(g[~cal].mean() - g[cal].mean())
    return {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "drift": drift,
        "drifted": bool(abs(drift) > MOVED_MGDL),
        "score": float(stat.max()) if stat.size else 0.0,
        "early": float(first.max()) if first.size else 0.0,
        "plain": abs(float(np.mean(a + b * e["cbg"])) - float(g[cal].mean())) if e["cbg"].size else 0.0,
        COUNT: int(e["ft"].size),
        "days": days,
        "stat": stat,
    }


def threshold(scores, drifted, rate: float = FALSE_ALARMS) -> float:
    """The smallest observed score that at most `rate` of the recordings without drift lie above."""
    quiet = np.sort(np.asarray(scores, dtype=float)[~np.asarray(drifted, dtype=bool)])
    if quiet.size == 0:
        raise ValueError("no recording without drift: a false-alarm rate cannot be set")
    above = quiet.size - np.searchsorted(quiet, quiet, side="right")  # how many lie above each score
    return float(quiet[np.argmax(above <= rate * quiet.size + 1e-9)])


def _auroc(y, s) -> float:
    y = np.asarray(y, dtype=int)
    return float(roc_auc_score(y, s)) if 0 < y.sum() < y.size else float("nan")


def boot_auroc(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """AUROC of each score, of the fingerstick count, and of the sum minus the plain average, with 95 %
    intervals from resampling patients.

    A resample in which every recording drifted, or none did, has no AUROC and is left out; the number of
    resamples used is returned.
    """
    names = (*SCORES, COUNT)
    y = df["drifted"].to_numpy(dtype=int)
    s = {name: df[name].to_numpy(dtype=float) for name in names}
    patient = df["patient_id"].to_numpy()
    groups = [np.flatnonzero(patient == u) for u in pd.unique(patient)]
    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {name: [] for name in (*names, "diff")}
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        if 0 < y[idx].sum() < idx.size:
            got = {name: _auroc(y[idx], s[name][idx]) for name in names}
            for name in names:
                draws[name].append(got[name])
            draws["diff"].append(got["score"] - got["plain"])
    point = {name: _auroc(y, s[name]) for name in names}
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
        # the rates above are a handful of recordings: say how many
        "drifted_alarmed": int((fired & y).sum()),
        "n_drifted": int(y.sum()),
        "quiet_alarmed": int((fired & ~y).sum()),
        "n_quiet": int((~y).sum()),
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
        "median_fingersticks": float(df[COUNT].median()),
        "auroc": boot_auroc(df, n_boot),
        **{name: alarms(rows, name, thresholds[name]) for name in SCORES},
    }


def run(
    scored: list[Recording],
    dev_recs: list[Recording],
    k_list: list[float],
    confirmatory: bool,
    n_boot: int = N_BOOT,
) -> dict:
    """Thresholds from development recordings, then `scored` under them. The pooled map is the development one.

    The first k is the primary one. A k at which no threshold can be set keeps its row, with the reason.
    """
    shared = {r.patient_id for r in scored} & {r.patient_id for r in dev_recs}
    if confirmatory and shared:
        raise ValueError(f"{len(shared)} patients are both scored and used to set the thresholds")
    result = {"confirmatory": confirmatory, "false_alarm_target": FALSE_ALARMS, "by_k": []}
    for i, k in enumerate(k_list):
        head = {"k_days": k, "primary": i == 0}
        pooled = pooled_line(dev_recs, k)
        dev = [row for row in (score_recording(r, k, pooled) for r in dev_recs) if row]
        drifted = [r["drifted"] for r in dev]
        try:
            thresholds = {name: threshold([r[name] for r in dev], drifted) for name in SCORES}
        except ValueError as err:
            result["by_k"].append({**head, "n_recordings": 0, "error": f"development recordings: {err}"})
            continue
        rows = [row for row in (score_recording(r, k, pooled) for r in scored) if row]
        block = {**head, **block_for(rows, thresholds, k, n_boot)}
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
        "`score` is the cumulative sum of fingerstick surprises against the frozen profile; `early` is the same "
        "sum over the first two days after the sensor only; `plain` is the fingerstick average against the "
        "report's mean. Drift: the hidden sensor mean more than 20 mg/dL from the calibration mean. The label "
        "and the scores look back over the same hidden window.",
    ]
    for block in result["by_k"]:
        role = "primary" if block.get("primary") else "reported"
        lines += ["", f"## k = {block['k_days']:g} days ({role})", ""]
        if "error" in block:
            lines.append(f"No threshold could be set: {block['error']}.")
            continue
        if not block["n_recordings"]:
            lines.append("No recording in the cohort.")
            continue
        au = block["auroc"]
        lines += [
            f"{block['n_recordings']} recordings of {block['n_patients']} patients; {block['n_drifted']} drifted "
            f"({block['n_drifted_down']} downwards). Thresholds from {block['development']['n_without_drift']} "
            f"development recordings without drift. Median {block['median_fingersticks']:g} fingersticks in the "
            "hidden window.",
            "",
            table(
                [
                    {
                        "alarm": name,
                        "auroc": au[name]["auroc"],
                        "lo": au[name]["lo"],
                        "hi": au[name]["hi"],
                        "threshold": block[name]["threshold"],
                        "caught": f"{block[name]['drifted_alarmed']} of {block[name]['n_drifted']}",
                        "false alarms": f"{block[name]['quiet_alarmed']} of {block[name]['n_quiet']}",
                        "median days to alarm": block[name].get("median_days_to_alarm"),
                    }
                    for name in SCORES
                ],
                digits=3,
            ),
            "",
            f"AUROC difference, cumulative sum minus plain: {au['diff']['difference']:.3f} "
            f"({au['diff']['lo']:.3f} to {au['diff']['hi']:.3f}); {au['n_resamples_used']} resamples used. "
            f"AUROC of the number of fingersticks alone: {au[COUNT]['auroc']:.3f} "
            f"({au[COUNT]['lo']:.3f} to {au[COUNT]['hi']:.3f}).",
        ]
    return "\n".join(lines) + "\n"


def check_frozen(cfg: FilterConfig) -> None:
    """A surprise and its scale are registered with the frozen filter: refuse any other defaults."""
    if (cfg.tau_min, cfg.slow) != REGISTERED_FILTER:
        raise SystemExit(f"the code defaults are not the frozen design {REGISTERED_FILTER}")
    if cfg.obs_sd != REGISTERED_OBS_SD:
        raise SystemExit(
            f"the fingerstick spread is {cfg.obs_sd:g} mg/dL where {REGISTERED_OBS_SD:g} is registered"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test recordings; this is done once")
    args = ap.parse_args()
    out_dir: Path = FOLDER / ("shanghai" if args.confirm else "shanghai-dev")
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        check_frozen(FilterConfig())
        refuse_second_pass(out_dir)
    prov = provenance(args.confirm, k=list(REGISTERED_K), n_boot=N_BOOT)
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    result = run(scored, dev_recs, list(REGISTERED_K), args.confirm)
    report = _report(result)
    write_outputs(out_dir, result, report, prov)
    print(report)


if __name__ == "__main__":
    main()
