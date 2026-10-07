# Gate 3: post-meal excursion above 180 mg/dL, predicted at meal time

Verdict: **NOT PASSED** (bars M1 and M2, Amendment 3)

```json
{
  "m1_fused_beats_every_single_stream": false,
  "m2_fused_beats_personal_rate": false,
  "m3_calibration_slope_in_range": false,
  "pass": false
}
```

Meals 1205, patients 47, share with the event 0.392.

|                        |   auprc |   auroc |   brier |   calibration_slope |   calibration_intercept |   within_patient_auroc |   within_patient_n |
|:-----------------------|--------:|--------:|--------:|--------------------:|------------------------:|-----------------------:|-------------------:|
| record                 |   0.566 |   0.646 |   0.238 |               0.525 |                  -0.349 |                  0.622 |                 20 |
| history                |   0.626 |   0.777 |   0.19  |               0.857 |                  -0.069 |                  0.623 |                 20 |
| fingersticks           |   0.642 |   0.703 |   0.205 |               0.999 |                   0.062 |                  0.568 |                 20 |
| fused                  |   0.596 |   0.713 |   0.216 |               0.482 |                  -0.338 |                  0.622 |                 20 |
| sensor_on              |   0.76  |   0.816 |   0.17  |               0.773 |                  -0.323 |                  0.78  |                 20 |
| personal_rate          |   0.587 |   0.756 |   0.224 |               0.119 |                  -0.507 |                  0.512 |                 20 |
| personal_rate_smoothed |   0.611 |   0.758 |   0.212 |               0.767 |                  -0.642 |                  0.512 |                 20 |

AUPRC of the fused sensor-off model minus each comparator (95 % interval over patients):

|                        |   diff |     lo |    hi |   n_resamples_used |
|:-----------------------|-------:|-------:|------:|-------------------:|
| record                 |  0.03  | -0.069 | 0.155 |               2000 |
| history                | -0.03  | -0.095 | 0.052 |               2000 |
| fingersticks           | -0.046 | -0.119 | 0.072 |               2000 |
| personal_rate          |  0.009 | -0.089 | 0.141 |               2000 |
| personal_rate_smoothed | -0.014 | -0.11  | 0.132 |               2000 |

`personal_rate` is the registered baseline, the plain share of calibration-window meals with the event (0.5 for the 0 meals with no scorable calibration meal). `personal_rate_smoothed` is the add-one version the history arm uses; it carries no bar.

Share of the sensor-on gain over prevalence kept without the sensor: 0.55

## Secondary (no bar)

Median minutes from meal to the first reading above 180: 30.0 (472 meals).

|                                       |   auprc |   auroc |   brier |   calibration_slope |   calibration_intercept |   within_patient_auroc |   within_patient_n |
|:--------------------------------------|--------:|--------:|--------:|--------------------:|------------------------:|-----------------------:|-------------------:|
| LightGBM, library defaults (fused)    |   0.623 |   0.761 |   0.211 |               0.473 |                  -0.095 |                  0.566 |                 20 |
| above_250: fused                      |   0.153 |   0.636 |   0.126 |               0.19  |                  -1.698 |                  0.639 |                  7 |
| above_250: personal rate              |   0.204 |   0.769 |   0.329 |               0.102 |                  -2.393 |                  0.528 |                  7 |
| starts_at_or_below_180: fused         |   0.493 |   0.689 |   0.209 |               0.401 |                  -0.603 |                  0.644 |                 20 |
| starts_at_or_below_180: personal rate |   0.482 |   0.743 |   0.239 |               0.102 |                  -0.852 |                  0.512 |                 20 |

|                |   n_meals |   n_patients |   auprc |   auroc |   brier |   calibration_slope |   calibration_intercept |
|:---------------|----------:|-------------:|--------:|--------:|--------:|--------------------:|------------------------:|
| on_insulin     |       676 |           28 |   0.613 |   0.739 |   0.219 |               0.51  |                  -0.504 |
| not_on_insulin |       529 |           20 |   0.606 |   0.691 |   0.213 |               0.563 |                  -0.069 |
| pump           |       214 |           19 |   0.705 |   0.727 |   0.25  |               0.681 |                  -0.767 |
| no_pump        |       991 |           28 |   0.587 |   0.706 |   0.209 |               0.483 |                  -0.283 |
| male           |       738 |           30 |   0.641 |   0.75  |   0.209 |               0.575 |                  -0.385 |
| female         |       467 |           17 |   0.478 |   0.613 |   0.227 |               0.325 |                  -0.421 |
| age_65_or_more |       559 |           19 |   0.703 |   0.717 |   0.219 |               0.55  |                   0.039 |
| under_65       |       646 |           28 |   0.531 |   0.723 |   0.215 |               0.463 |                  -0.661 |

Recordings skipped (development and test together): 4 (too short to hold out a day after calibration)
