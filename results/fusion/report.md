# The record as the prior

P1 (record prior helps at k = 1): **NOT PASSED**

|   k_days |   n_patients |   twin_record |   twin_population |   twin_median_diff |   twin_frac_record_better |   twin_p |   ode_record |   ode_population |   ode_median_diff |   ode_frac_record_better |   ode_p |
|---------:|-------------:|--------------:|------------------:|-------------------:|--------------------------:|---------:|-------------:|-----------------:|------------------:|-------------------------:|--------:|
|        1 |           20 |        30.318 |            30.795 |             -0.022 |                     0.65  |    0.156 |       29.91  |           31.994 |            -0.084 |                    0.75  |   0.029 |
|        3 |           19 |        23.802 |            23.793 |             -0     |                     0.579 |    0.187 |       24.231 |           24.21  |            -0.007 |                    0.579 |   0.113 |
|        5 |           19 |        21.945 |            21.669 |             -0.001 |                     0.632 |    0.078 |       23.267 |           23.269 |            -0.007 |                    0.632 |   0.044 |
|        7 |           18 |        22.008 |            22.005 |             -0     |                     0.556 |    0.351 |       23.234 |           23.213 |            -0.002 |                    0.611 |   0.234 |

Sensor days the population prior needs to match the record prior at k = 1: 3

This figure is not a number of sensor days saved: at k = 1 the two priors are not distinguishable patient by patient (see `twin_median_diff` and `twin_p`).
