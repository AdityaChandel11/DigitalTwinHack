# Staleness alarm on real drift

Test recordings; thresholds were set on development recordings. Descriptive: no bar.

`score` is the cumulative sum of fingerstick surprises against the frozen profile; `early` is the same sum over the first two days after the sensor only; `plain` is the fingerstick average against the report's mean. Drift: the hidden sensor mean more than 20 mg/dL from the calibration mean. The label and the scores look back over the same hidden window.

## k = 3 days (primary)

32 recordings of 29 patients; 11 drifted (9 downwards). Thresholds from 17 development recordings without drift. Median 32 fingersticks in the hidden window.

| alarm   |   auroc |    lo |    hi |   threshold | caught   | false alarms   |   median days to alarm |
|:--------|--------:|------:|------:|------------:|:---------|:---------------|-----------------------:|
| score   |   0.818 | 0.628 | 0.976 |       5.407 | 7 of 11  | 2 of 21        |                  2.583 |
| early   |   0.835 | 0.662 | 0.975 |       2.299 | 8 of 11  | 4 of 21        |                nan     |
| plain   |   0.818 | 0.608 | 0.972 |      44.9   | 3 of 11  | 0 of 21        |                nan     |

AUROC difference, cumulative sum minus plain: 0.000 (-0.161 to 0.181); 2000 resamples used. AUROC of the number of fingersticks alone: 0.593 (0.376 to 0.797).

## k = 5 days (reported)

24 recordings of 21 patients; 6 drifted (6 downwards). Thresholds from 15 development recordings without drift. Median 25.5 fingersticks in the hidden window.

| alarm   |   auroc |    lo |    hi |   threshold | caught   | false alarms   |   median days to alarm |
|:--------|--------:|------:|------:|------------:|:---------|:---------------|-----------------------:|
| score   |   0.667 | 0.348 | 0.92  |       5.607 | 2 of 6   | 1 of 18        |                   2.88 |
| early   |   0.741 | 0.496 | 0.938 |       3.206 | 0 of 6   | 2 of 18        |                 nan    |
| plain   |   0.731 | 0.404 | 1     |      26.947 | 2 of 6   | 1 of 18        |                 nan    |

AUROC difference, cumulative sum minus plain: -0.065 (-0.487 to 0.300); 1998 resamples used. AUROC of the number of fingersticks alone: 0.491 (0.238 to 0.744).
