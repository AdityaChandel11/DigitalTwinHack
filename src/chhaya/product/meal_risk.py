"""Meal excursion history: how often each meal type led to an excursion during sensor wear.

CRITICAL DISCIPLINE:
Only sensor readings before the calibration split (t_min < k_days * 1440.0) are ever read.
Only meals starting at least 120 minutes before the split are scored, ensuring every evaluated
reading falls strictly within the calibration window.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from chhaya.data.schema import Recording
from chhaya.eval.events import HORIZON_MIN, excursion, merge_meals

CANONICAL_LABELS = ("breakfast", "lunch", "dinner", "snack")
MIN_MEALS_FOR_PROFILE = 3


def _normalize_label(val: object) -> str:
    """Normalize label string to lowercase stripped form, standardizing snacks -> snack."""
    if val is None or pd.isna(val):
        return "meal"
    s = str(val).strip().lower()
    if not s:
        return "meal"
    if s == "snacks":
        return "snack"
    return s


def meal_risk_profile(rec: Recording, k_days: float) -> dict:
    """Historical excursion rate by meal type during the sensor wear.

    Parameters
    ----------
    rec : Recording
        Patient recording containing CGM and meals.
    k_days : float
        Calibration wear duration in days. Only sensor readings with
        t_min < k_days * 1440.0 are read.

    Returns
    -------
    dict
        {"state": "insufficient", "meals_scored": N} when fewer than 3 meals are scored,
        or a dict with meals_scored, excursions, rate, and by_type list.
    """
    split = float(k_days) * 1440.0
    cutoff = split - HORIZON_MIN

    # 1. Leakage guard: slice sensor data strictly before the calibration split
    t_all = rec.cgm["t_min"].to_numpy(dtype=float)
    g_all = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t_all < split
    t_cal, g_cal = t_all[cal], g_all[cal]

    if len(t_cal) == 0 or rec.meals.empty:
        return {"state": "insufficient", "meals_scored": 0}

    # 2. Select meals during the sensor wear that have a full 2-hour window before split
    meals_df = rec.meals[(rec.meals["t_min"] >= 0.0) & (rec.meals["t_min"] < cutoff)]
    if meals_df.empty:
        return {"state": "insufficient", "meals_scored": 0}

    meals_sorted = meals_df.sort_values("t_min").reset_index(drop=True)
    merged_times = merge_meals(meals_sorted["t_min"].to_numpy(dtype=float))

    scored_records: list[tuple[str, bool]] = []
    for m_t in merged_times:
        # Find the starting entry of this merged meal to extract its label
        idx = int((meals_sorted["t_min"] - m_t).abs().argmin())
        raw_label = meals_sorted.iloc[idx].get("label")
        label = _normalize_label(raw_label)

        # Check for excursion (> 180 mg/dL for 2 consecutive readings in next 2h)
        # using ONLY the calibration sensor readings
        exc = excursion(t_cal, g_cal, float(m_t))
        if exc is not None:
            scored_records.append((label, bool(exc)))

    n_scored = len(scored_records)
    if n_scored < MIN_MEALS_FOR_PROFILE:
        return {"state": "insufficient", "meals_scored": n_scored}

    total_excursions = sum(exc for _, exc in scored_records)
    overall_rate = round(float(total_excursions) / float(n_scored), 2)

    # Group by label
    grouped: dict[str, dict[str, int]] = {}
    for label, exc in scored_records:
        if label not in grouped:
            grouped[label] = {"total": 0, "excursions": 0}
        grouped[label]["total"] += 1
        if exc:
            grouped[label]["excursions"] += 1

    # Preserve canonical order where possible, followed by any other labels
    ordered_labels = [lbl for lbl in CANONICAL_LABELS if lbl in grouped] + sorted(
        lbl for lbl in grouped if lbl not in CANONICAL_LABELS
    )

    by_type = []
    for lbl in ordered_labels:
        tot = grouped[lbl]["total"]
        excs = grouped[lbl]["excursions"]
        rate = round(float(excs) / float(tot), 2) if tot > 0 else 0.0
        by_type.append({"label": lbl, "total": tot, "excursions": excs, "rate": rate})

    return {
        "state": "shown",
        "meals_scored": n_scored,
        "excursions": total_excursions,
        "rate": overall_rate,
        "by_type": by_type,
    }
