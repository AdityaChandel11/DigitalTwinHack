"""ShanghaiT2DM (Figshare, CC BY 4.0): Libre CGM, fingersticks, diet text, drug doses, labs; 100 patients.

Workbook column names are matched by pattern because the published description gives field names
without their exact header spelling. `python -m chhaya.data.audit` prints the headers it actually found.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RAW_DIR
from chhaya.data.schema import CGM_COLS, DOSE_COLS, MEAL_COLS, Recording
from chhaya.units import MGDL_PER_MMOL, hba1c_ifcc_to_percent, insulin_pmol_to_uu_ml

SERIES = {
    "ts": r"^date",
    "cgm": r"^cgm",
    "cbg": r"^cbg",
    "diet_en": r"^dietary intake",
    "diet_zh": r"饮食",
    "ins_sc": r"insulin dose.*s\.?\s*c",
    "ins_iv": r"insulin dose.*i\.?\s*v",
    "agents": r"non-?insulin",
    "csii_bolus": r"csii.*bolus",
    "csii_basal": r"csii.*basal",
}
SUMMARY = {
    "age": r"^age",
    "sex_code": r"^gender",
    "weight_kg": r"^weight",
    "bmi": r"^bmi",
    "diabetes_duration_y": r"duration of diabetes",
    "fasting_glucose_mgdl": r"^fasting plasma glucose",
    "fasting_insulin_pmol": r"^fasting insulin",
    "fasting_cpeptide_nmol": r"^fasting c-?peptide",
    "hba1c_ifcc": r"^hba1c",
    "egfr": r"glomerular",
    "agents": r"^hypoglycemic agents",
    "hypoglycemia": r"^hypoglycemia",
}


def match_columns(columns, patterns: dict[str, str]) -> dict[str, str]:
    """Map each logical field to the first header matching its pattern (case-insensitive)."""
    found = {}
    for key, pat in patterns.items():
        hit = next((c for c in columns if re.search(pat, str(c).strip(), re.I)), None)
        if hit is not None:
            found[key] = hit
    return found


def load_summary(root: Path) -> pd.DataFrame:
    """Clinical summary sheet, indexed by recording file stem."""
    path = next(iter(sorted(root.rglob("Shanghai_T2DM_Summary.*"))), None)
    if path is None:
        raise FileNotFoundError(f"Shanghai_T2DM_Summary not found under {root}; run python -m chhaya.data.download shanghai")
    df = pd.read_excel(path)
    return df.set_index(df.columns[0]).rename(index=lambda s: str(s).strip())


def _static(row: pd.Series | None) -> dict:
    if row is None:
        return {"group": "t2d"}
    cols = match_columns(row.index, SUMMARY)
    num = {k: float(pd.to_numeric(row[c], errors="coerce")) for k, c in cols.items() if k not in ("agents", "hypoglycemia")}
    return {
        "age": num.get("age", np.nan),
        "sex": {1.0: "F", 2.0: "M"}.get(num.get("sex_code")),
        "weight_kg": num.get("weight_kg", np.nan),
        "bmi": num.get("bmi", np.nan),
        "diabetes_duration_y": num.get("diabetes_duration_y", np.nan),
        "fasting_glucose_mgdl": num.get("fasting_glucose_mgdl", np.nan),
        "fasting_insulin_uu_ml": insulin_pmol_to_uu_ml(num.get("fasting_insulin_pmol", np.nan)),
        "fasting_cpeptide_nmol": num.get("fasting_cpeptide_nmol", np.nan),
        "hba1c_pct": hba1c_ifcc_to_percent(num.get("hba1c_ifcc", np.nan)),
        "egfr": num.get("egfr", np.nan),
        "agents": str(row[cols["agents"]]) if "agents" in cols else None,
        "hypoglycemia_history": str(row[cols["hypoglycemia"]]) if "hypoglycemia" in cols else None,
        "group": "t2d",
    }


def _glucose(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = pd.to_numeric(df[col], errors="coerce")
    d = pd.DataFrame({"t_min": df["t_min"], "glucose_mgdl": g}).dropna()
    if len(d) and d["glucose_mgdl"].median() < 35.0:  # a sheet in mmol/L
        d["glucose_mgdl"] *= MGDL_PER_MMOL
    d = d[(d["glucose_mgdl"] >= 20) & (d["glucose_mgdl"] <= 600)]
    return d.astype({"t_min": int, "glucose_mgdl": float}).reset_index(drop=True)[CGM_COLS]


def _text_rows(df: pd.DataFrame, col: str | None) -> pd.DataFrame:
    if col is None:
        return df.iloc[:0].assign(text=pd.Series(dtype=str))
    text = df[col].astype("string").str.strip()
    keep = text.notna() & (text != "") & (text != "0")
    return df.loc[keep, ["t_min"]].assign(text=text[keep])


def load_recording(path: Path, summary_row: pd.Series | None) -> Recording | None:
    df = pd.read_excel(path)
    cols = match_columns(df.columns, SERIES)
    if "ts" not in cols or "cgm" not in cols:
        raise ValueError(f"{path.name}: no date/CGM column among {list(df.columns)}")
    df["ts"] = pd.to_datetime(df[cols["ts"]], errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")
    if df.empty:
        return None
    start = df["ts"].iloc[0].floor("min")
    df["t_min"] = ((df["ts"] - start).dt.total_seconds() // 60).astype(int)
    df = df.drop_duplicates("t_min")

    cgm = _glucose(df, cols["cgm"])
    if len(cgm) < 96:
        return None
    diet = _text_rows(df, cols.get("diet_en") or cols.get("diet_zh"))
    meals = pd.DataFrame(
        {"t_min": diet["t_min"].to_numpy(dtype=float), "label": diet["text"].astype(str).to_numpy()}, columns=MEAL_COLS
    ).astype({c: float for c in MEAL_COLS[1:5]})
    doses = []
    for key, route in (("agents", "oral"), ("ins_sc", "sc"), ("ins_iv", "iv"), ("csii_bolus", "csii")):
        rows = _text_rows(df, cols.get(key))
        doses.append(pd.DataFrame({"t_min": rows["t_min"].astype(float), "drug": rows["text"].astype(str), "dose": np.nan, "route": route}))
    doses = pd.concat(doses, ignore_index=True)[DOSE_COLS].sort_values("t_min", ignore_index=True)

    stem = path.stem.strip()
    rec = Recording(
        rec_id=f"shanghai-{stem}",
        patient_id=f"shanghai-{stem.split('_')[0]}",
        dataset="shanghai",
        start=start,
        n_min=int(df["t_min"].iloc[-1]) + 1,
        cgm=cgm,
        fingersticks=_glucose(df, cols["cbg"]) if "cbg" in cols else cgm.iloc[:0],
        meals=meals,
        doses=doses,
        static=_static(summary_row),
    )
    rec.validate()
    return rec


def load_all(root: Path = RAW_DIR / "shanghai") -> list[Recording]:
    summary = load_summary(root)
    folder = next((p for p in sorted(root.rglob("Shanghai_T2DM")) if p.is_dir()), None)
    if folder is None:
        raise FileNotFoundError(f"Shanghai_T2DM folder not found under {root}")
    recs = []
    for path in sorted(folder.glob("*.xls*")):
        stem = path.stem.strip()
        rec = load_recording(path, summary.loc[stem] if stem in summary.index else None)
        if rec is not None:
            recs.append(rec)
    return recs


def food_strings(recs: list[Recording]) -> pd.Series:
    """Every distinct diet entry with its count: the worklist for the food-to-macros table."""
    labels = pd.concat([r.meals["label"] for r in recs], ignore_index=True)
    return labels.value_counts()
