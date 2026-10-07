"""Experiment F: after the sensor comes off, what do fingersticks add to the patient's daily shape?

Bars are in docs/PREREGISTRATION.md, Amendment 3, section F. The filter design is chosen on development
patients; test patients are scored once, with the code defaults, and only with --confirm.
Usage: python -m chhaya.eval.fingersticks [--tau 120] [--slow]     (development patients)
       python -m chhaya.eval.fingersticks --confirm                (the one confirmatory run)

The estimator reads every hidden fingerstick. Pairing with a sensor reading is used only to score: which
fingersticks the estimate uses must not depend on which hidden sensor timestamps exist.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
from collections import Counter

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.pairs import paired
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline
from chhaya.eval.gate2 import _clean, _git, _paired_p
from chhaya.eval.gate3 import refuse_second_run
from chhaya.eval.metrics import clarke_zones, mard, rmse, within_15_15
from chhaya.eval.reveal import why_skipped
from chhaya.twin.assimilate import FilterConfig, deviation, map_source, pooled_map, sensor_map

BIN = 30
MIN_HIDDEN_DAYS = 2.0
MIN_STICKS_PER_DAY = 1.0
MIN_HIDDEN_PAIRS = 3
RULES = ("all", "2/day", "1/day", "every 2nd day")
REGISTERED_K = (3.0, 5.0)  # primary, then the one that is also reported


def thin(t, day, rule: str) -> np.ndarray:
    """Which fingersticks are kept under a thinning rule. The first of the day is always the one kept."""
    keep = np.zeros(len(t), dtype=bool)
    if rule == "all":
        keep[:] = True
        return keep
    for d in np.unique(day):
        idx = np.flatnonzero(day == d)
        if rule == "2/day":
            keep[idx[0]] = keep[idx[-1]] = True
        elif rule == "1/day" or (rule == "every 2nd day" and d % 2 == 0):
            keep[idx[0]] = True
    return keep


def why_not(rec: Recording, k_days: float) -> str | None:
    """Why this recording is outside the cohort of section F, or None when it is in."""
    why = why_skipped(rec, k_days, min_test_days=MIN_HIDDEN_DAYS)
    if why is not None:
        return why
    if len(rec.fingersticks) / (rec.n_min / 1440.0) < MIN_STICKS_PER_DAY:
        return "fewer than one fingerstick a day"
    if len(paired(rec, lo=k_days * 1440.0)) < MIN_HIDDEN_PAIRS:
        return "fewer than three paired fingersticks after the split"
    return None


def calibration_pairs(rec: Recording, k_days: float) -> pd.DataFrame:
    """Fingerstick and sensor pairs from the calibration window only.

    The sensor trace is cut at the split first: a fingerstick taken just before the split must not be paired
    with a hidden reading just after it.
    """
    split = k_days * 1440.0
    return paired(dataclasses.replace(rec, cgm=rec.cgm[rec.cgm["t_min"] < split]), hi=split)


def map_sources(rows: pd.DataFrame) -> dict[str, int]:
    """How many recordings used their own slope, the pooled slope with their own offset, or the pooled map."""
    return {str(k): int(v) for k, v in rows.drop_duplicates("rec_id")["map_source"].value_counts().items()}


def run_name(confirm: bool, tau: float | None, slow: bool) -> str:
    """Results folder. Each development design keeps its own, so the six compared designs can be regenerated."""
    if confirm:
        return "shanghai"
    return "shanghai-dev" + (f"-tau{tau:g}" if tau is not None else "") + ("-slow" if slow else "")


def estimates(
    rec: Recording, k_days: float, cfg: FilterConfig, pooled: tuple[float, float], rule: str = "all"
) -> dict:
    """Control, live and in-hindsight estimates on the hidden sensor timestamps, on the sensor's scale.

    Everything learned (shape, mean, map) comes from before the split. After it only fingersticks are read.
    """
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    tod0 = rec.start.hour * 60 + rec.start.minute
    cal = t < split
    centres = np.arange(0, 1440, BIN) + BIN // 2
    shape = 0.5 * average_day_baseline((tod0 + t[cal]) % 1440, g[cal], centres, BIN) + 0.5 * float(
        g[cal].mean()
    )
    at = lambda tt: shape[((tod0 + np.asarray(tt)) % 1440).astype(int) // BIN]  # noqa: E731
    cal_pairs = calibration_pairs(rec, k_days)
    a, b = sensor_map(cal_pairs["cbg"], cal_pairs["cgm"], pooled)
    sticks = rec.fingersticks[rec.fingersticks["t_min"] >= split].sort_values("t_min", kind="stable")
    day = ((tod0 + sticks["t_min"].to_numpy(dtype=float)) // 1440).astype(int)
    used = sticks[thin(sticks["t_min"].to_numpy(), day, rule)].reset_index(drop=True)
    ft = used["t_min"].to_numpy(dtype=float)
    cbg = used["glucose_mgdl"].to_numpy(dtype=float)
    z = a + b * cbg - at(ft)
    tt = t[~cal]
    control = at(tt)
    return {
        "t": tt, "control": control, "map": (a, b), "map_source": map_source(cal_pairs["cbg"]),
        "ft": ft, "cbg": cbg, "z": z, "shape_at": at,
        "live": control + deviation(ft, z, tt, cfg, smooth=False),
        "hindsight": control + deviation(ft, z, tt, cfg, smooth=True),
    }  # fmt: skip


def run_recording(
    rec: Recording, k_days: float, cfg: FilterConfig, pooled: tuple[float, float], rule: str = "all"
) -> dict | None:
    """One row of scores for a recording in the cohort; None when it is outside it."""
    if why_not(rec, k_days) is not None:
        return None
    e = estimates(rec, k_days, cfg, pooled, rule)
    if len(e["ft"]) < 2:
        return None
    split = k_days * 1440.0
    truth = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)[rec.cgm["t_min"].to_numpy() >= split]
    a, b = e["map"]
    scored = paired(
        rec, lo=split
    )  # every hidden fingerstick with a sensor reading beside it, whatever the rule
    st = scored["t_min"].to_numpy(dtype=float)
    ref = scored["cbg"].to_numpy(dtype=float)
    # each fingerstick predicted from the shape and the fingersticks strictly before it, on its own scale
    before = np.array([deviation(e["ft"][e["ft"] < s], e["z"][e["ft"] < s], [s], cfg)[0] for s in st])
    pred = {
        "sensor": scored["cgm"].to_numpy(dtype=float),
        "control": (e["shape_at"](st) - a) / b,
        "live": (e["shape_at"](st) + before - a) / b,
    }
    row = {
        "rec_id": rec.rec_id, "patient_id": rec.patient_id, "dev": is_dev_patient(rec.patient_id), "k_days": k_days,
        "rule": rule, "n_sticks": len(e["ft"]), "n_scored": len(st), "map_source": e["map_source"],
        "hidden_days": float((e["t"].max() - split) / 1440.0),
        "control_rmse": rmse(e["control"], truth), "live_rmse": rmse(e["live"], truth),
        "hindsight_rmse": rmse(e["hindsight"], truth),
    }  # fmt: skip
    for name, p in pred.items():
        row[f"{name}_mard"] = mard(p, ref)
        row[f"{name}_within15"] = within_15_15(p, ref)
        row[f"{name}_zone_a"] = clarke_zones(p, ref)["A"]
    return row


def summarise(df: pd.DataFrame) -> dict:
    """Patient-level medians and paired tests (recordings of one patient are averaged first)."""
    per = df.groupby("patient_id").mean(numeric_only=True)
    live, hind = per["live_rmse"] - per["control_rmse"], per["hindsight_rmse"] - per["control_rmse"]
    out = {
        "n_patients": int(len(per)),
        "control_rmse": float(per["control_rmse"].median()),
        "live_rmse": float(per["live_rmse"].median()),
        "hindsight_rmse": float(per["hindsight_rmse"].median()),
        "live_median_diff": float(live.median()), "live_frac_better": float((live < 0).mean()), "live_p": _paired_p(live),
        "hindsight_median_diff": float(hind.median()), "hindsight_frac_better": float((hind < 0).mean()),
        "hindsight_p": _paired_p(hind),
    }  # fmt: skip
    for col in per.columns:
        if col.endswith(("_mard", "_within15", "_zone_a")):
            out[col] = float(per[col].median())
    return out


def verdict(s: dict) -> dict:
    return {
        "f1_live_beats_control": bool(s["live_median_diff"] < 0 and s["live_p"] < 0.05),
        "f2_hindsight_beats_control": bool(s["hindsight_median_diff"] < 0 and s["hindsight_p"] < 0.05),
    }


def check_confirm(
    tau: float | None, slow: bool, src_status: str | None, k: tuple[float, ...] = REGISTERED_K
) -> None:
    """The confirmatory run uses the code defaults and the registered k, on committed code."""
    if tau is not None or slow:
        raise SystemExit("the confirmatory run uses the code defaults; remove --tau and --slow")
    if tuple(k) != REGISTERED_K:
        raise SystemExit("the confirmatory run is registered at k = 3 (primary) and k = 5; remove --k")
    if src_status is None:
        raise SystemExit(
            "git is not available, so the code that scores the test patients cannot be identified"
        )
    if src_status:
        raise SystemExit("uncommitted changes under src/: commit them before scoring the test patients")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test patients; this is done once")
    ap.add_argument("--k", type=float, nargs="+", default=list(REGISTERED_K))
    ap.add_argument("--tau", type=float, default=None, help="development runs only")
    ap.add_argument("--slow", action="store_true", help="development runs only")
    args = ap.parse_args()
    out_dir = RESULTS_DIR / "fingersticks" / run_name(args.confirm, args.tau, args.slow)
    if args.confirm:
        check_confirm(args.tau, args.slow, _git("status", "--porcelain", "--", "src"), tuple(args.k))
        refuse_second_run(out_dir)
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    cfg = FilterConfig()
    if not args.confirm and (args.tau is not None or args.slow):
        cfg = FilterConfig(tau_min=args.tau or cfg.tau_min, slow=args.slow)
    result = {"confirmatory": args.confirm, "filter": cfg._asdict(), "by_k": []}
    for k in args.k:
        cal = pd.concat([calibration_pairs(r, k) for r in dev_recs], ignore_index=True)
        pooled = pooled_map(cal["cbg"], cal["cgm"])
        skipped = Counter(w for w in (why_not(r, k) for r in scored) if w)
        block = {"k_days": k, "pooled_map": pooled, "skipped": dict(skipped), "rules": {}}
        for rule in RULES:
            rows = [row for row in (run_recording(r, k, cfg, pooled, rule) for r in scored) if row]
            if rows:
                df = pd.DataFrame(rows)
                s = summarise(df)
                block["rules"][rule] = {**s, **(verdict(s) if rule == "all" else {})}
                block.setdefault("recordings", int(df["rec_id"].nunique()))
                block.setdefault("map_sources", map_sources(df))
        result["by_k"].append(block)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(_clean(result), indent=2, allow_nan=False), encoding="utf-8"
    )
    status = _git("status", "--porcelain", "--", "src")
    prov = {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes_in_src": None if status is None else bool(status),
        "confirm": args.confirm,
        "k": args.k,
    }
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    lines = ["# Fingersticks after the sensor comes off", "", f"Filter: `{cfg._asdict()}`", ""]
    lines.append(
        "Confirmatory run on test patients." if args.confirm else "Development patients. Not confirmatory."
    )
    for block in result["by_k"]:
        lines += [
            "",
            f"## k = {block['k_days']:g} days",
            "",
            pd.DataFrame(block["rules"]).T.round(3).to_markdown(),
        ]
        lines += [
            "",
            f"Recordings scored: {block.get('recordings', 0)}. Sensor map used: "
            + "; ".join(f"{v} ({k})" for k, v in block.get("map_sources", {}).items()),
            "",
            "Recordings outside the cohort: " + "; ".join(f"{v} ({k})" for k, v in block["skipped"].items()),
        ]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
