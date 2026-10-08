"""One patient's bundle: everything the patient screen draws, computed here so the page computes nothing.

The hidden sensor enters in two places only: the `sensor` array of each day (what the reveal uncovers) and
`inside_band` (the share of that day's readings the band holds). Everything else is read from the sensor wear,
the meal log, the fingersticks and the record. A test changes every hidden reading and checks exactly that.

Never written here: time in range or time below range from an estimate, GMI or HbA1c from fingersticks, a
dose. The gates of the prompt and of the figures since the sensor are the ones the staleness and fingerstick
report records fixed (4.6 fingersticks a day, a wear of three or five days, day 11).
"""

from __future__ import annotations

import math

import numpy as np

from chhaya.data.schema import Recording
from chhaya.eval import stickband
from chhaya.eval.descriptive import profile_sigma
from chhaya.eval.fingersticks import estimates
from chhaya.product.record import fhir_record
from chhaya.product.treatment import treatment_since
from chhaya.twin.assimilate import FilterConfig
from chhaya.twin.staleness import cusum, first_alarm, surprise_scale

SCHEMA = 1
MIN_STICKS_PER_DAY = 4.6  # the lower quartile of the cohort the prompt and the report figures were tested on
LAST_TESTED_DAY = 11
GAP_MIN = 30  # a longer silence of the sensor is a break in the line
BIN = 30  # minutes, for the wear's daily profile


def _num(x, digits: int = 1):
    """A finite number rounded for the screen, else None (JSON has no NaN)."""
    x = float(x)
    return round(x, digits) if math.isfinite(x) else None


def _list(values, digits: int = 1) -> list:
    return [_num(v, digits) for v in values]


def _tod0(rec: Recording) -> int:
    return rec.start.hour * 60 + rec.start.minute


def wear_report(rec: Recording, k_days: float) -> dict:
    """What the sensor measured during the wear: mean, shares above 180 and below 70, the profile of the day."""
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < k_days * 1440.0
    t, g = t[cal], g[cal]
    slot = ((_tod0(rec) + t) % 1440 // BIN).astype(int)
    n = 1440 // BIN
    profile: dict[str, list] = {"p05": [], "p25": [], "p50": [], "p75": [], "p95": []}
    for i in range(n):
        near = g[np.isin(slot, [(i - 1) % n, i, (i + 1) % n])]  # a slot alone holds too few readings
        q = np.percentile(near, [5, 25, 50, 75, 95]) if near.size else [np.nan] * 5
        for key, value in zip(profile, q, strict=True):
            profile[key].append(_num(value))
    return {
        "days": _num(k_days, 0) if float(k_days).is_integer() else _num(k_days),
        "mean": _num(g.mean()),
        "above_180": _num(100.0 * np.mean(g > 180.0)),
        "below_70": _num(100.0 * np.mean(g < 70.0)),
        "profile": profile,
    }


def stick_estimate(rec: Recording, k_days: float, pooled: tuple[float, float]) -> dict:
    """The in-hindsight estimate of section F with the band its held-out pass scored (2026-10-09 record)."""
    b = stickband.band_of(rec, k_days, pooled, stickband.FROZEN, "hindsight")
    avg = estimates(rec, k_days, FilterConfig(), pooled)["control"]
    return {"kind": "fingersticks", "t": b["t"], "est": b["est"], "lo": b["lo"], "hi": b["hi"], "avg": avg}


def twin_estimate(trace: dict) -> dict:
    """The blend Gate 2 scored, from a reveal trace (`chhaya.eval.traces.trace_of`)."""
    return {
        "kind": "twin", "t": np.asarray(trace["t"], dtype=float), "est": trace["twin"], "lo": trace["lo"],
        "hi": trace["hi"], "avg": trace["day"],
    }  # fmt: skip


def _days(rec: Recording, k_days: float, estimate: dict | None) -> list[dict]:
    split = k_days * 1440.0
    t_all = rec.cgm["t_min"].to_numpy(dtype=float)
    hidden = t_all >= split
    t, truth = t_all[hidden], rec.cgm["glucose_mgdl"].to_numpy(dtype=float)[hidden]
    cols = {"sensor": truth}
    if estimate is not None:
        at = np.searchsorted(estimate["t"], t)
        found = (at < len(estimate["t"])) & (
            np.asarray(estimate["t"])[np.minimum(at, len(estimate["t"]) - 1)] == t
        )
        for key in ("est", "lo", "hi", "avg"):
            values = np.asarray(estimate[key], dtype=float)
            cols[key] = np.where(found, values[np.minimum(at, len(values) - 1)], np.nan)
    day = ((t - split) // 1440).astype(int) + 1
    meals, sticks = rec.meals, rec.fingersticks
    out = []
    for d in np.unique(day):
        start = split + (d - 1) * 1440.0
        sel = day == d
        rel = t[sel] - start
        rows: dict[str, list] = {"t": [], **{k: [] for k in cols}}
        for i, minute in enumerate(rel):
            if i and minute - rel[i - 1] > GAP_MIN:
                rows["t"].append(_num((minute + rel[i - 1]) / 2.0, 0))
                for k in cols:
                    rows[k].append(None)
            rows["t"].append(_num(minute, 0))
            for k in cols:
                rows[k].append(_num(cols[k][sel][i]))
        entry: dict = {"day": int(d), "clock0": int((_tod0(rec) + start) % 1440), **rows}
        if estimate is None:
            entry.update({"est": None, "lo": None, "hi": None, "avg": None, "inside_band": None})
        else:
            ok = np.isfinite(cols["lo"][sel])
            inside = (truth[sel] >= cols["lo"][sel]) & (truth[sel] <= cols["hi"][sel])
            entry["inside_band"] = _num(100.0 * inside[ok].mean(), 0) if ok.any() else None
        in_day = lambda df, start=start: df[(df["t_min"] >= start) & (df["t_min"] < start + 1440.0)]  # noqa: E731
        entry["meals"] = [
            {"t": _num(r["t_min"] - start, 0), "carbs": _num(r["carb_g"], 0), "label": str(r["label"])}
            for _, r in in_day(meals).iterrows()
        ]
        entry["sticks"] = [
            {"t": _num(r["t_min"] - start, 0), "v": _num(r["glucose_mgdl"], 0)}
            for _, r in in_day(sticks).iterrows()
        ]
        out.append(entry)
    return out


def _sticks(rec: Recording, k_days: float, pooled: tuple[float, float]) -> dict:
    """Hidden-window fingersticks on both scales, their rate, and how many days have passed."""
    split = k_days * 1440.0
    span = (float(rec.cgm["t_min"].max()) - split) / 1440.0
    out: dict = {"days_since": int(span) + 1, "span": span, "n": 0, "per_day": 0.0, "e": None}
    if (rec.fingersticks["t_min"] >= split).any():
        e = estimates(rec, k_days, FilterConfig(), pooled)
        out.update({"e": e, "n": int(e["ft"].size), "per_day": e["ft"].size / max(out["days_since"], 1)})
    return out


def since_sensor(rec: Recording, k_days: float, pooled: tuple[float, float], s: dict | None = None) -> dict:
    """Mean and share above 180 from the fingersticks since the sensor, sensor-equivalent beside as read."""
    s = s or _sticks(rec, k_days, pooled)
    out: dict = {"n": s["n"], "per_day": _num(s["per_day"]), "days": s["days_since"]}
    if s["per_day"] < MIN_STICKS_PER_DAY:
        return {**out, "state": "withheld", "reason": "few_sticks"}
    e = s["e"]
    a, b = e["map"]
    equivalent = a + b * e["cbg"]
    clock = ((_tod0(rec) + e["ft"]) % 1440 // 30 * 30).astype(int)
    slots, counts = np.unique(clock, return_counts=True)
    usual = slots[counts >= max(1, s["days_since"] // 2)]
    return {
        **out,
        "state": "shown",
        "outside": bool(s["days_since"] > LAST_TESTED_DAY),
        "sensor_equivalent": {
            "mean": _num(equivalent.mean(), 0),
            "above_180": _num(100 * np.mean(equivalent > 180), 0),
        },
        "meter": {"mean": _num(e["cbg"].mean(), 0), "above_180": _num(100 * np.mean(e["cbg"] > 180), 0)},
        "times": [f"{m // 60:02d}:{m % 60:02d}" for m in usual],
    }


def prompt_state(
    rec: Recording,
    k_days: float,
    pooled: tuple[float, float],
    thresholds: dict[float, float],
    s: dict | None = None,
) -> dict:
    """ "raised" with its day, "not_raised", or "not_computed" with the reason. A prompt, never a finding."""
    s = s or _sticks(rec, k_days, pooled)
    if float(k_days) not in thresholds:
        return {"state": "not_computed", "reason": "wear_length"}
    if s["per_day"] < MIN_STICKS_PER_DAY:
        return {"state": "not_computed", "reason": "few_sticks"}
    e = s["e"]
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    cfg = FilterConfig()
    scale = surprise_scale(profile_sigma(_tod0(rec) + t[cal], g[cal]), cfg.obs_sd)
    days = (e["ft"] - split) / 1440.0
    tested = days < LAST_TESTED_DAY
    first = first_alarm(days[tested], cusum(e["z"] / scale)[tested], thresholds[float(k_days)])
    a, b = e["map"]
    plain = {"report_mean": _num(g[cal].mean(), 0), "stick_mean": _num(np.mean(a + b * e["cbg"]), 0)}
    if first is not None:
        return {
            "state": "raised",
            "day": int(first) + 1,
            "outside": bool(s["days_since"] > LAST_TESTED_DAY),
            **plain,
        }
    if s["days_since"] > LAST_TESTED_DAY:
        return {"state": "not_computed", "reason": "too_late"}
    return {"state": "not_raised", **plain}


def patient_bundle(
    rec: Recording,
    k_days: float,
    *,
    name: str,
    cohort: str,
    estimate: dict | None,
    pooled: tuple[float, float],
    thresholds: dict[float, float],
    synthetic: bool = False,
) -> dict:
    s = _sticks(rec, k_days, pooled)
    return {
        "schema": SCHEMA,
        "id": rec.patient_id,
        "name": name,
        "cohort": cohort,
        "synthetic": synthetic,
        "record": fhir_record(rec, synthetic=synthetic),
        "wear": wear_report(rec, k_days),
        "days_since": s["days_since"],
        "treatment": treatment_since(rec, k_days),
        "estimate": None if estimate is None else {"kind": estimate["kind"]},
        "days": _days(rec, k_days, estimate),
        "since": since_sensor(rec, k_days, pooled, s),
        "prompt": prompt_state(rec, k_days, pooled, thresholds, s),
    }
