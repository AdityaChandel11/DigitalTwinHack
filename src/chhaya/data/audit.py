"""Data truth: what is actually in the downloaded datasets. Decides Gate 1.

Usage: python -m chhaya.data.audit
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR
from chhaya.data.schema import Recording
from chhaya.eval.metrics import time_in_ranges

GATE1_MIN_RECORDINGS = 60
GATE1_MIN_DAYS = 3.0
GATE1_MIN_MEALS_PER_DAY = 2.0


def low_events(t_min: np.ndarray, g: np.ndarray, threshold: float = 70.0, min_readings: int = 2) -> list[int]:
    """Start minutes of runs of at least `min_readings` consecutive readings below `threshold`."""
    starts, run = [], 0
    for i, below in enumerate(g < threshold):
        run = run + 1 if below else 0
        if run == min_readings:
            starts.append(int(t_min[i - min_readings + 1]))
    return starts


def audit_recording(rec: Recording) -> dict:
    days = rec.n_min / 1440.0
    t = rec.cgm["t_min"].to_numpy()
    g = rec.cgm["glucose_mgdl"].to_numpy()
    lows = low_events(t, g)
    tod0 = rec.start.hour * 60 + rec.start.minute
    night_lows = {(tod0 + s) // 1440 for s in lows if (tod0 + s) % 1440 < 360}
    routes = set(rec.doses["route"]) if len(rec.doses) else set()
    return {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "group": rec.static.get("group"),
        "days": round(days, 2),
        "n_cgm": len(rec.cgm),
        "n_ref": len(rec.cgm_ref),
        "n_fingersticks": len(rec.fingersticks),
        "fingersticks_per_day": round(len(rec.fingersticks) / days, 2),
        "n_meals": len(rec.meals),
        "meals_per_day": round(len(rec.meals) / days, 2),
        "n_meals_with_carbs": int(rec.meals["carb_g"].notna().sum()),
        "activity_minutes": len(rec.activity),
        "n_low_events": len(lows),
        "n_nights_with_low": len(night_lows),
        "on_insulin": bool(routes & {"sc", "iv", "csii"}),
        "has_fasting_insulin": bool(np.isfinite(rec.static.get("fasting_insulin_uu_ml", np.nan))),
        **{k: round(v, 1) for k, v in time_in_ranges(g).items()},
    }


def audit(recs: list[Recording]) -> pd.DataFrame:
    return pd.DataFrame([audit_recording(r) for r in recs])


def gate1(shanghai: pd.DataFrame) -> dict:
    """GO when enough Shanghai recordings are long enough and have meals logged."""
    usable = shanghai[(shanghai["days"] >= GATE1_MIN_DAYS) & (shanghai["meals_per_day"] >= GATE1_MIN_MEALS_PER_DAY)]
    return {"usable_recordings": int(len(usable)), "required": GATE1_MIN_RECORDINGS, "go": bool(len(usable) >= GATE1_MIN_RECORDINGS)}


def main(out_dir: Path = RESULTS_DIR / "audit") -> None:
    from chhaya.data import cgmacros, shanghai

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, module in (("cgmacros", cgmacros), ("shanghai", shanghai)):
        recs = module.load_all()
        df = audit(recs)
        df.to_csv(out_dir / f"{name}.csv", index=False)
        summary[name] = {
            "recordings": len(df),
            "patients": int(df["patient_id"].nunique()),
            "patient_days": round(float(df["days"].sum()), 1),
            "fingersticks": int(df["n_fingersticks"].sum()),
            "meals": int(df["n_meals"].sum()),
            "meals_with_carbs": int(df["n_meals_with_carbs"].sum()),
            "low_events": int(df["n_low_events"].sum()),
            "nights_with_low": int(df["n_nights_with_low"].sum()),
            "recordings_on_insulin": int(df["on_insulin"].sum()),
            "by_group": df["group"].value_counts(dropna=False).to_dict(),
        }
        if name == "shanghai":
            summary["gate1"] = gate1(df)
            foods = shanghai.food_strings(recs)
            foods.rename_axis("text").reset_index(name="count").to_csv(out_dir / "shanghai_food_strings.csv", index=False)
            summary[name]["distinct_diet_entries"] = int(len(foods))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
