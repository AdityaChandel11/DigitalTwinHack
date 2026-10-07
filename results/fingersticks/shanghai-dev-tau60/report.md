# Fingersticks after the sensor comes off

Filter: `{'tau_min': 60.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': False, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}`

Development patients. Not confirmatory.

`live` uses fingersticks stamped strictly before the minute being estimated; bar F1 is judged on it. `live_same_minute` may also read the fingerstick of that minute and carries no bar. Zone shares are medians over patients, so the five need not sum to 100.

## k = 3 days (primary)

|                              | all     |    2/day |   1/day |   every 2nd day |
|:-----------------------------|:--------|---------:|--------:|----------------:|
| n_patients                   | 24      | 24       | 24      |         24      |
| control_rmse                 | 36.01   | 36.01    | 36.01   |         36.01   |
| live_rmse                    | 35.55   | 36       | 36.23   |         36.24   |
| live_median_diff             | -0.94   | -0.27    | -0.04   |         -0.02   |
| live_diff_lo                 | -2.44   | -0.7     | -0.15   |         -0.15   |
| live_diff_hi                 | -0.45   | -0.08    | -0      |          0.04   |
| live_frac_better             | 0.79    |  0.79    |  0.71   |          0.58   |
| live_p                       | 1.2e-05 |  0.00048 |  0.054  |          0.094  |
| live_same_minute_rmse        | 35.44   | 36.01    | 36.29   |         36.31   |
| live_same_minute_median_diff | -1.47   | -0.47    | -0.06   |         -0.04   |
| live_same_minute_diff_lo     | -3.34   | -0.9     | -0.23   |         -0.2    |
| live_same_minute_diff_hi     | -0.73   | -0.18    | -0.03   |          0.01   |
| live_same_minute_frac_better | 0.88    |  0.83    |  0.75   |          0.58   |
| live_same_minute_p           | 1.1e-06 |  5.4e-05 |  0.018  |          0.035  |
| hindsight_rmse               | 33.08   | 35.93    | 36.43   |         36.51   |
| hindsight_median_diff        | -3.39   | -0.99    | -0.27   |         -0.16   |
| hindsight_diff_lo            | -6.14   | -2.21    | -0.6    |         -0.5    |
| hindsight_diff_hi            | -1.57   | -0.47    | -0.15   |         -0.02   |
| hindsight_frac_better        | 0.96    |  0.88    |  0.79   |          0.79   |
| hindsight_p                  | 1.8e-07 |  2.6e-06 |  0.0007 |          0.0036 |
| sensor_mard                  | 11.83   | 11.83    | 11.83   |         11.83   |
| sensor_within15              | 74.64   | 74.64    | 74.64   |         74.64   |
| sensor_zone_a                | 82.15   | 82.15    | 82.15   |         82.15   |
| sensor_zone_b                | 13.88   | 13.88    | 13.88   |         13.88   |
| sensor_zone_c                | 0.00    |  0       |  0      |          0      |
| sensor_zone_d                | 0.00    |  0       |  0      |          0      |
| sensor_zone_e                | 0.00    |  0       |  0      |          0      |
| control_mard                 | 19.34   | 19.34    | 19.34   |         19.34   |
| control_within15             | 47.12   | 47.12    | 47.12   |         47.12   |
| control_zone_a               | 56.88   | 56.88    | 56.88   |         56.88   |
| control_zone_b               | 36.54   | 36.54    | 36.54   |         36.54   |
| control_zone_c               | 0.00    |  0       |  0      |          0      |
| control_zone_d               | 0.00    |  0       |  0      |          0      |
| control_zone_e               | 0.00    |  0       |  0      |          0      |
| live_mard                    | 19.20   | 19.33    | 19.33   |         19.33   |
| live_within15                | 48.68   | 47.12    | 47.12   |         47.12   |
| live_zone_a                  | 57.97   | 56.88    | 56.88   |         56.88   |
| live_zone_b                  | 35.97   | 36.54    | 36.54   |         36.54   |
| live_zone_c                  | 0.00    |  0       |  0      |          0      |
| live_zone_d                  | 0.00    |  0       |  0      |          0      |
| live_zone_e                  | 0.00    |  0       |  0      |          0      |
| f1_live_beats_control        | yes     |          |         |                 |
| f2_hindsight_beats_control   | yes     |          |         |                 |

Recordings scored: 25. Sensor map used: 18 (own slope); 5 (pooled slope); 2 (pooled map)

Recordings outside the cohort: 6 (fewer than two days after the split); 25 (fewer than one fingerstick a day)

## k = 5 days (reported, no bar)

|                              |      all |    2/day |    1/day |   every 2nd day |
|:-----------------------------|---------:|---------:|---------:|----------------:|
| n_patients                   | 20       | 20       | 20       |        20       |
| control_rmse                 | 32.55    | 32.55    | 32.55    |        32.55    |
| live_rmse                    | 32.73    | 32.72    | 32.5     |        32.51    |
| live_median_diff             | -0.62    | -0.18    | -0.06    |        -0.04    |
| live_diff_lo                 | -1.28    | -0.47    | -0.14    |        -0.15    |
| live_diff_hi                 | -0.41    | -0.03    | -0.02    |         0.02    |
| live_frac_better             |  0.85    |  0.7     |  0.75    |         0.65    |
| live_p                       |  0.00013 |  0.0047  |  0.038   |         0.11    |
| live_same_minute_rmse        | 32.56    | 32.57    | 32.5     |        32.54    |
| live_same_minute_median_diff | -1.18    | -0.4     | -0.11    |        -0.07    |
| live_same_minute_diff_lo     | -2       | -0.64    | -0.22    |        -0.18    |
| live_same_minute_diff_hi     | -0.62    | -0.09    | -0.04    |        -0       |
| live_same_minute_frac_better |  0.9     |  0.8     |  0.8     |         0.75    |
| live_same_minute_p           |  4.1e-05 |  0.00084 |  0.0053  |         0.027   |
| hindsight_rmse               | 31.59    | 32.21    | 32.53    |        32.59    |
| hindsight_median_diff        | -2.38    | -1.03    | -0.25    |        -0.18    |
| hindsight_diff_lo            | -4.24    | -1.37    | -0.72    |        -0.47    |
| hindsight_diff_hi            | -1.15    | -0.49    | -0.16    |        -0.04    |
| hindsight_frac_better        |  0.95    |  0.9     |  0.9     |         0.85    |
| hindsight_p                  |  4.8e-06 |  4.1e-05 |  0.00013 |         0.00099 |
| sensor_mard                  | 12.94    | 12.94    | 12.94    |        12.94    |
| sensor_within15              | 75.46    | 75.46    | 75.46    |        75.46    |
| sensor_zone_a                | 77.27    | 77.27    | 77.27    |        77.27    |
| sensor_zone_b                | 21.59    | 21.59    | 21.59    |        21.59    |
| sensor_zone_c                |  0       |  0       |  0       |         0       |
| sensor_zone_d                |  0       |  0       |  0       |         0       |
| sensor_zone_e                |  0       |  0       |  0       |         0       |
| control_mard                 | 19.66    | 19.66    | 19.66    |        19.66    |
| control_within15             | 41.25    | 41.25    | 41.25    |        41.25    |
| control_zone_a               | 56.77    | 56.77    | 56.77    |        56.77    |
| control_zone_b               | 41.39    | 41.39    | 41.39    |        41.39    |
| control_zone_c               |  0       |  0       |  0       |         0       |
| control_zone_d               |  0       |  0       |  0       |         0       |
| control_zone_e               |  0       |  0       |  0       |         0       |
| live_mard                    | 19.4     | 19.71    | 19.71    |        19.7     |
| live_within15                | 42.5     | 40.42    | 40.42    |        40.42    |
| live_zone_a                  | 58.75    | 56.77    | 56.77    |        56.77    |
| live_zone_b                  | 40       | 40.97    | 40.97    |        41.39    |
| live_zone_c                  |  0       |  0       |  0       |         0       |
| live_zone_d                  |  0       |  0       |  0       |         0       |
| live_zone_e                  |  0       |  0       |  0       |         0       |

Recordings scored: 21. Sensor map used: 16 (own slope); 4 (pooled slope); 1 (pooled map)

Recordings outside the cohort: 12 (fewer than two days after the split); 23 (fewer than one fingerstick a day)
