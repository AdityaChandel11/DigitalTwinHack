"""Accuracy metrics. All glucose arguments are mg/dL."""

from __future__ import annotations

import numpy as np

from chhaya.units import gmi_percent


def rmse(pred, truth) -> float:
    return float(np.sqrt(np.mean((np.asarray(pred) - np.asarray(truth)) ** 2)))


def mae(pred, truth) -> float:
    return float(np.mean(np.abs(np.asarray(pred) - np.asarray(truth))))


def mard(pred, truth) -> float:
    """Mean absolute relative difference, percent."""
    pred, truth = np.asarray(pred), np.asarray(truth)
    return float(100.0 * np.mean(np.abs(pred - truth) / truth))


def pearson(pred, truth) -> float:
    pred, truth = np.asarray(pred), np.asarray(truth)
    if pred.size < 3 or np.ptp(pred) == 0.0 or np.ptp(truth) == 0.0:  # np.std of a constant is 1e-17, not 0
        return float("nan")
    return float(np.corrcoef(pred, truth)[0, 1])


def time_in_ranges(g) -> dict[str, float]:
    """Percent of readings below 70, within 70-180 and above 180 mg/dL."""
    g = np.asarray(g)
    return {
        "tbr": float(100.0 * np.mean(g < 70.0)),
        "tir": float(100.0 * np.mean((g >= 70.0) & (g <= 180.0))),
        "tar": float(100.0 * np.mean(g > 180.0)),
    }


def coverage(truth, lo, hi) -> float:
    truth = np.asarray(truth)
    return float(np.mean((truth >= np.asarray(lo)) & (truth <= np.asarray(hi))))


def score(pred, truth, lo=None, hi=None) -> dict[str, float]:
    """Every metric reported for an estimate of a hidden glucose trace."""
    pred, truth = np.asarray(pred, dtype=float), np.asarray(truth, dtype=float)
    if pred.shape != truth.shape or pred.size == 0:
        raise ValueError(f"pred {pred.shape} and truth {truth.shape} must match and be non-empty")
    rp, rt = time_in_ranges(pred), time_in_ranges(truth)
    out = {
        "rmse": rmse(pred, truth),
        "mae": mae(pred, truth),
        "mard": mard(pred, truth),
        "r": pearson(pred, truth),
        "bias": float(np.mean(pred - truth)),
        "tir_err": abs(rp["tir"] - rt["tir"]),
        "tar_err": abs(rp["tar"] - rt["tar"]),
        "tbr_err": abs(rp["tbr"] - rt["tbr"]),
        "gmi_err": float(abs(gmi_percent(pred.mean()) - gmi_percent(truth.mean()))),
    }
    if lo is not None and hi is not None:
        out["cov80"] = coverage(truth, lo, hi)
    return out


def within_15_15(pred, ref) -> float:
    """Percent of readings within 15 mg/dL of a reference below 100 mg/dL, or within 15 % of one at or above it.

    The agreement rule of ISO 15197:2013 for glucose meters, used here to put an estimate next to a real sensor.
    """
    pred, ref = np.asarray(pred, dtype=float), np.asarray(ref, dtype=float)
    err = np.abs(pred - ref)
    return float(100.0 * np.mean(np.where(ref < 100.0, err <= 15.0, err <= 0.15 * ref)))


def clarke_zones(pred, ref) -> dict[str, float]:
    """Percent of readings in each zone of the Clarke error grid (A: clinically accurate ... E: opposite treatment)."""
    pred, ref = np.asarray(pred, dtype=float), np.asarray(ref, dtype=float)
    a = ((ref <= 70) & (pred <= 70)) | ((pred >= 0.8 * ref) & (pred <= 1.2 * ref))
    e = ((ref >= 180) & (pred <= 70)) | ((ref <= 70) & (pred >= 180))
    c = ((ref >= 70) & (ref <= 290) & (pred >= ref + 110)) | (
        (ref >= 130) & (ref <= 180) & (pred <= 1.4 * ref - 182)
    )
    d = (
        ((ref >= 240) & (pred >= 70) & (pred <= 180))
        | ((ref <= 175 / 3) & (pred >= 70) & (pred <= 180))
        | ((ref >= 175 / 3) & (ref <= 70) & (pred >= 1.2 * ref))
    )
    zone = np.select([a, e, c, d], ["A", "E", "C", "D"], default="B")
    return {z: float(100.0 * np.mean(zone == z)) for z in "ABCDE"}
