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
