# Staleness alarm on real drift, 8 Oct 2026

**No verdict: descriptive, no bar.** Two findings. With three days of sensor data behind the report, a running
sum of fingerstick surprises told recordings whose sensor mean had since moved by more than 20 mg/dL from
those where it had not (AUROC 0.82, 95 % interval 0.63 to 0.98; 32 held-out recordings, 11 drifted). And **it
was not shown to do better than a plain baseline**: comparing the average of the same fingersticks with the
report's mean gives the same AUROC (0.82; difference 0.00, interval -0.16 to 0.18). With five days behind the
report (6 drifted recordings) the alarm was not shown to separate drifted from stable recordings at all.

"Alarm" is the name of the module and of the registered experiment. What it is for is a **prompt to consider a
new sensor wear**. It is not a finding about a patient's glucose and not advice on treatment, and on screen it
is never called an alarm. In the tables below a prompt raised on a recording that had not drifted is a "false
prompt". **In the product's own use case (an outpatient seen weeks after a fourteen-day report) the prompt is
outside everything tested here, so there it belongs on the Evidence screen only.**

## What this is

Registered in `docs/PREREGISTRATION.md`, Amendment 3, "Descriptive, no bar" ("Staleness alarm"). How each
number is computed is in the note on the descriptive outputs ("Staleness alarm") and in its second addendum of
8 Oct, written after two independent reviews of the code and before any test recording was scored.

- **Cohort:** that of section F, the fingerstick experiment. Primary k = 3 days of calibration; k = 5 is
  reported. The unit is the recording; intervals resample patients.
- **Drift (the label, the only thing that reads the hidden sensor):** the mean of the hidden sensor readings
  differs from the mean of the calibration days by more than 20 mg/dL, in either direction.
- **A surprise:** a fingerstick taken after the split, converted to the sensor's scale by the line the
  estimator learned during the wear, minus the patient's daily shape at that clock time, divided by its
  spread (the shape's own spread over the calibration days and 15 mg/dL for the meter).
- **The alarm:** a two-sided cumulative sum of the surprises with an allowance of half a standard deviation
  per fingerstick. A recording's score is the largest value the sum reaches; the alarm fires at the first
  fingerstick where the sum is above the threshold.
- **Beside it, with no bar:** the same sum over the fingersticks of the first two days only (added after the
  development figures had been seen; reported, not primary); the plain comparison, which is the absolute
  difference between the mean of the converted fingersticks and the report's mean; and the number of
  fingersticks alone, because a sum over more fingersticks can only grow.
- **Thresholds** come from development recordings without drift (17 at k = 3, 15 at k = 5): the smallest
  observed score that at most 10 % of them lie above. The pooled part of the meter-to-sensor line is also
  from development recordings. Test recordings only report.

Command: `python -m chhaya.eval.staleness --confirm`, run once. Provenance: commit `1595e71`, no uncommitted
changes under `src/`, seed 20261002, 2,000 resamples of patients. Results: `results/staleness/shanghai/`.
Development run: `results/staleness/shanghai-dev/`. Before the pass, the checkout it ran from gave back the
committed development report unchanged.

## The recordings

| | k = 3 (primary) | k = 5 (reported) |
|---|---|---|
| Held-out recordings (patients) | 32 (29) | 24 (21) |
| Drifted by more than 20 mg/dL | 11 (34 %) | 6 (25 %) |
| of which downward, upward | 9, 2 | 6, 0 |
| Not drifted | 21 | 18 |
| Distance of the hidden mean from the calibration mean, median | 12.2 mg/dL | 11.2 mg/dL |
| Fingersticks in the hidden window, median | 32 | 25.5 |
| Development recordings without drift that set the thresholds | 17 of 25 | 15 of 21 |

These are the patients of the fingerstick records: supervised care, tested about six times a day at fixed
clock times, hidden windows of two to eleven days.

## Results, k = 3 (primary)

| Score | AUROC (95 % interval) | Threshold | Raised in drifted recordings | Raised in stable recordings (false prompts) | Days from the split to the prompt, median |
|---|---|---|---|---|---|
| **Cumulative sum, whole hidden window (the registered score)** | **0.818** (0.628 to 0.976) | 5.41 | 7 of 11 (64 %) | 2 of 21 (10 %) | 2.6 |
| Cumulative sum, first two days only | 0.835 (0.662 to 0.975) | 2.30 | 8 of 11 (73 %) | 4 of 21 (19 %) | not computed |
| **Plain: fingerstick average against the report's mean** | **0.818** (0.608 to 0.972) | 44.9 mg/dL | 3 of 11 (27 %) | 0 of 21 | not applicable |
| Number of fingersticks alone | 0.593 (0.376 to 0.797) | | | | |

AUROC difference, cumulative sum minus plain: **0.000** (-0.161 to 0.181); all 2,000 resamples used.

The days are counted from the split, over the 7 drifted recordings in which the prompt was raised.

## Results, k = 5 (reported)

| Score | AUROC (95 % interval) | Threshold | Raised in drifted recordings | Raised in stable recordings (false prompts) | Days from the split to the prompt, median |
|---|---|---|---|---|---|
| Cumulative sum, whole hidden window | 0.667 (0.348 to 0.920) | 5.61 | 2 of 6 | 1 of 18 | 2.9 (two recordings) |
| Cumulative sum, first two days only | 0.741 (0.496 to 0.938) | 3.21 | 0 of 6 | 2 of 18 | not computed |
| Plain: fingerstick average against the report's mean | 0.731 (0.404 to 1.000) | 26.9 mg/dL | 2 of 6 | 1 of 18 | not applicable |
| Number of fingersticks alone | 0.491 (0.238 to 0.744) | | | | |

AUROC difference, cumulative sum minus plain: -0.065 (-0.487 to 0.300); 1,998 of 2,000 resamples used.

## What it means

In the order the plan fixed before the run.

1. **With three days behind the report, the alarm separated drifted from stable recordings.** AUROC 0.82, and
   the interval (0.63 to 0.98) excludes 0.5. It is wide because there are 11 drifted recordings.
2. **It was not shown to do better than comparing the fingerstick average with the report.** The two have the
   same AUROC, 0.818. The interval for the difference is -0.16 to 0.18, so neither "better" nor "worse" by
   that much is excluded. The daily shape at each clock time, the scaling of each surprise and the allowance
   added no measurable power to rank recordings over one subtraction.
3. **With five days behind the report, the alarm was not shown to separate drifted from stable recordings**
   (0.67, interval 0.35 to 0.92). Neither was the plain comparison (0.73, 0.40 to 1.00). Six recordings
   drifted; this is too few to say it fails.
4. **At their thresholds the two behave differently, and that is the thresholds, not the scores.** At k = 3
   the sum was raised in 7 of 11 drifted recordings and 2 of 21 stable ones; the plain comparison in 3 of 11
   and none. The plain threshold landed at 44.9 mg/dL, more than twice the 20 mg/dL that defines drift. By
   the rule it is the second largest of 17 values, so it rests on two development recordings in which the
   converted fingerstick average lay 44.9 mg/dL or more from the report while the sensor's own mean had moved
   by less than 20. Why was not investigated. At k = 5 the plain threshold is 26.9 mg/dL and the two were
   raised in the same number (2 of 6 drifted, 1 of 18 stable). **"7 against 3" is not evidence that the sum
   is the more sensitive detector.** What it does show: the sum's threshold, set on 17 recordings, gave a
   false-prompt rate at its target on held-out recordings (2 of 21, and 1 of 18; one more recording would
   make it 14 %), and the plain comparison's threshold did not give a usable operating point.
5. **The first two days alone separate as well** (0.84, 0.66 to 0.98), but its threshold let through 4 false
   prompts in 21, twice the target. Four against two in 21 recordings is not a difference that can be told
   apart.
6. **The separation is not explained by how much a patient was tested.** The number of fingersticks alone
   gives 0.59 (0.38 to 0.80), which includes 0.5, and the two-day sum, whose window is the same for every
   recording, does as well as the sum over the whole window. A part played by window length is not excluded.
7. **Where the prompt was raised on a drifted recording, it came a median of 2.6 days after the split**, in
   hidden windows of up to eleven days. This is the only prospective figure here, and it is over the 7
   recordings in which the prompt was raised, not over the 11 that drifted.
8. **Nothing here shows that the prompt is raised when a patient's glucose rises.** Nine of the eleven drifts
   were downward and two upward. The results folder holds aggregates only and does not say in which
   recordings the prompt was raised.

For the headline clause "when to wear a sensor again": there is now a prompt that was tested once on held-out
recordings and separated moved from unmoved reports in supervised care. It is not a rule for when to wear a
sensor, it was not shown to do better than one subtraction, and it has not been tried where the product would
be used. Whether the clause stays in the headline as worded is the team lead's decision.

## What a reader should weigh

- **The label and the scores look back over the same days.** The alarm does not predict drift. It notices,
  from fingersticks, a shift of level that the hidden sensor also recorded, and fingersticks and sensor
  measure the same glucose, so some separation is expected. Only the days from the split to the prompt are
  prospective.
- **Neither the setting nor the drift is the use case.** These patients were under supervised care with
  treatment being adjusted, and nine of the eleven drifts were downward. The product is for an outpatient
  seen weeks later whose glucose may have moved in either direction without anyone knowing. That was not
  observed.
- **About six fingersticks a day, at fixed clock times.** Lower testing frequencies were not measured. In
  section F the running gain from one fingerstick a day was 0.3 mg/dL.
- **Windows of two to eleven days.** A cumulative sum crosses any threshold more often the longer it runs, so
  the false-prompt rate measured here belongs to windows of this length. Over weeks it would be higher, by an
  amount that was not measured.
- **Small numbers.** 32 recordings, 11 drifted, 21 not. One recording moves the share of drifted recordings
  with a prompt by 9 points and the false-prompt rate by 5.
- **Thresholds from 17 and 15 recordings**, each resting on the two largest values among them. They exist for
  three and for five days of calibration only; a fourteen-day report has none.
- **The label is a cut.** Drift is the whole-window mean more than 20 mg/dL from the calibration mean, and
  the median distance is 12 mg/dL. A recording at 19 and one at 21 differ in label and in little else.
- **"The report" is mean glucose only.** Time below range and variability were not assessed. Nothing here
  concerns low glucose: the prompt neither indicates nor rules out low glucose, and each fingerstick is read
  on its own, as shown.
- The surprises are on the sensor's scale, by a line from meter to sensor learned during the wear from one
  sensor unit. Another sensor may read differently.
- The same sensor is the report and the yardstick. Nothing here is checked against laboratory glucose.
- On development recordings, with thresholds set on those same recordings, the sum's AUROC was 0.72 (0.45
  to 0.95). With intervals this wide the two halves of the cohort do not differ. What had been seen before
  this pass is in the addendum to the registration note.
- Two calibration lengths, three scores and a count are reported. No verdict hangs on any of them.
- The 32 recordings come from 29 patients, so some patients count more than once; the intervals resample
  patients.

## Consequences for the product

- **Where it goes.** In the product's own use case (an outpatient seen weeks after a fourteen-day report, who
  tests less often) every condition below fails, so there the prompt is **on the Evidence screen only**, as
  a result with its tables. On the patient screen it may appear only when all of these hold; otherwise the
  screen says "not computed", with the reason:
  - the profile comes from three or from five days of sensor data, the two lengths for which a threshold
    exists (5.41 and 5.61);
  - the patient tested at least as often as the tested recordings. Proposed gate, for this prompt and for
    the report since the sensor (whose record names no number): 4.6 fingersticks a day, the lower quartile
    of the held-out cohort in the fingerstick report record. It is a product gate, not a measured boundary;
  - the prompt is first raised by day 11. None is first raised later; one raised earlier stays, dated and
    marked "outside the tested range", because over a longer run of fingersticks the sum crosses its
    threshold more often and that rate was not measured;
  - the plain comparison is on the screen;
  - the "no prompt" and "not computed" texts are as visible as the prompt;
  - no badge, count, colour or sound of urgency, and no notification.
- **A prompt, never an alarm, and in the fingerstick panel**, not beside "days since the sensor": the expiry
  record keeps that line a fact with no threshold beside it. Text: "The sensor report may be out of date. A
  running comparison of fingersticks with the daily pattern of the sensor wear of [dates] crossed its preset
  threshold on [date]. This concerns the report, not this patient's glucose. Consider whether a new sensor
  wear is due."
- **It is driven by the registered cumulative sum at its development threshold**, the score whose
  false-prompt rate on held-out recordings was at its target (2 of 21, 1 of 18). Whenever the prompt is
  shown, the plain comparison is beside it: the sensor-equivalent fingerstick mean, which the fingerstick
  report record already puts on the screen, next to the report's mean.
- **Text beside it, whenever it is shown:** "A prompt to consider a new sensor wear. It is not a finding
  about this patient's glucose and not a reason to change or to keep treatment. In 32 recordings of
  supervised-care patients tested about six times a day, for up to 11 days, it was raised in 7 of 11 whose
  sensor mean had moved by more than 20 mg/dL and in 2 of 21 where it had not. It was not shown to tell the
  two apart better than comparing the fingerstick average with the report's mean. In 9 of those 11 the mean
  had moved downward, in patients whose treatment was being adjusted by staff; 2 moved upward. Whether the
  prompt is raised when glucose rises is not known. It does not say which way. Not tested in outpatient
  care, with fewer fingersticks or over longer periods. It neither indicates nor rules out low glucose. Not
  a rule for when to wear a sensor."
- **When there is no prompt:** "No prompt does not mean the report still holds, nor that glucose is unchanged
  or in range. 4 of 11 recordings whose sensor mean had moved raised none."
- **When it is not computed:** "Not computed: [fewer fingersticks than in the tested recordings / a sensor
  wear of a length that was not tested / more than 11 days since the sensor]. Not a recommendation to test
  at any frequency."
- **The prompt does not say which way.** Individual fingersticks are shown as read; the prompt is about the
  report.
- **Artifact build:** it calls `chhaya.twin.staleness` (`surprise_scale`, `cusum`, `first_alarm`) with the
  threshold read from `results/staleness/shanghai/summary.json`. Nothing is fitted live.
- **Clinic list:** one column with three states, never blank: "raised (date)", "not raised", "not computed
  (reason)". It is sortable, never the default ranking and never a count of patients "at risk". Under the
  list, the sentence of the expiry record (this describes how old the sensor report is, not how unwell a
  patient is or who should be seen first) and: "A patient with no prompt may still have changed."
- **Evidence screen:** the two tables above with both AUROCs side by side and the column names used here
  ("raised in", "false prompts"), and the sentence "not shown to do better than comparing the fingerstick
  average with the report".

## The claim to quote

Descriptive, no bar; a plain baseline does as well. On 32 held-out Shanghai recordings (29 patients under
supervised care, tested about six times a day, for up to eleven days after a three-day sensor report), 11 of
which drifted by more than 20 mg/dL in mean sensor glucose (9 downward, 2 upward), a running sum of
fingerstick surprises, used only as a prompt to consider a new sensor wear, separated drifted from stable
recordings with AUROC 0.82 (95 % interval 0.63 to 0.98), against 0.82 (0.61 to 0.97) for the plain
fingerstick average compared with the report's mean (difference 0.00, interval -0.16 to 0.18): it was not
shown to do better than that comparison. At a threshold set on development recordings so that at most 10 %
of stable ones would raise it, the prompt was raised in 7 of 11 drifted recordings (64 %) and 2 of 21 stable
ones (10 %); in those 7, a median of 2.6 days after the split. With a five-day report (24 recordings, 6
drifted) it was not shown to separate them (0.67, interval 0.35 to 0.92). The label and the score look back
over the same days. It is not a finding about a patient's glucose, not advice on treatment and not a rule for
when to wear a sensor, and it was not tested in outpatient care, at lower testing frequencies or over longer
periods.
