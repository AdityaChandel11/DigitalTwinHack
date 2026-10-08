# Expiry by day: ShanghaiT2DM

The daily shape of the first k days against each later day; no fingersticks are read.

Development patients. Not confirmatory.

## k = 3 days

49 patients, 52 recordings.

|   day |   n_patients |   share_of_cohort |   control_rmse |   abs_dmean |   dmean |   share_moved |   abs_dtar |
|------:|-------------:|------------------:|---------------:|------------:|--------:|--------------:|-----------:|
|     0 |           49 |              1    |          33.59 |       10.75 |    0    |          0.18 |       6.94 |
|     1 |           49 |              1    |          31.84 |        8.63 |   -1.53 |          0.27 |       7.12 |
|     2 |           48 |              0.98 |          31.04 |        9.67 |   -1.02 |          0.28 |       6.42 |
|     3 |           46 |              0.94 |          31.85 |       14.61 |   -2.77 |          0.34 |       7.29 |
|     4 |           43 |              0.88 |          33.3  |       13.14 |   -0.24 |          0.3  |       7.64 |
|     5 |           40 |              0.82 |          30.14 |       13.12 |   -5.25 |          0.35 |       8.07 |
|     6 |           40 |              0.82 |          34.04 |       14.42 |   -4.6  |          0.36 |       6.25 |
|     7 |           38 |              0.78 |          30.5  |       12.31 |   -3.66 |          0.22 |       4.69 |
|     8 |           37 |              0.76 |          30.39 |       10.61 |   -0.69 |          0.26 |       5.38 |
|     9 |           36 |              0.73 |          29.67 |       14.17 |   -5.07 |          0.35 |       8.7  |
|    10 |           32 |              0.65 |          30.27 |       13.99 |   -5.97 |          0.28 |       7.99 |
|    11 |           17 |              0.35 |          33    |       14.98 |  -11.13 |          0.35 |       5.5  |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| control_rmse |           46 |           0.03 |      -0.34 |       0.52 |          0.52 |
| abs_dmean    |           46 |           0.56 |       0.28 |       1.4  |          0.72 |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           49 |    8.625 |           10.75  |        -1.163 |    -3.525 |     3.25  |         0.449 | 0.253 |
|     2 | abs_dmean | then | inside    | greater       |           48 |    9.666 |           10.806 |         2.953 |    -0.64  |     5.75  |         0.625 | 0.03  |
|     3 | abs_dmean | then | inside    | greater       |           46 |   14.606 |           10.725 |         4.891 |    -0.681 |     8.874 |         0.587 | 0.005 |
|     4 | abs_dmean | then | inside    | greater       |           43 |   13.144 |           10.7   |         2.975 |     0.734 |     6.338 |         0.698 | 0.004 |
|     5 | abs_dmean | then | inside    | greater       |           40 |   13.119 |           10.4   |         5.672 |    -0.441 |     8.132 |         0.625 | 0.001 |
|     6 | abs_dmean | then | inside    | greater       |           40 |   14.425 |           10.4   |         3.575 |     1.494 |     7.819 |         0.75  | 0.001 |
|     7 | abs_dmean | then | inside    | greater       |           38 |   12.306 |           10.4   |         1.4   |    -1.078 |     8.419 |         0.579 | 0.042 |
|     8 | abs_dmean | then | inside    | greater       |           37 |   10.606 |           10.7   |         3.344 |    -1.05  |     8.038 |         0.622 | 0.015 |
|     9 | abs_dmean | then | inside    | greater       |           36 |   14.175 |           10.4   |         2.572 |     1.331 |     9.403 |         0.694 | 0.001 |
|    10 | abs_dmean | then | inside    | greater       |           32 |   13.988 |            8.103 |         5.326 |     1.013 |    14.012 |         0.719 | 0.001 |
|    11 | abs_dmean | then | inside    | greater       |           17 |   14.977 |            7.325 |         7.75  |     0.187 |    17.106 |         0.765 | 0.013 |

Not run: 4 (too short to hold out a day after calibration)

## k = 5 days

43 patients, 46 recordings.

|   day |   n_patients |   share_of_cohort |   control_rmse |   abs_dmean |   dmean |   share_moved |   abs_dtar |
|------:|-------------:|------------------:|---------------:|------------:|--------:|--------------:|-----------:|
|     0 |           43 |              1    |          30.71 |        9.11 |   -0    |          0.15 |       6.04 |
|     1 |           43 |              1    |          28.27 |       10.9  |   -0.08 |          0.26 |       5.63 |
|     2 |           43 |              1    |          31.03 |       10.15 |   -1.33 |          0.22 |       5.94 |
|     3 |           40 |              0.93 |          27.26 |       11.22 |   -5.92 |          0.15 |       5.31 |
|     4 |           40 |              0.93 |          30.59 |       12.39 |   -5.06 |          0.31 |       6.41 |
|     5 |           38 |              0.88 |          29.37 |       10.72 |   -5.33 |          0.2  |       3.54 |
|     6 |           37 |              0.86 |          30.05 |        9.51 |   -5.58 |          0.28 |       5.42 |
|     7 |           36 |              0.84 |          29.31 |       10.44 |   -3.43 |          0.29 |       8.02 |
|     8 |           32 |              0.74 |          30.54 |       12.38 |   -6.32 |          0.34 |       6.77 |
|     9 |           17 |              0.4  |          31.36 |       14.74 |   -8.03 |          0.35 |       7.31 |

Change per day inside each patient:

| column       |   n_patients |   median_slope |   slope_lo |   slope_hi |   frac_rising |
|:-------------|-------------:|---------------:|-----------:|-----------:|--------------:|
| control_rmse |           40 |           0.04 |      -0.39 |       0.61 |          0.57 |
| abs_dmean    |           40 |           0.45 |       0.06 |       1.06 |          0.68 |

Each day against the same patient's day 0:

|   day | column    | of   | against   | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_larger |     p |
|------:|:----------|:-----|:----------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
|     1 | abs_dmean | then | inside    | greater       |           43 |   10.901 |            9.105 |         2.812 |    -0.463 |     5.006 |         0.628 | 0.049 |
|     2 | abs_dmean | then | inside    | greater       |           43 |   10.148 |            9.105 |         2.606 |     1.074 |     3.469 |         0.674 | 0.021 |
|     3 | abs_dmean | then | inside    | greater       |           40 |   11.216 |            9.034 |         1.653 |    -1.673 |     5.614 |         0.55  | 0.094 |
|     4 | abs_dmean | then | inside    | greater       |           40 |   12.386 |            9.034 |         3.297 |    -0.308 |     6.93  |         0.625 | 0.003 |
|     5 | abs_dmean | then | inside    | greater       |           38 |   10.72  |            8.872 |         1.832 |    -1.702 |     5.764 |         0.605 | 0.09  |
|     6 | abs_dmean | then | inside    | greater       |           37 |    9.51  |            8.782 |         2.24  |    -0.906 |     7.747 |         0.622 | 0.009 |
|     7 | abs_dmean | then | inside    | greater       |           36 |   10.443 |            8.944 |         3.331 |     0.958 |     7.56  |         0.694 | 0.005 |
|     8 | abs_dmean | then | inside    | greater       |           32 |   12.384 |            8.386 |         4.764 |     0.88  |    11.255 |         0.656 | 0.002 |
|     9 | abs_dmean | then | inside    | greater       |           17 |   14.736 |            7.989 |         8.893 |    -0.144 |    11.664 |         0.706 | 0.01  |

Not run: 10 (too short to hold out a day after calibration)
