"""CGMacros (PhysioNet, CC BY-NC-SA 4.0): two CGMs, Fitbit, meal macros, 45 people, 10 days.

Column names below are taken from the dataset's own data dictionaries.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RAW_DIR
from chhaya.data.schema import ACTIVITY_COLS, CGM_COLS, MEAL_COLS, Recording, empty
from chhaya.units import INCH_TO_M, LB_TO_KG

MIN_PRIMARY_READINGS = 96  # one day of 15-minute readings


def _strip(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
    return df


def load_bio(root: Path) -> pd.DataFrame:
    """Demographics and labs, indexed by participant number."""
    path = next(iter(sorted(root.rglob("bio.csv"))), None)
    if path is None:
        raise FileNotFoundError(f"bio.csv not found under {root}; run python -m chhaya.data.download cgmacros")
    bio = _strip(pd.read_csv(path))
    id_col = next((c for c in bio.columns if re.search(r"subject|participant|^id$", c, re.I)), bio.columns[0])
    return bio.set_index(bio[id_col].astype(int))


def _num(row: pd.Series | None, prefix: str) -> float:
    """First column starting with `prefix`, as a float; NaN when absent or unparseable."""
    if row is None:
        return float("nan")
    for col, val in row.items():
        if str(col).lower().startswith(prefix.lower()):
            return float(pd.to_numeric(val, errors="coerce"))
    return float("nan")


def _static(row: pd.Series | None) -> dict:
    hba1c = _num(row, "A1c")
    group = None if np.isnan(hba1c) else "healthy" if hba1c < 5.7 else "prediabetes" if hba1c <= 6.4 else "t2d"
    sex = None if row is None else next((str(v) for c, v in row.items() if str(c).lower() == "gender"), None)
    return {
        "age": _num(row, "Age"),
        "sex": sex,
        "bmi": _num(row, "BMI"),
        "weight_kg": _num(row, "Body weight") * LB_TO_KG,
        "height_m": _num(row, "Height") * INCH_TO_M,
        "hba1c_pct": hba1c,
        "fasting_glucose_mgdl": _num(row, "Fasting GLU"),
        "fasting_insulin_uu_ml": _num(row, "Insulin"),
        "triglycerides_mgdl": _num(row, "Triglycerides"),
        "hdl_mgdl": _num(row, "HDL"),
        "group": group,
    }


def _thin(df: pd.DataFrame, col: str, step: int) -> pd.DataFrame:
    """One reading per `step`-minute bin, so a sensor interpolated to 1 minute is not over-weighted."""
    if col not in df.columns:
        return empty(CGM_COLS)
    d = df.loc[df[col].notna(), ["t_min", col]]
    d = d[(d[col] >= 20) & (d[col] <= 600)]
    d = d.groupby(d["t_min"] // step, sort=True).first()
    return d.rename(columns={col: "glucose_mgdl"}).astype({"t_min": int, "glucose_mgdl": float}).reset_index(drop=True)


def load_recording(csv_path: Path, bio_row: pd.Series | None) -> Recording | None:
    """Parse one participant file. Returns None when neither sensor has a day of data."""
    df = _strip(pd.read_csv(csv_path))
    df["ts"] = pd.to_datetime(df["Timestamp"], format="mixed", errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")
    start = df["ts"].iloc[0].floor("min")
    df["t_min"] = ((df["ts"] - start).dt.total_seconds() // 60).astype(int)
    df = df.drop_duplicates("t_min")
    n_min = int(df["t_min"].iloc[-1]) + 1

    libre, dexcom = _thin(df, "Libre GL", 15), _thin(df, "Dexcom GL", 5)
    static = _static(bio_row)
    if len(libre) >= MIN_PRIMARY_READINGS:
        cgm, ref, static["primary_sensor"] = libre, dexcom, "libre"
    elif len(dexcom) >= MIN_PRIMARY_READINGS * 3:
        cgm, ref, static["primary_sensor"] = _thin(df, "Dexcom GL", 15), empty(CGM_COLS), "dexcom"
    else:
        return None

    m = df[df["Meal Type"].notna() & df["Carbs"].notna()] if "Meal Type" in df.columns else df.iloc[:0]
    frac = (pd.to_numeric(m.get("Amount Consumed"), errors="coerce").fillna(100.0).clip(0.0, 100.0) / 100.0).to_numpy()
    meals = pd.DataFrame(
        {
            "t_min": m["t_min"].to_numpy(dtype=float),
            "carb_g": m["Carbs"].to_numpy(dtype=float) * frac,
            "protein_g": m["Protein"].to_numpy(dtype=float) * frac,
            "fat_g": m["Fat"].to_numpy(dtype=float) * frac,
            "fibre_g": m["Fiber"].to_numpy(dtype=float) * frac,
            "label": m["Meal Type"].astype(str).to_numpy(),
        },
        columns=MEAL_COLS,
    )

    a = df[df["Mets"].notna()] if "Mets" in df.columns else df.iloc[:0]
    activity = pd.DataFrame(
        {
            "t_min": a["t_min"].to_numpy(dtype=float),
            "met": a["Mets"].to_numpy(dtype=float) / 10.0,  # the file stores METs multiplied by 10
            "hr": pd.to_numeric(a.get("HR"), errors="coerce").to_numpy(dtype=float),
        },
        columns=ACTIVITY_COLS,
    )

    number = int(re.search(r"(\d+)", csv_path.stem).group(1))
    rec = Recording(
        rec_id=f"cgmacros-{number:03d}",
        patient_id=f"cgmacros-{number:03d}",
        dataset="cgmacros",
        start=start,
        n_min=n_min,
        cgm=cgm,
        cgm_ref=ref,
        meals=meals,
        activity=activity,
        static=static,
    )
    rec.validate()
    return rec


def load_all(root: Path = RAW_DIR / "cgmacros") -> list[Recording]:
    bio = load_bio(root)
    recs = []
    for path in sorted(root.rglob("CGMacros-*.csv")):
        number = int(re.search(r"(\d+)", path.stem).group(1))
        rec = load_recording(path, bio.loc[number] if number in bio.index else None)
        if rec is not None:
            recs.append(rec)
    if not recs:
        raise FileNotFoundError(f"no CGMacros-*.csv under {root}; run python -m chhaya.data.download cgmacros")
    return recs
