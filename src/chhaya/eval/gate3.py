"""Gate 3: is a post-meal excursion predictable at meal time, and does fusing the streams help?

Bars are in docs/PREREGISTRATION.md, Amendment 3, section M. Models are fitted on development patients.
Test patients are scored once, and only with --confirm.
Usage: python -m chhaya.eval.gate3            (development patients, cross-validated)
       python -m chhaya.eval.gate3 --confirm  (the one confirmatory run)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from chhaya.config import RESULTS_DIR, SEED
from chhaya.data.schema import Recording
from chhaya.eval.events import CONTEXT, HISTORY, RECORD, SENSOR, STICKS, meal_table
from chhaya.eval.gate2 import _clean, _git
from chhaya.eval.reveal import why_skipped

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


def build_table(recs: list[Recording], k_days: float = 3.0) -> tuple[pd.DataFrame, dict]:
    """Every eligible meal of every recording, and a count of recordings skipped with the reason."""
    frames, skipped = [], Counter()
    for rec in recs:
        why = why_skipped(rec, k_days)
        tab = meal_table(rec, k_days) if why is None else pd.DataFrame()
        if tab.empty:
            skipped[why or "no eligible meal after the split"] += 1
        else:
            frames.append(tab)
    table = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return table, dict(skipped)


def development_run(dev: pd.DataFrame, y: str = "y", n_boot: int = 2000) -> dict:
    """Cross-validated on development patients. For checking the pipeline; it gives no verdict."""
    oof = out_of_fold(dev, y)
    truth = dev[y].to_numpy(dtype=int)
    pid = dev["patient_id"].to_numpy()
    preds = {arm: oof[arm].to_numpy(dtype=float) for arm in ARMS}
    preds[BASELINE] = dev["h_rate"].to_numpy(dtype=float)
    return {
        "confirmatory": False,
        "n_meals": int(truth.size),
        "n_patients": int(pd.unique(pid).size),
        "prevalence": float(truth.mean()),
        "arms": {a: {**metrics(truth, p), **within_patient_auroc(pid, truth, p)} for a, p in preds.items()},
        "diffs": {b: boot_diff(pid, truth, preds["fused"], preds[b], n_boot) for b in (*SINGLE, BASELINE)},
    }


def _lightgbm(dev: pd.DataFrame, test: pd.DataFrame, y: str = "y") -> dict:
    """The fused arm with a LightGBM at library defaults: a sensitivity analysis, with no bar."""
    from lightgbm import LGBMClassifier

    cols = ARMS["fused"]
    model = LGBMClassifier(random_state=SEED, n_jobs=1, verbose=-1)
    model.fit(dev[cols].to_numpy(dtype=float), dev[y].to_numpy(dtype=int))
    p = model.predict_proba(test[cols].to_numpy(dtype=float))[:, 1]
    truth = test[y].to_numpy(dtype=int)
    return {**metrics(truth, p), **within_patient_auroc(test["patient_id"].to_numpy(), truth, p)}


def _secondary(dev: pd.DataFrame, test: pd.DataFrame, n_boot: int) -> dict:
    """The pre-declared secondary analyses: 250 mg/dL, meals that start in range, timing, LightGBM, subgroups.

    An analysis whose development meals hold one outcome only cannot be fitted; it is left out, not faked.
    """
    out = {}
    if dev["y250"].nunique() == 2:
        out["above_250"] = evaluate(dev, test, "y250", n_boot)
    low_dev, low_test = dev[dev["start_high"] == 0], test[test["start_high"] == 0]
    if len(low_test) and low_dev["y"].nunique() == 2:
        out["starts_at_or_below_180"] = evaluate(low_dev, low_test, "y", n_boot)
    mins = test["mins_to_high"].dropna()
    out["minutes_to_first_reading_above_180"] = {
        "median": float(mins.median()) if len(mins) else None,
        "n_meals": int(len(mins)),
    }
    out["lightgbm_fused"] = _lightgbm(dev, test)
    p = fit_predict(dev, test, ARMS["fused"])
    groups = {
        "on_insulin": test["r_insulin"] == 1,
        "not_on_insulin": test["r_insulin"] == 0,
        "pump": test["pump"] == 1,
        "no_pump": test["pump"] == 0,
        "male": test["r_male"] == 1,
        "female": test["r_male"] == 0,
        "age_65_or_more": test["r_age"] >= 65,
        "under_65": test["r_age"] < 65,
    }
    out["subgroups_fused"] = {
        name: {
            "n_meals": int(m.sum()),
            "n_patients": int(test.loc[m, "patient_id"].nunique()),
            **metrics(test.loc[m, "y"], p[m.to_numpy()]),
        }
        for name, m in groups.items()
        if m.any()
    }
    return out


def write_report(result: dict, out_dir: Path, confirmatory: bool) -> None:
    """summary.json and report.md. Aggregates only: no per-meal rows, no patient identifiers."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(_clean(result), indent=2, allow_nan=False), encoding="utf-8"
    )
    r = result["primary"]
    lines = ["# Gate 3: post-meal excursion above 180 mg/dL, predicted at meal time", ""]
    if confirmatory:
        verdict = "PASS" if r["verdict"]["pass"] else "NOT PASSED"
        lines.append(f"Verdict: **{verdict}** (bars M1 and M2, Amendment 3)")
        lines += ["", "```json", json.dumps(r["verdict"], indent=2), "```"]
    else:
        lines.append("Development patients, cross-validated. Not confirmatory: no verdict.")
    lines += [
        "",
        f"Meals {r['n_meals']}, patients {r['n_patients']}, share with the event {r['prevalence']:.3f}.",
        "",
    ]
    lines += [pd.DataFrame(r["arms"]).T.round(3).to_markdown(), ""]
    lines += ["AUPRC of the fused sensor-off model minus each comparator (95 % interval over patients):", ""]
    lines.append(pd.DataFrame(r["diffs"]).T.round(3).to_markdown())
    if "kept_without_sensor" in r:
        kept = r["kept_without_sensor"]
        lines += ["", f"Share of the sensor-on gain over prevalence kept without the sensor: {kept:.2f}"]
    sec = result.get("secondary")
    if sec:
        mins = sec["minutes_to_first_reading_above_180"]
        lines += ["", "## Secondary (no bar)", ""]
        lines.append(
            f"Median minutes from meal to the first reading above 180: {mins['median']} ({mins['n_meals']} meals)."
        )
        rows = {"LightGBM, library defaults (fused)": sec["lightgbm_fused"]}
        for name in ("above_250", "starts_at_or_below_180"):
            if name in sec:
                rows[f"{name}: fused"] = sec[name]["arms"]["fused"]
                rows[f"{name}: personal rate"] = sec[name]["arms"][BASELINE]
        lines += ["", pd.DataFrame(rows).T.round(3).to_markdown(), ""]
        lines.append(pd.DataFrame(sec["subgroups_fused"]).T.round(3).to_markdown())
    if result.get("skipped"):
        lines += ["", "Recordings skipped: " + "; ".join(f"{v} ({k})" for k, v in result["skipped"].items())]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def refuse_second_run(out_dir: Path) -> None:
    """The test split is scored once. A re-run after a defect is an amendment, made by hand, not by accident."""
    if (out_dir / "summary.json").exists():
        raise SystemExit(
            f"{out_dir} already holds the confirmatory run. Scoring the test patients again needs a dated "
            "amendment (docs/PREREGISTRATION.md); move the folder aside deliberately if that is what this is."
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test patients; this is done once")
    ap.add_argument("--k", type=float, default=3.0)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    out_dir = RESULTS_DIR / "gate3" / ("shanghai" if args.confirm else "shanghai-dev")
    if args.confirm:
        refuse_second_run(out_dir)
    from chhaya.data.shanghai import load_all

    table, skipped = build_table(load_all(), args.k)
    dev = table[table["dev"]].reset_index(drop=True)
    if not args.confirm:
        del table  # no test patient's row is used below this line
        result = {"primary": development_run(dev, n_boot=args.boot), "skipped": skipped}
    else:
        test = table[~table["dev"]].reset_index(drop=True)
        result = {
            "primary": evaluate(dev, test, "y", args.boot),
            "skipped": skipped,
            "secondary": _secondary(dev, test, args.boot),
        }
    write_report(result, out_dir, confirmatory=args.confirm)
    status = _git("status", "--porcelain", "--", "src")
    prov = {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes_in_src": bool(status),
        "k_days": args.k,
        "boot": args.boot,
        "seed": SEED,
        "confirm": args.confirm,
    }
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
