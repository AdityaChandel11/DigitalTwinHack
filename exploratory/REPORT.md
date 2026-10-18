# Exploratory Report: Obvious Fusion Alternatives

exploratory, development patients only, not confirmed.

## Summary Table

Development cohort: 1436 meals across 49 patients (prevalence = 0.364). Evaluated via 5-fold patient-grouped cross-validation across 5 fixed seeds with 2000 patient-level bootstrap resamples. Best single stream on development is `history` (AUPRC = 0.653, AUROC = 0.753, slope = 0.893; existing fused arm: AUPRC = 0.620, AUROC = 0.736, slope = 0.587). The comparator is the best of three streams chosen on the same folds, which favours it.

| Candidate | AUPRC | AUROC | Calibration Slope | Paired Difference vs Best Single Stream (95% CI) | Seeds Positive | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| C1 (Late fusion, equal weights) | 0.604 | 0.723 | 1.235 | -0.048 [-0.100, +0.004] | 0/5 | no gain |
| C2 (Stacked late fusion) | 0.648 | 0.750 | 1.037 | -0.005 [-0.018, +0.006] | 0/5 | no gain |
| C3 (Recalibration / Platt scaling) | 0.583 | 0.721 | 1.598 | -0.069 [-0.145, +0.015] | 0/5 | no gain |
| C4 (Stronger regularisation) | 0.621 | 0.739 | 0.870 | -0.032 [-0.102, +0.025] | 0/5 | no gain |

### Recalibration Details (Candidate C3)
- Platt scaling calibration slope: 0.587 before, 1.598 after.
- Brier score: 0.2015 before, 0.2035 after.
- A monotone map does not change AUPRC or AUROC.

## Findings

None of the four candidates yielded a lower bound above zero for the paired difference in AUPRC against the best single-stream arm. All four candidates also yielded non-positive point differences across all five cross-validation seeds. The data show no gain from these fusion alternatives over single-stream models on development patients.
