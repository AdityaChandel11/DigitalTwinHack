# Gate 3: post-meal excursion above 180 mg/dL, predicted at meal time

Development patients, cross-validated. Not confirmatory: no verdict.

Meals 1436, patients 49, share with the event 0.364.

|                        |   auprc |   auroc |   brier |   calibration_slope |   calibration_intercept |   within_patient_auroc |   within_patient_n |
|:-----------------------|--------:|--------:|--------:|--------------------:|------------------------:|-----------------------:|-------------------:|
| record                 |   0.495 |   0.645 |   0.24  |               0.312 |                  -0.374 |                  0.63  |                 31 |
| history                |   0.644 |   0.753 |   0.188 |               0.853 |                  -0.038 |                  0.675 |                 31 |
| fingersticks           |   0.534 |   0.632 |   0.217 |               0.719 |                  -0.142 |                  0.59  |                 31 |
| fused                  |   0.618 |   0.73  |   0.205 |               0.473 |                  -0.335 |                  0.669 |                 31 |
| sensor_on              |   0.717 |   0.798 |   0.176 |               0.597 |                  -0.265 |                  0.739 |                 31 |
| personal_rate          |   0.577 |   0.711 |   0.232 |               0.18  |                  -0.651 |                  0.503 |                 31 |
| personal_rate_smoothed |   0.575 |   0.711 |   0.221 |               0.66  |                  -0.586 |                  0.503 |                 31 |

AUPRC of the fused sensor-off model minus each comparator (95 % interval over patients):

|                        |   diff |     lo |    hi |   n_resamples_used |
|:-----------------------|-------:|-------:|------:|-------------------:|
| record                 |  0.123 |  0.022 | 0.191 |               2000 |
| history                | -0.025 | -0.07  | 0.015 |               2000 |
| fingersticks           |  0.084 |  0.013 | 0.158 |               2000 |
| personal_rate          |  0.042 | -0.011 | 0.116 |               2000 |
| personal_rate_smoothed |  0.043 | -0.01  | 0.117 |               2000 |

`personal_rate` is the registered baseline, the plain share of calibration-window meals with the event (0.5 for the 0 meals with no scorable calibration meal). `personal_rate_smoothed` is the add-one version the history arm uses; it carries no bar.

Recordings skipped (development and test together): 4 (too short to hold out a day after calibration)
