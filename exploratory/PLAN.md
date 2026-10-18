# Exploratory Plan: Fusion Alternatives for Post-Meal Excursions (Development Patients Only)

*Label: exploratory, development patients only, not confirmed.*

## 1. Context and Objective
Gate 3 (post-meal excursions on ShanghaiT2DM) missed M1 (fused must beat each single stream), M2 (fused must beat the personal rate), and M3 (calibration slope between 0.8 and 1.2) on held-out patients. Those are published results scored once and remain as they are.

This exploratory task addresses one narrow question on development patients only:
**Would an obvious alternative to naive feature concatenation have helped?**
"No" is an informative and valid answer.

## 2. Hard Limits
1. Use only patients for which `chhaya.config.is_dev_patient(pid)` is True. Assert this on every dataset and meal.
2. Never run any command with `--confirm`. Never write anything to `results/`. Write only to `exploratory/`.
3. Do not open anything under `results/` except `results/gate3/shanghai/summary.json` (aggregate numbers only). Never open per-patient or per-meal files.
4. Do not look at held-out patients or held-out metrics to choose features, models, thresholds, or seeds.
5. Do not modify `src/` or `tests/`. Import and reuse feature builders and arms from `chhaya.eval.gate3`.
6. No new dependencies; use only locked dependencies (`scikit-learn`, `lightgbm`).
7. At most 4 pre-specified candidates. No fifth candidate, and no modification of candidate definitions after observing results.

## 3. Candidates
- **C1 Late fusion, equal weights**: Average the out-of-fold predicted probabilities of the three single-stream arms (`record` only, sensor `history` only, and `fingersticks` only):
  $$\hat{p}_{\text{C1}} = \frac{1}{3} (\hat{p}_{\text{record}} + \hat{p}_{\text{history}} + \hat{p}_{\text{fingersticks}})$$
- **C2 Stacked late fusion**: Logistic regression fitted on the logits of the three single-stream arms, trained using nested patient-grouped cross-validation to prevent leakage.
- **C3 Recalibration of the existing fused arm**: Platt scaling fitted on nested out-of-fold scores of the fused arm. Report calibration slope and Brier score before and after recalibration. Note explicitly that any monotone transformation preserves ranking and therefore does not change AUPRC or AUROC.
- **C4 Stronger regularisation of the existing fused arm**: Inverse regularisation parameter $C$ selected via nested patient-grouped cross-validation from the grid $\{0.01, 0.03, 0.1, 0.3, 1\}$.

## 4. Evaluation Protocol
- **Dataset**: ShanghaiT2DM development cohort meals after the 3-day calibration split ($k = 3.0$ days), exactly as built by `chhaya.eval.gate3.build_table`.
- **Folds**: Patient-grouped 5-fold cross-validation (`GroupKFold(n_splits=5, shuffle=True, random_state=seed)`), repeated across 5 fixed seeds ($20261002, 20261003, 20261004, 20261005, 20261006$).
- **Comparators**: Evaluated on the exact same folds:
  - Each single-stream arm: `record`, `history`, `fingersticks`.
  - The existing `fused` arm.
  - The `personal_rate` baseline.
- **Metrics**: AUPRC, AUROC, and calibration slope, pooled out-of-fold.
- **Uncertainty**: Patient-level bootstrap with 2000 resamples (`n_boot = 2000`).
- **Primary Comparison**: Paired difference in AUPRC against the best-performing single-stream arm on development patients, along with its 95% bootstrap percentile interval.

## 5. Fixed Decision Rule
A candidate "helps" if and only if:
1. The lower end of its 95% bootstrap interval of paired AUPRC difference versus the best development single-stream arm is strictly above 0 in the pooled run; **AND**
2. The paired point estimate difference is strictly positive in at least 4 of the 5 seeds.

Otherwise, the verdict is **"no gain"**. All four candidates will be reported in this exact order.
