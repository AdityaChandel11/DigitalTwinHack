# Gate 2 — sensor-off twin vs the patient's own average day

Verdict at k=5 days: **NO-GO**

```json
{
  "p1_beats_average_day": false,
  "p2_tir_within_bar": true,
  "p3_band_calibrated": true,
  "go": false
}
```

|   k_days |   n_patients |   n_failed |   twin_rmse |   day_rmse |   mean_rmse |   median_diff |   frac_twin_better |   wilcoxon_p |   twin_mard |   twin_tir_err |   day_tir_err |   cov80 |   floor_rmse |
|---------:|-------------:|-----------:|------------:|-----------:|------------:|--------------:|-------------------:|-------------:|------------:|---------------:|--------------:|--------:|-------------:|
|        3 |           45 |          0 |      22.875 |     25.772 |      23.729 |        -1.46  |              0.733 |        0.001 |      14.91  |          6.657 |         5.43  |   0.882 |       39.374 |
|        5 |           45 |          0 |      23.088 |     23.095 |      23.265 |         0.3   |              0.489 |        0.783 |      15.649 |          4.959 |         4.268 |   0.876 |       39.543 |
|        7 |           44 |          0 |      22.203 |     21.996 |      22.612 |         0.763 |              0.409 |        0.971 |      14.275 |          3.267 |         4.534 |   0.895 |       38.885 |
