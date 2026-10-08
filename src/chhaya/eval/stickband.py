"""A band for the fingerstick estimate (Amendment 3, note of 8 Oct 2026 on the band). Descriptive: no bar.

The estimates of section F had no band. This gives them one from what the frozen filter already knows: its own
spread at each minute, which depends on when fingersticks were taken and never on a reading. Two constructions
are compared on development patients, with nothing fitted in either: `filter` (the filter's spread as it is)
and `patient` (the same, with its width taken from the patient's own spread about their daily shape in the
calibration window). Development patients choose one; test patients then report how often the hidden sensor
lies inside it.

Usage: python -m chhaya.eval.stickband             (development patients; they choose the construction)
       python -m chhaya.eval.stickband --confirm   (test patients, once, with the frozen construction)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import (
    MIN_DAY_READINGS,
    check_committed,
    day_index,
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
from chhaya.twin.stickband import band, deviation_sd

CONSTRUCTIONS = ("filter", "patient")
ESTIMATES = ("live", "hindsight")  # live reads fingersticks stamped strictly before the minute, as F1 did
TARGET = 80.0  # percent of hidden readings an 80 % band should hold
WITHIN = (70.0, 90.0)
TIE_POINTS = 1.0  # two constructions this close to the target are tied
REGISTERED_SPREADS = (25.0, 15.0)  # the filter's deviation and fingerstick spreads, mg/dL
FROZEN: str | None = (
    None  # the construction development patients chose; written with the addendum to the note
)
FOLDER = RESULTS_DIR / "stickband"


def _bands(rec: Recording, k_days: float, pooled: tuple[float, float], cfg: FilterConfig) -> dict:
    """Every estimate with every band, at the hidden sensor timestamps.

    Read: the calibration window (shape, sensor map, the patient's spread) and the hidden fingersticks.
    Not read: any hidden sensor value.
    """
    e = estimates(rec, k_days, cfg, pooled)
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    assert (e["t"] >= split).all() and (e["ft"] >= split).all()  # rule 1
    own = profile_sigma(rec.start.hour * 60 + rec.start.minute + t[cal], g[cal]) / cfg.fast_sd
    out = {}
    for which in ESTIMATES:
        sd = deviation_sd(e["ft"], e["t"], cfg, smooth=which == "hindsight", strictly_before=which == "live")
        for construction, scale in zip(CONSTRUCTIONS, (1.0, own), strict=True):
            lo, hi = band(e[which], sd, scale)
            out[which, construction] = {"t": e["t"], "est": e[which], "lo": lo, "hi": hi}
    return out


def band_of(
    rec: Recording,
    k_days: float,
    pooled: tuple[float, float],
    construction: str,
    which: str = "live",
    cfg: FilterConfig = FilterConfig(),
) -> dict:
    """One estimate of section F with one band: `t`, `est`, `lo`, `hi` at the hidden sensor timestamps."""
    if construction not in CONSTRUCTIONS:
        raise ValueError(f"construction must be one of {CONSTRUCTIONS}, got {construction!r}")
    if which not in ESTIMATES:
        raise ValueError(f"estimate must be one of {ESTIMATES}, got {which!r}")
    return _bands(rec, k_days, pooled, cfg)[which, construction]


def score_recording(
    rec: Recording, k_days: float, pooled: tuple[float, float], cfg: FilterConfig = FilterConfig()
) -> dict | None:
    """Coverage and mean half-width of each band on one recording of section F's cohort; None outside it.

    Only here is the hidden sensor read, and only to count how many of its readings a band holds.
    """
    if why_not(rec, k_days) is not None:
        return None
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    truth = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)[t >= split]
    bands = _bands(rec, k_days, pooled, cfg)
    day = day_index(t[t >= split], split)
    kept = [int(d) for d in np.unique(day) if (day == d).sum() >= MIN_DAY_READINGS]
    days = {d: {"day": d} for d in kept}
    row: dict = {"rec_id": rec.rec_id, "patient_id": rec.patient_id, "k_days": k_days}
    for (which, construction), b in bands.items():
        inside = (truth >= b["lo"]) & (truth <= b["hi"])
        row[f"{which}_{construction}_cov"] = float(100.0 * inside.mean())
        row[f"{which}_{construction}_half"] = float(np.mean(b["hi"] - b["est"]))
        for d in kept:
            days[d][f"{which}_{construction}_cov"] = float(100.0 * inside[day == d].mean())
    row["days"] = list(days.values())
    return row


def summarise(rows: list[dict], which: str, construction: str) -> dict:
    """One band over patients: recordings of one patient are averaged first."""
    cov, half = f"{which}_{construction}_cov", f"{which}_{construction}_half"
    per = pd.DataFrame(rows).groupby("patient_id")[[cov, half]].mean()
    return {
        "n_patients": int(len(per)),
        "mean": float(per[cov].mean()),
        "min": float(per[cov].min()),
        "max": float(per[cov].max()),
        "n_within": int(per[cov].between(*WITHIN).sum()),
        "median_half_width": float(per[half].median()),
    }


def choose(by_construction: dict[str, dict]) -> str:
    """The registered rule: closer to 80 %; within a point of each other, more patients within 70 to 90 %;
    still tied, the first (the filter's spread as it is)."""
    first, second = CONSTRUCTIONS
    off = {c: abs(by_construction[c]["mean"] - TARGET) for c in CONSTRUCTIONS}
    if abs(off[first] - off[second]) >= TIE_POINTS:
        return min(CONSTRUCTIONS, key=off.get)
    if by_construction[second]["n_within"] > by_construction[first]["n_within"]:
        return second
    return first


def by_day(rows: list[dict]) -> list[dict]:
    """Mean coverage over patients on each day since the sensor, with the share of the cohort that reaches it."""
    flat = [{"patient_id": r["patient_id"], **d} for r in rows for d in r["days"]]
    if not flat:
        return []
    df = pd.DataFrame(flat)
    cohort = df["patient_id"].nunique()
    out = []
    for d, g in df.groupby("day"):
        per = g.drop(columns="day").groupby("patient_id").mean()
        out.append(
            {
                "day": int(d),
                "n_patients": int(len(per)),
                "share_of_cohort": len(per) / cohort,
                **{c: float(per[c].mean()) for c in per.columns},
            }
        )
    return out


def _score_all(recs: list[Recording], k_days: float, pooled: tuple[float, float]) -> tuple[list[dict], list]:
    """Scored rows and, for a recording whose band cannot be formed, a row with its error (rule 4)."""
    rows, errors = [], []
    for rec in recs:
        try:
            row = score_recording(rec, k_days, pooled)
        except ValueError as err:
            errors.append({"rec_id": rec.rec_id, "error": str(err)})
            continue
        if row is not None:
            rows.append(row)
    return rows, errors


def _bands_block(rows: list[dict]) -> dict:
    return {which: {c: summarise(rows, which, c) for c in CONSTRUCTIONS} for which in ESTIMATES}


def run(
    scored: list[Recording],
    dev_recs: list[Recording],
    k_list: list[float],
    confirmatory: bool,
    frozen: str | None,
) -> dict:
    """Development recordings choose the construction at the first k, on the live estimate; `scored` reports.

    A pass over test recordings needs `frozen`, and stops if the development recordings would choose another.
    """
    shared = {r.patient_id for r in scored} & {r.patient_id for r in dev_recs}
    if confirmatory and shared:
        raise ValueError(f"{len(shared)} patients are both development and test patients of this run")
    if confirmatory and frozen is None:
        raise ValueError("no construction is frozen: run the development pass and write its choice first")
    result: dict = {
        "confirmatory": confirmatory,
        "target": TARGET,
        "within": list(WITHIN),
        "frozen": frozen,
        "by_k": [],
    }
    chosen = None
    for i, k in enumerate(k_list):
        pooled = pooled_line(dev_recs, k)
        dev_rows, dev_errors = _score_all(dev_recs, k, pooled)
        dev_bands = _bands_block(dev_rows) if dev_rows else None
        if i == 0:
            if dev_bands is None:
                raise ValueError("no development recording in the cohort: the construction cannot be chosen")
            chosen = choose(dev_bands["live"])
            if confirmatory and chosen != frozen:
                raise ValueError(f"development patients choose {chosen!r}, the code has {frozen!r} frozen")
        rows, errors = _score_all(scored, k, pooled) if confirmatory else (dev_rows, dev_errors)
        block: dict = {
            "k_days": k,
            "primary": i == 0,
            "n_recordings": len(rows),
            "n_patients": len({r["patient_id"] for r in rows}),
            "errors": errors,
            "choice": {"on": "live", "at_k": k_list[0], "chosen": chosen, "development": dev_bands},
        }
        if rows:
            block["bands"] = _bands_block(rows)
            block["by_day"] = by_day(rows)
        result["by_k"].append(block)
    return result


def _report(result: dict) -> str:
    lines = ["# A band for the fingerstick estimate", ""]
    lines.append(
        f"Test patients, with the construction frozen on development patients (`{result['frozen']}`). "
        "Descriptive: no bar."
        if result["confirmatory"]
        else "Development patients: they choose the construction, so these figures are in-sample for that choice."
    )
    lines += [
        "",
        "Coverage is the percent of hidden sensor readings inside the band; the patient is the unit. `filter` is "
        "the frozen filter's own spread; `patient` takes its width from the patient's spread about their daily "
        "shape in the calibration window. Nothing in either is fitted. Half-widths are in mg/dL.",
    ]
    for block in result["by_k"]:
        role = "primary" if block["primary"] else "reported"
        lines += ["", f"## k = {block['k_days']:g} days ({role})", ""]
        choice = block["choice"]
        lines.append(
            f"{block['n_recordings']} recordings of {block['n_patients']} patients; {len(block['errors'])} could "
            f"not be scored. Chosen on development patients at k = {choice['at_k']:g}, on the live estimate: "
            f"`{choice['chosen']}`."
        )
        if "bands" not in block:
            continue
        rows = [
            {
                "estimate": which,
                "band": c + (" (chosen)" if c == choice["chosen"] else ""),
                "mean coverage": s["mean"],
                "smallest": s["min"],
                "largest": s["max"],
                "within 70 to 90": f"{s['n_within']} of {s['n_patients']}",
                "median half-width": s["median_half_width"],
            }
            for which in ESTIMATES
            for c, s in block["bands"][which].items()
        ]
        lines += ["", table(rows), "", "By day since the sensor (mean coverage over patients):", ""]
        lines.append(table(block["by_day"]))
    return "\n".join(lines) + "\n"


def check_frozen(cfg: FilterConfig) -> None:
    """The band is the registered filter's own spread: refuse any other constants."""
    if (cfg.tau_min, cfg.slow) != REGISTERED_FILTER:
        raise SystemExit(f"the code defaults are not the frozen design {REGISTERED_FILTER}")
    if (cfg.fast_sd, cfg.obs_sd) != REGISTERED_SPREADS:
        raise SystemExit(
            f"the filter's spreads are {(cfg.fast_sd, cfg.obs_sd)} where {REGISTERED_SPREADS} are registered"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test patients; this is done once")
    args = ap.parse_args()
    out_dir: Path = FOLDER / ("shanghai" if args.confirm else "shanghai-dev")
    check_frozen(FilterConfig())
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        refuse_second_pass(out_dir)
    prov = provenance(args.confirm, k=list(REGISTERED_K), frozen=FROZEN)
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    try:
        result = run(scored, dev_recs, list(REGISTERED_K), args.confirm, FROZEN)
    except ValueError as err:
        raise SystemExit(str(err)) from err
    report = _report(result)
    write_outputs(out_dir, result, report, prov)
    print(report)


if __name__ == "__main__":
    main()
