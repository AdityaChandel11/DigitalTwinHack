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
