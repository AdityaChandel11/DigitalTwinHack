# Expiry by day: CGMacros

The twin (`twin`), its control with no meals (`control`) and the raw average day, by day since the sensor.

Test patients. Descriptive: no bar.

## k = 3 days

19 patients, 19 recordings.

|   day |   n_patients |   share_of_cohort |   twin_rmse |   control_rmse |   avgday_rmse |   cov80 |   abs_dmean |   share_moved |
|------:|-------------:|------------------:|------------:|---------------:|--------------:|--------:|------------:|--------------:|
|     0 |           19 |              1    |      nan    |         nan    |        nan    |  nan    |        4.99 |          0.07 |
|     1 |           19 |              1    |       28.78 |          31.07 |         32.55 |    0.9  |        8.25 |          0.11 |
|     2 |           18 |              0.95 |       19.8  |          19.29 |         23.14 |    0.92 |        5.13 |          0.06 |
|     3 |           19 |              1    |       21.6  |          22.12 |         24.58 |    0.93 |        8.74 |          0.11 |
|     4 |           18 |              0.95 |       25.59 |          26.91 |         28.12 |    0.88 |        6.63 |          0.11 |
|     5 |           18 |              0.95 |       21.53 |          21.93 |         24.06 |    0.94 |        6.51 |          0.11 |
|     6 |           18 |              0.95 |       23.94 |          24.15 |         26.39 |    0.85 |       10    |          0.17 |
|     7 |           18 |              0.95 |       21.36 |          24.27 |         25.96 |    0.89 |        7.78 |          0.11 |
|     8 |            9 |              0.47 |       24.03 |          23.42 |         25.24 |    0.89 |        6.99 |          0    |
|     9 |            2 |              0.11 |       28.37 |          24.71 |         27.07 |    0.51 |       18.73 |          0.5  |
|    10 |            1 |              0.05 |       33.11 |          29.47 |         30.32 |    0.71 |       18.87 |          0    |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| twin_rmse    |           18 |          -0.43 |      -0.81 |       0.66 |          0.39 |
| control_rmse |           18 |          -0.44 |      -0.97 |       0.37 |          0.39 |
| cov80        |           18 |          -0    |      -0.01 |       0.01 |          0.44 |
| abs_dmean    |           18 |           0.1  |      -0.76 |       0.76 |          0.5  |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           19 |    8.25  |            4.995 |         0.329 |    -2.664 |     4.156 |         0.579 | 0.209 |
|     2 | abs_dmean | then | inside    | greater       |           18 |    5.134 |            6.495 |        -0.01  |    -6.499 |     5.205 |         0.5   | 0.5   |
|     3 | abs_dmean | then | inside    | greater       |           19 |    8.74  |            4.995 |         2.031 |    -2.75  |     5.105 |         0.579 | 0.245 |
|     4 | abs_dmean | then | inside    | greater       |           18 |    6.634 |            6.495 |        -0.698 |    -2     |     3.936 |         0.444 | 0.466 |
|     5 | abs_dmean | then | inside    | greater       |           18 |    6.512 |            6.495 |        -1.646 |    -3.949 |     5.174 |         0.444 | 0.466 |
|     6 | abs_dmean | then | inside    | greater       |           18 |    9.996 |            6.495 |         0.545 |    -2.554 |     6.501 |         0.556 | 0.162 |
|     7 | abs_dmean | then | inside    | greater       |           18 |    7.782 |            6.495 |        -0.798 |    -3.309 |     6.361 |         0.444 | 0.399 |
|     8 | abs_dmean | then | inside    | greater       |            9 |    6.99  |            8.899 |        -2.264 |    -4.5   |     7.06  |         0.444 | 0.674 |

## k = 5 days

19 patients, 19 recordings.

|   day |   n_patients |   share_of_cohort |   twin_rmse |   control_rmse |   avgday_rmse |   cov80 |   abs_dmean |   share_moved |
|------:|-------------:|------------------:|------------:|---------------:|--------------:|--------:|------------:|--------------:|
|     0 |           19 |              1    |      nan    |         nan    |        nan    |  nan    |        7.28 |          0.07 |
|     1 |           19 |              1    |       19.42 |          20.91 |         22.33 |    0.85 |        6.45 |          0    |
|     2 |           18 |              0.95 |       24.94 |          25.06 |         26.47 |    0.83 |        5.12 |          0.11 |
|     3 |           18 |              0.95 |       20.09 |          21.02 |         21.87 |    0.91 |        5.99 |          0.06 |
|     4 |           18 |              0.95 |       24.45 |          24.45 |         25    |    0.86 |        9.9  |          0.11 |
|     5 |           18 |              0.95 |       20.52 |          22.95 |         23.95 |    0.88 |        7.98 |          0.17 |
|     6 |            9 |              0.47 |       22.85 |          22.12 |         22.78 |    0.92 |        8.26 |          0.11 |
|     7 |            2 |              0.11 |       27.21 |          23.81 |         25.81 |    0.58 |       17.07 |          0.5  |
|     8 |            1 |              0.05 |       31.08 |          27.62 |         28.44 |    0.77 |       15.09 |          0    |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| twin_rmse    |           18 |          -0.01 |      -0.45 |       0.84 |          0.5  |
| control_rmse |           18 |          -0.03 |      -0.86 |       0.69 |          0.5  |
| cov80        |           18 |           0    |      -0.01 |       0.01 |          0.56 |
| abs_dmean    |           18 |           0.01 |      -0.08 |       0.99 |          0.56 |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           19 |    6.452 |            7.277 |        -0.117 |    -3.014 |     2.79  |         0.474 | 0.508 |
|     2 | abs_dmean | then | inside    | greater       |           18 |    5.124 |            7.595 |        -2.496 |    -4.864 |     0.641 |         0.389 | 0.791 |
|     3 | abs_dmean | then | inside    | greater       |           18 |    5.991 |            7.595 |        -0.39  |    -4.022 |     2.731 |         0.444 | 0.601 |
|     4 | abs_dmean | then | inside    | greater       |           18 |    9.895 |            7.595 |         0.866 |    -2.235 |     4.841 |         0.611 | 0.221 |
|     5 | abs_dmean | then | inside    | greater       |           18 |    7.976 |            7.595 |         0.064 |    -4.342 |     3.886 |         0.5   | 0.383 |
|     6 | abs_dmean | then | inside    | greater       |            9 |    8.256 |            7.277 |         0.817 |    -4.43  |     3.832 |         0.556 | 0.545 |
