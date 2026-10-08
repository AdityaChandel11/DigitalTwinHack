# Pre-registration — sensor-off evaluation

Committed before any model in this repository was run on real patient data. Amendments are appended
below with a date and a reason; nothing above an amendment is edited.

## Question

After calibrating on the first *k* days of a patient's CGM, can the twin estimate that patient's glucose
on the following days **without CGM input**, using logged meals and band activity, better than the
patient's own average daily curve?

## Experiment

- **Data.** Every CGMacros participant with at least one day of primary-sensor data. Primary sensor:
  FreeStyle Libre Pro, one reading per 15 minutes. The Dexcom G6 Pro trace is never used for calibration.
- **Split in time.** Calibrate on readings with `t < k × 1440` minutes. Score on all later readings.
  Recordings that leave less than one full day to score are skipped and counted.
- **Calibration lengths.** k = 3, 5, 7 days. **Primary: k = 5.**
- **What the twin may see in the scored window.** Logged meals (time and macronutrients) and Fitbit METs.
  Nothing else.
- **Comparators.** (a) The patient's own average daily curve: mean glucose per 30-minute time-of-day bin
  over the calibration window. (b) The patient's calibration-window mean.
- **Unit of analysis.** The patient. Several recordings of one patient are averaged first.
- **Failures.** A calibration that fails is recorded with its error and reported as a count. It is not
  replaced or retried with different settings.

## Pass bars (primary, k = 5)

| | Bar | Role |
|---|---|---|
| **P1** | Median over patients of (twin RMSE − average-day RMSE) is below 0, and a one-sided Wilcoxon signed-rank test gives p < 0.05 | Required for GO |
| **P2** | Median absolute error in time-in-range (70–180 mg/dL) is at most 10 percentage points | Required for GO |
| **P3** | The 80 % predictive band contains between 70 % and 90 % of hidden readings | Reported; if it fails, bands are recalibrated on dev patients and re-reported on test patients |

**GO** = P1 and P2. **NO-GO** switches the headline to the overnight-low module on the same engine, as
planned in `docs/WAR_ROOM.md`.

## Also reported, without a bar

RMSE, MAE, MARD, correlation, bias, GMI error, time-above and time-below-range error; all of these for
k = 3 and k = 7; results by group (healthy, pre-diabetes, T2D — the T2D group is about 14 people, too few
for its own test); RMSE between the two physical sensors as a noise floor; twin RMSE against the Dexcom
reference.

## What counts as tuning

The first run uses the defaults in this commit, so every patient counts toward the verdict. After that
run, any change to model structure, fixed constants, priors or band width is chosen using **dev patients
only** (`chhaya.config.is_dev_patient`) and its effect is claimed on **test patients only**.

## Amendments

None.

### Amendment 1, 3 Oct 2026

The first run (defaults of commit `1c9f754`, every participant) is recorded in
`docs/decisions/2026-10-03-gate2-run1.md`: NO-GO at k = 5 (P1 failed, P2 and P3 passed). It stands as run.

Two input defects in the CGMacros loader were found afterwards (the unit of `Amount Consumed`, and meal clocks
one hour early in four files). Finding them involved inspecting meal columns and a model-free lag statistic
for all 45 files. They will be fixed by general rules, and the model will be changed as listed in that
decision record, using development patients only.

Because all of this follows a look at the first results, **every later claim against P1 to P3 is made on the
20 test patients only** (`is_dev_patient` false), with the same bars and the same primary k = 5. Results on
all 45 participants are reported alongside, labelled as not confirmatory.

### Amendment 2, 3 Oct 2026 (after the break test)

A break test of everything up to Gate 2 (record: `docs/decisions/2026-10-03-break-test.md`) found no
leakage and regenerated the committed results exactly. It also found defects in the inputs, gaps in how the
gate is decided, and a weak comparator. This amendment was committed before any re-run.

**Input corrections.** Decided from the input files, not from how the estimator scores.

1. *Derived activity.* In the 11 files without a METs column, activity was derived as kcal x 60 / kg. In the
   33 files that have both columns, stored METs equal activity kcal divided by the participant's resting kcal
   per minute, to within 0.2 METs; the weight formula is 27 % low at the median. The loader now uses the
   resting-rate formula. Five test patients are affected (011, 033, 035, 038, 042).
2. *`Amount Consumed` of 0* is read as "not recorded" (the whole meal counts), not "nothing eaten". Seven such
   meals carry 15 g of carbohydrate or more, and glucose rises after them as it does after whole meals
   (+31 vs +25 mg/dL in the first hour). This was judged from sensor data of all files, test patients included.
3. *More than six logged items inside twelve hours* lost the oldest items in the simulation. Four development
   patients were affected (004, 015, 031, 043) and no test patient.

**Guards.** Each can only turn a GO into a NO-GO or remove a recording.

4. A recording is skipped at k when fewer than half of the 15-minute slots of its calibration window hold a
   sensor reading. Test patient 018 has 16 hours of data followed by a ten-day gap, so its "k-day
   calibration" was never k days. Skipped recordings now appear in the outputs with the reason.
5. GO also requires that at most 10 % of attempted fits failed. A run that omits k = 5 gives no verdict.
6. Only a full run on the test split is labelled confirmatory in the outputs.

**Comparators.**

7. The registered comparator (the raw average day from k days in 30-minute bins) is a noisy estimator: at
   k = 5 it is no better than the patient's mean. A physiology-free control, half average day and half mean,
   is now computed in every run and reported next to P1. P1 as registered remains the Gate 2 bar.
   **From Milestone 3 on, the primary comparator is this control**: an estimator that does not beat it has
   not shown that its physiology adds anything.
8. P2 (time-in-range error at most 10 points) cannot discriminate, because a constant passes it. It stays in
   the verdict as registered and is reported next to the same figure for the baselines.
9. The two-sensor "noise floor" compared the primary sensor with a flat extrapolation of the reference
   sensor after that sensor had stopped recording. It now uses only readings both sensors took. It was
   never a bar.

**Consequence for Gate 2.** The test split is re-run once with these corrections and both runs are reported
side by side: the registered run of commit `a57227f` and the corrected run. No setting of the estimator
(blend weight, loss, priors) is changed.

**Addendum to Amendment 2 (3 Oct 2026, still before any re-run).** Two further input corrections, found by
inspecting the files after the first fixes were committed:

10. *Sensor limits.* The Libre writes `LO` and `HI` as exactly 40 and 400 mg/dL. Readings at or beyond the
    limits are now dropped. They made up 43 % of participant 015's trace, 36 % of 007's and 12 % of 032's
    (16 of 45 files have some); test patients 007 and 048 are affected.
11. *Impossible macronutrients* (fibre above total carbohydrate; fat worth more than 1.5 times the meal's
    stated calories) are treated as missing.

No corrected run has been executed. When it is, the registered results of commit `a57227f` stay in
`results/gate2/cgmacros-*-registered/` and the corrected run is reported beside them.

### Amendment 3, 4 Oct 2026 (Milestone 3: the experiments that follow Gate 2)

Committed before any code for these experiments exists and before any of them is run on a test-split patient.
Record of what led to it: `docs/decisions/2026-10-04-plan-revision.md`.

**What had been seen when this was written.**

- The corrected Gate 2 run on the CGMacros test split (`docs/decisions/2026-10-04-gate2-corrected.md`).
- On ShanghaiT2DM, for all patients including the test split: label and availability counts only (nights with a
  sensor low per patient, fingerstick clock times and density, agreement between sensor and fingerstick, change
  of the sensor mean within a recording, record completeness, drug names). The share of meals followed by an
  excursion above 180 mg/dL was **not** looked at, for any patient.
- On ShanghaiT2DM development patients only: three exploratory probes of fingerstick filters
  (`scripts/research_2026-10-04/probe*.py`). No estimator or predictor has been scored on a Shanghai test patient.

**Gate 2 is closed.** The corrected run is GO as registered. Its effect against the physiology-free control is
0.35 mg/dL at k = 5.

**The fallback is withdrawn.** "NO-GO switches the headline to the overnight-low module" no longer applies, and
no low-glucose model will be trained or evaluated on sensor lows: where a fingerstick was taken at the same
moment, 12 % of sensor readings below 70 mg/dL were confirmed. On screen a sensor low is shown as
"sensor low, unconfirmed".

**Common rules for everything below.**

- Split: `chhaya.config.is_dev_patient`. On Shanghai that is 53 development and 47 test patients. Anything
  fitted or chosen (model coefficients, imputation values, filter constants, thresholds) uses development
  patients only.
- Each experiment's test split is scored **once**, by a command that requires an explicit `--confirm` flag.
  A defect found afterwards is handled as in Amendment 2: dated, described, both runs reported.
- Unit of analysis: the patient. Intervals are 95 % percentile bootstrap intervals over test patients, 2,000
  resamples, seed `config.SEED`. Paired tests are one-sided Wilcoxon signed-rank tests over patients.
- Three bars are primary (M1, M2, F1). No multiplicity correction is applied; every bar is reported with its
  p-value or interval whether it passes or not.
- Results folders hold aggregates only. No per-meal or per-patient feature table is written.

#### L. Label check (descriptive, no bar)

Every fingerstick is paired with the nearest sensor reading no more than 10 minutes away. Reported: MARD and bias
overall and by fingerstick range; for the thresholds below 54, below 70, above 180 and above 250 mg/dL, how many
sensor flags, how many fingerstick flags, how many both, positive predictive value and sensitivity; the
below-70 figures for pairs with a flat sensor trace and for night pairs.

#### M. Post-meal excursion, predicted at meal time (ShanghaiT2DM)

- **Meal.** A diet entry; an entry within 60 minutes of the start of the current meal belongs to that meal.
- **Calibration window.** The first k = 3 days of the recording. Recordings that fail the Gate 2 coverage rule
  or leave less than one day after the split are skipped and counted.
- **Eligible meal.** After the split; at least 6 sensor readings in the 120 minutes after it; a sensor reading
  in the 20 minutes before it. Every arm is scored on the same meals.
- **Event.** Two consecutive sensor readings (no more than 20 minutes apart) above 180 mg/dL in the 120 minutes
  after the meal. Secondary threshold: 250 mg/dL.
- **Prediction time.** The logged meal time. A feature may use nothing stamped at or after it, except in the
  sensor-on arm, which may use sensor readings up to it.
- **Arms.** All include the meal's clock time (sine and cosine).
  - *Record only*: age, sex, BMI, duration, HbA1c, fasting and 2-hour plasma glucose, fasting C-peptide, eGFR,
    and four flags from the agents list (insulin, sulfonylurea or glinide, alpha-glucosidase inhibitor,
    metformin). The sheet's "Hypoglycemia (yes/no)" column is excluded.
  - *Sensor history only* (calibration window): mean, standard deviation, share above 180, the shrunk average
    day at the meal's clock time, its maximum over the next 120 minutes, and the share of calibration-window
    meals with the event.
  - *Fingersticks only* (after the split, before the meal): the last value within 180 minutes and its age,
    whether there was one, the count and mean of all earlier ones.
  - *Fused, sensor off*: the three above together.
  - *Sensor on* (reference, what other entries build): fused plus the last sensor value, its 30-minute change
    and the 120-minute mean before the meal.
  - *Personal rate* (baseline, no learner): the share of calibration-window meals with the event.
- **Learner.** L2 logistic regression, C = 1, standardised inputs, median imputation with missing-value
  indicators, fitted on development patients' meals. No tuning. A LightGBM with library defaults is reported
  as a sensitivity analysis without a bar.
- **Primary metric.** Area under the precision-recall curve (AUPRC) on test patients' meals.

| | Bar | Role |
|---|---|---|
| **M1** | Fused (sensor off) minus each of record only, sensor history only and fingersticks only: the lower end of the interval for the AUPRC difference is above 0 for all three | Primary: fusion beats every single stream |
| **M2** | Fused (sensor off) minus the personal rate: lower end of the interval above 0 | Primary: the model adds to the obvious baseline |
| M3 | Calibration slope of the fused model on test meals between 0.8 and 1.2 | Reported; if it fails, the dashboard shows risk bands, not probabilities |

Also reported: AUROC; within-patient AUROC (patients with at least 5 events and 5 non-events); Brier score;
the sensor-on arm and the share of its gain over prevalence that survives without the sensor; sensitivity and
false alerts per patient-week at the threshold that gives 80 % sensitivity on development patients; net benefit
at thresholds 0.3, 0.5 and 0.7 against alert-always; median minutes from meal to the first reading above 180;
the 250 mg/dL threshold; meals that start at or below 180; subgroups by insulin use, pump use, sex and age 65.

If M1 fails, the result is published as "fusion did not beat the best single stream, by this much" and the
dashboard's stream switch shows the measured numbers.

#### P. The record as the prior (CGMacros, the twin)

The reveal is run on the test split at k = 1, 3, 5, 7 twice: with the record-informed prior that Gate 2 used
(`record_prior`) and with the population prior (`population_prior`). No other setting changes.

| | Bar | Role |
|---|---|---|
| P1 | At k = 1, the estimate with the record prior has lower RMSE than with the population prior: median paired difference below 0, p < 0.05 | Secondary: the record is worth something when sensor data is short |

Also reported: the same comparison at every k for the estimate and for the physiology alone, and the number of
sensor days the population prior needs to match the record prior at k = 1.

#### F. Fingersticks after the sensor comes off (ShanghaiT2DM)

- **Cohort.** Recordings of at least k + 2 days with at least one fingerstick a day on average and at least 3
  paired fingersticks after the split. Primary k = 3; k = 5 is reported.
- **Control.** Half the patient's average day, half their mean, from the calibration window; no fingersticks.
- **Estimators.** The control plus a deviation estimated from fingersticks: *live* (only fingersticks already
  taken) and *in hindsight* (all fingersticks of the hidden window, for the retrospective report). A fingerstick
  is first mapped to the sensor's scale by a line fitted on calibration-window pairs.
- **Design freedom, declared.** The filter is a decaying deviation with time constant 60, 120 or 240 minutes,
  with or without a slow level. The choice among those six is made on development patients by the live
  estimate's RMSE and written into the code defaults and the decision record before the test run.

| | Bar | Role |
|---|---|---|
| **F1** | Live estimate against the control: median paired RMSE difference below 0, p < 0.05 | Primary |
| F2 | In-hindsight estimate against the control: the same test | Secondary |

Also reported: both estimators with fingersticks thinned to two a day, one a day and one every second day
(the first of the day is kept); accuracy against each hidden fingerstick before it is used (MARD, share within
15 mg/dL below 100 and 15 % above, Clarke error-grid zones) for the real sensor, the control and the live
estimate; error in mean glucose, time above 180 and time in range over the hidden window against the stale
sensor report and against the plain fingerstick average; error by day since the sensor came off.

#### Descriptive, no bar

- **Expiry.** Error of the control and of Chhaya by day since the sensor (both datasets), and a case series of
  the eight Shanghai patients recorded again 12 to 168 days later: the profile from the first recording applied
  to the later one. Treatment changed between recordings for some; this is stated per patient.
- **Band.** A recalibration of the 80 % band chosen on CGMacros development patients (one factor, or one per day
  since the sensor). Reported on test patients: mean coverage and how many patients fall within 70 to 90 %
  (mean coverage is 0.83 before recalibration, with a per-patient range of 0.60 to 0.99).
- **Staleness alarm.** A recording has drifted when its hidden-window sensor mean differs from its calibration
  mean by more than 20 mg/dL. The alarm is a cumulative sum of standardised fingerstick surprises against the
  frozen profile, with its threshold set on development recordings at 10 % false alarms. Reported on test
  recordings: AUROC with its interval, sensitivity, false-alarm rate, median days to alarm.

#### Genetic markers

Neither dataset has genotypes. The record schema carries one genetic-marker field; it is synthetic, labelled as
such on screen, and switched off in every experiment above.

### Note to Amendment 3, section M, 8 Oct 2026 (before the Gate 3 test run)

Written after the code for section M existed and after two independent reviews of it, and before any Shanghai
test patient was scored. No bar changes. This note fixes how the registered words were turned into code, so
that the choices cannot be made after the result.

**What had been seen when this was written.** One cross-validated run on the 49 development patients with
eligible meals (1,436 meals, 36.4 % with the event): AUPRC record 0.495, sensor history 0.644, fingersticks
0.534, fused 0.618, sensor on 0.717; fused minus sensor history -0.025 (interval -0.070 to 0.015). So M1 is
expected to miss. Nothing was tuned in response: features, label and learner are as in the plan of 7 Oct. The
plain-share baseline described below had not been computed for any patient.

**The personal rate.** Section M says "the share of calibration-window meals with the event". The plan of
7 Oct implemented an add-one smoothed share, (events + 1) / (meals + 2), because 0 of 0 is undefined. That is
not the registered quantity and it changes how patients rank. Resolved as follows:

- **M2 is judged against the plain share**, as registered. Where no calibration-window meal could be scored
  the baseline is 0.5, and the number of such meals is reported.
- The smoothed share stays as the history arm's feature, as planned, and the fused model's difference from it
  is reported beside M2 with no bar.
- A calibration-window meal counts toward either share when it starts at least 120 minutes before the split
  and has at least 6 sensor readings in the 120 minutes after it.

**Other readings of the text, fixed as coded.**

- A sensor reading stamped exactly at the meal time counts as "in the 20 minutes before it" and is available
  to the sensor-on arm. A fingerstick stamped exactly at the meal time is not used by any arm.
- A meal exactly at the split counts as after it.
- "Its maximum over the next 120 minutes" is the maximum over the five half-hour bins starting with the
  meal's bin (120 to 150 minutes).
- The sensor-on arm's "30-minute change" is the last reading minus the trace interpolated 30 minutes before
  the meal.
- A record with no agents entry has its four drug flags missing (imputed, with an indicator when development
  data has such a case), not zero. No development record lacks the entry.
- In the 250 mg/dL analysis the personal rate and the history features are still the 180 mg/dL ones.
- The "starts at or below 180" analysis selects meals by a sensor reading at meal time, so it describes
  which meals, not a sensor-off product.
- Secondary analyses carry no verdict. One that fails is published with its error.

**Guards added to the command.** `--confirm` runs only at k = 3 and 2,000 resamples, on committed code, and
refuses to run when a confirmatory result is already on disk. The primary result is written before any
secondary analysis starts.

### Note to Amendment 3, section F, 8 Oct 2026 (before the fingerstick test run)

Written after the code for section F existed, after two independent reviews of it and after the six declared
designs were run on development patients, and before any Shanghai test patient was scored for this
experiment. No bar changes. One declared choice is made differently from the plan of 7 Oct, and it is stated
here so that it cannot be mistaken for a choice made after the result.

**What had been seen when this was written.** Development patients only (24 patients, 25 recordings at
k = 3; control RMSE 36.0 mg/dL), all six designs, twice: before and after the review fixes below. After the
fixes, at k = 3 with all fingersticks, live estimate against control:

| Design | Median live RMSE | Median paired difference (95 % interval) | Patients better | p |
|---|---|---|---|---|
| tau 60 | 35.55 | -0.94 (-2.44 to -0.45) | 79 % | 0.00001 |
| tau 120 | 35.25 | -1.19 (-2.66 to -0.37) | 75 % | 0.0008 |
| tau 240 | 34.89 | -0.44 (-2.39 to 0.24) | 62 % | 0.03 |
| tau 60, slow level | 34.15 | -0.94 (-2.05 to 0.85) | 58 % | 0.13 |
| tau 120, slow level | 34.32 | -0.85 (-2.03 to 1.44) | 58 % | 0.17 |
| tau 240, slow level | 34.49 | +0.39 (-2.05 to 2.41) | 46 % | 0.43 |

**The design choice, and how it departs from the plan.** Section F says the choice among the six is made on
development patients "by the live estimate's RMSE". The plan of 7 Oct turned that into: lowest cohort-median
live RMSE at k = 3, a tie within 0.1 mg/dL going to the simpler design. That rule selects **tau 60 with the
slow level**. It is not used. The design frozen for the test run is **tau 120 without the slow level**, chosen
by the **median paired difference from the control** at k = 3 (the quantity F1 tests), with the same tie rule;
the runner-up is 0.25 mg/dL behind.

- Why: every design is scored against the same control, so the cohort median of the RMSE differs between
  designs only through which patient happens to sit in the middle. The paired difference removes that. The
  design the plan's rule selects is better than the control in 58 % of development patients, with an interval
  that crosses zero.
- This was decided by the team lead after seeing the table above. It is a choice on development data, made
  before the test run; it is still a departure from the written rule, and a reader should weigh F1 knowing it.
- Before the review fixes the same criterion selected tau 60 without the slow level (-1.47 against -1.44 for
  tau 120). That table included the same-minute reading described next.
- tau 120 without the slow level was also the code default from the exploration of 4 Oct.

**"Only fingersticks already taken" is read strictly.** The live estimate at a minute uses fingersticks
stamped before that minute. In the Shanghai sheets every hidden fingerstick shares its row with a sensor
reading, and an estimate allowed to read it is scored there on fingerstick-against-sensor agreement. On
development patients that reading accounted for a third to a half of the tau 60 effect. **F1 is judged on the
strict estimate.** The at-or-before variant is reported beside it, with no bar.

**Other readings of the text, fixed as coded.**

- Cohort: the Gate 2 coverage rule also applies (it removed no development recording). "At least k + 2
  days" is measured to the last sensor reading. The cohort is the same under every thinning rule; with no
  fingerstick kept, the estimate is the control.
- The sensor-scale line is the patient's own when there are at least 8 calibration pairs spanning more than
  40 mg/dL (slope kept within 0.6 to 1.2), the development patients' pooled slope with the patient's own
  offset with 3 to 7 pairs, and the pooled line otherwise. Calibration pairs use sensor readings from before
  the split only. The run reports how many recordings fell in each case.
- Thinning: "two a day" keeps the first and the last fingerstick of the clock day; "one every second day"
  counts clock days from the day the sensor came off and keeps that day.
- Accuracy against a hidden fingerstick: the fingerstick is predicted from fingersticks stamped before it;
  the control and the live estimate are mapped back to the fingerstick's scale; the real sensor is scored as
  read. All five Clarke zones are kept.
- The in-hindsight estimate is the exact smoothed mean of the filter's model.
- F1 and F2 are judged at k = 3 only; k = 5 is reported without a verdict. A 95 % percentile interval for
  each median paired difference is reported (2,000 resamples of patients, seed `config.SEED`).

**Outputs deferred, declared.** Section F also lists error in mean glucose, time above 180 and time in range
against the stale report and the plain fingerstick average, and error by day since the sensor came off. They
are not in this run. They will be computed by a second guarded command (Plan 4) with `estimates` and
`FilterConfig` as committed for this run. They are descriptive and carry no bar; that second pass reads the
same test patients after F1 is known, and is declared here for that reason.

**Guards on the command.** `--confirm` runs only with the frozen filter, at k = 3 and 5, on committed code, and
refuses when a confirmatory result is already on disk. The primary result (k = 3, all fingersticks) is written
before anything else is computed.

### Note to Amendment 3, descriptive outputs and the second pass of section F, 8 Oct 2026 (before any of them reads a test patient)

Written after the three confirmatory runs of Amendment 3 (sections M, P and F) were known and before any
output below was computed for a test patient. No bar is added, changed or removed: everything here is
descriptive, as registered. This note fixes how the registered words become code, so that those choices
cannot be made after the numbers. Task-level plan: `docs/plans/2026-10-08-chhaya-plan-4-expiry-band-staleness.md`.

**What had been seen when this was written.**

- The confirmatory results of sections M, P and F on test patients, and the Gate 2 results, including the
  range of per-patient band coverage (0.60 to 0.99) and, from the break test of 3 Oct on the registered run,
  that the twin's advantage held on each of the first five days after the sensor and reversed on the sixth.
- From the counts of 4 Oct, on all Shanghai patients including the test split: that the sensor mean falls by
  more than 20 mg/dL between the first and last three days in 29 % of recordings of eight days or more and
  rises by that much in 5 % (a quantity close to the drift label below), and which patients were recorded more
  than once, with the gaps between their recordings.
- The code for these outputs, written and tested on synthetic recordings in a scratch copy of the repository,
  and **one run of each output on development patients** from that copy. Those runs showed, at k = 3 unless
  said otherwise:
  - Second pass of F (24 patients): the stale report missed the hidden window's mean by a median of 14.8 mg/dL
    (8.9 at k = 5) and the report rebuilt in hindsight missed it by 12.1 (11.4 at k = 5); the rebuilt report
    was not better than the stale one on time above 180 (9.9 against 8.8 points) or time in range (13.0
    against 9.4). Patients who test more often gained more from the live estimate (Spearman -0.67).
  - Expiry, Shanghai (49 patients): a day's mean lay a median of 10.8 mg/dL from the report inside the wear
    and 9 to 15 on days 1 to 11; inside each patient the distance grew by 0.56 mg/dL per day (interval 0.28 to
    1.40).
  - Expiry, CGMacros (25 patients): the twin was closer than its control on every day that at least 23
    patients reached (days 1 to 7; days 1 to 5 at k = 5) and further on the later days, which half the patients
    or fewer reach and which are the last days of their sensor. Band coverage fell on those same days.
  - Case series: three of the eight patients are development patients; one of them had moved by more than
    20 mg/dL, with a treatment change.
  - Band (25 patients, k = 5): mean coverage 0.874 before; the rule below chose one factor, 0.78.
  - Staleness (25 recordings, 8 drifted): AUROC 0.735 with the threshold set on the same recordings, against
    0.728 for the plain fingerstick average.
- **Three things were changed after those development runs**, and nothing else: the test of each day against
  day 0 was turned to ask "further than inside the wear" (it had asked the opposite); the AUROC of the number
  of fingersticks was added beside the alarm; and the rule for a band factor per day was tightened twice (a day
  must be reached by 80 % of the cohort; the per-day design must not leave fewer patients within 70 to 90 %),
  because the first version fitted a factor on the last days of the wear, where half the patients are gone.
  Under the first version the per-day design was chosen; under the rule below, the single factor.
- No output below had been computed for any test patient, by any code.

**Common readings.**

- *Day since the sensor.* 24-hour blocks counted from the split; day 1 is the first 24 hours. A day of a
  recording is scored when it holds at least 48 sensor readings. A day reached by fewer than 6 patients keeps
  its medians and gets no paired comparison. Each by-day summary records what share of the cohort reaches the
  day.
- *A report.* Mean glucose, percent of readings above 180 mg/dL and percent within 70 to 180, on the
  sensor's scale. The stale report is these three numbers from the calibration window. Errors are absolute
  differences from the same numbers of the hidden sensor readings.
- *Day 0, inside the wear.* Each 24-hour block of the calibration window against the report of its other
  blocks, averaged. It uses k - 1 days where a later day is read against k, so it slightly overstates the
  error of a report that has not aged. Each later day's distance from the report's mean is compared with it,
  one-sided ("further than inside the wear").
- *Inside each patient.* Recordings end at different lengths, so a curve of daily medians mixes ageing with
  who is still recording. The least-squares slope of each quantity on the day, inside each patient with at
  least three scored days, is reported as a median with its interval.
- *Statistics.* The patient is the unit; recordings of one patient are averaged first. Medians over patients;
  paired differences with 95 % percentile bootstrap intervals (2,000 resamples of patients, seed
  `config.SEED`) and one-sided signed-rank p-values. They are reported as description. None is a verdict.

**F, second pass** (`python -m chhaya.eval.fingersticks_report`).

- Cohort, k, map and estimator are those of the confirmatory run: `estimates` and `FilterConfig` are imported
  unchanged. Before anything is written the pass recomputes, at k = 3 and k = 5, the number of patients, the
  control's median RMSE and the live and in-hindsight median paired differences, and stops if any differs
  from `results/fingersticks/shanghai/summary.json` by more than 1e-6.
- *Chhaya's report* is read from the **in-hindsight** estimate (the registration calls it the estimate "for
  the retrospective report"). The live estimate and the daily shape alone are reported beside it.
- *Time above 180 and time in range from an estimate.* Each estimated value is the centre of a normal
  distribution whose standard deviation is one number per recording: the root-mean-square difference between
  the calibration readings and the daily shape built without their own clock day. The probabilities are
  averaged. The plain count of crossings is reported beside it for the in-hindsight estimate.
- *The plain fingerstick average.* All hidden fingersticks: their mean, the share above 180 and the share
  within 70 to 180. The comparator is the average on the sensor's scale, by the same line the estimator
  uses; the average as read from the meter is reported beside it.
- *Comparisons reported*, for each of the three numbers: in hindsight against the stale report, against the
  fingerstick average and against the shape alone; live against the stale report; the fingerstick average
  against the stale report.
- *Error by day:* RMSE of the control, the live and the in-hindsight estimate against the hidden sensor; the
  distance of the day's mean from the report's mean and the share of patients beyond 20 mg/dL; the error of
  the in-hindsight estimate's daily mean.
- *Fingersticks per day:* over the whole recording (the cohort rule's quantity) and in the hidden window,
  with quartiles, for the test cohort and beside it the development cohort; and the Spearman correlation
  between hidden-window density and the live gain. This checks the guess in the fingerstick record that
  test patients gained more because they test more.

**Expiry** (`python -m chhaya.eval.expiry {shanghai,cgmacros,cases}`).

- *Shanghai, by day.* The control of section F (half the average day, half the mean, from the first k days)
  on every recording that passes the Gate 2 rule at k, at k = 3 and k = 5. No fingerstick is read, so the
  cohort is wider than section F's. Reported: the control's RMSE, the distance of the day's report from the
  stale report, the share of patients whose daily mean has moved by more than 20 mg/dL, day 0, slopes.
- *CGMacros, by day.* `run_reveal` with its defaults at k = 3 and k = 5, exactly as Gate 2. The traces must
  give back, per recording, the RMSE and the band coverage in `results/gate2/cgmacros-test/metrics.csv`
  within 1e-6, or nothing is written. Reported by day: the twin, its control and the average day; the twin
  against its control (paired); band coverage; the twin's daily mean against the stale report's mean; the
  type 2 group beside the whole cohort.
- *Case series.* Every Shanghai patient with more than one recording: eight patients, nine later wears,
  development and test patients together, since nothing is fitted across patients. The earliest wear is the
  reference; its daily shape, from all of its readings, is read at the later wear's clock times. Beside the
  old shape's RMSE: what the later wear's own shape gives for a day it has not seen, and the same inside the
  first wear. Treatment is stated per wear from the files (any insulin, pump, whether the agents list
  changed). No test and no interval. Two wears are two sensors, so a difference between them includes the
  difference between the sensors.

**Band** (`python -m chhaya.eval.calibrate`).

- The band's two half-widths about the estimate are multiplied by a factor from 0.50 to 2.00 in steps of
  0.01. The single factor is the one whose mean coverage over development patients is closest to 80 % at
  k = 5 (of two equally close, the one nearer 1).
- A factor per day is fitted for the consecutive days reached by at least 10 development patients and at
  least 80 % of them; later days use the last one.
- The choice is made on development patients left out of the fit, one at a time. The factor per day is used
  only if it brings each day's coverage closer to 80 % by at least 2 points on average **and** leaves no
  fewer patients within 70 to 90 %. Otherwise the single factor is used.
- Reported on test patients at k = 5, and at k = 3 with the same factor: mean coverage, its range, the number
  of patients within 70 to 90 %, before and after, and coverage by day.
- **Which band the product shows.** The recalibrated band is used only if, on test patients at k = 5, its mean
  coverage is no further from 80 % than before and no fewer patients fall within 70 to 90 %. Otherwise the
  band stays as Gate 2 scored it and the result is published as "the recalibration did not transfer".
- `run_reveal` and the Gate 2 results folder are not changed. The factor is applied to cached traces.

**Staleness alarm** (`python -m chhaya.eval.staleness`).

- Cohort: that of section F. Primary k = 3; k = 5 is reported. The unit is the recording, as registered;
  intervals resample patients.
- *Drift:* the hidden-window sensor mean differs from the calibration mean by more than 20 mg/dL, in either
  direction.
- *Surprise:* a hidden fingerstick, mapped to the sensor's scale by the estimator's line, minus the daily
  shape at its clock time, divided by the square root of (the spread defined above, squared, plus the
  filter's fingerstick spread of 15 mg/dL, squared).
- *The sum:* two-sided, with an allowance of half a standard deviation per fingerstick; a recording's score
  is its maximum. The alarm fires at the first fingerstick where the sum is above the threshold.
- *Threshold:* the smallest observed score that at most 10 % of the development recordings without drift lie
  above.
- *Reported on test recordings:* AUROC with its interval; sensitivity and false-alarm rate at the threshold;
  the median number of days from the split to the alarm, among drifted recordings that alarmed.
- *Beside it, with no bar:* the absolute difference between the mean of the mapped hidden fingersticks and
  the calibration mean, with a threshold set the same way; the AUROC difference with its interval; and the
  AUROC of the number of fingersticks alone, because a sum over more fingersticks can only grow.
- The label and both scores look back over the same hidden window. Only "days to alarm" is prospective.

**Guards on every command that reads test patients.** `--confirm`; committed code under `src/`; refusal when
its results folder already holds a summary. Results folders hold aggregates; the case series holds one row
per later wear with derived quantities and no glucose readings. Reveal traces are written under the data
folder, which is not committed.

**Order and cuts, unchanged:** the second pass of F, then expiry, then the band; the staleness alarm only if
those are done by 16:00 on 10 Oct. Whatever is cut is stated as not done.

**Added 8 Oct 2026, after two independent reviews of the code for the outputs above and before any test
patient was read by it.** The reviews found no path by which a hidden sensor reading or a test patient reaches
an estimate, a shape, a spread or a fitted value. They found defects, each fixed with a test that failed first
(commits `d4df1a0` and `e4e0076`). What a reader of the note above should know:

- *The spread.* The code left the scored day out of the average-day half of the daily shape but not out of
  the mean half. It now leaves it out of both, as written above. On development patients at k = 3 the
  in-hindsight report's error in time above 180 went from 9.9 to 9.8 points and in time in range from 13.0 to
  13.1, and day 0's shape error from 31.3 to 33.6 mg/dL. No other figure listed above moved, and the band's
  design is the same (one factor, 0.78).
- *The band.* Its half-widths are signed, so a factor of 1 is exactly the band Gate 2 scored, also where an
  estimate lies outside its own band; the code checks this recording by recording. On the development traces
  no estimate lies outside its band. The test pass reads the band file only if it is committed and unchanged,
  and records its hash.
- *Tracing test patients* (`python -m chhaya.eval.traces --split test`) needs `--confirm`, committed code and
  the registered settings, and stops unless every recording Gate 2 scored is reproduced. It is the one command
  that reads test patients and may be repeated: it writes no result, only a cache, under the data folder, of
  estimates whose scores are already committed. The three guards listed above apply to the commands that
  write results.
- *Two reported quantities.* The share of the cohort that reaches a day is taken over every patient with a
  row on any day (it had been taken over the best-attended day). Where a day is compared with day 0, the share
  reported is of patients further from the report than inside the wear.

Nothing else in the note changes.

**Added 8 Oct 2026, after two independent reviews of the code for the staleness alarm and before any test
recording was scored by it.** The reviews found no path by which a hidden sensor reading reaches a surprise, a
score or a threshold, and none by which a test recording reaches a threshold. What changed (commit `7adc06c`),
each with a test that failed first:

- *The threshold.* The code took a score one rank too high whenever the number of development recordings
  without drift is a multiple of ten. It is now the rule as written above. With 17 such recordings at k = 3
  and 15 at k = 5 the thresholds are the same as before.
- *Added beside the alarm, with no bar:* the same cumulative sum over the fingersticks of the first two days
  after the sensor only, with a threshold set the same way; and an interval for the AUROC of the number of
  fingersticks. The reason: a sum over more fingersticks can only grow and hidden windows differ in length,
  while every recording in the cohort has two hidden days. The registered alarm stays the sum over the whole
  hidden window; the two-day sum is reported, not primary. It was added after the development figures below
  had been seen.
- *Guards.* A pass over test recordings refuses a patient who is also among the development recordings,
  refuses filter constants other than the registered ones (time constant 120 minutes, no slow level,
  fingerstick spread 15 mg/dL), and is closed by any file of an earlier pass, not by the summary alone. A
  calibration length at which no development recording is without drift keeps its row, with the reason.
- *What had been seen on development recordings* (thresholds set on the same recordings, so in-sample). At
  k = 3: 25 recordings, 8 drifted (7 downward), thresholds from 17. AUROC of the alarm 0.721 (interval 0.45 to
  0.95); it was 0.735 before the fix to the spread recorded in the addendum above. First two days only: 0.757
  (0.47 to 0.97). Plain fingerstick average: 0.728 (0.44 to 0.96). Number of fingersticks alone: 0.559 (0.32
  to 0.78). The three caught 4, 5 and 3 of the 8 drifted recordings, each with 1 false alarm in 17. At k = 5
  (21 recordings, 6 drifted): 0.744, 0.667 and 0.789.

Nothing else in the note changes.

### Note to Amendment 3, a band for the fingerstick estimate, 8 Oct 2026 (before its code, and before it is computed for any patient)

Decided at the start of Milestone 4 (`docs/decisions/2026-10-08-m4-kickoff.md`). The estimates of section F
(control, live, in hindsight) have no band, and rule 5 forbids drawing an estimate without one. This note adds
one descriptive output, with no bar, and fixes how it is computed before any of it is written. No bar is added,
changed or removed. The estimator of section F is frozen: its filter (time constant 120 minutes, no slow
level, spreads of 25 and 15 mg/dL) and its code are not touched.

**What had been seen when this was written.**

- Every confirmatory result of Amendment 3 on test patients, among them the size of the error of section F's
  estimates on held-out patients (control RMSE about 37 mg/dL at k = 3; live 2.8 and hindsight 9.5 closer) and
  the staleness pass, which uses the same fingerstick surprises and the same per-patient spread as its scale.
- The two spreads of the filter. They are its registered constants and are not tuned here.
- **No band of these estimates, and no coverage of one, had been computed for any patient, development or
  test, by any code.** The module that computes them did not exist.

**What is estimated.** The live estimate (fingersticks stamped strictly before the minute, as F1 was scored)
and the in-hindsight estimate, on the sensor's scale, at the hidden sensor timestamps. Cohort: section F's
(`why_not`). Primary k = 3; k = 5 is reported.

**The band.** Symmetric about the estimate, half-width `1.2816 x s(t) x c`, where `s(t)` is the spread the
frozen filter itself assigns to the fading deviation at minute `t`, given only the times of the fingersticks it
has used: 25 mg/dL far from any fingerstick, 12.9 mg/dL at one, in between by the filter's own recursion; for
the in-hindsight estimate, the smoothed spread. `s(t)` does not depend on any reading. Two constructions are
compared, and nothing in either is fitted:

1. **filter**: `c = 1`. The filter's own spread, the same constants for every patient.
2. **patient**: `c` is the patient's own spread about their daily shape in the calibration window
   (`profile_sigma`, each day read against a shape built from the other days) divided by 25. The band keeps
   the filter's narrowing near a fingerstick and takes its width from the patient.

Both use only the calibration window and the times of hidden-window fingersticks. A test changes every hidden
sensor reading and asserts that the estimate and both edges of the band do not move.

**The choice, on development patients only.** At k = 3, for the live estimate: per recording, the share of
hidden sensor readings inside the band; recordings of one patient are averaged; then the mean over patients.
The construction whose mean lies closer to 80 % is frozen. If the two distances differ by less than one
percentage point, the one with more development patients within 70 to 90 %; if still tied, the first. The
frozen construction is used for both estimates and both calibration lengths. The choice and the development
figures are written into an addendum to this note before the test pass.

**What the one pass over test patients reports** (`python -m chhaya.eval.stickband --confirm`, results in
`results/stickband/shanghai/`), for the frozen construction, for the live and the in-hindsight estimate, at
k = 3 and k = 5: mean coverage over patients, the smallest and the largest patient, how many patients fall
within 70 to 90 %, the median over patients of the mean half-width in mg/dL, and coverage by day since the
sensor with the share of the cohort that reaches each day. The patient is the unit. The construction that was
not chosen is reported beside it, marked as not chosen. Descriptive: no bar, no verdict.

**What the product does with it, fixed now.** On Shanghai patients the dashboard draws the estimated trace
with the frozen band and, beside it, the measured coverage on held-out patients (mean and range). The band is
called an "80 % band" on screen only if that mean lies within 70 to 90 %; otherwise it is called "the band",
with the measured figure. If the mean lies below 60 % or above 95 %, the band is not a fair picture of the
error: it is not drawn, and neither is the estimated trace, and those patients show measured things only.

**Guards**, as for the other descriptive passes: committed code; the registered filter constants; a patient
may not be both a development and a test patient of the run; the pass over test patients is made once and is
closed by any file of an earlier one.

**Cut rule.** Science stops at midnight on 10 Oct. If the pass over test patients has not been run by 10 Oct
2026, 16:00, it is not run, the module stays in the repository with its development figures, and Shanghai
patients show measured things only.

**Added 8 Oct 2026, after two independent reviews of the code and one run on development patients, and before
any test patient was scored by it.**

*The reviews* found no path by which a hidden sensor reading reaches an
estimate, an edge of the band, the patient's scale or the choice of construction, and none by which a test
patient reaches the choice or the pooled map. Both compared the module's mean and spread with the exact
Gaussian posterior of the filter's own model, computed by plain linear algebra, and found agreement to 1e-13;
the mean is the frozen estimator's. What changed (commits `265c8e1` and `c07b61b`), each with a test that failed
first or that fails on the wrong code the earlier tests let through:

- Tests: the exact posterior, for the live, strictly-before and in-hindsight spreads, with two fingersticks
  in one minute; leakage over extreme and random hidden values, both calibration lengths, a gap and readings
  off the 15-minute grid, and with hidden rows removed; the patient's scale read on the clock of the day; the
  choice made once, on the live estimate at the first k; the band at a fingerstick's own minute; hindsight
  narrower than live in the middle of a gap; by-day shares with recordings of different lengths.
- A recording that cannot be given a band has its own error and keeps a row that names the patient; any other
  error stops the run. Everything the development recordings decide is computed for every k before a test
  recording is scored, and a failure at k = 5 leaves a row with its error and keeps the result at k = 3.
- The report names the two estimates and the scale, says how many recordings were outside the cohort and why,
  marks both constructions as chosen or not chosen (also by day), and marks a day that fewer than six patients
  reach.

*Readings of the note, fixed as coded.* A reading on an edge of the band is inside it, and a patient at exactly
70 or 90 % is within 70 to 90 %. A recording with no spread about its daily shape in the calibration window
cannot be given the `patient` band; it is left out of both constructions, so the two are always compared on the
same recordings, and it is reported as a row with its reason. The share of the cohort that reaches a day is
taken over patients with at least one scored day.

*What the development run showed* (`results/stickband/shanghai-dev/`; in-sample for the choice). Percent of
hidden sensor readings inside the band, mean over patients, then the smallest and the largest patient, patients
within 70 to 90 %, and the median half-width in mg/dL:

| k | estimate | `filter` | `patient` |
|---|---|---|---|
| 3 (25 recordings, 24 patients) | live | 60.2 (24.6 to 88.4; 9 of 24; 30.3) | 77.4 (46.3 to 98.8; 15 of 24; 44.8) |
| 3 | in hindsight | 62.1 (22.2 to 86.9; 9 of 24; 28.1) | 78.7 (42.8 to 97.6; 12 of 24; 40.0) |
| 5 (21 recordings, 20 patients) | live | 63.8 (32.7 to 89.8; 8 of 20; 30.3) | 79.7 (46.0 to 94.1; 15 of 20; 40.8) |
| 5 | in hindsight | 65.4 (30.3 to 89.6; 10 of 20; 28.2) | 80.3 (38.2 to 94.7; 13 of 20; 36.7) |

No recording failed. Coverage of the `patient` band by day, live, k = 3: 81 % on days 1 and 2, 79 % on day 3,
then 71 to 78 % on days 4 to 11, with half the cohort left by day 10. That was seen and nothing was changed
because of it.

*The choice.* At k = 3 on the live estimate the two constructions lie 19.8 and 2.6 points from 80 %. By the
rule above the frozen construction is **`patient`**, written into the code (`FROZEN = "patient"`). The filter's
own spread is too narrow on its own: the error of the estimate is larger than the filter's model of it.

Nothing had been computed for any test patient, by any code, when this was written. Nothing else in the note
changes.
