"""Gate 3: is a post-meal excursion predictable at meal time, and does fusing the streams help?

Bars are in docs/PREREGISTRATION.md, Amendment 3, section M. Models are fitted on development patients.
Test patients are scored once, and only with --confirm.
Usage: python -m chhaya.eval.gate3            (development patients, cross-validated)
       python -m chhaya.eval.gate3 --confirm  (the one confirmatory run)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from chhaya.config import SEED
from chhaya.eval.events import CONTEXT, HISTORY, RECORD, SENSOR, STICKS

ARMS = {
    "record": CONTEXT + RECORD,
    "history": CONTEXT + HISTORY,
    "fingersticks": CONTEXT + STICKS,
    "fused": CONTEXT + RECORD + HISTORY + STICKS,
    "sensor_on": CONTEXT + RECORD + HISTORY + STICKS + SENSOR,
}
SINGLE = ("record", "history", "fingersticks")
BASELINE = "personal_rate"
TARGET_SENSITIVITY = 0.80
NB_THRESHOLDS = (0.3, 0.5, 0.7)
MIN_EACH = 5  # events and non-events a patient needs for a within-patient AUROC


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], y: str = "y") -> np.ndarray:
    """L2 logistic regression with median imputation, fitted on `train` only."""
    model = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=2000),
    )
    model.fit(train[cols].to_numpy(dtype=float), train[y].to_numpy(dtype=int))
    return model.predict_proba(test[cols].to_numpy(dtype=float))[:, 1]


def _two_classes(y) -> bool:
    return 0 < int(np.sum(y)) < len(y)


def metrics(y, p) -> dict:
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    if not _two_classes(y):
        return {
            "auprc": float("nan"),
            "auroc": float("nan"),
            "brier": float("nan"),
            "calibration_slope": float("nan"),
            "calibration_intercept": float("nan"),
        }
    out = {
        "auprc": float(average_precision_score(y, p)),
        "auroc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, np.clip(p, 0, 1))),
        "calibration_slope": float("nan"),
        "calibration_intercept": float("nan"),
    }
    if np.ptp(p) > 0:
        q = np.clip(p, 1e-6, 1 - 1e-6)
        cal = LogisticRegression(C=1e6, max_iter=2000).fit(np.log(q / (1 - q)).reshape(-1, 1), y)
        out["calibration_slope"] = float(cal.coef_[0, 0])
        out["calibration_intercept"] = float(cal.intercept_[0])
    return out


def within_patient_auroc(patient, y, p) -> dict:
    """Mean AUROC inside patients that have enough of both outcomes: does it know *when*, not just *who*?"""
    df = pd.DataFrame(
        {"patient": np.asarray(patient), "y": np.asarray(y, dtype=int), "p": np.asarray(p, dtype=float)}
    )
    vals = [
        roc_auc_score(g["y"], g["p"])
        for _, g in df.groupby("patient")
        if g["y"].sum() >= MIN_EACH and (1 - g["y"]).sum() >= MIN_EACH
    ]
    return {
        "within_patient_auroc": float(np.mean(vals)) if vals else float("nan"),
        "within_patient_n": len(vals),
    }


def boot_diff(patient, y, pa, pb, n_boot: int = 2000, seed: int = SEED) -> dict:
    """AUPRC(a) - AUPRC(b) with a percentile interval from resampling patients."""
    patient, y = np.asarray(patient), np.asarray(y, dtype=int)
    pa, pb = np.asarray(pa, dtype=float), np.asarray(pb, dtype=float)
    groups = [np.flatnonzero(patient == u) for u in pd.unique(patient)]
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        if _two_classes(y[idx]):
            diffs.append(average_precision_score(y[idx], pa[idx]) - average_precision_score(y[idx], pb[idx]))
    point = (
        average_precision_score(y, pa) - average_precision_score(y, pb) if _two_classes(y) else float("nan")
    )
    lo, hi = np.percentile(diffs, [2.5, 97.5]) if diffs else (float("nan"), float("nan"))
    return {"diff": float(point), "lo": float(lo), "hi": float(hi)}


def out_of_fold(dev: pd.DataFrame, y: str = "y", folds: int = 5) -> pd.DataFrame:
    """Each development meal predicted by models that never saw its patient."""
    out = pd.DataFrame(index=dev.index, columns=list(ARMS), dtype=float)
    k = min(folds, dev["patient_id"].nunique())
    for tr, te in GroupKFold(k).split(dev, groups=dev["patient_id"]):
        for arm, cols in ARMS.items():
            out.iloc[te, out.columns.get_loc(arm)] = fit_predict(dev.iloc[tr], dev.iloc[te], cols, y)
    return out


def _alerts(dev: pd.DataFrame, dev_p, test: pd.DataFrame, test_p, y: str) -> dict:
    """Threshold giving the target sensitivity on development meals, applied to the scored meals."""
    pos = np.sort(np.asarray(dev_p)[dev[y].to_numpy(dtype=bool)])
    if pos.size == 0:
        return {}
    thr = float(pos[int(np.floor((1 - TARGET_SENSITIVITY) * pos.size))])
    alert = np.asarray(test_p) >= thr
    truth = test[y].to_numpy(dtype=bool)
    weeks = float(test.drop_duplicates("rec_id")["hidden_days"].sum() / 7.0)
    return {
        "threshold": thr,
        "sensitivity": float(alert[truth].mean()) if truth.any() else float("nan"),
        "false_alerts_per_patient_week": float((alert & ~truth).sum() / weeks) if weeks > 0 else float("nan"),
    }


def _net_benefit(y, p) -> dict:
    y, p = np.asarray(y, dtype=bool), np.asarray(p, dtype=float)
    out = {}
    for pt in NB_THRESHOLDS:
        w = pt / (1 - pt)
        alert = p >= pt
        out[str(pt)] = {
            "model": float(((alert & y).sum() - w * (alert & ~y).sum()) / y.size),
            "alert_always": float((y.sum() - w * (~y).sum()) / y.size),
        }
    return out


def evaluate(dev: pd.DataFrame, test: pd.DataFrame, y: str = "y", n_boot: int = 2000) -> dict:
    """Fit every arm on `dev`, score `test`, and apply the bars of Amendment 3, section M."""
    truth = test[y].to_numpy(dtype=int)
    pid = test["patient_id"].to_numpy()
    preds = {arm: fit_predict(dev, test, cols, y) for arm, cols in ARMS.items()}
    preds[BASELINE] = test["h_rate"].to_numpy(dtype=float)
    arms = {a: {**metrics(truth, p), **within_patient_auroc(pid, truth, p)} for a, p in preds.items()}
    diffs = {b: boot_diff(pid, truth, preds["fused"], preds[b], n_boot) for b in (*SINGLE, BASELINE)}
    m1 = all(diffs[b]["lo"] > 0 for b in SINGLE)
    m2 = diffs[BASELINE]["lo"] > 0
    slope = arms["fused"]["calibration_slope"]
    prevalence = float(truth.mean()) if truth.size else float("nan")
    gain_on, gain_off = arms["sensor_on"]["auprc"] - prevalence, arms["fused"]["auprc"] - prevalence
    oof = out_of_fold(dev, y)["fused"].to_numpy(dtype=float)
    return {
        "n_meals": int(truth.size),
        "n_patients": int(pd.unique(pid).size),
        "prevalence": prevalence,
        "arms": arms,
        "diffs": diffs,
        "kept_without_sensor": float(gain_off / gain_on) if gain_on > 0 else float("nan"),
        "alerts": _alerts(dev, oof, test, preds["fused"], y),
        "net_benefit": _net_benefit(truth, preds["fused"]),
        "verdict": {
            "m1_fused_beats_every_single_stream": bool(m1),
            "m2_fused_beats_personal_rate": bool(m2),
            "m3_calibration_slope_in_range": bool(0.8 <= slope <= 1.2),
            "pass": bool(m1 and m2),
        },
    }
