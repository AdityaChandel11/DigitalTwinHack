"""Shared pieces of the descriptive outputs of Milestone 3: the second pass of section F, expiry, the band.

Days since the sensor, the three numbers a sensor report states, paired summaries over patients, and the
guards of a pass that reads test patients again. Nothing here carries a bar. How the registered words were
turned into these functions is fixed in docs/PREREGISTRATION.md, "Note to Amendment 3, descriptive outputs".
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from chhaya.config import SEED
from chhaya.eval.baselines import lodo_average_day
from chhaya.eval.fingersticks import _interval, calibration_pairs
from chhaya.eval.gate2 import _clean, _git, _paired_p
from chhaya.eval.metrics import rmse, time_in_ranges
from chhaya.twin.assimilate import pooled_map

DAY_MIN = 1440
REPORT_KEYS = ("mean", "tar", "tir")  # mg/dL, then percentage points twice
MIN_DAY_READINGS = 48  # a day counts when at least half of its 15-minute slots hold a reading
MIN_DAY_PATIENTS = 6  # below this a day keeps its medians and gets no paired comparison
MIN_SLOPE_DAYS = 3
MOVED_MGDL = 20.0  # the registered size of a drift: the mean has moved by more than this
NOT_SUMMARISED = ("day", "n", "k_days", "dev", "moved")


def day_index(t, split: float) -> np.ndarray:
    """Days since the sensor came off, in 24-hour blocks from the split: 1 for the first 24 hours."""
    t = np.asarray(t, dtype=float)
    if t.size and t.min() < split:
        raise ValueError("a reading from before the split has no day since the sensor")
    return ((t - split) // DAY_MIN).astype(int) + 1


def glucose_report(g) -> dict[str, float]:
    """What a sensor report states about a period: mean glucose, percent of time above 180 and within 70-180."""
    g = np.asarray(g, dtype=float)
    if g.size == 0:
        raise ValueError("no readings: a report needs at least one")
    r = time_in_ranges(g)
    return {"mean": float(g.mean()), "tar": r["tar"], "tir": r["tir"]}


def estimated_report(est, sigma: float) -> dict[str, float]:
    """The same three numbers from an estimated trace whose error has spread `sigma` (mg/dL).

    An estimate is a smoothed mean, so counting how often it crosses 180 undercounts the time above 180. Each
    value is the centre of a normal distribution and the probabilities are averaged. Without a spread this is
    the plain count.
    """
    est = np.asarray(est, dtype=float)
    if not sigma > 0.0:
        return glucose_report(est)
    if est.size == 0:
        raise ValueError("no readings: a report needs at least one")
    above = norm.sf((180.0 - est) / sigma)
    below = norm.cdf((70.0 - est) / sigma)
    return {
        "mean": float(est.mean()),
        "tar": float(100.0 * above.mean()),
        "tir": float(100.0 * (1.0 - above - below).mean()),
    }


def profile_sigma(clock_min, g) -> float:
    """Spread of sensor readings around the daily shape built without their own day (mg/dL).

    `clock_min` counts minutes from midnight of the first day. The shape is half the average day of the other
    days, half the mean: the control of sections F and M.
    """
    clock_min = np.asarray(clock_min, dtype=int)
    g = np.asarray(g, dtype=float)
    seen = 0.5 * lodo_average_day(clock_min // DAY_MIN, clock_min, g) + 0.5 * float(g.mean())
    return rmse(seen, g)


def aging(now: dict, report: dict) -> dict[str, float]:
    """How far a period's own report (`now`) lies from an older `report` of the same patient."""
    d = now["mean"] - report["mean"]
    return {
        "dmean": float(d),
        "abs_dmean": float(abs(d)),
        "moved": float(abs(d) > MOVED_MGDL),
        "abs_dtar": float(abs(now["tar"] - report["tar"])),
        "abs_dtir": float(abs(now["tir"] - report["tir"])),
    }


def day_report(row: dict) -> dict[str, float]:
    """The report of the day a `daily_rows` row describes."""
    return {k: row[f"day_{k}"] for k in REPORT_KEYS}


def daily_rows(t, split: float, truth, estimates: dict, min_readings: int = MIN_DAY_READINGS) -> list[dict]:
    """One row per day since the sensor that holds enough readings.

    Each row has the day's own report (`day_mean`, `day_tar`, `day_tir`) and, for every estimate, its RMSE
    against the hidden readings of that day and its mean over them.
    """
    t, truth = np.asarray(t, dtype=float), np.asarray(truth, dtype=float)
    day = day_index(t, split)
    rows = []
    for d in np.unique(day):
        m = day == d
        if m.sum() < min_readings:
            continue
        row = {"day": int(d), "n": int(m.sum())}
        row.update({f"day_{k}": v for k, v in glucose_report(truth[m]).items()})
        for name, est in estimates.items():
            est = np.asarray(est, dtype=float)
            row[f"{name}_rmse"] = rmse(est[m], truth[m])
            row[f"{name}_mean"] = float(est[m].mean())
        rows.append(row)
    return rows


def inside_the_wear(t, g, min_readings: int = MIN_DAY_READINGS) -> dict[str, float] | None:
    """Day 0: how far one day of the wear lies from the report of its other days, averaged over its days.

    This is what "not aged at all" looks like for this patient, so a later day is read against it. None when
    the wear does not hold two days with enough readings.
    """
    t, g = np.asarray(t, dtype=float), np.asarray(g, dtype=float)
    block = (t // DAY_MIN).astype(int)
    rows = []
    for b in np.unique(block):
        m = block == b
        if m.sum() >= min_readings and (~m).sum() >= min_readings:
            rows.append(aging(glucose_report(g[m]), glucose_report(g[~m])))
    if not rows:
        return None
    return {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}


def paired_summary(per: pd.DataFrame, a: str, b: str, alternative: str = "less") -> dict:
    """Column `a` against column `b` over patients: both medians and the median paired difference a - b.

    Below zero means `a` is the smaller error. The interval is a 95 % percentile bootstrap over patients and
    the p-value a one-sided signed-rank test, as everywhere in Amendment 3: that `a` is smaller ("less"), or,
    where the question is whether something got worse, that it is larger ("greater"). No bar hangs on it.
    """
    if alternative not in ("less", "greater"):
        raise ValueError(f"alternative must be 'less' or 'greater', got {alternative!r}")
    both = per[[a, b]].dropna()
    out: dict = {"of": a, "against": b, "alternative": alternative, "n_patients": int(len(both))}
    if both.empty:
        return out
    diff = both[a] - both[b]
    lo, hi = _interval(diff)
    out.update(
        {
            "median": float(both[a].median()),
            "median_against": float(both[b].median()),
            "median_diff": float(diff.median()),
            "diff_lo": lo,
            "diff_hi": hi,
            "frac_better": float((diff < 0).mean()),
            "p": _paired_p(diff if alternative == "less" else -diff),
        }
    )
    return out


def summarise_days(df: pd.DataFrame, pairs: tuple[tuple[str, str], ...] = ()) -> list[dict]:
    """Per day since the sensor: patients, the median of every numeric column over patients, paired comparisons.

    Recordings of one patient are averaged first. `moved` becomes `share_moved`, the share of patients whose
    daily mean lies more than 20 mg/dL from the report. A day with fewer than MIN_DAY_PATIENTS patients keeps
    its medians and gets no paired comparison.
    """
    out = []
    for d, g in df.groupby("day"):
        per = g.groupby("patient_id").mean(numeric_only=True)
        row: dict = {"day": int(d), "n_patients": int(len(per))}
        row.update({c: float(per[c].median()) for c in per.columns if c not in NOT_SUMMARISED})
        if "moved" in per.columns:
            row["share_moved"] = float(per["moved"].mean())
        if len(per) >= MIN_DAY_PATIENTS:
            for a, b in pairs:
                row[f"{a}_vs_{b}"] = paired_summary(per, a, b)
        out.append(row)
    most = max((r["n_patients"] for r in out), default=0)
    for row in out:  # a day that few patients reach is read with care: it holds whoever is left
        row["share_of_cohort"] = row["n_patients"] / most
    return out


def slope_per_day(df: pd.DataFrame, col: str) -> dict:
    """Change of `col` per day since the sensor inside each patient: a least-squares slope each, then the median.

    Recordings end at different lengths, so a curve of daily medians mixes ageing with who is still there. A
    slope inside each patient does not. Day 0 (inside the wear) is left out.
    """
    later = df[df["day"] >= 1].dropna(subset=[col])
    per = later.groupby(["patient_id", "day"])[col].mean().reset_index()
    slopes = [
        float(np.polyfit(g["day"], g[col], 1)[0])
        for _, g in per.groupby("patient_id")
        if len(g) >= MIN_SLOPE_DAYS
    ]
    out: dict = {"column": col, "n_patients": len(slopes)}
    if not slopes:
        return out
    s = pd.Series(slopes, dtype=float)
    lo, hi = _interval(s)
    out.update(
        {
            "median_slope": float(s.median()),
            "slope_lo": lo,
            "slope_hi": hi,
            "frac_rising": float((s > 0).mean()),
        }
    )
    return out


def excess_over_day_zero(df: pd.DataFrame, col: str) -> list[dict]:
    """For each day since the sensor, `col` on that day against the same patient's day 0 (inside the wear).

    The question is whether the report has aged, so the test is one-sided the other way: larger than day 0.
    """
    wide = df.dropna(subset=[col]).groupby(["patient_id", "day"])[col].mean().unstack("day")
    if 0 not in wide.columns:
        return []
    out = []
    for d in [c for c in wide.columns if c >= 1]:
        per = pd.DataFrame({"then": wide[d], "inside": wide[0]})
        if per.dropna().shape[0] >= MIN_DAY_PATIENTS:
            out.append({"day": int(d), "column": col, **paired_summary(per, "then", "inside", "greater")})
    return out


def pooled_line(dev_recs: list, k_days: float) -> tuple[float, float]:
    """The pooled line of the sensor map, from development recordings' calibration pairs.

    The same line the confirmatory fingerstick run fitted. No test patient may be among `dev_recs`.
    """
    pairs = [calibration_pairs(r, k_days) for r in dev_recs]
    n = sum(len(p) for p in pairs)
    if n < 2:
        raise ValueError(f"{n} development calibration pairs: the pooled sensor map cannot be fitted")
    cal = pd.concat(pairs, ignore_index=True)
    return pooled_map(cal["cbg"], cal["cgm"])


def differences(found: dict, committed: dict, tol: float = 1e-6) -> list[str]:
    """Which committed numbers a second computation does not reproduce. Empty: same estimator, same cohort."""
    out = []
    for key, want in committed.items():
        got = found.get(key)
        same = got is not None and want is not None and abs(float(got) - float(want)) <= tol
        if not same:
            out.append(f"{key}: committed {want}, found {got}")
    return out


def check_committed(src_status: str | None) -> None:
    """A pass over test patients runs on committed code, or not at all."""
    if src_status is None:
        raise SystemExit(
            "git is not available, so the code that reads the test patients cannot be identified"
        )
    if src_status:
        raise SystemExit("uncommitted changes under src/: commit them before reading the test patients")


def provenance(confirm: bool, **settings) -> dict:
    status = _git("status", "--porcelain", "--", "src")
    return {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes_in_src": None if status is None else bool(status),
        "confirm": confirm,
        "seed": SEED,
        **settings,
    }


def _plain(value):
    """numpy integers and booleans are not JSON; their Python values are."""
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"{type(value).__name__} is not JSON serialisable")


def write_outputs(out_dir: Path, result: dict, report: str, prov: dict | None = None) -> None:
    """summary.json (strict JSON), report.md and, when given, provenance.json. Aggregates only."""
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_clean(result), indent=2, allow_nan=False, default=_plain)
    (out_dir / "summary.json").write_text(text, encoding="utf-8")
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    if prov is not None:
        (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2, default=_plain), encoding="utf-8")


def table(rows: list[dict], columns: list[str] | None = None, digits: int = 1) -> str:
    """A markdown table of flat rows; nested values (paired comparisons) are left to the summary file."""
    flat = [{k: v for k, v in r.items() if not isinstance(v, dict | list)} for r in rows]
    df = pd.DataFrame(flat)
    if df.empty:
        return "(no rows)"
    df = df[[c for c in (columns or list(df.columns)) if c in df.columns]]
    return df.round(digits).to_markdown(index=False)
