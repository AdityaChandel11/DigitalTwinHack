# Expiry by day: ShanghaiT2DM

The daily shape of the first k days against each later day; no fingersticks are read.

Test patients. Descriptive: no bar.

## k = 3 days

47 patients, 53 recordings.

|   day |   n_patients |   share_of_cohort |   control_rmse |   abs_dmean |   dmean |   share_moved |   abs_dtar |
|------:|-------------:|------------------:|---------------:|------------:|--------:|--------------:|-----------:|
|     0 |           47 |              1    |          40.39 |       13.52 |    0    |          0.31 |      12.15 |
|     1 |           47 |              1    |          36.71 |       11.37 |   -6.34 |          0.32 |      10.07 |
|     2 |           45 |              0.96 |          35.56 |       13.99 |   -9.73 |          0.3  |       9.37 |
|     3 |           42 |              0.89 |          40.11 |       15.95 |   -4.44 |          0.42 |      10.24 |
|     4 |           37 |              0.79 |          37.1  |       12.79 |  -10.33 |          0.34 |       8.68 |
|     5 |           35 |              0.74 |          38.11 |       13.55 |   -8.58 |          0.4  |      11.81 |
|     6 |           31 |              0.66 |          38.68 |       20.62 |   -6.91 |          0.48 |      12.15 |
|     7 |           28 |              0.6  |          35.08 |       17.59 |   -9.87 |          0.43 |      10.94 |
|     8 |           24 |              0.51 |          35.24 |       19.84 |  -17.43 |          0.51 |      10.59 |
|     9 |           22 |              0.47 |          33.43 |       14.41 |  -10.96 |          0.42 |       7.99 |
|    10 |           20 |              0.43 |          31.49 |       16.27 |   -6.21 |          0.36 |       6.94 |
|    11 |           13 |              0.28 |          32.46 |        8.44 |   -2.7  |          0.08 |       4.85 |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| control_rmse |           42 |           0.18 |      -0.32 |       1.05 |          0.52 |
| abs_dmean    |           42 |           1.04 |       0.66 |       2.64 |          0.79 |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           47 |   11.366 |           13.525 |         1.706 |    -1.962 |     3.981 |         0.553 | 0.277 |
|     2 | abs_dmean | then | inside    | greater       |           45 |   13.994 |           12.6   |         1.919 |    -1.341 |     6.375 |         0.6   | 0.082 |
|     3 | abs_dmean | then | inside    | greater       |           42 |   15.955 |           13.727 |         2.222 |    -3.592 |     8.05  |         0.548 | 0.074 |
|     4 | abs_dmean | then | inside    | greater       |           37 |   12.794 |           13.525 |         1.006 |    -4.72  |     6.981 |         0.541 | 0.185 |
|     5 | abs_dmean | then | inside    | greater       |           35 |   13.547 |           12.312 |         4.575 |    -1.45  |    10.844 |         0.6   | 0.03  |
|     6 | abs_dmean | then | inside    | greater       |           31 |   20.625 |           10.712 |         6.078 |     1.637 |    13.231 |         0.71  | 0.005 |
|     7 | abs_dmean | then | inside    | greater       |           28 |   17.591 |           10.425 |         7.991 |     0.113 |    17.389 |         0.679 | 0.004 |
|     8 | abs_dmean | then | inside    | greater       |           24 |   19.841 |            9.567 |        12.487 |    -1.309 |    25.143 |         0.667 | 0.004 |
|     9 | abs_dmean | then | inside    | greater       |           22 |   14.408 |           10.425 |         5.031 |    -6.856 |    17.387 |         0.591 | 0.046 |
|    10 | abs_dmean | then | inside    | greater       |           20 |   16.267 |            9.567 |         3.286 |    -2.225 |    15.924 |         0.5   | 0.101 |
|    11 | abs_dmean | then | inside    | greater       |           13 |    8.437 |           10.138 |        -4.276 |   -10.712 |     5.442 |         0.308 | 0.863 |

## k = 5 days

37 patients, 43 recordings.

|   day |   n_patients |   share_of_cohort |   control_rmse |   abs_dmean |   dmean |   share_moved |   abs_dtar |
|------:|-------------:|------------------:|---------------:|------------:|--------:|--------------:|-----------:|
|     0 |           37 |              1    |          39.84 |       13.51 |   -0    |          0.28 |      10    |
|     1 |           37 |              1    |          35.16 |       11.97 |   -4.56 |          0.4  |       6.46 |
|     2 |           37 |              1    |          32.54 |        9.95 |   -9.18 |          0.25 |       8.54 |
|     3 |           35 |              0.95 |          30.6  |       11.13 |   -7.52 |          0.3  |       8.54 |
|     4 |           31 |              0.84 |          32.08 |       17.46 |   -6.64 |          0.41 |       8.75 |
|     5 |           28 |              0.76 |          29.54 |       16.22 |   -8.17 |          0.47 |       9.08 |
|     6 |           24 |              0.65 |          29.88 |       19.66 |  -13.11 |          0.49 |      10.21 |
|     7 |           22 |              0.59 |          30.39 |       12.29 |  -10.19 |          0.35 |       7.71 |
|     8 |           20 |              0.54 |          31.8  |       15.36 |   -7.01 |          0.33 |       5.26 |
|     9 |           13 |              0.35 |          31.37 |        8.93 |   -2.07 |          0.08 |       5.14 |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| control_rmse |           35 |           0.6  |      -0.46 |       1.19 |          0.6  |
| abs_dmean    |           35 |           0.89 |       0.5  |       1.78 |          0.77 |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           37 |   11.968 |           13.509 |        -0.917 |    -4.669 |     7.184 |         0.486 | 0.301 |
|     2 | abs_dmean | then | inside    | greater       |           37 |    9.953 |           13.509 |        -0.231 |    -2.269 |     3.816 |         0.459 | 0.423 |
|     3 | abs_dmean | then | inside    | greater       |           35 |   11.134 |           11.192 |         1.012 |    -2.704 |     6.533 |         0.543 | 0.104 |
|     4 | abs_dmean | then | inside    | greater       |           31 |   17.46  |           10.688 |         6.056 |     2.28  |    10.599 |         0.677 | 0.005 |
|     5 | abs_dmean | then | inside    | greater       |           28 |   16.222 |           10.216 |         6.079 |     0.505 |    12.652 |         0.679 | 0.002 |
|     6 | abs_dmean | then | inside    | greater       |           24 |   19.659 |            9.663 |         7.256 |     1.222 |    21.002 |         0.708 | 0.002 |
|     7 | abs_dmean | then | inside    | greater       |           22 |   12.289 |            9.663 |         1.588 |    -5.133 |    14.017 |         0.591 | 0.088 |
|     8 | abs_dmean | then | inside    | greater       |           20 |   15.364 |            9.496 |         3.518 |     0.323 |    11.434 |         0.75  | 0.022 |
|     9 | abs_dmean | then | inside    | greater       |           13 |    8.934 |            9.581 |        -1.393 |    -8.236 |     2.014 |         0.308 | 0.892 |

Not run: 10 (too short to hold out a day after calibration)
