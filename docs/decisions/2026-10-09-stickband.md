# A band for the fingerstick estimate: the pass over held-out patients (9 Oct 2026)

Descriptive, no bar. Registered in the note to Amendment 3 of 8 Oct ("a band for the fingerstick estimate")
and its addendum, which froze the construction on development patients before this pass. Run once:
`python -m chhaya.eval.stickband --confirm`, results in `results/stickband/shanghai/`.

## What this is

The estimates of section F (live, and in hindsight) had no band. The band is the frozen filter's own spread
at each minute, which depends on when fingersticks were taken and on no reading, with its width taken from
the patient's own spread about their daily shape during the sensor wear (`patient` construction). Nothing is
fitted. Coverage is the percent of hidden sensor readings inside the band; the patient is the unit.

## Held-out patients

| k | estimate | mean coverage | smallest to largest patient | within 70 to 90 % | median half-width |
|---|---|---|---|---|---|
| 3 (32 recordings, 29 patients) | live | 83.6 % | 49.9 to 98.9 | 12 of 29 | 47.6 mg/dL |
| 3 | in hindsight | 86.1 % | 56.7 to 100 | 14 of 29 | 44.6 mg/dL |
| 5 (24 recordings, 21 patients) | live | 85.5 % | 66.2 to 99.1 | 12 of 21 | 44.5 mg/dL |
| 5 | in hindsight | 87.2 % | 73.2 to 100 | 11 of 21 | 40.9 mg/dL |

No recording failed. The construction that was not chosen (the filter's spread as it is, about 29 mg/dL each
side) held 61.8 % live and 65.4 % in hindsight at k = 3, and as little as 0.8 % for one patient. Coverage by
day is in `results/stickband/shanghai/report.md`.

## What it means

- **The band is honest on average and wide.** It holds a little more than the 80 % it is named for (83.6 %
  on development patients it was 77.4 %), and it is about 45 mg/dL each side: it says the fingerstick estimate
  is a rough one.
- **It is not calibrated per patient.** One patient in the cohort has half of their readings outside it;
  fewer than half of the patients fall within 70 to 90 %. The same was true of the Gate 2 band.
- **The filter's own model of its error is too narrow**, by about a third: the estimate's error is larger
  than the filter assumes.

## What a reader should weigh

- Supervised care, one country, about six fingersticks a day, at most eleven days, 29 patients.
- The construction was chosen on 24 development patients between two candidates; the held-out figure is
  higher than the development one, so the choice did not flatter it.
- The same sensor is the yardstick. Nothing is checked against laboratory glucose.
- A band on the sensor's scale: it is not a band on meter values.

## Consequences for the product

By the rule fixed in the note (mean within 70 to 90 %), the band is drawn on Shanghai patients' estimated
trace and may be called an 80 % band. The trace drawn for days already past is the in-hindsight estimate.
Beside it, pending the clinical-wording review (Plan 5, Task D1):

> "80 % band; on held-out patients tested about six times a day it held 86 % of sensor readings on average
> and between 57 % and 100 % for an individual. About 45 mg/dL each side: a rough estimate, on the sensor's
> scale, not a measurement."

It becomes a tenth entry in `chhaya.product.claims` with Task B6.

## The claim to quote

Descriptive, no bar. On 29 held-out Shanghai patients under supervised care, calibrated on three days of
sensor data and tested about six times a day, a band built from the fingerstick filter's own spread and each
patient's spread during the sensor wear, with nothing fitted, held 83.6 % of hidden sensor readings around the
running estimate (49.9 % to 98.9 % for an individual; 12 of 29 patients within 70 to 90 %) and 86.1 % around
the estimate in hindsight (56.7 % to 100 %), at a half-width of about 45 mg/dL. It is calibrated on average,
not per patient, and it is wide.
