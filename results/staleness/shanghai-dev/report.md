# Staleness alarm on real drift

Development recordings: the thresholds are set on these same recordings, so this is in-sample.

`score` is the cumulative sum of fingerstick surprises against the frozen profile; `early` is the same sum over the first two days after the sensor only; `plain` is the fingerstick average against the report's mean. Drift: the hidden sensor mean more than 20 mg/dL from the calibration mean. The label and the scores look back over the same hidden window.

## k = 3 days (primary)

25 recordings of 24 patients; 8 drifted (7 downwards). Thresholds from 17 development recordings without drift. Median 32 fingersticks in the hidden window.

| alarm   |   auroc |    lo |    hi |   threshold | caught   | false alarms   |   median days to alarm |
|:--------|--------:|------:|------:|------------:|:---------|:---------------|-----------------------:|
| score   |   0.721 | 0.446 | 0.953 |       5.407 | 4 of 8   | 1 of 17        |                  1.885 |
| early   |   0.757 | 0.471 | 0.969 |       2.299 | 5 of 8   | 1 of 17        |                nan     |
| plain   |   0.728 | 0.438 | 0.958 |      44.9   | 3 of 8   | 1 of 17        |                nan     |

AUROC difference, cumulative sum minus plain: -0.007 (-0.250 to 0.229); 1999 resamples used. AUROC of the number of fingersticks alone: 0.559 (0.317 to 0.782).

## k = 5 days (reported)

21 recordings of 20 patients; 6 drifted (6 downwards). Thresholds from 15 development recordings without drift. Median 22 fingersticks in the hidden window.

| alarm   |   auroc |    lo |    hi |   threshold | caught   | false alarms   |   median days to alarm |
|:--------|--------:|------:|------:|------------:|:---------|:---------------|-----------------------:|
| score   |   0.744 | 0.463 | 0.944 |       5.607 | 1 of 6   | 1 of 15        |                  4.646 |
| early   |   0.667 | 0.377 | 0.92  |       3.206 | 0 of 6   | 1 of 15        |                nan     |
| plain   |   0.789 | 0.571 | 0.97  |      26.947 | 1 of 6   | 1 of 15        |                nan     |

AUROC difference, cumulative sum minus plain: -0.044 (-0.347 to 0.209); 1998 resamples used. AUROC of the number of fingersticks alone: 0.478 (0.161 to 0.806).
