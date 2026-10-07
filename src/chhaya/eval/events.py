"""Post-meal excursions: the adverse event of Amendment 3, and what each data stream knows before the meal."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from chhaya.config import is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline
from chhaya.eval.reveal import why_skipped

EVENT_MGDL = 180.0
SEVERE_MGDL = 250.0
HORIZON_MIN = 120.0
MERGE_MIN = 60.0  # a diet entry this soon after a meal's start belongs to that meal
MIN_READINGS = 6  # of the 8 a 15-minute sensor takes in two hours
MAX_STEP_MIN = 20.0  # two readings further apart than this are not consecutive
PRE_GAP_MIN = 20.0  # the sensor-on arm needs a reading this soon before the meal
RECENT_MIN = 180.0  # a fingerstick older than this is not "the last fingerstick"
BIN = 30

CONTEXT = ["c_sin", "c_cos"]
RECORD = [
    "r_age",
    "r_male",
    "r_bmi",
    "r_duration",
    "r_hba1c",
    "r_fpg",
    "r_pp2h",
    "r_cpep",
    "r_egfr",
    "r_insulin",
    "r_secretagogue",
    "r_agi",
    "r_metformin",
]
HISTORY = ["h_mean", "h_sd", "h_tar", "h_at", "h_peak", "h_rate"]
STICKS = ["f_has", "f_last", "f_age", "f_n", "f_mean"]
SENSOR = ["s_last", "s_slope", "s_mean"]

_DRUGS = {
    "r_insulin": r"insulin|novolin|humulin|gansulin|scilin|aspart|glargine|glarigine|degludec|detemir|glulisine",
    "r_secretagogue": r"gliclazide|glimepiride|gliquidone|glipizide|glibenclamide|repaglinide|nateglinide",
    "r_agi": r"acarbose|voglibose|miglitol",
    "r_metformin": r"metformin",
}


def merge_meals(t_min) -> np.ndarray:
    """Meal start times: an entry within MERGE_MIN of the current meal's start belongs to that meal."""
    out: list[float] = []
    for t in np.sort(np.asarray(t_min, dtype=float)):
        if not out or t - out[-1] > MERGE_MIN:
            out.append(float(t))
    return np.array(out)


def excursion(t, g, meal_t: float, threshold: float = EVENT_MGDL) -> bool | None:
    """Two consecutive readings above `threshold` in the two hours after the meal; None when too few readings."""
    m = (t > meal_t) & (t <= meal_t + HORIZON_MIN)
    if int(m.sum()) < MIN_READINGS:
        return None
    above = g[m] > threshold
    return bool(np.any(above[1:] & above[:-1] & (np.diff(t[m]) <= MAX_STEP_MIN)))


def minutes_to_high(t, g, meal_t: float, threshold: float = EVENT_MGDL) -> float:
    """Minutes from the meal to the first reading above `threshold` in the two hours after it; NaN if none.

    Known only after the meal: a description of the event, never a feature.
    """
    m = (t > meal_t) & (t <= meal_t + HORIZON_MIN) & (g > threshold)
    return float(t[m][0] - meal_t) if m.any() else float("nan")


def drug_flags(agents) -> dict[str, float]:
    text = "" if agents is None else str(agents).lower()
    return {k: float(bool(re.search(p, text))) for k, p in _DRUGS.items()}


def _record(static: dict) -> dict[str, float]:
    num = lambda key: float(static[key]) if static.get(key) is not None else np.nan  # noqa: E731
    sex = static.get("sex")
    return {
        "r_age": num("age"),
        "r_male": np.nan if sex is None else float(sex == "M"),
        "r_bmi": num("bmi"),
        "r_duration": num("diabetes_duration_y"),
        "r_hba1c": num("hba1c_pct"),
        "r_fpg": num("fasting_glucose_mgdl"),
        "r_pp2h": num("pp2h_glucose_mgdl"),
        "r_cpep": num("fasting_cpeptide_nmol"),
        "r_egfr": num("egfr"),
        **drug_flags(static.get("agents")),
    }


def meal_table(rec: Recording, k_days: float = 3.0) -> pd.DataFrame:
    """One row per eligible meal after the split: the label and every arm's features.

    Record features come from the static record; history features from sensor readings before the split;
    fingerstick features from fingersticks after the split and before the meal; sensor features from sensor
    readings up to the meal. Nothing else may look past the meal time.
    """
    if why_skipped(rec, k_days) is not None:
        return pd.DataFrame()
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    tod0 = rec.start.hour * 60 + rec.start.minute
    cal = t < split
    centres = np.arange(0, 1440, BIN) + BIN // 2
    shape = 0.5 * average_day_baseline((tod0 + t[cal]) % 1440, g[cal], centres, BIN) + 0.5 * float(
        g[cal].mean()
    )
    meals = merge_meals(rec.meals["t_min"])
    seen = [
        e for e in (excursion(t[cal], g[cal], m) for m in meals[meals < split - HORIZON_MIN]) if e is not None
    ]
    history = {
        "h_mean": float(g[cal].mean()),
        "h_sd": float(g[cal].std()),
        "h_tar": float(np.mean(g[cal] > EVENT_MGDL)),
        "h_rate": (sum(seen) + 1.0) / (len(seen) + 2.0),  # shrunk toward one half when few meals were seen
    }
    record = _record(rec.static)
    ft = rec.fingersticks["t_min"].to_numpy(dtype=float)
    fg = rec.fingersticks["glucose_mgdl"].to_numpy(dtype=float)
    pump = float("csii" in set(rec.doses["route"])) if len(rec.doses) else 0.0
    rows = []
    for m in meals[meals >= split]:
        y = excursion(t, g, m)
        before = (t <= m) & (t >= m - HORIZON_MIN)
        if y is None or not before.any() or m - t[before][-1] > PRE_GAP_MIN:
            continue
        clock = (tod0 + m) % 1440
        b0 = int(clock) // BIN
        earlier = (ft >= split) & (ft < m)
        recent = earlier & (ft >= m - RECENT_MIN)
        rows.append(
            {
                "rec_id": rec.rec_id,
                "patient_id": rec.patient_id,
                "dev": is_dev_patient(rec.patient_id),
                "t_min": float(m),
                "hidden_days": float((t.max() - split) / 1440.0),
                "pump": pump,
                "y": int(y),
                "y250": int(bool(excursion(t, g, m, SEVERE_MGDL))),
                "start_high": int(g[before][-1] > EVENT_MGDL),
                "mins_to_high": minutes_to_high(t, g, m) if y else float("nan"),
                "c_sin": float(np.sin(2 * np.pi * clock / 1440)),
                "c_cos": float(np.cos(2 * np.pi * clock / 1440)),
                **record,
                **history,
                "h_at": float(shape[b0]),
                "h_peak": float(max(shape[(b0 + i) % shape.size] for i in range(5))),
                "f_has": int(recent.any()),
                "f_last": float(fg[recent][-1]) if recent.any() else np.nan,
                "f_age": float(m - ft[recent][-1]) if recent.any() else np.nan,
                "f_n": int(earlier.sum()),
                "f_mean": float(fg[earlier].mean()) if earlier.any() else np.nan,
                "s_last": float(g[before][-1]),
                "s_slope": float(g[before][-1] - np.interp(m - 30.0, t, g)),
                "s_mean": float(g[before].mean()),
            }
        )
    return pd.DataFrame(rows)
