"""Sensor readings paired with fingersticks: is a sensor threshold crossing also a capillary one?"""

from __future__ import annotations

import numpy as np
import pandas as pd

from chhaya.data.schema import Recording

MAX_GAP_MIN = 10
PAIR_COLS = ["t_min", "cbg", "cgm", "slope", "hour"]
THRESHOLDS = {
    "below_54": (54.0, True),
    "below_70": (70.0, True),
    "above_180": (180.0, False),
    "above_250": (250.0, False),
}
RANGES = [(0.0, 70.0), (70.0, 100.0), (100.0, 180.0), (180.0, 250.0), (250.0, 600.0)]
FLAT_SLOPE = 5.0  # mg/dL per 15 minutes: below this the sensor trace is flat, so a mismatch is not lag


def paired(
    rec: Recording, lo: float = 0.0, hi: float | None = None, max_gap: float = MAX_GAP_MIN
) -> pd.DataFrame:
    """Each fingerstick in [lo, hi) with the nearest sensor reading no further than `max_gap` minutes away.

    `slope` is the sensor's change per reading around the pair (NaN at the ends of the trace); `hour` is the
    clock hour of the fingerstick.
    """
    hi = float(rec.n_min) if hi is None else hi
    fs = rec.fingersticks[(rec.fingersticks["t_min"] >= lo) & (rec.fingersticks["t_min"] < hi)]
    ft = fs["t_min"].to_numpy(dtype=float)
    fg = fs["glucose_mgdl"].to_numpy(dtype=float)
    ct = rec.cgm["t_min"].to_numpy(dtype=float)
    cg = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    if ft.size == 0 or ct.size < 2:
        return pd.DataFrame({c: pd.Series(dtype=float) for c in PAIR_COLS})
    j = np.clip(np.searchsorted(ct, ft), 1, ct.size - 1)
    near = np.where(np.abs(ct[j] - ft) < np.abs(ct[j - 1] - ft), j, j - 1)
    ok = np.abs(ct[near] - ft) <= max_gap
    inner = (near > 0) & (near < ct.size - 1)
    slope = np.where(
        inner, (cg[np.clip(near + 1, 0, ct.size - 1)] - cg[np.clip(near - 1, 0, ct.size - 1)]) / 2.0, np.nan
    )
    tod0 = rec.start.hour * 60 + rec.start.minute
    return pd.DataFrame(
        {
            "t_min": ft[ok],
            "cbg": fg[ok],
            "cgm": cg[near][ok],
            "slope": slope[ok],
            "hour": ((tod0 + ft[ok]) % 1440) // 60,
        }
    )


def validity_table(pairs: pd.DataFrame) -> dict:
    """For each threshold: how often the sensor flags, the fingerstick flags, and both."""
    out = {}
    for name, (thr, low) in THRESHOLDS.items():
        s = pairs["cgm"] < thr if low else pairs["cgm"] > thr
        f = pairs["cbg"] < thr if low else pairs["cbg"] > thr
        both = int((s & f).sum())
        out[name] = {
            "sensor_flags": int(s.sum()),
            "fingerstick_flags": int(f.sum()),
            "both": both,
            "ppv": both / int(s.sum()) if s.any() else None,
            "sensitivity": both / int(f.sum()) if f.any() else None,
        }
    return out


def label_validity(recs: list[Recording]) -> dict:
    """The label check of Amendment 3, section L, over every recording given."""
    frames = [paired(r).assign(patient_id=r.patient_id) for r in recs]
    p = pd.concat([f for f in frames if len(f)], ignore_index=True)
    diff = p["cgm"] - p["cbg"]
    by_range = []
    for lo, hi in RANGES:
        m = (p["cbg"] >= lo) & (p["cbg"] < hi)
        if m.any():
            by_range.append(
                {
                    "fingerstick_from": lo,
                    "fingerstick_to": hi,
                    "n": int(m.sum()),
                    "bias": float(diff[m].mean()),
                    "mard_percent": float(100 * (diff[m].abs() / p.loc[m, "cbg"]).mean()),
                }
            )
    low = p[p["cgm"] < 70.0]
    flat = low[low["slope"].abs() <= FLAT_SLOPE]
    night = low[low["hour"] < 6]
    share = lambda d: float((d["cbg"] < 70.0).mean()) if len(d) else None  # noqa: E731
    return {
        "n_pairs": int(len(p)),
        "n_patients": int(p["patient_id"].nunique()),
        "mard_percent": float(100 * (diff.abs() / p["cbg"]).mean()),
        "bias": float(diff.mean()),
        "thresholds": validity_table(p),
        "by_fingerstick_range": by_range,
        "sensor_below_70": {
            "n": int(len(low)),
            "patients": int(low["patient_id"].nunique()),
            "fingerstick_median": float(low["cbg"].median()) if len(low) else None,
            "confirmed_share": share(low),
            "flat_trace_n": int(len(flat)),
            "flat_trace_confirmed_share": share(flat),
            "night_n": int(len(night)),
            "night_confirmed_share": share(night),
        },
    }
