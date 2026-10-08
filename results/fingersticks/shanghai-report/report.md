# Fingersticks, second pass: the report a doctor reads

Test patients, read a second time after F1 and F2 were known. Descriptive: no bar.

Filter: `{'tau_min': 120.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': False, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}` (frozen). Errors are absolute, medians over patients: mean glucose in mg/dL, time above 180 and time in range in percentage points. `stale` is the report of the calibration days; `sticks` the average of the hidden fingersticks on the sensor's scale and `sticks_raw` as read; `shape` the daily shape alone; `hindsight_count` counts crossings of the estimate with no spread.

## k = 3 days

29 patients, 32 recordings. Since the calibration days the mean moved by a median of 13.0 mg/dL (signed -8.2); 38 % of patients moved more than 20.

Fingersticks per day: 6.3 over the recording (quartiles 4.6 to 6.9), 6.1 in the hidden window.

| source          |   mean |   tar |   tir |
|:----------------|-------:|------:|------:|
| stale           |  12.95 | 12.43 | 13.25 |
| sticks          |   6.42 |  3.12 |  4.95 |
| sticks_raw      |  18.34 |  8.48 |  9.06 |
| shape           |  12.53 | 10.27 | 15.71 |
| live            |  11.85 |  9.57 | 15.64 |
| hindsight       |   8.85 |  8.77 | 15.16 |
| hindsight_count |   8.85 |  6.37 |  6.98 |

| what   | of                 | against         | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_better |     p |
|:-------|:-------------------|:----------------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
| mean   | hindsight_mean_err | stale_mean_err  | less          |           29 |    8.854 |           12.952 |        -3.398 |    -8.913 |    -1.556 |         0.828 | 0     |
| mean   | hindsight_mean_err | sticks_mean_err | less          |           29 |    8.854 |            6.423 |         1.883 |    -0.817 |     3.112 |         0.379 | 0.931 |
| mean   | hindsight_mean_err | shape_mean_err  | less          |           29 |    8.854 |           12.528 |        -4.688 |    -9.371 |    -1.517 |         0.828 | 0     |
| mean   | live_mean_err      | stale_mean_err  | less          |           29 |   11.845 |           12.952 |        -1.764 |    -3.862 |    -0.89  |         0.828 | 0     |
| mean   | sticks_mean_err    | stale_mean_err  | less          |           29 |    6.423 |           12.952 |        -4.682 |    -9.477 |    -0.98  |         0.724 | 0.001 |
| tar    | hindsight_tar_err  | stale_tar_err   | less          |           29 |    8.771 |           12.427 |        -1.721 |    -6.469 |     0.039 |         0.655 | 0.004 |
| tar    | hindsight_tar_err  | sticks_tar_err  | less          |           29 |    8.771 |            3.117 |         2.082 |     0.039 |     5.967 |         0.31  | 0.991 |
| tar    | hindsight_tar_err  | shape_tar_err   | less          |           29 |    8.771 |           10.27  |        -0.931 |    -4.431 |     0.005 |         0.621 | 0.005 |
| tar    | live_tar_err       | stale_tar_err   | less          |           29 |    9.566 |           12.427 |        -0.718 |    -3.725 |     0.271 |         0.621 | 0.025 |
| tar    | sticks_tar_err     | stale_tar_err   | less          |           29 |    3.117 |           12.427 |        -2.145 |    -8.414 |    -0.296 |         0.69  | 0.001 |
| tir    | hindsight_tir_err  | stale_tir_err   | less          |           29 |   15.159 |           13.25  |        -1.014 |    -4.257 |     4.026 |         0.517 | 0.492 |
| tir    | hindsight_tir_err  | sticks_tir_err  | less          |           29 |   15.159 |            4.952 |        10.091 |     5.569 |    12.385 |         0.241 | 0.999 |
| tir    | hindsight_tir_err  | shape_tir_err   | less          |           29 |   15.159 |           15.71  |        -0.163 |    -3.229 |     0.72  |         0.586 | 0.033 |
| tir    | live_tir_err       | stale_tir_err   | less          |           29 |   15.644 |           13.25  |         1.246 |    -2.03  |     3.885 |         0.483 | 0.766 |
| tir    | sticks_tir_err     | stale_tir_err   | less          |           29 |    4.952 |           13.25  |        -4.637 |   -11.869 |    -1.856 |         0.759 | 0.002 |

By day since the sensor came off (RMSE against the hidden sensor, mg/dL):

|   day |   n_patients |   share_of_cohort |   control_rmse |   live_rmse |   hindsight_rmse |   abs_dmean |   share_moved |   hindsight_mean_err |
|------:|-------------:|------------------:|---------------:|------------:|-----------------:|------------:|--------------:|---------------------:|
|     1 |           29 |              1    |          36.71 |       33.62 |            27.93 |       11.26 |          0.31 |                 6.21 |
|     2 |           29 |              1    |          35.13 |       30.48 |            24.75 |       13.84 |          0.33 |                12.06 |
|     3 |           27 |              0.93 |          33.9  |       30.5  |            23.26 |       14.8  |          0.43 |                 9.28 |
|     4 |           23 |              0.79 |          29.13 |       27.83 |            23.25 |       13.64 |          0.35 |                 7.34 |
|     5 |           21 |              0.72 |          32.59 |       31.88 |            24.6  |       14.83 |          0.48 |                12.06 |
|     6 |           18 |              0.62 |          34.58 |       31.86 |            25.8  |       20.18 |          0.5  |                11.28 |
|     7 |           16 |              0.55 |          31.07 |       29.85 |            27.03 |       16.39 |          0.5  |                12.43 |
|     8 |           13 |              0.45 |          27.08 |       27.67 |            22.4  |       17.31 |          0.42 |                 8.42 |
|     9 |           11 |              0.38 |          29.64 |       29.66 |            28.1  |       14.57 |          0.41 |                 9.53 |
|    10 |           11 |              0.38 |          26.15 |       25.76 |            24.02 |        8.98 |          0.14 |                 6.29 |
|    11 |            9 |              0.31 |          27.86 |       25.69 |            25.69 |        8.67 |          0.11 |                 6.96 |

## k = 5 days

21 patients, 24 recordings. Since the calibration days the mean moved by a median of 12.1 mg/dL (signed -10.9); 29 % of patients moved more than 20.

Fingersticks per day: 5.5 over the recording (quartiles 4.1 to 6.7), 5.2 in the hidden window.

| source          |   mean |   tar |   tir |
|:----------------|-------:|------:|------:|
| stale           |  12.08 |  4.49 |  8.21 |
| sticks          |   8.63 |  4.89 |  5.03 |
| sticks_raw      |  16.37 |  5.03 |  6.16 |
| shape           |  11.43 |  5.42 |  9.8  |
| live            |  11.33 |  5.51 | 10.55 |
| hindsight       |   9.94 |  4.85 | 11.69 |
| hindsight_count |   9.94 |  4.06 |  6.12 |

| what   | of                 | against         | alternative   |   n_patients |   median |   median_against |   median_diff |   diff_lo |   diff_hi |   frac_better |     p |
|:-------|:-------------------|:----------------|:--------------|-------------:|---------:|-----------------:|--------------:|----------:|----------:|--------------:|------:|
| mean   | hindsight_mean_err | stale_mean_err  | less          |           21 |    9.943 |           12.085 |        -2.111 |    -7.861 |    -1.543 |         0.905 | 0     |
| mean   | hindsight_mean_err | sticks_mean_err | less          |           21 |    9.943 |            8.632 |        -0.209 |    -3.666 |     1.378 |         0.524 | 0.367 |
| mean   | hindsight_mean_err | shape_mean_err  | less          |           21 |    9.943 |           11.429 |        -1.822 |    -8.104 |    -1.408 |         0.857 | 0     |
| mean   | live_mean_err      | stale_mean_err  | less          |           21 |   11.326 |           12.085 |        -1.312 |    -4.138 |    -0.822 |         0.905 | 0     |
| mean   | sticks_mean_err    | stale_mean_err  | less          |           21 |    8.632 |           12.085 |        -3.322 |    -7.041 |     1.966 |         0.667 | 0.038 |
| tar    | hindsight_tar_err  | stale_tar_err   | less          |           21 |    4.848 |            4.486 |        -1.184 |    -3.415 |     0.084 |         0.619 | 0.032 |
| tar    | hindsight_tar_err  | sticks_tar_err  | less          |           21 |    4.848 |            4.889 |         0.004 |    -0.889 |     5.292 |         0.476 | 0.719 |
| tar    | hindsight_tar_err  | shape_tar_err   | less          |           21 |    4.848 |            5.417 |        -0.153 |    -4.632 |     0.015 |         0.619 | 0.018 |
| tar    | live_tar_err       | stale_tar_err   | less          |           21 |    5.506 |            4.486 |        -0.36  |    -1.995 |     0.138 |         0.619 | 0.095 |
| tar    | sticks_tar_err     | stale_tar_err   | less          |           21 |    4.889 |            4.486 |        -1.241 |    -5.208 |     0.365 |         0.571 | 0.029 |
| tir    | hindsight_tir_err  | stale_tir_err   | less          |           21 |   11.689 |            8.209 |         1.544 |    -1.415 |     5.862 |         0.429 | 0.892 |
| tir    | hindsight_tir_err  | sticks_tir_err  | less          |           21 |   11.689 |            5.03  |         3.557 |     0.773 |     9.41  |         0.286 | 0.987 |
| tir    | hindsight_tir_err  | shape_tir_err   | less          |           21 |   11.689 |            9.804 |         0.062 |    -2.017 |     0.719 |         0.476 | 0.226 |
| tir    | live_tir_err       | stale_tir_err   | less          |           21 |   10.552 |            8.209 |         2.028 |    -0.371 |     4.988 |         0.333 | 0.979 |
| tir    | sticks_tir_err     | stale_tir_err   | less          |           21 |    5.03  |            8.209 |        -2.917 |    -8.31  |     0.401 |         0.619 | 0.054 |

By day since the sensor came off (RMSE against the hidden sensor, mg/dL):

|   day |   n_patients |   share_of_cohort |   control_rmse |   live_rmse |   hindsight_rmse |   abs_dmean |   share_moved |   hindsight_mean_err |
|------:|-------------:|------------------:|---------------:|------------:|-----------------:|------------:|--------------:|---------------------:|
|     1 |           21 |              1    |          31.65 |       26.38 |            20.91 |        8.4  |          0.36 |                 4.06 |
|     2 |           21 |              1    |          24.73 |       24.38 |            21.35 |        9.95 |          0.24 |                 7.88 |
|     3 |           21 |              1    |          27.97 |       25.39 |            23.44 |       13.68 |          0.31 |                 9.72 |
|     4 |           18 |              0.86 |          29.99 |       28.37 |            23.71 |       15.86 |          0.39 |                 9.39 |
|     5 |           16 |              0.76 |          29.35 |       27.92 |            24.83 |       12.9  |          0.44 |                10.79 |
|     6 |           13 |              0.62 |          25.78 |       25.29 |            22.2  |       15.3  |          0.38 |                 6.36 |
|     7 |           11 |              0.52 |          28.24 |       28.66 |            27.39 |       12.03 |          0.27 |                11.25 |
|     8 |           11 |              0.52 |          28.65 |       25.48 |            23.21 |        9.01 |          0.09 |                 6.51 |
|     9 |            9 |              0.43 |          24.63 |       24.17 |            23.78 |        8.93 |          0.11 |                 4.14 |
