# Band recalibration

Development patients: the factor is chosen here, so its coverage below is in-sample.

Design: one factor, 0.78. On development patients left out of the fit, distance of each day's coverage from 80 %: {'single': 0.029746450993870632, 'by_day': 0.0019940638892283367}; patients within 70 to 90 %: {'single': 17, 'by_day': 14}.

## k = 5 days (25 patients)

| band   |   mean_coverage |   min |   max |   patients_within |
|:-------|----------------:|------:|------:|------------------:|
| before |           0.874 | 0.505 | 0.986 |                14 |
| after  |           0.802 | 0.382 | 0.957 |                17 |

|   day |   n_patients |   before |   after |
|------:|-------------:|---------:|--------:|
|     1 |           25 |    0.882 |   0.806 |
|     2 |           24 |    0.891 |   0.818 |
|     3 |           24 |    0.901 |   0.84  |
|     4 |           24 |    0.893 |   0.838 |
|     5 |           23 |    0.92  |   0.853 |
|     6 |           12 |    0.761 |   0.688 |
|     7 |            6 |    0.782 |   0.717 |

## k = 3 days (25 patients)

| band   |   mean_coverage |   min |   max |   patients_within |
|:-------|----------------:|------:|------:|------------------:|
| before |           0.867 | 0.642 | 0.992 |                14 |
| after  |           0.796 | 0.526 | 0.987 |                16 |

|   day |   n_patients |   before |   after |
|------:|-------------:|---------:|--------:|
|     1 |           25 |    0.886 |   0.826 |
|     2 |           25 |    0.878 |   0.799 |
|     3 |           25 |    0.852 |   0.768 |
|     4 |           24 |    0.87  |   0.795 |
|     5 |           24 |    0.899 |   0.845 |
|     6 |           24 |    0.892 |   0.838 |
|     7 |           23 |    0.913 |   0.846 |
|     8 |           12 |    0.739 |   0.682 |
|     9 |            6 |    0.745 |   0.703 |
