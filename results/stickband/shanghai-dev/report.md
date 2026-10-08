# A band for the fingerstick estimate

Development patients: they choose the construction, so these figures are in-sample for that choice.

`live` is the estimate that reads fingersticks stamped strictly before each minute, as F1 was scored; `hindsight` reads every fingerstick of the hidden window. Both are on the sensor's scale, and coverage is the percent of hidden sensor readings inside the band, not of meter values. The patient is the unit. `filter` is the frozen filter's own spread; `patient` takes its width from the patient's spread about their daily shape in the calibration window. Nothing in either is fitted. Half-widths are in mg/dL. The construction that was not chosen is reported beside the chosen one.

## k = 3 days (primary)

25 recordings of 24 patients; 0 could not be given a band. Outside the cohort of section F: fewer than two days after the split: 6; fewer than one fingerstick a day: 25. Chosen on development patients at k = 3, on the live estimate: `patient` (0 development recordings could not be given a band).

| estimate   | band                |   mean coverage |   smallest |   largest | within 70 to 90   |   median half-width |
|:-----------|:--------------------|----------------:|-----------:|----------:|:------------------|--------------------:|
| live       | filter (not chosen) |            60.2 |       24.6 |      88.4 | 9 of 24           |                30.3 |
| live       | patient (chosen)    |            77.4 |       46.3 |      98.8 | 15 of 24          |                44.8 |
| hindsight  | filter (not chosen) |            62.1 |       22.2 |      86.9 | 9 of 24           |                28.1 |
| hindsight  | patient (chosen)    |            78.7 |       42.8 |      97.6 | 12 of 24          |                40   |

By day since the sensor (mean coverage over patients):

|   day |   patients |   share of cohort |   live filter (not chosen) |   live patient (chosen) |   hindsight filter (not chosen) |   hindsight patient (chosen) |
|------:|-----------:|------------------:|---------------------------:|------------------------:|--------------------------------:|-----------------------------:|
|     1 |         24 |              1    |                      62.83 |                   81.38 |                           66.75 |                        84.66 |
|     2 |         24 |              1    |                      63.93 |                   81.38 |                           63.98 |                        82.44 |
|     3 |         23 |              0.96 |                      64.65 |                   79.05 |                           65.61 |                        80.42 |
|     4 |         21 |              0.88 |                      58.13 |                   71.96 |                           59.29 |                        74.06 |
|     5 |         19 |              0.79 |                      68.41 |                   77.94 |                           68.74 |                        77.44 |
|     6 |         19 |              0.79 |                      61.8  |                   73.35 |                           61.69 |                        72.55 |
|     7 |         17 |              0.71 |                      62.29 |                   74.48 |                           63.54 |                        75.55 |
|     8 |         16 |              0.67 |                      63.49 |                   76.62 |                           63.02 |                        76.12 |
|     9 |         15 |              0.62 |                      62.35 |                   77.22 |                           64.07 |                        78.24 |
|    10 |         12 |              0.5  |                      61.32 |                   73.53 |                           60.75 |                        71.62 |
|    11 |          8 |              0.33 |                      55.56 |                   71.44 |                           53.6  |                        69.37 |

## k = 5 days (reported)

21 recordings of 20 patients; 0 could not be given a band. Outside the cohort of section F: fewer than two days after the split: 12; fewer than one fingerstick a day: 23. Chosen on development patients at k = 3, on the live estimate: `patient` (0 development recordings could not be given a band).

| estimate   | band                |   mean coverage |   smallest |   largest | within 70 to 90   |   median half-width |
|:-----------|:--------------------|----------------:|-----------:|----------:|:------------------|--------------------:|
| live       | filter (not chosen) |            63.8 |       32.7 |      89.8 | 8 of 20           |                30.3 |
| live       | patient (chosen)    |            79.7 |       46   |      94.1 | 15 of 20          |                40.8 |
| hindsight  | filter (not chosen) |            65.4 |       30.3 |      89.6 | 10 of 20          |                28.2 |
| hindsight  | patient (chosen)    |            80.3 |       38.2 |      94.7 | 13 of 20          |                36.7 |

By day since the sensor (mean coverage over patients):

|   day |   patients |   share of cohort |   live filter (not chosen) |   live patient (chosen) |   hindsight filter (not chosen) |   hindsight patient (chosen) |
|------:|-----------:|------------------:|---------------------------:|------------------------:|--------------------------------:|-----------------------------:|
|     1 |         20 |              1    |                      72.14 |                   83.7  |                           73.44 |                        84.79 |
|     2 |         20 |              1    |                      65.21 |                   81.22 |                           68.65 |                        82.99 |
|     3 |         19 |              0.95 |                      72.19 |                   82.77 |                           72.91 |                        82.9  |
|     4 |         19 |              0.95 |                      58.67 |                   75.03 |                           58.57 |                        75.36 |
|     5 |         17 |              0.85 |                      63.79 |                   77.6  |                           65.17 |                        77.27 |
|     6 |         16 |              0.8  |                      66.39 |                   82.82 |                           65.45 |                        81.56 |
|     7 |         15 |              0.75 |                      63.1  |                   80.45 |                           64.97 |                        82.32 |
|     8 |         12 |              0.6  |                      60.61 |                   73.72 |                           60.68 |                        72.53 |
|     9 |          8 |              0.4  |                      58.24 |                   75.94 |                           57.4  |                        73.42 |
