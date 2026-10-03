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
|        3 |           20 |          0 |      24.464 |     27.156 |      24.604 |        -3.332 |              1     |            0 |      15.227 |          5.231 |         4.487 |   0.863 |       38.613 |
|        5 |           20 |          0 |      22.543 |     24.248 |      24.152 |        -1.484 |              0.9   |            0 |      14.557 |          4.713 |         3.399 |   0.832 |       38.815 |
|        7 |           19 |          0 |      21.89  |     23.928 |      24.075 |        -1.181 |              0.895 |            0 |      13.278 |          2.034 |         4.691 |   0.888 |       37.779 |
