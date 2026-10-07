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
|        1 |           20 |          0 |           0 |             0 |      30.318 |     33.165 |      27.9   |        -3.634 |              0.9   |      0.0006  |      19.339 |          5.127 |         9.496 |   0.826 |       0.491 |       0.97  |        28.754 |                  -0.338 |                   0.6   |       0.41    |       37.339 |
|        3 |           19 |          0 |           1 |             0 |      23.802 |     27.589 |      23.412 |        -3.284 |              1     |      1.9e-06 |      14.856 |          6.065 |         3.698 |   0.857 |       0.708 |       0.982 |        23.984 |                  -0.478 |                   0.579 |       0.057   |       36.111 |
|        5 |           19 |          0 |           1 |             0 |      21.945 |     23.306 |      24.471 |        -1.36  |              0.895 |      3.6e-05 |      14.158 |          5.96  |         3.512 |   0.835 |       0.6   |       0.985 |        22.309 |                  -0.347 |                   0.632 |       0.036   |       35.134 |
|        7 |           18 |          0 |           2 |             0 |      22.008 |     22.144 |      23.22  |        -1.161 |              0.889 |      0.00013 |      13.241 |          2.104 |         3.479 |   0.888 |       0.715 |       1     |        21.664 |                  -0.572 |                   0.778 |       0.00097 |       32.049 |
