# Fingersticks after the sensor comes off

Filter: `{'tau_min': 60.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': True, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}`

Development patients. Not confirmatory.

`live` uses fingersticks stamped strictly before the minute being estimated; bar F1 is judged on it. `live_same_minute` may also read the fingerstick of that minute and carries no bar. Zone shares are medians over patients, so the five need not sum to 100.

## k = 3 days (primary)

|                              | all     |   2/day |   1/day |   every 2nd day |
|:-----------------------------|:--------|--------:|--------:|----------------:|
| n_patients                   | 24      |   24    |   24    |           24    |
| control_rmse                 | 36.01   |   36.01 |   36.01 |           36.01 |
| live_rmse                    | 34.15   |   35.13 |   37.35 |           37.29 |
| live_median_diff             | -0.94   |   -0.33 |    0.1  |           -0.15 |
| live_diff_lo                 | -2.05   |   -1.87 |   -2.08 |           -2.3  |
| live_diff_hi                 | 0.85    |    2.18 |    1.91 |            2.14 |
| live_frac_better             | 0.58    |    0.54 |    0.5  |            0.54 |
| live_p                       | 0.13    |    0.36 |    0.35 |            0.35 |
| live_same_minute_rmse        | 33.82   |   34.97 |   37.37 |           37.32 |
| live_same_minute_median_diff | -1.17   |   -0.45 |    0.05 |           -0.16 |
| live_same_minute_diff_lo     | -2.34   |   -1.94 |   -2.11 |           -2.35 |
| live_same_minute_diff_hi     | 0.29    |    1.99 |    1.9  |            2.21 |
| live_same_minute_frac_better | 0.71    |    0.54 |    0.5  |            0.54 |
| live_same_minute_p           | 0.048   |    0.33 |    0.34 |            0.35 |
| hindsight_rmse               | 31.40   |   34.43 |   37.92 |           37.96 |
| hindsight_median_diff        | -3.30   |   -1.02 |   -0.55 |           -0.45 |
| hindsight_diff_lo            | -5.54   |   -3.44 |   -3.85 |           -3.82 |
| hindsight_diff_hi            | -1.34   |    1.05 |    2.49 |            2.49 |
| hindsight_frac_better        | 0.79    |    0.62 |    0.54 |            0.62 |
| hindsight_p                  | 0.00042 |    0.1  |    0.2  |            0.23 |
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
| live_mard                    | 19.41   |   20.21 |   19.06 |           19.97 |
| live_within15                | 47.97   |   49.29 |   44.24 |           45.36 |
| live_zone_a                  | 58.40   |   57.27 |   58.94 |           55.28 |
| live_zone_b                  | 38.12   |   40.76 |   36.83 |           41.52 |
| live_zone_c                  | 0.00    |    0    |    0    |            0    |
| live_zone_d                  | 0.71    |    0    |    0.88 |            0    |
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
| live_rmse                    | 32.08  |   32.65 |   33.63 |           33.74 |
| live_median_diff             |  0.72  |    0.66 |    0.91 |            0.53 |
| live_diff_lo                 | -1.49  |   -1    |   -0.97 |           -1.08 |
| live_diff_hi                 |  1.26  |    2.47 |    1.82 |            1.61 |
| live_frac_better             |  0.35  |    0.4  |    0.4  |            0.4  |
| live_p                       |  0.54  |    0.73 |    0.71 |            0.65 |
| live_same_minute_rmse        | 31.87  |   32.59 |   33.66 |           33.73 |
| live_same_minute_median_diff |  0.2   |    0.54 |    0.87 |            0.52 |
| live_same_minute_diff_lo     | -1.71  |   -1.2  |   -0.98 |           -1.11 |
| live_same_minute_diff_hi     |  0.74  |    2.43 |    1.81 |            1.58 |
| live_same_minute_frac_better |  0.4   |    0.4  |    0.4  |            0.4  |
| live_same_minute_p           |  0.48  |    0.64 |    0.71 |            0.65 |
| hindsight_rmse               | 29.18  |   32.48 |   33.59 |           34.68 |
| hindsight_median_diff        | -2.48  |   -0.14 |    0.43 |            0.9  |
| hindsight_diff_lo            | -3.35  |   -3.03 |   -0.91 |           -1.12 |
| hindsight_diff_hi            |  0.07  |    1.87 |    2.36 |            1.97 |
| hindsight_frac_better        |  0.7   |    0.55 |    0.4  |            0.45 |
| hindsight_p                  |  0.035 |    0.39 |    0.7  |            0.69 |
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
| live_mard                    | 20.85  |   19.9  |   20.18 |           19.75 |
| live_within15                | 44.95  |   50    |   44.79 |           42.72 |
| live_zone_a                  | 61.04  |   58.11 |   57.45 |           57.79 |
| live_zone_b                  | 35.49  |   38.54 |   38.61 |           38.54 |
| live_zone_c                  |  0     |    0    |    0    |            0    |
| live_zone_d                  |  0     |    0    |    0    |            0    |
| live_zone_e                  |  0     |    0    |    0    |            0    |

Recordings scored: 21. Sensor map used: 16 (own slope); 4 (pooled slope); 1 (pooled map)

Recordings outside the cohort: 12 (fewer than two days after the split); 23 (fewer than one fingerstick a day)
