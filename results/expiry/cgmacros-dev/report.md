# Expiry by day: CGMacros

The twin (`twin`), its control with no meals (`control`) and the raw average day, by day since the sensor.

Development patients. Not confirmatory.

## k = 3 days

25 patients, 25 recordings.

|   day |   n_patients |   share_of_cohort |   twin_rmse |   control_rmse |   avgday_rmse |   cov80 |   abs_dmean |   share_moved |
|------:|-------------:|------------------:|------------:|---------------:|--------------:|--------:|------------:|--------------:|
|     0 |           25 |              1    |      nan    |         nan    |        nan    |  nan    |        7.72 |          0.05 |
|     1 |           25 |              1    |       22.65 |          25.72 |         25.68 |    0.91 |        4.95 |          0.08 |
|     2 |           25 |              1    |       16.5  |          18.07 |         21.69 |    0.91 |        4.21 |          0.08 |
|     3 |           25 |              1    |       19.38 |          19.47 |         20.91 |    0.9  |        9.13 |          0.08 |
|     4 |           24 |              0.96 |       20    |          22.08 |         23.07 |    0.9  |        7.92 |          0.12 |
|     5 |           24 |              0.96 |       16.54 |          18.87 |         19.42 |    0.95 |        4.78 |          0.08 |
|     6 |           24 |              0.96 |       17.33 |          19.85 |         19.38 |    0.91 |        5.86 |          0.12 |
|     7 |           23 |              0.92 |       18.2  |          18.8  |         20.45 |    0.93 |        4.7  |          0.04 |
|     8 |           12 |              0.48 |       26.13 |          25.2  |         26.97 |    0.77 |        5.95 |          0.08 |
|     9 |            6 |              0.24 |       27.37 |          25.35 |         27.12 |    0.74 |        6.39 |          0    |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| twin_rmse    |           25 |          -0.14 |      -0.82 |       0.18 |          0.4  |
| control_rmse |           25 |          -0.14 |      -1.12 |       0.18 |          0.32 |
| cov80        |           25 |          -0    |      -0.01 |       0    |          0.4  |
| abs_dmean    |           25 |          -0.15 |      -0.62 |       0.42 |          0.4  |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           25 |    4.948 |            7.715 |         0.062 |    -5.719 |     5.406 |         0.52  | 0.532 |
|     2 | abs_dmean | then | inside    | greater       |           25 |    4.207 |            7.715 |        -1.052 |    -2.927 |     3.511 |         0.44  | 0.573 |
|     3 | abs_dmean | then | inside    | greater       |           25 |    9.134 |            7.715 |         3.833 |    -2.323 |     5.885 |         0.68  | 0.051 |
|     4 | abs_dmean | then | inside    | greater       |           24 |    7.917 |            7.469 |         2.005 |    -1.758 |     5.913 |         0.583 | 0.064 |
|     5 | abs_dmean | then | inside    | greater       |           24 |    4.777 |            7.469 |        -0.995 |    -6.573 |     2.904 |         0.458 | 0.594 |
|     6 | abs_dmean | then | inside    | greater       |           24 |    5.856 |            7.469 |        -0.662 |    -3.292 |     2.194 |         0.417 | 0.583 |
|     7 | abs_dmean | then | inside    | greater       |           23 |    4.695 |            7.715 |        -0.875 |    -4.847 |     1.236 |         0.391 | 0.877 |
|     8 | abs_dmean | then | inside    | greater       |           12 |    5.947 |            7.469 |         0.929 |    -3.919 |     5.417 |         0.5   | 0.367 |
|     9 | abs_dmean | then | inside    | greater       |            6 |    6.386 |            6.945 |        -2.086 |    -6.632 |     3.642 |         0.333 | 0.844 |

## k = 5 days

25 patients, 25 recordings.

|   day |   n_patients |   share_of_cohort |   twin_rmse |   control_rmse |   avgday_rmse |   cov80 |   abs_dmean |   share_moved |
|------:|-------------:|------------------:|------------:|---------------:|--------------:|--------:|------------:|--------------:|
|     0 |           25 |              1    |      nan    |         nan    |        nan    |  nan    |        5.97 |          0.04 |
|     1 |           25 |              1    |       18.8  |          17.98 |         19.92 |    0.94 |        7.79 |          0.04 |
|     2 |           24 |              0.96 |       17.81 |          20.94 |         22.01 |    0.91 |        7.22 |          0.08 |
|     3 |           24 |              0.96 |       15.92 |          17.96 |         18.88 |    0.92 |        4.29 |          0.04 |
|     4 |           24 |              0.96 |       16.22 |          18.76 |         19.56 |    0.93 |        5.43 |          0.04 |
|     5 |           23 |              0.92 |       17.35 |          18.54 |         19.68 |    0.94 |        4.67 |          0.04 |
|     6 |           12 |              0.48 |       24.8  |          23.97 |         23.58 |    0.8  |        5.28 |          0.08 |
|     7 |            6 |              0.24 |       26.39 |          25.14 |         25.32 |    0.77 |        3.99 |          0    |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| twin_rmse    |           24 |           0.3  |      -1.05 |       1.04 |          0.54 |
| control_rmse |           24 |          -0.41 |      -1.2  |       0.57 |          0.46 |
| cov80        |           24 |          -0.01 |      -0.02 |       0    |          0.42 |
| abs_dmean    |           24 |          -0.15 |      -0.94 |       0.24 |          0.46 |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           25 |    7.789 |            5.967 |        -0.214 |    -2.389 |     3.257 |         0.48  | 0.375 |
|     2 | abs_dmean | then | inside    | greater       |           24 |    7.225 |            5.944 |         0.879 |    -1.748 |     5.023 |         0.5   | 0.145 |
|     3 | abs_dmean | then | inside    | greater       |           24 |    4.29  |            5.944 |        -1.537 |    -4.719 |     3.875 |         0.333 | 0.727 |
|     4 | abs_dmean | then | inside    | greater       |           24 |    5.425 |            5.944 |        -0.442 |    -2.459 |     1.404 |         0.375 | 0.605 |
|     5 | abs_dmean | then | inside    | greater       |           23 |    4.671 |            5.967 |        -1.854 |    -2.72  |     0.924 |         0.304 | 0.915 |
|     6 | abs_dmean | then | inside    | greater       |           12 |    5.283 |            6.318 |        -1.073 |    -6.455 |     4.55  |         0.5   | 0.661 |
|     7 | abs_dmean | then | inside    | greater       |            6 |    3.991 |            7.674 |        -4.508 |   -12.378 |     3.223 |         0.167 | 0.891 |
