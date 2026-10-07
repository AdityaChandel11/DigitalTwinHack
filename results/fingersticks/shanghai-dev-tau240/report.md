# Fingersticks after the sensor comes off

Filter: `{'tau_min': 240.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': False, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}`

Development patients. Not confirmatory.

`live` uses fingersticks stamped strictly before the minute being estimated; bar F1 is judged on it. `live_same_minute` may also read the fingerstick of that minute and carries no bar. Zone shares are medians over patients, so the five need not sum to 100.

## k = 3 days (primary)

|                              | all     |   2/day |   1/day |   every 2nd day |
|:-----------------------------|:--------|--------:|--------:|----------------:|
| n_patients                   | 24      |  24     |  24     |          24     |
| control_rmse                 | 36.01   |  36.01  |  36.01  |          36.01  |
| live_rmse                    | 34.89   |  36.59  |  36.73  |          36.78  |
| live_median_diff             | -0.44   |  -0.24  |   0.05  |           0.03  |
| live_diff_lo                 | -2.39   |  -1.27  |  -1.07  |          -0.55  |
| live_diff_hi                 | 0.24    |   0.35  |   0.42  |           0.24  |
| live_frac_better             | 0.62    |   0.62  |   0.46  |           0.5   |
| live_p                       | 0.03    |   0.099 |   0.21  |           0.25  |
| live_same_minute_rmse        | 34.10   |  36.59  |  36.74  |          36.79  |
| live_same_minute_median_diff | -0.77   |  -0.42  |   0.03  |          -0.01  |
| live_same_minute_diff_lo     | -3.23   |  -1.46  |  -1.09  |          -0.55  |
| live_same_minute_diff_hi     | -0.45   |   0.23  |   0.38  |           0.24  |
| live_same_minute_frac_better | 0.75    |   0.62  |   0.5   |           0.5   |
| live_same_minute_p           | 0.0075  |   0.057 |   0.18  |           0.2   |
| hindsight_rmse               | 30.94   |  35.22  |  36.57  |          36.69  |
| hindsight_median_diff        | -4.40   |  -1.44  |  -0.42  |          -0.21  |
| hindsight_diff_lo            | -6.57   |  -3.73  |  -2.13  |          -1.44  |
| hindsight_diff_hi            | -1.32   |   0.1   |  -0.02  |           0.21  |
| hindsight_frac_better        | 0.79    |   0.67  |   0.75  |           0.62  |
| hindsight_p                  | 1.8e-05 |   0.013 |   0.013 |           0.045 |
| sensor_mard                  | 11.83   |  11.83  |  11.83  |          11.83  |
| sensor_within15              | 74.64   |  74.64  |  74.64  |          74.64  |
| sensor_zone_a                | 82.15   |  82.15  |  82.15  |          82.15  |
| sensor_zone_b                | 13.88   |  13.88  |  13.88  |          13.88  |
| sensor_zone_c                | 0.00    |   0     |   0     |           0     |
| sensor_zone_d                | 0.00    |   0     |   0     |           0     |
| sensor_zone_e                | 0.00    |   0     |   0     |           0     |
| control_mard                 | 19.34   |  19.34  |  19.34  |          19.34  |
| control_within15             | 47.12   |  47.12  |  47.12  |          47.12  |
| control_zone_a               | 56.88   |  56.88  |  56.88  |          56.88  |
| control_zone_b               | 36.54   |  36.54  |  36.54  |          36.54  |
| control_zone_c               | 0.00    |   0     |   0     |           0     |
| control_zone_d               | 0.00    |   0     |   0     |           0     |
| control_zone_e               | 0.00    |   0     |   0     |           0     |
| live_mard                    | 20.10   |  19.28  |  19.38  |          19.42  |
| live_within15                | 42.93   |  47.12  |  47.12  |          47.6   |
| live_zone_a                  | 55.62   |  55.76  |  55.76  |          54.67  |
| live_zone_b                  | 40.31   |  40.83  |  40.65  |          41.33  |
| live_zone_c                  | 0.00    |   0     |   0     |           0     |
| live_zone_d                  | 0.00    |   0     |   0     |           0     |
| live_zone_e                  | 0.00    |   0     |   0     |           0     |
| f1_live_beats_control        | yes     |         |         |                 |
| f2_hindsight_beats_control   | yes     |         |         |                 |

Recordings scored: 25. Sensor map used: 18 (own slope); 5 (pooled slope); 2 (pooled map)

Recordings outside the cohort: 6 (fewer than two days after the split); 25 (fewer than one fingerstick a day)

## k = 5 days (reported, no bar)

|                              |      all |   2/day |   1/day |   every 2nd day |
|:-----------------------------|---------:|--------:|--------:|----------------:|
| n_patients                   | 20       |  20     |  20     |          20     |
| control_rmse                 | 32.55    |  32.55  |  32.55  |          32.55  |
| live_rmse                    | 33.15    |  33.17  |  33.24  |          33.45  |
| live_median_diff             | -0.06    |  -0.13  |   0.21  |           0.15  |
| live_diff_lo                 | -1.41    |  -0.87  |  -0.17  |          -0.3   |
| live_diff_hi                 |  1.16    |   1.14  |   0.55  |           0.36  |
| live_frac_better             |  0.5     |   0.55  |   0.4   |           0.4   |
| live_p                       |  0.27    |   0.45  |   0.65  |           0.64  |
| live_same_minute_rmse        | 32.96    |  32.95  |  33.23  |          33.45  |
| live_same_minute_median_diff | -0.43    |  -0.43  |   0.14  |           0.11  |
| live_same_minute_diff_lo     | -1.56    |  -1.01  |  -0.2   |          -0.35  |
| live_same_minute_diff_hi     |  0.45    |   1.01  |   0.53  |           0.34  |
| live_same_minute_frac_better |  0.55    |   0.55  |   0.4   |           0.4   |
| live_same_minute_p           |  0.14    |   0.36  |   0.64  |           0.55  |
| hindsight_rmse               | 29.54    |  31.57  |  32.75  |          33.2   |
| hindsight_median_diff        | -2.6     |  -0.77  |  -0.19  |          -0.16  |
| hindsight_diff_lo            | -3.29    |  -2.46  |  -1.17  |          -1.1   |
| hindsight_diff_hi            | -1.98    |   0.67  |   0.04  |           0.16  |
| hindsight_frac_better        |  0.75    |   0.55  |   0.7   |           0.6   |
| hindsight_p                  |  0.00084 |   0.082 |   0.032 |           0.082 |
| sensor_mard                  | 12.94    |  12.94  |  12.94  |          12.94  |
| sensor_within15              | 75.46    |  75.46  |  75.46  |          75.46  |
| sensor_zone_a                | 77.27    |  77.27  |  77.27  |          77.27  |
| sensor_zone_b                | 21.59    |  21.59  |  21.59  |          21.59  |
| sensor_zone_c                |  0       |   0     |   0     |           0     |
| sensor_zone_d                |  0       |   0     |   0     |           0     |
| sensor_zone_e                |  0       |   0     |   0     |           0     |
| control_mard                 | 19.66    |  19.66  |  19.66  |          19.66  |
| control_within15             | 41.25    |  41.25  |  41.25  |          41.25  |
| control_zone_a               | 56.77    |  56.77  |  56.77  |          56.77  |
| control_zone_b               | 41.39    |  41.39  |  41.39  |          41.39  |
| control_zone_c               |  0       |   0     |   0     |           0     |
| control_zone_d               |  0       |   0     |   0     |           0     |
| control_zone_e               |  0       |   0     |   0     |           0     |
| live_mard                    | 20.91    |  20.02  |  20.02  |          19.69  |
| live_within15                | 39.81    |  40.69  |  37.5   |          40.62  |
| live_zone_a                  | 57.08    |  56.88  |  56.88  |          56.17  |
| live_zone_b                  | 42.3     |  41.98  |  43.12  |          43.12  |
| live_zone_c                  |  0       |   0     |   0     |           0     |
| live_zone_d                  |  0       |   0     |   0     |           0     |
| live_zone_e                  |  0       |   0     |   0     |           0     |

Recordings scored: 21. Sensor map used: 16 (own slope); 4 (pooled slope); 1 (pooled map)

Recordings outside the cohort: 12 (fewer than two days after the split); 23 (fewer than one fingerstick a day)
