""" "Treatment changed since the sensor", from the dose table of one recording.

The expiry record's case series compared three things between two wears: the agents listed, whether insulin
was given, whether a pump was used. This applies the same three comparisons to the doses before and after the
split of one recording. Dose amounts are not compared. It states what the files say; it is never a predictor,
and "no change recorded" does not mean the report still holds (the screen says so beside it).
"""

from __future__ import annotations

import pandas as pd

from chhaya.data.schema import Recording
from chhaya.eval.descriptive import day_index
from chhaya.eval.events import drug_flags
from chhaya.eval.expiry import INSULIN_ROUTES


def _kinds(doses: pd.DataFrame) -> set[str]:
    """What kinds of treatment a set of dose rows shows: agent classes, insulin by any route, a pump."""
    routes = set(doses["route"])
    text = " ".join(doses["drug"].astype(str))
    kinds = {name for name, flag in drug_flags(text).items() if flag == 1.0}
    if routes & INSULIN_ROUTES:
        kinds.add("r_insulin")
    if "csii" in routes:
        kinds.add("pump")
    return kinds


def treatment_since(rec: Recording, k_days: float) -> dict:
    """`state` is "changed", "none" or "not_recorded"; `day` is the day since the sensor of the first dose of a
    kind not seen during the wear, when there is one (a stop has no date).

    With no dose on one side of the split there is nothing to compare, and that is "not recorded", never
    "unchanged".
    """
    split = k_days * 1440.0
    before, after = rec.doses[rec.doses["t_min"] < split], rec.doses[rec.doses["t_min"] >= split]
    if before.empty or after.empty:
        return {"state": "not_recorded", "day": None}
    then, now = _kinds(before), _kinds(after)
    if then == now:
        return {"state": "none", "day": None}
    day = None
    if now - then:
        for _, row in after.sort_values("t_min", kind="stable").iterrows():
            if _kinds(row.to_frame().T) - then:
                day = int(day_index([row["t_min"]], split)[0])
                break
    return {"state": "changed", "day": day}
