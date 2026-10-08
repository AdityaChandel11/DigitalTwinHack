# A band for the fingerstick estimate

Test patients, with the construction frozen on development patients (`patient`). Descriptive: no bar.

`live` is the estimate that reads fingersticks stamped strictly before each minute, as F1 was scored; `hindsight` reads every fingerstick of the hidden window. Both are on the sensor's scale, and coverage is the percent of hidden sensor readings inside the band, not of meter values. The patient is the unit. `filter` is the frozen filter's own spread; `patient` takes its width from the patient's spread about their daily shape in the calibration window. Nothing in either is fitted. Half-widths are in mg/dL. The construction that was not chosen is reported beside the chosen one.

## k = 3 days (primary)

32 recordings of 29 patients; 0 could not be given a band. Outside the cohort of section F: fewer than two days after the split: 3; fewer than three paired fingersticks after the split: 2; fewer than one fingerstick a day: 16. Chosen on development patients at k = 3, on the live estimate: `patient` (0 development recordings could not be given a band).

| estimate   | band                |   mean coverage |   smallest |   largest | within 70 to 90   |   median half-width |
|:-----------|:--------------------|----------------:|-----------:|----------:|:------------------|--------------------:|
| live       | filter (not chosen) |            61.8 |        0.8 |      94.5 | 11 of 29          |                29.3 |
| live       | patient (chosen)    |            83.6 |       49.9 |      98.9 | 12 of 29          |                47.6 |
| hindsight  | filter (not chosen) |            65.4 |        3.4 |      94.5 | 12 of 29          |                26   |
| hindsight  | patient (chosen)    |            86.1 |       56.7 |     100   | 14 of 29          |                44.6 |

By day since the sensor (mean coverage over patients):

|   day |   patients |   share of cohort |   live filter (not chosen) |   live patient (chosen) |   hindsight filter (not chosen) |   hindsight patient (chosen) |
|------:|-----------:|------------------:|---------------------------:|------------------------:|--------------------------------:|-----------------------------:|
|     1 |         29 |              1    |                      62.39 |                   86.93 |                           67.56 |                        88.78 |
|     2 |         29 |              1    |                      63.16 |                   85.61 |                           66.47 |                        87.88 |
|     3 |         27 |              0.93 |                      61.33 |                   84    |                           65.05 |                        86.43 |
|     4 |         23 |              0.79 |                      64.68 |                   81.87 |                           66.11 |                        84.18 |
|     5 |         21 |              0.72 |                      64.77 |                   83.74 |                           68.38 |                        85.78 |
|     6 |         18 |              0.62 |                      67.72 |                   82.19 |                           71.47 |                        86.24 |
|     7 |         16 |              0.55 |                      64.89 |                   79.8  |                           68.23 |                        83.46 |
|     8 |         13 |              0.45 |                      72.69 |                   80.18 |                           74.73 |                        83.05 |
|     9 |         11 |              0.38 |                      70.12 |                   80.4  |                           73.11 |                        80.97 |
|    10 |         11 |              0.38 |                      77.51 |                   86.02 |                           79.88 |                        86.26 |
|    11 |          9 |              0.31 |                      75.89 |                   87.99 |                           76.63 |                        89.5  |

## k = 5 days (reported)

24 recordings of 21 patients; 0 could not be given a band. Outside the cohort of section F: fewer than two days after the split: 12; fewer than three paired fingersticks after the split: 1; fewer than one fingerstick a day: 16. Chosen on development patients at k = 3, on the live estimate: `patient` (0 development recordings could not be given a band).

| estimate   | band                |   mean coverage |   smallest |   largest | within 70 to 90   |   median half-width |
|:-----------|:--------------------|----------------:|-----------:|----------:|:------------------|--------------------:|
| live       | filter (not chosen) |            68.7 |       26.4 |      94.7 | 9 of 21           |                29.7 |
| live       | patient (chosen)    |            85.5 |       66.2 |      99.1 | 12 of 21          |                44.5 |
| hindsight  | filter (not chosen) |            71.4 |       31.7 |      94.3 | 12 of 21          |                26.9 |
| hindsight  | patient (chosen)    |            87.2 |       73.2 |     100   | 11 of 21          |                40.9 |

By day since the sensor (mean coverage over patients):

|   day |   patients |   share of cohort |   live filter (not chosen) |   live patient (chosen) |   hindsight filter (not chosen) |   hindsight patient (chosen) |
|------:|-----------:|------------------:|---------------------------:|------------------------:|--------------------------------:|-----------------------------:|
|     1 |         21 |              1    |                      68.9  |                   87.65 |                           73.88 |                        89.29 |
|     2 |         21 |              1    |                      72.47 |                   87.1  |                           73.44 |                        88.22 |
|     3 |         21 |              1    |                      68.84 |                   86.35 |                           70.91 |                        87.54 |
|     4 |         18 |              0.86 |                      72.01 |                   85.46 |                           75.25 |                        88.17 |
|     5 |         16 |              0.76 |                      69.39 |                   82.95 |                           72.39 |                        85.8  |
|     6 |         13 |              0.62 |                      75.77 |                   83.63 |                           77.01 |                        84.74 |
|     7 |         11 |              0.52 |                      74.38 |                   80.92 |                           75.76 |                        81.49 |
|     8 |         11 |              0.52 |                      77.91 |                   86.04 |                           79.45 |                        85.55 |
|     9 |          9 |              0.43 |                      80.53 |                   88.81 |                           79.59 |                        88.09 |
