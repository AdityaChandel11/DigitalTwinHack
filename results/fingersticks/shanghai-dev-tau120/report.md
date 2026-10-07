# Fingersticks after the sensor comes off

Filter: `{'tau_min': 120.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': False, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}`

Development patients. Not confirmatory.

`live` uses fingersticks stamped strictly before the minute being estimated; bar F1 is judged on it. `live_same_minute` may also read the fingerstick of that minute and carries no bar. Zone shares are medians over patients, so the five need not sum to 100.

## k = 3 days (primary)

|                              | all     |    2/day |   1/day |   every 2nd day |
|:-----------------------------|:--------|---------:|--------:|----------------:|
| n_patients                   | 24      | 24       | 24      |         24      |
| control_rmse                 | 36.01   | 36.01    | 36.01   |         36.01   |
| live_rmse                    | 35.25   | 36.17    | 36.57   |         36.58   |
| live_median_diff             | -1.19   | -0.26    | -0.04   |          0.02   |
| live_diff_lo                 | -2.66   | -1.19    | -0.28   |         -0.22   |
| live_diff_hi                 | -0.37   | -0.06    |  0.18   |          0.1    |
| live_frac_better             | 0.75    |  0.71    |  0.54   |          0.5    |
| live_p                       | 0.00079 |  0.012   |  0.17   |          0.2    |
| live_same_minute_rmse        | 34.32   | 36.18    | 36.58   |         36.61   |
| live_same_minute_median_diff | -1.44   | -0.46    | -0.07   |         -0.01   |
| live_same_minute_diff_lo     | -3.59   | -1.35    | -0.31   |         -0.26   |
| live_same_minute_diff_hi     | -0.63   | -0.08    |  0.17   |          0.09   |
| live_same_minute_frac_better | 0.79    |  0.75    |  0.58   |          0.5    |
| live_same_minute_p           | 7.5e-05 |  0.0036  |  0.13   |          0.15   |
| hindsight_rmse               | 31.43   | 36.09    | 36.53   |         36.59   |
| hindsight_median_diff        | -3.69   | -1.11    | -0.41   |         -0.15   |
| hindsight_diff_lo            | -7.30   | -2.91    | -0.81   |         -0.82   |
| hindsight_diff_hi            | -2.05   | -0.4     | -0.15   |          0.03   |
| hindsight_frac_better        | 0.83    |  0.79    |  0.75   |          0.67   |
| hindsight_p                  | 4.2e-06 |  0.00028 |  0.0058 |          0.0097 |
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
| live_mard                    | 19.40   | 19.26    | 19.3    |         19.33   |
| live_within15                | 45.33   | 47.76    | 47.12   |         47.12   |
| live_zone_a                  | 58.09   | 57.97    | 57.97   |         56.88   |
| live_zone_b                  | 40.65   | 39.3     | 39.29   |         38.42   |
| live_zone_c                  | 0.00    |  0       |  0      |          0      |
| live_zone_d                  | 0.00    |  0       |  0      |          0      |
| live_zone_e                  | 0.00    |  0       |  0      |          0      |
| f1_live_beats_control        | yes     |          |         |                 |
| f2_hindsight_beats_control   | yes     |          |         |                 |

Recordings scored: 25. Sensor map used: 18 (own slope); 5 (pooled slope); 2 (pooled map)

Recordings outside the cohort: 6 (fewer than two days after the split); 25 (fewer than one fingerstick a day)

## k = 5 days (reported, no bar)

|                              |      all |   2/day |    1/day |   every 2nd day |
|:-----------------------------|---------:|--------:|---------:|----------------:|
| n_patients                   | 20       | 20      | 20       |         20      |
| control_rmse                 | 32.55    | 32.55   | 32.55    |         32.55   |
| live_rmse                    | 32.56    | 32.89   | 32.84    |         32.9    |
| live_median_diff             | -0.62    | -0.23   | -0.01    |         -0      |
| live_diff_lo                 | -1.16    | -0.75   | -0.11    |         -0.19   |
| live_diff_hi                 |  0.12    |  0.38   |  0.2     |          0.19   |
| live_frac_better             |  0.65    |  0.55   |  0.55    |          0.5    |
| live_p                       |  0.012   |  0.12   |  0.43    |          0.42   |
| live_same_minute_rmse        | 32.26    | 32.87   | 32.87    |         32.94   |
| live_same_minute_median_diff | -0.98    | -0.37   | -0.01    |         -0.01   |
| live_same_minute_diff_lo     | -1.66    | -0.95   | -0.17    |         -0.24   |
| live_same_minute_diff_hi     | -0.49    |  0.17   |  0.15    |          0.14   |
| live_same_minute_frac_better |  0.75    |  0.55   |  0.55    |          0.5    |
| live_same_minute_p           |  0.0012  |  0.053  |  0.27    |          0.3    |
| hindsight_rmse               | 29.65    | 31.85   | 32.87    |         32.95   |
| hindsight_median_diff        | -2.7     | -0.74   | -0.29    |         -0.23   |
| hindsight_diff_lo            | -4.23    | -2.08   | -0.78    |         -0.7    |
| hindsight_diff_hi            | -1.65    | -0.34   | -0.21    |         -0      |
| hindsight_frac_better        |  0.9     |  0.8    |  0.8     |          0.75   |
| hindsight_p                  |  6.7e-05 |  0.0016 |  0.00043 |          0.0086 |
| sensor_mard                  | 12.94    | 12.94   | 12.94    |         12.94   |
| sensor_within15              | 75.46    | 75.46   | 75.46    |         75.46   |
| sensor_zone_a                | 77.27    | 77.27   | 77.27    |         77.27   |
| sensor_zone_b                | 21.59    | 21.59   | 21.59    |         21.59   |
| sensor_zone_c                |  0       |  0      |  0       |          0      |
| sensor_zone_d                |  0       |  0      |  0       |          0      |
| sensor_zone_e                |  0       |  0      |  0       |          0      |
| control_mard                 | 19.66    | 19.66   | 19.66    |         19.66   |
| control_within15             | 41.25    | 41.25   | 41.25    |         41.25   |
| control_zone_a               | 56.77    | 56.77   | 56.77    |         56.77   |
| control_zone_b               | 41.39    | 41.39   | 41.39    |         41.39   |
| control_zone_c               |  0       |  0      |  0       |          0      |
| control_zone_d               |  0       |  0      |  0       |          0      |
| control_zone_e               |  0       |  0      |  0       |          0      |
| live_mard                    | 19.93    | 19.74   | 19.75    |         19.69   |
| live_within15                | 42.5     | 42.08   | 42.08    |         41.25   |
| live_zone_a                  | 56.88    | 55.9    | 55.62    |         55.62   |
| live_zone_b                  | 43.12    | 44.1    | 44.1     |         44.1    |
| live_zone_c                  |  0       |  0      |  0       |          0      |
| live_zone_d                  |  0       |  0      |  0       |          0      |
| live_zone_e                  |  0       |  0      |  0       |          0      |

Recordings scored: 21. Sensor map used: 16 (own slope); 4 (pooled slope); 1 (pooled map)

Recordings outside the cohort: 12 (fewer than two days after the split); 23 (fewer than one fingerstick a day)
