# Gate 2 — sensor-off twin vs the patient's own average day

Verdict at k=5 days: **GO**

```json
{
  "p1_beats_average_day": true,
  "p2_tir_within_bar": true,
  "p3_band_calibrated": true,
  "go": true
}
```

|   k_days |   n_patients |   n_failed |   twin_rmse |   day_rmse |   mean_rmse |   median_diff |   frac_twin_better |   wilcoxon_p |   twin_mard |   twin_tir_err |   day_tir_err |   cov80 |   floor_rmse |
|---------:|-------------:|-----------:|------------:|-----------:|------------:|--------------:|-------------------:|-------------:|------------:|---------------:|--------------:|--------:|-------------:|
|        3 |           25 |          0 |      20.203 |     23.897 |      23.729 |        -1.887 |               0.96 |            0 |      14.052 |          5.644 |         7.783 |   0.858 |       42.415 |
|        5 |           25 |          0 |      18.542 |     22.108 |      23.265 |        -1.312 |               0.88 |            0 |      13.101 |          5.556 |         5.342 |   0.872 |       42.977 |
|        7 |           25 |          0 |      19.36  |     21.481 |      21.987 |        -0.98  |               0.84 |            0 |      13.042 |          5.724 |         4.377 |   0.876 |       43.379 |
