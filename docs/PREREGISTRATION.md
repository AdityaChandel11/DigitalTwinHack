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
