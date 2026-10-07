# Fingersticks after the sensor comes off

Filter: `{'tau_min': 120.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': True, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}`

Development patients. Not confirmatory.

`live` uses fingersticks stamped strictly before the minute being estimated; bar F1 is judged on it. `live_same_minute` may also read the fingerstick of that minute and carries no bar. Zone shares are medians over patients, so the five need not sum to 100.

## k = 3 days (primary)

|                              | all     |   2/day |   1/day |   every 2nd day |
|:-----------------------------|:--------|--------:|--------:|----------------:|
| n_patients                   | 24      |   24    |   24    |           24    |
| control_rmse                 | 36.01   |   36.01 |   36.01 |           36.01 |
| live_rmse                    | 34.32   |   35.19 |   37.7  |           37.41 |
| live_median_diff             | -0.85   |   -0.15 |    0.29 |           -0.12 |
| live_diff_lo                 | -2.03   |   -1.97 |   -2.04 |           -2.36 |
| live_diff_hi                 | 1.44    |    2.39 |    1.96 |            2.37 |
| live_frac_better             | 0.58    |    0.54 |    0.46 |            0.54 |
| live_p                       | 0.17    |    0.36 |    0.34 |            0.38 |
| live_same_minute_rmse        | 34.01   |   35.13 |   37.71 |           37.44 |
| live_same_minute_median_diff | -1.13   |   -0.32 |    0.24 |           -0.14 |
| live_same_minute_diff_lo     | -2.13   |   -2.05 |   -2.08 |           -2.4  |
| live_same_minute_diff_hi     | 0.72    |    2.18 |    1.95 |            2.08 |
| live_same_minute_frac_better | 0.67    |    0.54 |    0.5  |            0.54 |
| live_same_minute_p           | 0.068   |    0.35 |    0.33 |            0.35 |
| hindsight_rmse               | 30.55   |   34.37 |   37.43 |           38.15 |
| hindsight_median_diff        | -3.65   |   -0.95 |   -0.5  |           -0.41 |
| hindsight_diff_lo            | -6.01   |   -3.45 |   -4    |           -3.9  |
| hindsight_diff_hi            | -1.41   |    1.34 |    2.7  |            2.77 |
| hindsight_frac_better        | 0.83    |    0.62 |    0.54 |            0.62 |
| hindsight_p                  | 0.00032 |    0.11 |    0.2  |            0.22 |
| sensor_mard                  | 11.83   |   11.83 |   11.83 |           11.83 |
| sensor_within15              | 74.64   |   74.64 |   74.64 |           74.64 |
| sensor_zone_a                | 82.15   |   82.15 |   82.15 |           82.15 |
| sensor_zone_b                | 13.88   |   13.88 |   13.88 |           13.88 |
| sensor_zone_c                | 0.00    |    0    |    0    |            0    |
| sensor_zone_d                | 0.00    |    0    |    0    |            0    |
| sensor_zone_e                | 0.00    |    0    |    0    |            0    |
| control_mard                 | 19.34   |   19.34 |   19.34 |           19.34 |
| control_within15             | 47.12   |   47.12 |   47.12 |           47.12 |
| control_zone_a               | 56.88   |   56.88 |   56.88 |           56.88 |
| control_zone_b               | 36.54   |   36.54 |   36.54 |           36.54 |
| control_zone_c               | 0.00    |    0    |    0    |            0    |
| control_zone_d               | 0.00    |    0    |    0    |            0    |
| control_zone_e               | 0.00    |    0    |    0    |            0    |
| live_mard                    | 19.53   |   20.15 |   19.08 |           19.97 |
| live_within15                | 47.46   |   47.72 |   44.24 |           44.64 |
| live_zone_a                  | 60.98   |   57.28 |   58.48 |           55.28 |
| live_zone_b                  | 35.88   |   40.31 |   37.71 |           39.64 |
| live_zone_c                  | 0.00    |    0    |    0    |            0    |
| live_zone_d                  | 0.71    |    0    |    1.96 |            0    |
| live_zone_e                  | 0.00    |    0    |    0    |            0    |
| f1_live_beats_control        | no      |         |         |                 |
| f2_hindsight_beats_control   | yes     |         |         |                 |

Recordings scored: 25. Sensor map used: 18 (own slope); 5 (pooled slope); 2 (pooled map)

Recordings outside the cohort: 6 (fewer than two days after the split); 25 (fewer than one fingerstick a day)

## k = 5 days (reported, no bar)

|                              |    all |   2/day |   1/day |   every 2nd day |
|:-----------------------------|-------:|--------:|--------:|----------------:|
| n_patients                   | 20     |   20    |   20    |           20    |
| control_rmse                 | 32.55  |   32.55 |   32.55 |           32.55 |
| live_rmse                    | 32.12  |   32.68 |   33.91 |           33.72 |
| live_median_diff             |  0.88  |    0.71 |    0.87 |            0.58 |
| live_diff_lo                 | -1.53  |   -1.01 |   -0.9  |           -1.06 |
| live_diff_hi                 |  1.6   |    2.87 |    1.96 |            1.67 |
| live_frac_better             |  0.35  |    0.4  |    0.4  |            0.4  |
| live_p                       |  0.61  |    0.73 |    0.75 |            0.65 |
| live_same_minute_rmse        | 31.95  |   32.6  |   33.93 |           33.71 |
| live_same_minute_median_diff |  0.54  |    0.61 |    0.86 |            0.57 |
| live_same_minute_diff_lo     | -1.74  |   -1.16 |   -0.91 |           -1.08 |
| live_same_minute_diff_hi     |  1.21  |    2.79 |    1.96 |            1.64 |
| live_same_minute_frac_better |  0.4   |    0.4  |    0.4  |            0.4  |
| live_same_minute_p           |  0.49  |    0.69 |    0.74 |            0.65 |
| hindsight_rmse               | 28.45  |   32.43 |   33.59 |           34.63 |
| hindsight_median_diff        | -2.53  |    0.51 |    0.51 |            1.03 |
| hindsight_diff_lo            | -4.43  |   -3.14 |   -1.05 |           -1.08 |
| hindsight_diff_hi            |  0.41  |    1.75 |    2.46 |            2.12 |
| hindsight_frac_better        |  0.65  |    0.45 |    0.4  |            0.45 |
| hindsight_p                  |  0.032 |    0.46 |    0.7  |            0.69 |
| sensor_mard                  | 12.94  |   12.94 |   12.94 |           12.94 |
| sensor_within15              | 75.46  |   75.46 |   75.46 |           75.46 |
| sensor_zone_a                | 77.27  |   77.27 |   77.27 |           77.27 |
| sensor_zone_b                | 21.59  |   21.59 |   21.59 |           21.59 |
| sensor_zone_c                |  0     |    0    |    0    |            0    |
| sensor_zone_d                |  0     |    0    |    0    |            0    |
| sensor_zone_e                |  0     |    0    |    0    |            0    |
| control_mard                 | 19.66  |   19.66 |   19.66 |           19.66 |
| control_within15             | 41.25  |   41.25 |   41.25 |           41.25 |
| control_zone_a               | 56.77  |   56.77 |   56.77 |           56.77 |
| control_zone_b               | 41.39  |   41.39 |   41.39 |           41.39 |
| control_zone_c               |  0     |    0    |    0    |            0    |
| control_zone_d               |  0     |    0    |    0    |            0    |
| control_zone_e               |  0     |    0    |    0    |            0    |
| live_mard                    | 21     |   20.12 |   20.19 |           19.89 |
| live_within15                | 46.9   |   50    |   44.79 |           42.72 |
| live_zone_a                  | 59.44  |   57.65 |   58.36 |           57.79 |
| live_zone_b                  | 39.17  |   39.44 |   38.54 |           38.54 |
| live_zone_c                  |  0     |    0    |    0    |            0    |
| live_zone_d                  |  0     |    0    |    0    |            0    |
| live_zone_e                  |  0     |    0    |    0    |            0    |

Recordings scored: 21. Sensor map used: 16 (own slope); 4 (pooled slope); 1 (pooled map)

Recordings outside the cohort: 12 (fewer than two days after the split); 23 (fewer than one fingerstick a day)
