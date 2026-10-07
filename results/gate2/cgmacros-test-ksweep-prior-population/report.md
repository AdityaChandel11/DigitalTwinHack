# Gate 2 — sensor-off twin vs the patient's own average day

Verdict at k=5 days: **GO** (not confirmatory: only a full run on the held-out test split supports a claim)

```json
{
  "p1_beats_average_day": true,
  "p2_tir_within_bar": true,
  "p3_band_calibrated": true,
  "few_failed_fits": true,
  "go": true,
  "primary_k_run": true,
  "confirmatory": false
}
```

|   k_days |   n_patients |   n_failed |   n_skipped |   frac_failed |   twin_rmse |   day_rmse |   mean_rmse |   median_diff |   frac_twin_better |   wilcoxon_p |   twin_mard |   twin_tir_err |   day_tir_err |   cov80 |   cov80_min |   cov80_max |   shrunk_rmse |   median_diff_vs_shrunk |   frac_better_vs_shrunk |   p_vs_shrunk |   floor_rmse |
|---------:|-------------:|-----------:|------------:|--------------:|------------:|-----------:|------------:|--------------:|-------------------:|-------------:|------------:|---------------:|--------------:|--------:|------------:|------------:|--------------:|------------------------:|------------------------:|--------------:|-------------:|
|        1 |           20 |          0 |           0 |             0 |      30.795 |     33.165 |      27.9   |        -3.27  |              0.95  |      2.4e-05 |      19.301 |          3.737 |         9.496 |   0.821 |       0.487 |       0.991 |        28.754 |                  -0.232 |                   0.55  |       0.39    |       37.339 |
|        3 |           19 |          0 |           1 |             0 |      23.793 |     27.589 |      23.412 |        -3.284 |              1     |      1.9e-06 |      14.859 |          6.065 |         3.698 |   0.86  |       0.709 |       0.995 |        23.984 |                  -0.452 |                   0.579 |       0.072   |       36.111 |
|        5 |           19 |          0 |           1 |             0 |      21.669 |     23.306 |      24.471 |        -1.4   |              0.895 |      3.6e-05 |      14.156 |          5.96  |         3.512 |   0.838 |       0.601 |       0.987 |        22.309 |                  -0.346 |                   0.632 |       0.033   |       35.134 |
|        7 |           18 |          0 |           2 |             0 |      22.005 |     22.144 |      23.22  |        -1.15  |              0.889 |      0.00013 |      13.233 |          2.104 |         3.479 |   0.889 |       0.72  |       1     |        21.664 |                  -0.641 |                   0.778 |       0.00079 |       32.049 |
