# Expiry: patients recorded again (case series)

The first wear's daily shape against the later wear. `fresh_profile_rmse` is what a new wear's own shape gives. A case series of a handful of patients under changing treatment: no test, no interval.

Development patients only. Not confirmatory.

3 later wears of 3 patients. The table has one row per later wear, and the counts and medians in the summary are over wears: a patient recorded three times has two.

| patient_id    | dev   | later_rec                |   days_between_starts |   days_since_first_sensor |   first_wear_days |   later_wear_days |   old_profile_rmse |   fresh_profile_rmse |   first_wear_rmse |   dmean |   abs_dmean |   moved |   abs_dtar |   abs_dtir | insulin_first   | insulin_later   | pump_first   | pump_later   | agents_changed   |
|:--------------|:------|:-------------------------|----------------------:|--------------------------:|------------------:|------------------:|-------------------:|---------------------:|------------------:|--------:|------------:|--------:|-----------:|-----------:|:----------------|:----------------|:-------------|:-------------|:-----------------|
| shanghai-2017 | True  | shanghai-2017_0_20210102 |                    47 |                      33.1 |              13.9 |              13.9 |               35.9 |                 35.5 |              33.2 |    -0.1 |         0.1 |       0 |        2.5 |        2.6 | True            | True            | False        | False        | False            |
| shanghai-2055 | True  | shanghai-2055_0_20210524 |                   168 |                     154.1 |              13.9 |              10.9 |               21.1 |                 21.4 |              21.8 |     1   |         1   |       0 |        1.3 |        1.3 | False           | False           | False        | False        | True             |
| shanghai-2078 | True  | shanghai-2078_1_20210817 |                    14 |                       0.1 |              13.9 |              13.9 |               32.5 |                 21   |              31   |   -25.1 |        25.1 |       1 |        9.2 |        9.1 | False           | True            | False        | True         | True             |
