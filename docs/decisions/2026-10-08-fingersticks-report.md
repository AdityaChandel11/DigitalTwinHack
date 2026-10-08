# Fingersticks, second pass: the report a doctor reads (section F), 8 Oct 2026

**No verdict: descriptive, no bar.** Two findings. In supervised-care patients tested about six times a day,
a report rebuilt from those fingersticks was closer to the following days' sensor mean than the three-day
sensor report was. And **a plain baseline beats our estimator at it**: the average of the same fingersticks,
converted to the sensor's scale, is as close or closer on all three numbers of the report.

The yardstick throughout is the hidden sensor. Figures "on the sensor's scale" are not meter values: in this
dataset the sensor reads lower than the meter.

## What this is

The second pass of section F that the confirmatory run deferred and declared (`docs/PREREGISTRATION.md`, note
of 8 Oct to section F, "Outputs deferred, declared"). How each number is computed was fixed beforehand in the
note on the descriptive outputs and its addendum. The estimator is the frozen one: before writing anything
the pass recomputed the confirmatory run's cohort (29 patients), control error (36.708 mg/dL) and both paired
differences (-2.793 live, -9.495 in hindsight; and the k = 5 figures) and they matched.

Command: `python -m chhaya.eval.fingersticks_report --confirm`, run once.
Provenance: commit `6ac5b48`, no uncommitted changes under `src/`, seed 20261002. Results:
`results/fingersticks/shanghai-report/`. Development run: `results/fingersticks/shanghai-dev-report/`.

Cohort as in the confirmatory run: 29 test patients (32 recordings) at k = 3 days, 21 (24) at k = 5. All
errors are absolute, medians over patients. "The report" is mean glucose, time above 180 mg/dL and time in
range (70 to 180) of the hidden sensor readings, up to eleven days after the split.

## How far the old report had aged

| | k = 3 | k = 5 |
|---|---|---|
| Distance of the hidden window's mean from the stale report's mean, median | 13.0 mg/dL | 12.1 |
| Signed median (hidden minus stale) | -8.2 | -10.9 |
| Patients whose mean moved by more than 20 mg/dL | 38 % | 29 % |

Glucose fell after the calibration days in most patients, consistent with treatment being adjusted under
supervised care.

## The three numbers of the report, k = 3 (29 patients)

Median absolute error against what the sensor then showed.

| Who states the report | Mean glucose (mg/dL) | Time above 180 (points) | Time in range (points) |
|---|---|---|---|
| The stale sensor report (the calibration days) | 12.95 | 12.43 | 13.25 |
| **Plain fingerstick average, converted to the sensor's scale** (its last two columns are shares of readings, not time) | **6.42** | **3.12** | **4.95** |
| Plain fingerstick average, as read from the meter | 18.34 | 8.48 | 9.06 |
| Daily shape alone | 12.53 | 10.27 | 15.71 |
| Chhaya, live estimate | 11.85 | 9.57 | 15.64 |
| **Chhaya, in hindsight** (registered reading: normal spread) | **8.85** | 8.77 | 15.16 |
| Chhaya, in hindsight, plain count of crossings (no spread) | 8.85 | 6.37 | 6.98 |

The registered comparisons (median paired difference, 95 % interval, share of patients closer, one-sided p):

| Comparison | Mean glucose | Time above 180 | Time in range |
|---|---|---|---|
| In hindsight against the stale report | **-3.40** (-8.91 to -1.56), 83 %, 0.0001 | -1.72 (-6.47 to 0.04), 66 %, 0.004 | -1.01 (-4.26 to 4.03), 52 %, 0.49 |
| In hindsight against the fingerstick average | **+1.88** (-0.82 to 3.11), 38 %, 0.93 | **+2.08** (0.04 to 5.97), 31 %, 0.99 | **+10.09** (5.57 to 12.38), 24 %, 1.00 |
| In hindsight against the shape alone | -4.69 (-9.37 to -1.52), 83 %, 0.0001 | -0.93 (-4.43 to 0.01), 62 %, 0.005 | -0.16 (-3.23 to 0.72), 59 %, 0.03 |
| Live against the stale report | -1.76 (-3.86 to -0.89), 83 %, 0.0001 | -0.72 (-3.73 to 0.27), 62 %, 0.03 | +1.25 (-2.03 to 3.88), 48 %, 0.77 |
| Fingerstick average against the stale report | -4.68 (-9.48 to -0.98), 72 %, 0.0008 | -2.14 (-8.41 to -0.30), 69 %, 0.001 | -4.64 (-11.87 to -1.86), 76 %, 0.002 |

Below zero means the first is closer. A positive difference with an interval above zero means the second is.

### k = 5 (21 patients; reported, as registered)

| Who states the report | Mean glucose | Time above 180 | Time in range |
|---|---|---|---|
| Stale sensor report | 12.08 | 4.49 | 8.21 |
| Plain fingerstick average, on the sensor's scale | 8.63 | 4.89 | 5.03 |
| Plain fingerstick average, as read | 16.37 | 5.03 | 6.16 |
| Chhaya, in hindsight (normal spread) | 9.94 | 4.85 | 11.69 |
| Chhaya, in hindsight, plain count | 9.94 | 4.06 | 6.12 |

In hindsight against the stale report on mean glucose: -2.11 (-7.86 to -1.54), 90 % of patients, p = 0.0002.
Against the fingerstick average: -0.21 (-3.67 to 1.38), 52 %: no difference. On time in range the fingerstick
average is again closer (+3.56, interval 0.77 to 9.41).

## Error by day since the sensor came off (k = 3)

RMSE against the hidden sensor, medians over patients; the paired differences are against the control (the
daily shape alone).

| Day | Patients (share of the cohort) | Control | Live | In hindsight | Live minus control | In hindsight minus control |
|---|---|---|---|---|---|---|
| 1 | 29 (100 %) | 36.7 | 33.6 | 27.9 | -1.81 (-3.33 to -0.45) | -6.38 (-11.73 to -3.40) |
| 2 | 29 (100 %) | 35.1 | 30.5 | 24.7 | -3.93 (-5.78 to -2.19) | -8.35 (-14.63 to -6.61) |
| 3 | 27 (93 %) | 33.9 | 30.5 | 23.3 | -2.99 (-6.63 to -0.42) | -7.04 (-15.81 to -3.38) |
| 4 | 23 (79 %) | 29.1 | 27.8 | 23.2 | -2.02 (-6.83 to -0.17) | -7.11 (-15.11 to -3.68) |
| 5 | 21 (72 %) | 32.6 | 31.9 | 24.6 | -2.03 (-2.91 to 0.03) | -3.33 (-8.67 to -0.94) |
| 6 | 18 (62 %) | 34.6 | 31.9 | 25.8 | -2.70 (-8.72 to -0.83) | -7.64 (-18.17 to -2.91) |
| 7 | 16 (55 %) | 31.1 | 29.8 | 27.0 | -1.16 (-6.18 to 0.38) | -3.04 (-11.70 to -1.21) |
| 8 | 13 (45 %) | 27.1 | 27.7 | 22.4 | -0.29 (-4.46 to 0.32) | -2.38 (-9.22 to -0.09) |
| 9 | 11 (38 %) | 29.6 | 29.7 | 28.1 | -0.33 (-3.12 to 0.02) | -2.48 (-7.37 to -0.02) |
| 10 | 11 (38 %) | 26.2 | 25.8 | 24.0 | -0.39 (-2.44 to 0.00) | -1.12 (-5.97 to 0.00) |
| 11 | 9 (31 %) | 27.9 | 25.7 | 25.7 | -2.01 (-10.75 to 0.00) | -4.25 (-10.54 to -1.55) |

- Fewer than 80 % of the cohort reach day 4 and later, and fewer than half reach day 8: those rows describe
  whoever was still recording.
- The gain from fingersticks was not seen to fade with days since the sensor on the days most patients reach: in
  hindsight it is 6 to 8 mg/dL on days 1 to 4, and the live gain 2 to 4.
- The daily shape's own error does not grow by day: inside each patient its slope is 0.21 mg/dL per day
  (interval -0.46 to 1.20; 27 patients). The in-hindsight estimate's is 0.78 (0.02 to 1.50).
- The distance of a day's mean from the stale report's mean grows by 1.51 mg/dL per day inside each patient
  (0.36 to 4.38). Expiry by day on the wider cohort is in the expiry record.

## How often these patients test

| Fingersticks per day, median (quartiles) | Test cohort | Development cohort |
|---|---|---|
| Over the recording, k = 3 | 6.3 (4.6 to 6.9) | 3.9 (2.8 to 7.0) |
| In the hidden window, k = 3 | 6.1 (4.6 to 6.7) | 3.9 (2.9 to 6.9) |
| Over the recording, k = 5 | 5.6 (4.1 to 6.7) | 3.3 (2.3 to 6.6) |

Inside the test cohort, patients who test more often gain more from the live estimate (Spearman -0.52 between
fingersticks per hidden day and the live RMSE difference, p = 0.004; -0.67 in the development cohort).

**This supports the guess in the fingerstick record of 8 Oct.** The test cohort tests about six times a day
where the development cohort tests about four, and the gain rises with testing frequency inside both. That
is the likely reason F1 was larger on test patients (-2.79) than on development patients (-1.19). It is an
association across patients, not an experiment; the thinning table of the fingerstick record is the
experiment, and it says the same.

## What it means

- **With frequent testing, fingersticks tracked the report and not only the trace.** In 29 supervised-care
  patients tested about six times a day, the report rebuilt from those fingersticks missed the sensor's mean
  by 8.9 mg/dL where the three-day sensor report missed it by 13.0 (median paired difference 3.4, interval
  1.6 to 8.9, 83 % of patients). A fourteen-day report would start closer than a three-day one.
- **Our estimator is not what does it. A plain baseline beats it.** The plain average of the same
  fingersticks, converted to the sensor's scale, missed mean glucose by 6.4 mg/dL; its share of readings
  above 180 was 3.1 points from the sensor's time above 180 and its share within 70 to 180 was 5.0 points
  from the sensor's time in range, against 8.9, 8.8 and 15.2 for the estimate. The fading deviation that won
  F1 pulls back to the old daily shape between fingersticks, so it under-corrects a patient whose level has
  moved. It was chosen for the trace; for the report's level it is the wrong tool.
- **What the sensor wear contributes is comparability with the old report.** With the hidden sensor as the
  yardstick, the same fingerstick average as read from the meter lay 18.3 mg/dL from the sensor's mean. That
  is not meter error: this sensor reads lower than the meter, and fingersticks are taken at fixed clock
  times. A line from meter to sensor learned during the wear (the patient's own in 26 of 32 recordings)
  removes most of that gap. Sensor-scale values are not capillary values.
- **Time in range from the estimate is not usable.** With the registered normal spread it missed by 15.2
  points, no better than the stale report (13.3) and far worse than the plain count of the same estimate
  (7.0). This agrees with the break test of 3 Oct.

## What a reader should weigh

- This pass read the test patients a second time, after F1 and F2 were known. It was declared before the
  first run and its readings were fixed before it; it is still a second look.
- On development patients the picture was weaker: at k = 5 the rebuilt report did not beat the stale one.
  Those patients test less often. The registration note records what had been seen.
- **Lower testing frequencies were not measured at report level.** Everything here is at about six
  fingersticks a day, at fixed clock times, with nights unsampled. It is not a recommendation to test at any
  frequency.
- A fingerstick share above 180 is a share of spot readings, not time. It tracked the sensor's time above
  180 under this testing schedule; nothing shows it would under another.
- The meter-to-sensor line belongs to one sensor unit and was fitted over three to five days. It is applied
  after the patient's level has moved, and another sensor may read differently. In 6 of 32 recordings it was
  not the patient's own line.
- The same sensor is the report and the yardstick. Nothing here is checked against capillary or laboratory
  glucose.
- Nothing here concerns low glucose.
- A three-day or five-day report stands in for a fourteen-day one, so the stale report here is noisier than
  a real one would be.
- Neither the setting nor the cohort is the use case: supervised care, one country, hidden windows of at most
  eleven days, 29 patients.
- The comparator was registered on the sensor's scale. "As read from the meter" is reported beside it.

## Consequences for the product

- **Report since the sensor (patient screen):** an estimated mean glucose and an estimated share of
  fingerstick readings above 180 mg/dL, both labelled "sensor-equivalent, estimated from N fingersticks over
  D days", each beside the same figure as read from the meter. Individual fingersticks are always shown as
  read. The figures are withheld below the cohort's testing frequency and marked "outside the tested range"
  after day 11. No GMI or estimated HbA1c is derived from them. The estimator draws the trace, with its band,
  and is not the source of these figures.
- **Text beside it:** "Sensor-equivalent, not meter values: this patient's sensor read lower than the meter.
  Converted with the line learned during the wear of [date]; another sensor may read differently. A share of
  readings taken at [times], not time above range; nights are not sampled. In 29 supervised-care patients
  tested about six times a day, for up to 11 days, the median miss was 6 mg/dL (mean) and 3 points (above
  180); half of patients were missed by more. Not measured with fewer fingersticks. Says nothing about low
  glucose. Not for dosing."
- **No time in range and no time below range since the sensor is shown from any source.** On screen: "Time
  in range and low glucose since the sensor are not estimated. This screen says nothing about
  hypoglycaemia."
- **"What keeps it true", second line for fingersticks:** "In 29 supervised-care patients who were already
  tested about six times a day, the plain average of their fingersticks, converted to the sensor's scale, lay
  a median of 6 mg/dL from the sensor's mean over the following days; a three-day sensor report lay 13 (a
  fourteen-day report would be closer). Not measured at lower testing frequencies. This describes those
  patients; it is not a recommendation to test at any frequency."
- The meter-to-sensor line of each patient becomes part of the artifact bundle.

## The claim to quote

Descriptive, no bar; a plain baseline beats our estimator. On 29 held-out Shanghai patients under supervised
care who were tested about six times a day, with the hidden sensor as the yardstick, a three-day sensor
report missed the mean sensor glucose of the following days (up to eleven) by a median of 13.0 mg/dL.
Chhaya's report rebuilt in hindsight from those fingersticks missed it by 8.9 (median paired difference 3.4,
95 % interval 1.6 to 8.9, 83 % of patients), but was no closer than the plain average of the same
fingersticks converted to the sensor's scale by a line learned during the wear (6.4). The share of those
converted readings above 180 mg/dL and within 70 to 180 was also closer to the sensor's time above 180 and
time in range (3.1 against 8.8 points; 5.0 against 15.2). As read from the meter the same average lay 18.3
mg/dL from the sensor's mean; sensor-scale figures are not meter values. Lower testing frequencies were not
measured, and this is not a recommendation to test at any frequency.
