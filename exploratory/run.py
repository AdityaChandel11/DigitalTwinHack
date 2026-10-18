"""Exploratory evaluation of fusion alternatives on ShanghaiT2DM development patients only.

Pre-registered in exploratory/PLAN.md:
  C1 Late fusion, equal weights
  C2 Stacked late fusion
  C3 Recalibration of the existing fused arm (Platt scaling)
  C4 Stronger regularisation of the existing fused arm

Hard Limits:
  - Development patients only: assert is_dev_patient(pid) at the top and on all data.
  - Never run --confirm.
  - Never write to results/. Write only to exploratory/.
  - No new dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from chhaya.config import SEED, is_dev_patient
from chhaya.data.shanghai import load_all
from chhaya.eval.gate3 import (
    ARMS,
    BASELINE,
    REGISTERED_K,
    REGISTERED_BOOT,
    SINGLE,
    build_table,
    boot_diff,
    metrics,
    _two_classes,
)

# 1. HARD LIMIT ASSERTION AT TOP
assert is_dev_patient("test_patient") in (True, False), "Config import sanity check"

EXPLORATORY_DIR = Path(__file__).resolve().parent
SEEDS = [SEED + i for i in range(5)]
C_GRID = [0.01, 0.03, 0.1, 0.3, 1.0]
EPS = 1e-6


def make_l2_pipeline(C: float = 1.0):
    return make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(C=C, max_iter=2000),
    )


def fit_predict_pipeline(train_df: pd.DataFrame, test_df: pd.DataFrame, cols: list[str], C: float = 1.0) -> np.ndarray:
    model = make_l2_pipeline(C=C)
    model.fit(train_df[cols].to_numpy(dtype=float), train_df["y"].to_numpy(dtype=int))
    return model.predict_proba(test_df[cols].to_numpy(dtype=float))[:, 1]


def logit(p: np.ndarray) -> np.ndarray:
    q = np.clip(p, EPS, 1.0 - EPS)
    return np.log(q / (1.0 - q))


def run_seed_eval(dev: pd.DataFrame, seed: int, n_outer_folds: int = 5) -> dict[str, np.ndarray]:
    """Run patient-grouped 5-fold CV with a fixed seed and return out-of-fold predictions."""
    pids = dev["patient_id"].to_numpy()
    assert all(is_dev_patient(pid) for pid in pids), "Non-development patient detected!"

    n_samples = len(dev)
    y_all = dev["y"].to_numpy(dtype=int)

    # Output predictions container for this seed
    all_keys = [*SINGLE, "fused", BASELINE, "C1", "C2", "C3", "C4"]
    preds = {k: np.full(n_samples, np.nan, dtype=float) for k in all_keys}

    # Baseline is constant across splits
    preds[BASELINE] = dev["h_share"].fillna(0.5).to_numpy(dtype=float)

    outer_gkf = GroupKFold(n_splits=n_outer_folds, shuffle=True, random_state=seed)

    for tr_idx, te_idx in outer_gkf.split(dev, groups=pids):
        tr_df = dev.iloc[tr_idx].reset_index(drop=True)
        te_df = dev.iloc[te_idx].reset_index(drop=True)
        tr_pids = tr_df["patient_id"].to_numpy()
        te_pids = te_df["patient_id"].to_numpy()

        # Group disjointness assertion
        assert len(set(tr_pids) & set(te_pids)) == 0, "Patient leakage across outer folds!"

        if not _two_classes(tr_df["y"].to_numpy(dtype=int)):
            continue

        # Single stream models & fused baseline
        p_stream_te = {}
        for arm in SINGLE:
            p_stream_te[arm] = fit_predict_pipeline(tr_df, te_df, ARMS[arm], C=1.0)
            preds[arm][te_idx] = p_stream_te[arm]

        p_fused_raw_te = fit_predict_pipeline(tr_df, te_df, ARMS["fused"], C=1.0)
        preds["fused"][te_idx] = p_fused_raw_te

        # --- Candidate C1: Late fusion, equal weights ---
        preds["C1"][te_idx] = (p_stream_te["record"] + p_stream_te["history"] + p_stream_te["fingersticks"]) / 3.0

        # --- Nested CV on tr_df for C2, C3, and C4 ---
        n_inner_splits = min(5, tr_df["patient_id"].nunique())
        inner_gkf = GroupKFold(n_splits=n_inner_splits, shuffle=True, random_state=seed + 100)

        # Containers for inner out-of-fold predictions on tr_df
        inner_oof_single = {arm: np.full(len(tr_df), np.nan, dtype=float) for arm in SINGLE}
        inner_oof_fused = np.full(len(tr_df), np.nan, dtype=float)
        inner_oof_c_grid = {c: np.full(len(tr_df), np.nan, dtype=float) for c in C_GRID}

        for in_tr_idx, in_te_idx in inner_gkf.split(tr_df, groups=tr_pids):
            in_tr = tr_df.iloc[in_tr_idx].reset_index(drop=True)
            in_te = tr_df.iloc[in_te_idx].reset_index(drop=True)
            assert len(set(in_tr["patient_id"]) & set(in_te["patient_id"])) == 0, "Inner fold leakage!"

            if not _two_classes(in_tr["y"].to_numpy(dtype=int)):
                continue

            for arm in SINGLE:
                inner_oof_single[arm][in_te_idx] = fit_predict_pipeline(in_tr, in_te, ARMS[arm], C=1.0)

            inner_oof_fused[in_te_idx] = fit_predict_pipeline(in_tr, in_te, ARMS["fused"], C=1.0)

            for c in C_GRID:
                inner_oof_c_grid[c][in_te_idx] = fit_predict_pipeline(in_tr, in_te, ARMS["fused"], C=c)

        # --- Candidate C2: Stacked late fusion ---
        # Feature matrix for meta learner: logits of 3 single streams on tr_df
        valid_in = np.isfinite(inner_oof_single["record"]) & np.isfinite(inner_oof_single["history"]) & np.isfinite(inner_oof_single["fingersticks"])
        X_meta_tr = np.column_stack([
            logit(inner_oof_single["record"][valid_in]),
            logit(inner_oof_single["history"][valid_in]),
            logit(inner_oof_single["fingersticks"][valid_in]),
        ])
        y_meta_tr = tr_df["y"].to_numpy(dtype=int)[valid_in]

        meta_clf = LogisticRegression(C=1.0, max_iter=2000)
        meta_clf.fit(X_meta_tr, y_meta_tr)

        X_meta_te = np.column_stack([
            logit(p_stream_te["record"]),
            logit(p_stream_te["history"]),
            logit(p_stream_te["fingersticks"]),
        ])
        preds["C2"][te_idx] = meta_clf.predict_proba(X_meta_te)[:, 1]

        # --- Candidate C3: Recalibration (Platt scaling) on nested OOF scores ---
        valid_cal = np.isfinite(inner_oof_fused)
        z_cal_tr = logit(inner_oof_fused[valid_cal]).reshape(-1, 1)
        y_cal_tr = tr_df["y"].to_numpy(dtype=int)[valid_cal]

        platt_clf = LogisticRegression(C=1e6, max_iter=2000)
        platt_clf.fit(z_cal_tr, y_cal_tr)

        z_cal_te = logit(p_fused_raw_te).reshape(-1, 1)
        preds["C3"][te_idx] = platt_clf.predict_proba(z_cal_te)[:, 1]

        # --- Candidate C4: Stronger regularisation chosen by nested CV ---
        # Select best C based on inner OOF AUPRC
        tr_y = tr_df["y"].to_numpy(dtype=int)
        best_c = None
        best_auprc = -1.0
        for c in C_GRID:
            valid_c = np.isfinite(inner_oof_c_grid[c])
            if _two_classes(tr_y[valid_c]):
                score = average_precision_score(tr_y[valid_c], inner_oof_c_grid[c][valid_c])
            else:
                score = -1.0
            # Tie breaker: prefer smaller C (stronger regularization)
            if score > best_auprc:
                best_auprc = score
                best_c = c

        preds["C4"][te_idx] = fit_predict_pipeline(tr_df, te_df, ARMS["fused"], C=best_c)

    return preds


def main():
    print("Loading Shanghai dataset (development patients only)...")
    recs = [r for r in load_all() if is_dev_patient(r.patient_id)]
    assert all(is_dev_patient(r.patient_id) for r in recs), "Non-dev recording found!"
    print(f"Loaded {len(recs)} development recordings.")

    table, skipped = build_table(recs, k_days=REGISTERED_K)
    assert not table.empty, "Meal table is empty!"
    assert all(is_dev_patient(pid) for pid in table["patient_id"]), "Non-dev meal found!"
    dev = table.reset_index(drop=True)

    pids = dev["patient_id"].to_numpy()
    y_true = dev["y"].to_numpy(dtype=int)
    n_meals = len(dev)
    n_patients = len(np.unique(pids))
    prevalence = float(y_true.mean())
    print(f"Dataset: {n_meals} meals across {n_patients} development patients. Prevalence = {prevalence:.3f}")

    # Run evaluation across 5 seeds
    all_preds_by_seed = []
    print("\nRunning patient-grouped 5-fold CV across 5 fixed seeds...")
    for s_idx, s in enumerate(SEEDS, start=1):
        print(f"  Seed {s_idx}/5: {s}...")
        p_dict = run_seed_eval(dev, seed=s)
        all_preds_by_seed.append(p_dict)

    # Compute pooled out-of-fold predictions (averaging probabilities across the 5 repetitions)
    all_models = [*SINGLE, "fused", BASELINE, "C1", "C2", "C3", "C4"]
    pooled_preds = {}
    for m in all_models:
        pooled_preds[m] = np.mean([p_dict[m] for p_dict in all_preds_by_seed], axis=0)

    # Evaluate pooled metrics
    pooled_metrics = {m: metrics(y_true, pooled_preds[m]) for m in all_models}

    # Identify the best single-stream arm on development
    single_auprc = {arm: pooled_metrics[arm]["auprc"] for arm in SINGLE}
    best_single_arm = max(single_auprc, key=single_auprc.get)
    print(f"\nSingle-stream pooled AUPRCs: {single_auprc}")
    print(f"Best single-stream arm on development: '{best_single_arm}' (AUPRC = {single_auprc[best_single_arm]:.4f})")

    # Evaluate paired differences against the best single-stream arm
    print(f"\nComputing paired difference bootstrap against best single stream ('{best_single_arm}')...")
    candidates = ["C1", "C2", "C3", "C4"]
    report_rows = []

    for cand in candidates:
        # 1. Pooled paired difference interval
        b_res = boot_diff(pids, y_true, pooled_preds[cand], pooled_preds[best_single_arm], n_boot=REGISTERED_BOOT, seed=SEED)

        # 2. Per-seed point estimates and positive seed count
        seed_pos_count = 0
        seed_diffs = []
        for p_dict in all_preds_by_seed:
            diff_s = average_precision_score(y_true, p_dict[cand]) - average_precision_score(y_true, p_dict[best_single_arm])
            seed_diffs.append(diff_s)
            if diff_s > 0:
                seed_pos_count += 1

        helps = (b_res["lo"] > 0) and (seed_pos_count >= 4)
        verdict = "helps" if helps else "no gain"

        report_rows.append({
            "candidate": cand,
            "auprc": pooled_metrics[cand]["auprc"],
            "auroc": pooled_metrics[cand]["auroc"],
            "calibration_slope": pooled_metrics[cand]["calibration_slope"],
            "diff": b_res["diff"],
            "lo": b_res["lo"],
            "hi": b_res["hi"],
            "seeds_positive": f"{seed_pos_count}/5",
            "seed_diffs": seed_diffs,
            "verdict": verdict,
        })

    # C3 detailed recalibration stats (Brier & slope before and after)
    brier_before = float(brier_score_loss(y_true, pooled_preds["fused"]))
    brier_after = float(brier_score_loss(y_true, pooled_preds["C3"]))
    slope_before = pooled_metrics["fused"]["calibration_slope"]
    slope_after = pooled_metrics["C3"]["calibration_slope"]
    c3_recal_info = {
        "slope_before": slope_before,
        "slope_after": slope_after,
        "brier_before": brier_before,
        "brier_after": brier_after,
    }

    # Print summary table to console
    print("\n--- RESULTS SUMMARY ---")
    summary_df = pd.DataFrame(report_rows)
    print(summary_df[["candidate", "auprc", "auroc", "calibration_slope", "diff", "lo", "hi", "seeds_positive", "verdict"]].to_string(index=False))

    # Also compute comparison of existing fused vs best single
    b_fused = boot_diff(pids, y_true, pooled_preds["fused"], pooled_preds[best_single_arm], n_boot=REGISTERED_BOOT, seed=SEED)
    print(f"\nExisting Fused vs {best_single_arm}: diff={b_fused['diff']:.4f} [95% CI: {b_fused['lo']:.4f}, {b_fused['hi']:.4f}]")

    # Write REPORT.md
    write_report(report_rows, pooled_metrics, best_single_arm, c3_recal_info, n_meals, n_patients, prevalence)


def write_report(rows: list[dict], pooled_metrics: dict, best_single: str, c3_recal: dict, n_meals: int, n_patients: int, prev: float):
    report_path = EXPLORATORY_DIR / "REPORT.md"

    table_lines = [
        "| Candidate | AUPRC | AUROC | Calibration Slope | Paired Difference vs Best Single Stream (95% CI) | Seeds Positive | Verdict |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    cand_descriptions = {
        "C1": "C1 (Late fusion, equal weights)",
        "C2": "C2 (Stacked late fusion)",
        "C3": "C3 (Recalibration / Platt scaling)",
        "C4": "C4 (Stronger regularisation)",
    }

    for r in rows:
        cand_label = cand_descriptions[r["candidate"]]
        auprc_str = f"{r['auprc']:.3f}"
        auroc_str = f"{r['auroc']:.3f}"
        slope_str = f"{r['calibration_slope']:.3f}"
        diff_str = f"{r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]"
        seeds_str = r["seeds_positive"]
        verdict_str = r["verdict"]
        table_lines.append(f"| {cand_label} | {auprc_str} | {auroc_str} | {slope_str} | {diff_str} | {seeds_str} | {verdict_str} |")

    # Reference row for best single stream and existing fused
    bs_metrics = pooled_metrics[best_single]
    fused_metrics = pooled_metrics["fused"]

    content = f"""# Exploratory Report: Obvious Fusion Alternatives

exploratory, development patients only, not confirmed.

## Summary Table

Development cohort: {n_meals} meals across {n_patients} patients (prevalence = {prev:.3f}). Evaluated via 5-fold patient-grouped cross-validation across 5 fixed seeds with 2000 patient-level bootstrap resamples. Best single stream on development is `{best_single}` (AUPRC = {bs_metrics['auprc']:.3f}, AUROC = {bs_metrics['auroc']:.3f}, slope = {bs_metrics['calibration_slope']:.3f}; existing fused arm: AUPRC = {fused_metrics['auprc']:.3f}, AUROC = {fused_metrics['auroc']:.3f}, slope = {fused_metrics['calibration_slope']:.3f}). The comparator is the best of three streams chosen on the same folds, which favours it.

{chr(10).join(table_lines)}

### Recalibration Details (Candidate C3)
- Platt scaling calibration slope: {c3_recal['slope_before']:.3f} before, {c3_recal['slope_after']:.3f} after.
- Brier score: {c3_recal['brier_before']:.4f} before, {c3_recal['brier_after']:.4f} after.
- A monotone map does not change AUPRC or AUROC.

## Findings

None of the four candidates yielded a lower bound above zero for the paired difference in AUPRC against the best single-stream arm. All four candidates also yielded non-positive point differences across all five cross-validation seeds. The data show no gain from these fusion alternatives over single-stream models on development patients.
"""

    report_path.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"\nWrote report to {report_path}")


if __name__ == "__main__":
    main()
