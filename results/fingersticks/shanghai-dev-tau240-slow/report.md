# Fingersticks after the sensor comes off

Filter: `{'tau_min': 240.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': True, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}`

Development patients. Not confirmatory.

`live` uses fingersticks stamped strictly before the minute being estimated; bar F1 is judged on it. `live_same_minute` may also read the fingerstick of that minute and carries no bar. Zone shares are medians over patients, so the five need not sum to 100.

## k = 3 days (primary)

|                              | all     |   2/day |   1/day |   every 2nd day |
|:-----------------------------|:--------|--------:|--------:|----------------:|
| n_patients                   | 24      |   24    |   24    |           24    |
| control_rmse                 | 36.01   |   36.01 |   36.01 |           36.01 |
| live_rmse                    | 34.49   |   35.41 |   38.23 |           37.66 |
| live_median_diff             | 0.39    |    0.18 |    0.54 |           -0.08 |
| live_diff_lo                 | -2.05   |   -2.01 |   -2.05 |           -2.39 |
| live_diff_hi                 | 2.41    |    2.91 |    2.25 |            2.07 |
| live_frac_better             | 0.46    |    0.46 |    0.46 |            0.54 |
| live_p                       | 0.43    |    0.47 |    0.39 |            0.39 |
| live_same_minute_rmse        | 34.38   |   35.33 |   38.25 |           37.69 |
| live_same_minute_median_diff | -0.36   |    0.02 |    0.49 |           -0.1  |
| live_same_minute_diff_lo     | -2.12   |   -2.06 |   -2.12 |           -2.44 |
| live_same_minute_diff_hi     | 1.40    |    2.64 |    2.23 |            2.05 |
| live_same_minute_frac_better | 0.58    |    0.5  |    0.46 |            0.54 |
| live_same_minute_p           | 0.22    |    0.44 |    0.38 |            0.37 |
| hindsight_rmse               | 30.80   |   34.15 |   36.55 |           38.54 |
| hindsight_median_diff        | -3.75   |   -0.79 |   -0.41 |           -0.32 |
| hindsight_diff_lo            | -5.32   |   -3.4  |   -4.31 |           -3.98 |
| hindsight_diff_hi            | -1.11   |    1.33 |    2.8  |            3.13 |
| hindsight_frac_better        | 0.79    |    0.54 |    0.54 |            0.62 |
| hindsight_p                  | 0.00048 |    0.18 |    0.21 |            0.21 |
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
| live_mard                    | 19.58   |   20.12 |   19.34 |           20.03 |
| live_within15                | 48.45   |   47.82 |   44.24 |           44.64 |
| live_zone_a                  | 60.87   |   56.33 |   57.52 |           55.28 |
| live_zone_b                  | 36.58   |   40.31 |   37.14 |           39.64 |
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
| live_rmse                    | 32.28  |   32.68 |   34.55 |           33.7  |
| live_median_diff             |  1.48  |    1.4  |    0.96 |            0.74 |
| live_diff_lo                 | -1.4   |   -0.91 |   -0.76 |           -0.97 |
| live_diff_hi                 |  2.59  |    3.85 |    2.29 |            1.84 |
| live_frac_better             |  0.35  |    0.35 |    0.4  |            0.4  |
| live_p                       |  0.75  |    0.8  |    0.77 |            0.74 |
| live_same_minute_rmse        | 32.1   |   32.6  |   34.54 |           33.69 |
| live_same_minute_median_diff |  0.94  |    1.08 |    0.95 |            0.73 |
| live_same_minute_diff_lo     | -1.61  |   -1.05 |   -0.77 |           -1    |
| live_same_minute_diff_hi     |  2.16  |    3.75 |    2.26 |            1.81 |
| live_same_minute_frac_better |  0.35  |    0.35 |    0.4  |            0.4  |
| live_same_minute_p           |  0.64  |    0.78 |    0.76 |            0.69 |
| hindsight_rmse               | 28.9   |   32.1  |   33.41 |           34.36 |
| hindsight_median_diff        | -1.88  |    0.96 |    0.77 |            1.24 |
| hindsight_diff_lo            | -4.14  |   -2.04 |   -1.15 |           -1.11 |
| hindsight_diff_hi            |  0.96  |    2.35 |    2.64 |            2.17 |
| hindsight_frac_better        |  0.65  |    0.45 |    0.4  |            0.4  |
| hindsight_p                  |  0.041 |    0.52 |    0.7  |            0.7  |
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
| live_mard                    | 21.01  |   20.57 |   20.15 |           20.29 |
| live_within15                | 43.61  |   50    |   46.09 |           42.72 |
| live_zone_a                  | 57.39  |   59.6  |   57.13 |           57.81 |
| live_zone_b                  | 37.5   |   37.23 |   38.96 |           39.44 |
| live_zone_c                  |  0     |    0    |    0    |            0    |
| live_zone_d                  |  0.91  |    0    |    0    |            0    |
| live_zone_e                  |  0     |    0    |    0    |            0    |

Recordings scored: 21. Sensor map used: 16 (own slope); 4 (pooled slope); 1 (pooled map)

Recordings outside the cohort: 12 (fewer than two days after the split); 23 (fewer than one fingerstick a day)
