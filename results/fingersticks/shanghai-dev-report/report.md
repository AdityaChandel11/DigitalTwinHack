# Fingersticks, second pass: the report a doctor reads

Development patients. Not confirmatory.

Filter: `{'tau_min': 120.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': False, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}` (frozen). Errors are absolute, medians over patients: mean glucose in mg/dL, time above 180 and time in range in percentage points. `stale` is the report of the calibration days; `sticks` the average of the hidden fingersticks on the sensor's scale and `sticks_raw` as read; `shape` the daily shape alone; `hindsight_count` counts crossings of the estimate with no spread.

## k = 3 days

24 patients, 25 recordings. Since the calibration days the mean moved by a median of 14.8 mg/dL (signed -9.0); 33 % of patients moved more than 20.

Fingersticks per day: 3.9 over the recording (quartiles 2.8 to 7.0), 3.9 in the hidden window.

| source          |   mean |   tar |   tir |
|:----------------|-------:|------:|------:|
| stale           |  14.83 |  8.76 |  9.39 |
| sticks          |  12.85 |  7.07 |  6.89 |
| sticks_raw      |  15.09 | 11.33 | 11.11 |
| shape           |  14.75 | 11.54 | 14.62 |
| live            |  12.46 | 10.65 | 15.05 |
| hindsight       |  12.1  |  9.79 | 13.13 |
| hindsight_count |  12.1  |  8.99 | 11.38 |

| what   | of                 | against         | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_better |     p |
|:-------|:-------------------|:----------------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
| mean   | hindsight_mean_err | stale_mean_err  | less          |           24 |   12.105 |           14.831 |        -1.134 |    -3.074 |     0.216 |         0.667 | 0.032 |
| mean   | hindsight_mean_err | sticks_mean_err | less          |           24 |   12.105 |           12.85  |        -0.222 |    -3.246 |     4.974 |         0.5   | 0.417 |
| mean   | hindsight_mean_err | shape_mean_err  | less          |           24 |   12.105 |           14.747 |        -1.071 |    -3.508 |     0.594 |         0.625 | 0.037 |
| mean   | live_mean_err      | stale_mean_err  | less          |           24 |   12.464 |           14.831 |        -0.842 |    -1.521 |    -0.069 |         0.708 | 0.008 |
| mean   | sticks_mean_err    | stale_mean_err  | less          |           24 |   12.85  |           14.831 |        -0.257 |    -6.781 |     3.803 |         0.5   | 0.282 |
| tar    | hindsight_tar_err  | stale_tar_err   | less          |           24 |    9.785 |            8.759 |         0.238 |    -1.186 |     1.423 |         0.5   | 0.363 |
| tar    | hindsight_tar_err  | sticks_tar_err  | less          |           24 |    9.785 |            7.073 |        -0.345 |    -3.733 |     2.004 |         0.583 | 0.439 |
| tar    | hindsight_tar_err  | shape_tar_err   | less          |           24 |    9.785 |           11.538 |        -0.996 |    -2.742 |     0.188 |         0.625 | 0.013 |
| tar    | live_tar_err       | stale_tar_err   | less          |           24 |   10.65  |            8.759 |         0.312 |    -1.086 |     1.981 |         0.458 | 0.637 |
| tar    | sticks_tar_err     | stale_tar_err   | less          |           24 |    7.073 |            8.759 |         0.934 |    -2.778 |     2.491 |         0.375 | 0.416 |
| tir    | hindsight_tir_err  | stale_tir_err   | less          |           24 |   13.127 |            9.392 |         2.946 |    -0.996 |     5.339 |         0.375 | 0.94  |
| tir    | hindsight_tir_err  | sticks_tir_err  | less          |           24 |   13.127 |            6.891 |         3.282 |    -1.58  |     9.806 |         0.417 | 0.968 |
| tir    | hindsight_tir_err  | shape_tir_err   | less          |           24 |   13.127 |           14.615 |        -0.671 |    -1.723 |     0.86  |         0.583 | 0.145 |
| tir    | live_tir_err       | stale_tir_err   | less          |           24 |   15.051 |            9.392 |         2.59  |    -0.053 |     4.658 |         0.333 | 0.979 |
| tir    | sticks_tir_err     | stale_tir_err   | less          |           24 |    6.891 |            9.392 |         0.149 |    -2.778 |     3.661 |         0.458 | 0.262 |

By day since the sensor came off (RMSE against the hidden sensor, mg/dL):

|   day |   n_patients |   share_of_cohort |   control_rmse |   live_rmse |   hindsight_rmse |   abs_dmean |   share_moved |   hindsight_mean_err |
|------:|-------------:|------------------:|---------------:|------------:|-----------------:|------------:|--------------:|---------------------:|
|     1 |           24 |              1    |          36.29 |       33.43 |            26.49 |       15.92 |          0.38 |                13.24 |
|     2 |           24 |              1    |          33.61 |       31.49 |            28.87 |       13.53 |          0.33 |                12.69 |
|     3 |           23 |              0.96 |          32.75 |       32.95 |            29.43 |       16.02 |          0.43 |                15.03 |
|     4 |           21 |              0.88 |          36.52 |       33.53 |            29.46 |       16.98 |          0.48 |                11.93 |
|     5 |           19 |              0.79 |          31.33 |       28.08 |            21.77 |       14.09 |          0.42 |                 8.56 |
|     6 |           19 |              0.79 |          35.48 |       35.71 |            33.86 |       14.29 |          0.37 |                16.81 |
|     7 |           17 |              0.71 |          30.24 |       30.47 |            28.5  |       10.5  |          0.24 |                 7.5  |
|     8 |           16 |              0.67 |          31.38 |       30.62 |            28.47 |       10.73 |          0.31 |                 9.73 |
|     9 |           15 |              0.62 |          31.03 |       29.07 |            28.83 |       16.36 |          0.33 |                13.47 |
|    10 |           12 |              0.5  |          34.54 |       36.47 |            33.67 |       13.79 |          0.25 |                11.09 |
|    11 |            8 |              0.33 |          34.3  |       34.69 |            35.14 |       20.69 |          0.5  |                26.75 |

## k = 5 days

20 patients, 21 recordings. Since the calibration days the mean moved by a median of 8.9 mg/dL (signed -5.7); 30 % of patients moved more than 20.

Fingersticks per day: 3.3 over the recording (quartiles 2.3 to 6.6), 3.9 in the hidden window.

| source          |   mean |   tar |   tir |
|:----------------|-------:|------:|------:|
| stale           |   8.93 |  3.58 |  5.4  |
| sticks          |  10.71 |  7.6  |  9.29 |
| sticks_raw      |  18.09 | 11.08 |  8.75 |
| shape           |   9.19 |  3.25 |  8.96 |
| live            |   9.66 |  4.22 |  8.44 |
| hindsight       |  11.42 |  4.22 |  9.38 |
| hindsight_count |  11.42 |  6.58 | 11.35 |

| what   | of                 | against         | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_better |     p |
|:-------|:-------------------|:----------------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
| mean   | hindsight_mean_err | stale_mean_err  | less          |           20 |   11.421 |            8.928 |        -1.177 |    -2.482 |     0.936 |          0.6  | 0.139 |
| mean   | hindsight_mean_err | sticks_mean_err | less          |           20 |   11.421 |           10.708 |        -2.546 |    -9.371 |     2.799 |          0.6  | 0.108 |
| mean   | hindsight_mean_err | shape_mean_err  | less          |           20 |   11.421 |            9.191 |        -0.97  |    -2.485 |     0.791 |          0.6  | 0.147 |
| mean   | live_mean_err      | stale_mean_err  | less          |           20 |    9.664 |            8.928 |        -0.966 |    -1.335 |     0.201 |          0.65 | 0.041 |
| mean   | sticks_mean_err    | stale_mean_err  | less          |           20 |   10.708 |            8.928 |         2.009 |    -5.293 |     9.125 |          0.4  | 0.727 |
| tar    | hindsight_tar_err  | stale_tar_err   | less          |           20 |    4.225 |            3.576 |        -0.578 |    -1.338 |     2.187 |          0.6  | 0.536 |
| tar    | hindsight_tar_err  | sticks_tar_err  | less          |           20 |    4.225 |            7.605 |        -2.6   |    -3.955 |    -0.222 |          0.7  | 0.032 |
| tar    | hindsight_tar_err  | shape_tar_err   | less          |           20 |    4.225 |            3.249 |         0.075 |    -0.897 |     0.636 |          0.5  | 0.478 |
| tar    | live_tar_err       | stale_tar_err   | less          |           20 |    4.22  |            3.576 |        -0.012 |    -1.521 |     2.368 |          0.5  | 0.622 |
| tar    | sticks_tar_err     | stale_tar_err   | less          |           20 |    7.605 |            3.576 |         3.466 |    -0.587 |     5.851 |          0.4  | 0.959 |
| tir    | hindsight_tir_err  | stale_tir_err   | less          |           20 |    9.379 |            5.396 |         3.105 |     0.409 |     5.054 |          0.25 | 0.978 |
| tir    | hindsight_tir_err  | sticks_tir_err  | less          |           20 |    9.379 |            9.285 |        -0.756 |    -3.854 |     5.858 |          0.5  | 0.649 |
| tir    | hindsight_tir_err  | shape_tir_err   | less          |           20 |    9.379 |            8.961 |        -0.181 |    -1.433 |     0.809 |          0.55 | 0.364 |
| tir    | live_tir_err       | stale_tir_err   | less          |           20 |    8.441 |            5.396 |         2.688 |     0.088 |     4.646 |          0.3  | 0.99  |
| tir    | sticks_tir_err     | stale_tir_err   | less          |           20 |    9.285 |            5.396 |         3.279 |    -3.244 |     6.205 |          0.45 | 0.816 |

By day since the sensor came off (RMSE against the hidden sensor, mg/dL):

|   day |   n_patients |   share_of_cohort |   control_rmse |   live_rmse |   hindsight_rmse |   abs_dmean |   share_moved |   hindsight_mean_err |
|------:|-------------:|------------------:|---------------:|------------:|-----------------:|------------:|--------------:|---------------------:|
|     1 |           20 |              1    |          29.51 |       28.82 |            25.73 |       10.73 |          0.3  |                12    |
|     2 |           20 |              1    |          31.66 |       29.06 |            25.31 |       10.72 |          0.25 |                 7.99 |
|     3 |           19 |              0.95 |          27.44 |       25.51 |            20.75 |       11.56 |          0.16 |                10.63 |
|     4 |           19 |              0.95 |          31.71 |       33.06 |            33.06 |       12.84 |          0.32 |                13.66 |
|     5 |           17 |              0.85 |          30.47 |       30.72 |            28.88 |       10.36 |          0.24 |                 7.38 |
|     6 |           16 |              0.8  |          29.9  |       29.32 |            27.05 |        9.16 |          0.38 |                 7.98 |
|     7 |           15 |              0.75 |          28.74 |       27.23 |            27.23 |       11.17 |          0.27 |                 8.81 |
|     8 |           12 |              0.6  |          33.91 |       35.63 |            33.78 |       16.41 |          0.42 |                16.34 |
|     9 |            8 |              0.4  |          32.08 |       32.34 |            32.52 |       20.36 |          0.5  |                21.59 |
