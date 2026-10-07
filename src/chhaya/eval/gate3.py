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
from collections.abc import Callable
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
BASELINE = (
    "personal_rate"  # the registered comparator of M2: the plain share of calibration meals with the event
)
SMOOTHED = "personal_rate_smoothed"  # the add-one version the history arm uses; reported, carries no bar
NO_RATE = 0.5  # the baseline's value when no calibration meal could be scored (0 of 0)
REGISTERED_K = 3.0
REGISTERED_BOOT = 2000
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
        out["calibration_intercept"] = float(cal.intercept_[0])  # fitted jointly with the slope
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
    """AUPRC(a) - AUPRC(b) with a percentile interval from resampling patients.

    A resample that holds one outcome only has no AUPRC; it is left out and the number used is returned.
    """
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
    return {"diff": float(point), "lo": float(lo), "hi": float(hi), "n_resamples_used": len(diffs)}


def out_of_fold(dev: pd.DataFrame, y: str = "y", folds: int = 5) -> pd.DataFrame:
    """Each development meal predicted by models that never saw its patient.

    A fold whose training meals hold one outcome only cannot be fitted; its meals stay NaN.
    """
    out = pd.DataFrame(index=dev.index, columns=list(ARMS), dtype=float)
    k = min(folds, dev["patient_id"].nunique())
    if k < 2:
        return out
    for tr, te in GroupKFold(k).split(dev, groups=dev["patient_id"]):
        if not _two_classes(dev[y].to_numpy(dtype=int)[tr]):
            continue
        for arm, cols in ARMS.items():
            out.iloc[te, out.columns.get_loc(arm)] = fit_predict(dev.iloc[tr], dev.iloc[te], cols, y)
    return out


def _alerts(dev: pd.DataFrame, dev_p, test: pd.DataFrame, test_p, y: str) -> dict:
    """Threshold giving the target sensitivity on development meals, applied to the scored meals.

    False alerts are counted at eligible meals only but divided by all hidden weeks, so the rate reads low;
    the number of eligible meals per week is given beside it.
    """
    pos = np.asarray(dev_p, dtype=float)[dev[y].to_numpy(dtype=bool)]
    pos = np.sort(pos[np.isfinite(pos)])
    if pos.size == 0:
        return {}
    # the small term keeps 0.2 * 10 from landing on 1.999... and picking the reading below
    thr = float(pos[int(np.floor((1 - TARGET_SENSITIVITY) * pos.size + 1e-9))])
    alert = np.asarray(test_p) >= thr
    truth = test[y].to_numpy(dtype=bool)
    weeks = float(test.drop_duplicates("rec_id")["hidden_days"].sum() / 7.0)
    per_week = lambda n: float(n / weeks) if weeks > 0 else float("nan")  # noqa: E731
    return {
        "threshold": thr,
        "sensitivity": float(alert[truth].mean()) if truth.any() else float("nan"),
        "false_alerts_per_patient_week": per_week((alert & ~truth).sum()),
        "eligible_meals_per_patient_week": per_week(truth.size),
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


def _baselines(table: pd.DataFrame) -> dict[str, np.ndarray]:
    """The two no-learner comparators: the registered plain share, and the smoothed share beside it."""
    return {
        BASELINE: table["h_share"].fillna(NO_RATE).to_numpy(dtype=float),
        SMOOTHED: table["h_rate"].to_numpy(dtype=float),
    }


def evaluate(dev: pd.DataFrame, test: pd.DataFrame, y: str = "y", n_boot: int = 2000) -> dict:
    """Fit every arm on `dev`, score `test`, and apply the bars of Amendment 3, section M."""
    truth = test[y].to_numpy(dtype=int)
    pid = test["patient_id"].to_numpy()
    preds = {arm: fit_predict(dev, test, cols, y) for arm, cols in ARMS.items()} | _baselines(test)
    arms = {a: {**metrics(truth, p), **within_patient_auroc(pid, truth, p)} for a, p in preds.items()}
    diffs = {
        b: boot_diff(pid, truth, preds["fused"], preds[b], n_boot) for b in (*SINGLE, BASELINE, SMOOTHED)
    }
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
        "n_meals_without_a_personal_rate": int(test["h_share"].isna().sum()),
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
    # rule 1: nothing is scored from the calibration window
    assert table.empty or (table["t_min"] >= k_days * 1440.0).all(), (
        "a meal before the split reached the table"
    )
    return table, dict(skipped)


def development_run(dev: pd.DataFrame, y: str = "y", n_boot: int = 2000) -> dict:
    """Cross-validated on development patients. For checking the pipeline; it gives no verdict."""
    oof = out_of_fold(dev, y)
    truth = dev[y].to_numpy(dtype=int)
    pid = dev["patient_id"].to_numpy()
    preds = {arm: oof[arm].to_numpy(dtype=float) for arm in ARMS} | _baselines(dev)
    return {
        "confirmatory": False,
        "n_meals": int(truth.size),
        "n_patients": int(pd.unique(pid).size),
        "prevalence": float(truth.mean()),
        "n_meals_without_a_personal_rate": int(dev["h_share"].isna().sum()),
        "arms": {a: {**metrics(truth, p), **within_patient_auroc(pid, truth, p)} for a, p in preds.items()},
        "diffs": {
            b: boot_diff(pid, truth, preds["fused"], preds[b], n_boot) for b in (*SINGLE, BASELINE, SMOOTHED)
        },
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


def _without_a_bar(result: dict) -> dict:
    """A secondary analysis reuses `evaluate`, but it has no bar: its verdict block must not be published."""
    return {k: v for k, v in result.items() if k != "verdict"}


def _subgroups(dev: pd.DataFrame, test: pd.DataFrame) -> dict:
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
    return {
        name: {
            "n_meals": int(m.sum()),
            "n_patients": int(test.loc[m, "patient_id"].nunique()),
            **metrics(test.loc[m, "y"], p[m.to_numpy()]),
        }
        for name, m in groups.items()
        if m.any()
    }


def _minutes(test: pd.DataFrame) -> dict:
    mins = test["mins_to_high"].dropna()
    return {"median": float(mins.median()) if len(mins) else None, "n_meals": int(len(mins))}


def _secondary(dev: pd.DataFrame, test: pd.DataFrame, n_boot: int) -> dict:
    """The pre-declared secondary analyses: 250 mg/dL, meals that start in range, timing, LightGBM, subgroups.

    An analysis whose development meals hold one outcome only cannot be fitted; it is left out, not faked.
    One that fails is recorded with its error and the others still run: the test split is scored once, so
    nothing here may take the run down.
    """
    low_dev, low_test = dev[dev["start_high"] == 0], test[test["start_high"] == 0]
    todo: dict[str, Callable[[], dict]] = {}
    if dev["y250"].nunique() == 2:
        # its personal rate and history features are still the 180 mg/dL ones
        todo["above_250"] = lambda: _without_a_bar(evaluate(dev, test, "y250", n_boot))
    if len(low_test) and low_dev["y"].nunique() == 2:
        todo["starts_at_or_below_180"] = lambda: _without_a_bar(evaluate(low_dev, low_test, "y", n_boot))
    todo["minutes_to_first_reading_above_180"] = lambda: _minutes(test)
    todo["lightgbm_fused"] = lambda: _lightgbm(dev, test)
    todo["subgroups_fused"] = lambda: _subgroups(dev, test)
    out = {}
    for name, run in todo.items():
        try:
            out[name] = run()
        except Exception as err:  # noqa: BLE001 - any failure becomes a published row, never a lost run
            out[name] = {"error": repr(err)}
    return out


def _secondary_lines(sec: dict) -> list[str]:
    lines = ["", "## Secondary (no bar)", ""]
    failed = {k: v["error"] for k, v in sec.items() if isinstance(v, dict) and "error" in v}
    if "error" in sec:
        return [*lines, f"The secondary analyses failed: `{sec['error']}`"]
    mins = sec.get("minutes_to_first_reading_above_180", {})
    if "median" in mins:
        lines.append(
            f"Median minutes from meal to the first reading above 180: {mins['median']} ({mins['n_meals']} meals)."
        )
    rows = {}
    if "lightgbm_fused" in sec and "lightgbm_fused" not in failed:
        rows["LightGBM, library defaults (fused)"] = sec["lightgbm_fused"]
    for name in ("above_250", "starts_at_or_below_180"):
        if name in sec and name not in failed:
            rows[f"{name}: fused"] = sec[name]["arms"]["fused"]
            rows[f"{name}: personal rate"] = sec[name]["arms"][BASELINE]
    if rows:
        lines += ["", pd.DataFrame(rows).T.round(3).to_markdown()]
    if "subgroups_fused" in sec and "subgroups_fused" not in failed:
        lines += ["", pd.DataFrame(sec["subgroups_fused"]).T.round(3).to_markdown()]
    lines += [f"\n`{name}` failed: `{err}`" for name, err in failed.items()]
    return lines


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
    lines += [
        "",
        "`personal_rate` is the registered baseline, the plain share of calibration-window meals with the event "
        f"({NO_RATE} for the {r['n_meals_without_a_personal_rate']} meals with no scorable calibration meal). "
        "`personal_rate_smoothed` is the add-one version the history arm uses; it carries no bar.",
    ]
    if "kept_without_sensor" in r:
        kept = r["kept_without_sensor"]
        lines += ["", f"Share of the sensor-on gain over prevalence kept without the sensor: {kept:.2f}"]
    if result.get("secondary"):
        lines += _secondary_lines(result["secondary"])
    if result.get("skipped"):
        lines += [
            "",
            "Recordings skipped (development and test together): "
            + "; ".join(f"{v} ({k})" for k, v in result["skipped"].items()),
        ]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def refuse_second_run(out_dir: Path) -> None:
    """The test split is scored once. A re-run after a defect is an amendment, made by hand, not by accident."""
    if (out_dir / "summary.json").exists():
        raise SystemExit(
            f"{out_dir} already holds the confirmatory run. Scoring the test patients again needs a dated "
            "amendment (docs/PREREGISTRATION.md); move the folder aside deliberately if that is what this is."
        )


def check_registered(k_days: float, n_boot: int, src_status: str | None) -> None:
    """The confirmatory run happens at the registered settings, on committed code, or not at all."""
    if k_days != REGISTERED_K or n_boot != REGISTERED_BOOT:
        raise SystemExit(
            f"the confirmatory run is registered at k = {REGISTERED_K:g} days and {REGISTERED_BOOT} resamples; "
            "remove --k and --boot"
        )
    if src_status is None:
        raise SystemExit(
            "git is not available, so the code that scores the test patients cannot be identified"
        )
    if src_status:
        raise SystemExit("uncommitted changes under src/: commit them before scoring the test patients")


def _provenance(out_dir: Path, k_days: float, n_boot: int, confirm: bool) -> None:
    status = _git("status", "--porcelain", "--", "src")
    prov = {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes_in_src": None if status is None else bool(status),
        "k_days": k_days,
        "boot": n_boot,
        "seed": SEED,
        "confirm": confirm,
    }
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")


def confirmatory_run(
    dev: pd.DataFrame, test: pd.DataFrame, skipped: dict, out_dir: Path, n_boot: int
) -> dict:
    """Score the test patients. The primary result is on disk before any secondary analysis starts.

    Once the primary result is written, `refuse_second_run` holds: a failure later in this function cannot
    lead to the test split being scored again by a simple re-run.
    """
    both = set(dev["patient_id"]) & set(test["patient_id"])
    assert not both, f"{len(both)} patients are in both the development and the test table"
    result = {"primary": evaluate(dev, test, "y", n_boot), "skipped": skipped}
    write_report(result, out_dir, confirmatory=True)
    try:
        result["secondary"] = _secondary(dev, test, n_boot)
    except Exception as err:  # noqa: BLE001 - the primary result stands whatever happens here
        result["secondary"] = {"error": repr(err)}
    write_report(result, out_dir, confirmatory=True)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test patients; this is done once")
    ap.add_argument("--k", type=float, default=REGISTERED_K)
    ap.add_argument("--boot", type=int, default=REGISTERED_BOOT)
    args = ap.parse_args()
    out_dir = RESULTS_DIR / "gate3" / ("shanghai" if args.confirm else "shanghai-dev")
    if args.confirm:
        check_registered(args.k, args.boot, _git("status", "--porcelain", "--", "src"))
        refuse_second_run(out_dir)
    from chhaya.data.shanghai import load_all

    table, skipped = build_table(load_all(), args.k)
    if table.empty:
        raise SystemExit(f"no eligible meal in any recording; skipped: {skipped}")
    dev = table[table["dev"]].reset_index(drop=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    _provenance(out_dir, args.k, args.boot, args.confirm)  # before any scoring, so it survives a failure
    if not args.confirm:
        del table  # no test patient's row is used below this line
        result = {"primary": development_run(dev, n_boot=args.boot), "skipped": skipped}
        write_report(result, out_dir, confirmatory=False)
    else:
        test = table[~table["dev"]].reset_index(drop=True)
        confirmatory_run(dev, test, skipped, out_dir, args.boot)
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
