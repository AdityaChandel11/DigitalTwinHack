"""The single interchange type between loaders, the twin and evaluation."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

CGM_COLS = ["t_min", "glucose_mgdl"]
MEAL_COLS = ["t_min", "carb_g", "protein_g", "fat_g", "fibre_g", "label"]
ACTIVITY_COLS = ["t_min", "met", "hr"]
DOSE_COLS = ["t_min", "drug", "dose", "route"]
_TEXT_COLS = ("label", "drug", "route")


def empty(cols: list[str]) -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object" if c in _TEXT_COLS else "float64") for c in cols})


@dataclass(frozen=True)
class Recording:
    """One continuous monitoring period of one patient. `t_min` counts minutes from `start`."""

    rec_id: str
    patient_id: str
    dataset: str
    start: pd.Timestamp
    n_min: int
    cgm: pd.DataFrame
    static: dict
    cgm_ref: pd.DataFrame = field(default_factory=lambda: empty(CGM_COLS))
    fingersticks: pd.DataFrame = field(default_factory=lambda: empty(CGM_COLS))
    meals: pd.DataFrame = field(default_factory=lambda: empty(MEAL_COLS))
    activity: pd.DataFrame = field(default_factory=lambda: empty(ACTIVITY_COLS))
    doses: pd.DataFrame = field(default_factory=lambda: empty(DOSE_COLS))

    def validate(self) -> None:
        """Raise ValueError when the recording would silently corrupt a fit."""
        for name, cols in (
            ("cgm", CGM_COLS),
            ("cgm_ref", CGM_COLS),
            ("fingersticks", CGM_COLS),
            ("meals", MEAL_COLS),
            ("activity", ACTIVITY_COLS),
            ("doses", DOSE_COLS),
        ):
            df = getattr(self, name)
            missing = [c for c in cols if c not in df.columns]
            if missing:
                raise ValueError(f"{self.rec_id}: {name} lacks columns {missing}")
            if len(df) and ((df["t_min"] < 0).any() or (df["t_min"] >= self.n_min).any()):
                raise ValueError(f"{self.rec_id}: {name} has t_min outside [0, {self.n_min})")
        if self.cgm.empty:
            raise ValueError(f"{self.rec_id}: no CGM readings")
        if not self.cgm["t_min"].is_monotonic_increasing:
            raise ValueError(f"{self.rec_id}: cgm is not sorted by time")
        g = self.cgm["glucose_mgdl"]
        if g.isna().any() or (g < 20).any() or (g > 600).any():
            raise ValueError(f"{self.rec_id}: cgm glucose missing or outside 20-600 mg/dL")
