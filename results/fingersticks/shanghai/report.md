# Fingersticks after the sensor comes off

Filter: `{'tau_min': 120.0, 'fast_sd': 25.0, 'obs_sd': 15.0, 'slow': False, 'slow_sd_per_sqrt_day': 8.0, 'slow_sd0': 20.0}`

Confirmatory run on test patients.

`live` uses fingersticks stamped strictly before the minute being estimated; bar F1 is judged on it. `live_same_minute` may also read the fingerstick of that minute and carries no bar. Zone shares are medians over patients, so the five need not sum to 100.

## k = 3 days (primary)

|                              | all     |    2/day |    1/day |   every 2nd day |
|:-----------------------------|:--------|---------:|---------:|----------------:|
| n_patients                   | 29      | 29       | 29       |        29       |
| control_rmse                 | 36.71   | 36.71    | 36.71    |        36.71    |
| live_rmse                    | 32.11   | 36.65    | 36.45    |        36.87    |
| live_median_diff             | -2.79   | -0.79    | -0.32    |        -0.35    |
| live_diff_lo                 | -4.69   | -2.02    | -0.92    |        -0.81    |
| live_diff_hi                 | -1.60   | -0.25    | -0.03    |         0.03    |
| live_frac_better             | 0.86    |  0.76    |  0.69    |         0.66    |
| live_p                       | 3.8e-06 |  0.00013 |  0.0019  |         0.0084  |
| live_same_minute_rmse        | 30.74   | 36.51    | 36.37    |        36.86    |
| live_same_minute_median_diff | -3.95   | -0.99    | -0.57    |        -0.39    |
| live_same_minute_diff_lo     | -5.97   | -2.41    | -1.05    |        -0.93    |
| live_same_minute_diff_hi     | -2.27   | -0.4     | -0.12    |        -0.04    |
| live_same_minute_frac_better | 0.86    |  0.79    |  0.72    |         0.72    |
| live_same_minute_p           | 1.4e-06 |  5.5e-05 |  0.00044 |         0.0035  |
| hindsight_rmse               | 27.02   | 35.5     | 35.68    |        36.75    |
| hindsight_median_diff        | -9.50   | -2.27    | -1.12    |        -0.55    |
| hindsight_diff_lo            | -12.15  | -5.85    | -2.45    |        -1.82    |
| hindsight_diff_hi            | -4.56   | -1.17    | -0.56    |        -0.21    |
| hindsight_frac_better        | 0.93    |  0.93    |  0.86    |         0.76    |
| hindsight_p                  | 3.1e-07 |  6e-06   |  2.1e-05 |         0.00028 |
| sensor_mard                  | 11.51   | 11.51    | 11.51    |        11.51    |
| sensor_within15              | 71.93   | 71.93    | 71.93    |        71.93    |
| sensor_zone_a                | 84.85   | 84.85    | 84.85    |        84.85    |
| sensor_zone_b                | 13.33   | 13.33    | 13.33    |        13.33    |
| sensor_zone_c                | 0.00    |  0       |  0       |         0       |
| sensor_zone_d                | 0.00    |  0       |  0       |         0       |
| sensor_zone_e                | 0.00    |  0       |  0       |         0       |
| control_mard                 | 22.46   | 22.46    | 22.46    |        22.46    |
| control_within15             | 44.44   | 44.44    | 44.44    |        44.44    |
| control_zone_a               | 57.14   | 57.14    | 57.14    |        57.14    |
| control_zone_b               | 40.35   | 40.35    | 40.35    |        40.35    |
| control_zone_c               | 0.00    |  0       |  0       |         0       |
| control_zone_d               | 0.00    |  0       |  0       |         0       |
| control_zone_e               | 0.00    |  0       |  0       |         0       |
| live_mard                    | 21.79   | 22.29    | 22.28    |        22.43    |
| live_within15                | 46.67   | 45.33    | 45.33    |        45.33    |
| live_zone_a                  | 55.56   | 56       | 56       |        57.14    |
| live_zone_b                  | 41.33   | 43.1     | 43.1     |        41.33    |
| live_zone_c                  | 0.00    |  0       |  0       |         0       |
| live_zone_d                  | 0.00    |  0       |  0       |         0       |
| live_zone_e                  | 0.00    |  0       |  0       |         0       |
| f1_live_beats_control        | yes     |          |          |                 |
| f2_hindsight_beats_control   | yes     |          |          |                 |

Recordings scored: 32. Sensor map used: 26 (own slope); 4 (pooled slope); 2 (pooled map)

Recordings outside the cohort: 3 (fewer than two days after the split); 2 (fewer than three paired fingersticks after the split); 16 (fewer than one fingerstick a day)

## k = 5 days (reported, no bar)

|                              |       all |    2/day |    1/day |   every 2nd day |
|:-----------------------------|----------:|---------:|---------:|----------------:|
| n_patients                   |  21       | 21       | 21       |         21      |
| control_rmse                 |  30.99    | 30.99    | 30.99    |         30.99   |
| live_rmse                    |  27.47    | 30.17    | 30.81    |         30.81   |
| live_median_diff             |  -1.08    | -0.51    | -0.19    |         -0.05   |
| live_diff_lo                 |  -5.08    | -1.23    | -0.27    |         -0.39   |
| live_diff_hi                 |  -0.4     | -0.22    |  0.13    |          0.13   |
| live_frac_better             |   0.81    |  0.86    |  0.57    |          0.52   |
| live_p                       |   0.00015 |  0.00012 |  0.069   |          0.089  |
| live_same_minute_rmse        |  26.66    | 29.95    | 30.68    |         30.74   |
| live_same_minute_median_diff |  -1.89    | -0.69    | -0.3     |         -0.07   |
| live_same_minute_diff_lo     |  -6.27    | -1.5     | -0.46    |         -0.48   |
| live_same_minute_diff_hi     |  -0.61    | -0.37    |  0.07    |          0.06   |
| live_same_minute_frac_better |   0.86    |  0.86    |  0.57    |          0.57   |
| live_same_minute_p           |   1.2e-05 |  4.2e-05 |  0.027   |          0.048  |
| hindsight_rmse               |  23.98    | 27.59    | 29.58    |         30.14   |
| hindsight_median_diff        |  -5.7     | -1.49    | -0.59    |         -0.3    |
| hindsight_diff_lo            | -11.04    | -3.66    | -1.83    |         -0.98   |
| hindsight_diff_hi            |  -2.42    | -1       |  0.01    |         -0.04   |
| hindsight_frac_better        |   0.95    |  0.95    |  0.67    |          0.71   |
| hindsight_p                  |   1.4e-06 |  4.8e-06 |  0.00069 |          0.0019 |
| sensor_mard                  |  12.56    | 12.56    | 12.56    |         12.56   |
| sensor_within15              |  66.67    | 66.67    | 66.67    |         66.67   |
| sensor_zone_a                |  84.21    | 84.21    | 84.21    |         84.21   |
| sensor_zone_b                |  15.79    | 15.79    | 15.79    |         15.79   |
| sensor_zone_c                |   0       |  0       |  0       |          0      |
| sensor_zone_d                |   0       |  0       |  0       |          0      |
| sensor_zone_e                |   0       |  0       |  0       |          0      |
| control_mard                 |  22.3     | 22.3     | 22.3     |         22.3    |
| control_within15             |  44.44    | 44.44    | 44.44    |         44.44   |
| control_zone_a               |  55.56    | 55.56    | 55.56    |         55.56   |
| control_zone_b               |  42.11    | 42.11    | 42.11    |         42.11   |
| control_zone_c               |   0       |  0       |  0       |          0      |
| control_zone_d               |   0       |  0       |  0       |          0      |
| control_zone_e               |   0       |  0       |  0       |          0      |
| live_mard                    |  20.8     | 21.84    | 21.99    |         22.08   |
| live_within15                |  46.67    | 45.16    | 45.16    |         45      |
| live_zone_a                  |  57.14    | 55.56    | 55.56    |         55.56   |
| live_zone_b                  |  41.33    | 42.11    | 42.11    |         42.11   |
| live_zone_c                  |   0       |  0       |  0       |          0      |
| live_zone_d                  |   0       |  0       |  0       |          0      |
| live_zone_e                  |   0       |  0       |  0       |          0      |

Recordings scored: 24. Sensor map used: 23 (own slope); 1 (pooled slope)

Recordings outside the cohort: 12 (fewer than two days after the split); 1 (fewer than three paired fingersticks after the split); 16 (fewer than one fingerstick a day)
