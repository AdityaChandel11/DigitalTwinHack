# Chhaya Plan 4: Expiry, Band, Staleness and the Second Pass of Section F Implementation Plan

> **Status, 8 Oct 2026, later:** Tasks 0 to 8 are done, each pass over held-out patients run once with its record in `docs/decisions/2026-10-08-*.md`. Nothing was cut. Only Task 9 is left.

> **Status, 8 Oct 2026:** Tasks 0 to 5 are done. The code blocks of Tasks 1 to 5 show each file as first committed. The independent reviews of Task 6 then changed all five modules (commits `d4df1a0` and `e4e0076`; the list is at the end of this plan, under "Changes made by the reviews of Task 6"). **The repository is the source of truth for those files, not the blocks below.** Tasks 7 to 9 are written against the reviewed code.

**Goal:** Produce the last evidence of Milestone 3: what the frozen fingerstick estimator says at the level a doctor reads, how fast a sensor report stops being true (by day on both datasets and in the eight re-recorded patients), a recalibrated band, and, if time allows, the staleness alarm.

**Architecture:** Seven new modules and no change to any existing source file, so the estimators that Gate 2 and section F scored stay byte-identical. Every pass over test patients first recomputes numbers that are already committed and refuses to write unless they match, then refuses to run a second time. Per-reading arrays (reveal traces) go to a git-ignored cache under the data folder; results folders hold aggregates only.

**Tech Stack:** Python 3.13, NumPy, pandas, SciPy (normal distribution, Wilcoxon, Spearman), scikit-learn (AUROC only), the existing JAX twin (reveal traces only), pytest, ruff.

**Spec:** `docs/specs/2026-10-04-chhaya-m3-design.md` (experiments E, B, S and the last line of F); registered text in `docs/PREREGISTRATION.md`, Amendment 3, section F ("Also reported"), its note of 8 Oct ("Outputs deferred, declared") and "Descriptive, no bar". Task 0 of this plan adds the note that fixes how those words become code.

## What decides what we claim

All four outputs are descriptive: Amendment 3 gives them no bar, so there is no PASS or FAIL here. What they decide is the wording of two clauses of the headline.

| Clause | What Plan 4 measures | What we will be able to say |
|---|---|---|
| "How long that sensor report stays true" | Distance of each later day's mean from the report's mean, against the same distance inside the wear; its slope inside each patient; the same in a free-living cohort; eight patients weeks later | A number of mg/dL per day and a share of patients moved by more than 20 mg/dL by day d, with intervals, or "no ageing detectable within ten days" |
| "What keeps it true" (fingersticks) | Error of the report rebuilt from fingersticks against the stale report and against the logbook average | Expected from the development look: the rebuilt report does **not** beat a week-old sensor report on mean or time in range, and does beat the plain fingerstick average on time above 180. If so, that is what we say |
| "With an honest band" | Coverage on held-out patients after a factor chosen on development patients | "Calibrated on average, N of M patients within 70 to 90 %" |
| "When to wear a sensor again" | Alarm on fingerstick surprises against real drift | An AUROC with a wide interval, beside the plain fingerstick average. If cut: the dashboard shows days since the sensor and the README says the alarm is untested |

## Calendar and cut rules

| When | Work |
|---|---|
| Thu 8 Oct, afternoon | Tasks 0 to 5; start the development traces (background, about 15 minutes) |
| Fri 9 Oct | Task 6, then Task 7 in this order: second pass of F, expiry (Shanghai, case series, CGMacros), band |
| Sat 10 Oct, by 16:00 | **Checkpoint.** Staleness (Task 8) starts only if the three records of Task 7 are committed |
| Sat 10 Oct, midnight | Science stops. Task 9 |

Cut order if time runs out, as registered: staleness first, then the band, then expiry by day. The second pass of F and the case series are not cut. An output that is cut becomes a "not done" line in the README (Task 9 has the sentences).

## Global Constraints

- Split by patient only: `chhaya.config.is_dev_patient`. Anything fitted or chosen (band factor and its design, alarm thresholds, the pooled sensor map) uses development patients only.
- No existing file under `src/` is modified by this plan. If a step seems to need it, stop: the estimator would no longer be the one that was scored.
- Test patients are read only by a command given `--confirm`, on committed code, once per output. Each such command first reproduces committed numbers and writes nothing if they differ.
- In the hidden window nothing but fingersticks (Shanghai) or meals and activity (CGMacros) reaches an estimate. A stale report, a daily shape, a spread and a band factor come from before the split.
- Results folders hold aggregates only. Reveal traces are per-reading patient data: they live under `DATA_DIR/derived/traces/` (git-ignored) and never under `results/`. The case series has one row per later wear with derived quantities only.
- Descriptive outputs carry no bar and no verdict. Reports say "Descriptive: no bar". Paired comparisons give a median difference, a 95 % percentile bootstrap interval over patients (2,000 resamples, seed `config.SEED`) and a one-sided signed-rank p-value, and are reported whatever they show.
- Glucose in mg/dL. `encoding="utf-8"` on every text read and write.
- `uv run ruff check src tests` and `uv run ruff format src tests` clean; line length 110.
- Docs and code change in the same commit. Each output gets `docs/decisions/<date>-<topic>.md` and a line in the roadmap Status table in the commit that adds its results.

**Running from a git worktree** (no `.venv`, no `data/` there): use the main checkout's interpreter.

```bash
PY="/c/Users/prath/OneDrive/Desktop/Digital Twin Hack/.venv/Scripts/python.exe"
export PYTHONPATH="$PWD/src" CHHAYA_DATA_DIR="C:/Users/prath/OneDrive/Desktop/Digital Twin Hack/data" PYTHONIOENCODING=utf-8
```

Then read every `uv run python` below as `"$PY"` and every `uv run pytest` as `"$PY" -m pytest`.

## Review Focus

Inputs and failure modes the registered text is silent on, most likely first. Each is pinned by a test in the task that owns the code.

- **A hidden day with a sensor gap, or the last partial day of a recording.** Expected: not scored as a day, not averaged as if whole. `test_daily_rows_score_each_day_with_enough_readings` (Task 1).
- **A second pass whose estimator is no longer the committed one** (an edited default, a changed cohort rule, another k). Expected: nothing is written, not even the k that matched. `test_the_pass_is_written_only_when_it_reproduces_the_run_it_repeats` (Task 2), `test_traces_must_give_back_what_gate2_committed` (Task 3).
- **A test patient's trace in the development folder.** Expected: refused before a factor is fitted on it. `test_a_test_patients_file_in_the_development_folder_is_refused` (Task 3).
- **A later wear that starts at another clock time than the first** (case series). Expected: the old shape is read by the later wear's clock, not by minutes since its start. `test_a_shape_is_read_by_the_clock_of_the_recording_it_is_applied_to` (Task 4).
- **A band of zero width at some reading** (a collapsed ensemble). Expected: a finite factor, never a division by zero. `test_a_band_with_no_width_cannot_divide_by_zero` (Task 5).

Also covered: a patient recorded once (no case), a cohort with no recording, a bootstrap resample in which every recording drifted or none did, no development recording without drift, a development cohort with no calibration pair.

## What was run before this plan was written

The same practice as Plan 1. Every module and test below was written in a scratch copy of the repository and run there on 8 Oct: 60 new tests pass, the full suite passes (274 tests, about four and a half minutes), `ruff` is clean. The Shanghai commands were also run once on **development patients** from that scratch copy, and the CGMacros development traces were built once. No command was run on any test patient. What those development runs showed is in the note of Task 0, where it belongs. The numbers must come out the same from the committed code in Task 6.

## File Structure

| File | Responsibility |
|---|---|
| `src/chhaya/eval/descriptive.py` (new) | Days since the sensor, the three numbers of a report, ageing against a report, paired summaries, the guards and writers every pass shares |
| `src/chhaya/eval/fingersticks_report.py` (new) | Second pass of section F: report-level errors, error by day, fingersticks per day |
| `src/chhaya/eval/traces.py` (new) | Reveal traces cached per recording and k; the check that they are what Gate 2 scored |
| `src/chhaya/eval/expiry.py` (new) | Expiry by day (Shanghai profile, CGMacros twin) and the case series |
| `src/chhaya/eval/calibrate.py` (new) | Band factor: fit, choice of design, report |
| `src/chhaya/twin/staleness.py` (new) | The cumulative sum and its alarm time |
| `src/chhaya/eval/staleness.py` (new) | Drift label, thresholds from development recordings, AUROC and alarm statistics |
| `tests/test_descriptive.py`, `test_fingersticks_report.py`, `test_traces.py`, `test_expiry.py`, `test_calibrate.py`, `test_staleness.py` (new) | Tests; `test_expiry.py` reuses `fake_trace` from `test_traces.py` |
| `docs/PREREGISTRATION.md` (append) | The note of Task 0 |
| `docs/decisions/<date>-fingersticks-report.md`, `-expiry.md`, `-band.md`, `-staleness.md` (new) | One record per output |

Results: `results/fingersticks/shanghai-report/`, `results/expiry/{shanghai,cgmacros,cases}/`, `results/calibrate/cgmacros/`, `results/staleness/shanghai/`; development runs write beside them with a `-dev` suffix (`shanghai-dev-report` for the second pass).

---

### Task 0: Register the readings, before any code

**Files:**
- Modify: `docs/PREREGISTRATION.md` (append at the end; nothing above is edited)

- [ ] **Step 1: Append the note**

Append the text below to `docs/PREREGISTRATION.md`. If the commit is made on 9 Oct, change the date in its heading and nothing else.

````markdown

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
````

- [ ] **Step 2: Commit**

```bash
git add docs/PREREGISTRATION.md docs/plans/2026-10-08-chhaya-plan-4-expiry-band-staleness.md docs/PROGRESS.md docs/plans/2026-10-02-chhaya-roadmap.md docs/PROJECT_GUIDE.md
git commit -m "register: readings for the descriptive outputs and the second pass of section F; Plan 4"
```

---

### Task 1: Shared pieces of the descriptive outputs

**Files:**
- Create: `src/chhaya/eval/descriptive.py`
- Test: `tests/test_descriptive.py`

**Interfaces:**
- Consumes: `chhaya.eval.fingersticks._interval(diff, n_boot=2000, seed=SEED) -> (lo, hi)`, `chhaya.eval.fingersticks.calibration_pairs(rec, k_days) -> DataFrame[t_min, cbg, cgm, ...]`, `chhaya.eval.gate2._paired_p(diff) -> float`, `chhaya.eval.gate2._clean`, `chhaya.eval.gate2._git`, `chhaya.eval.baselines.lodo_average_day(day, tod, g)`, `chhaya.twin.assimilate.pooled_map(cbg, cgm) -> (intercept, slope)`.
- Produces (later tasks use these names exactly):
  - `REPORT_KEYS = ("mean", "tar", "tir")`, `MIN_DAY_READINGS = 48`, `MIN_DAY_PATIENTS = 6`, `MOVED_MGDL = 20.0`
  - `day_index(t, split: float) -> np.ndarray` (1 for the first 24 hours after the split)
  - `glucose_report(g) -> dict` and `estimated_report(est, sigma: float) -> dict`, both with keys `mean`, `tar`, `tir`
  - `profile_sigma(clock_min, g) -> float`
  - `aging(now: dict, report: dict) -> dict` with keys `dmean`, `abs_dmean`, `moved`, `abs_dtar`, `abs_dtir`
  - `daily_rows(t, split, truth, estimates: dict, min_readings=48) -> list[dict]` (keys `day`, `n`, `day_mean`, `day_tar`, `day_tir`, and `<name>_rmse`, `<name>_mean` per estimate); `day_report(row) -> dict`
  - `inside_the_wear(t, g, min_readings=48) -> dict | None`
  - `paired_summary(per, a, b, alternative="less") -> dict`; `summarise_days(df, pairs=()) -> list[dict]`; `slope_per_day(df, col) -> dict`; `excess_over_day_zero(df, col) -> list[dict]`
  - `pooled_line(dev_recs, k_days) -> (intercept, slope)`
  - `differences(found: dict, committed: dict, tol=1e-6) -> list[str]`; `check_committed(src_status: str | None) -> None`
  - `provenance(confirm: bool, **settings) -> dict`; `write_outputs(out_dir, result, report, prov=None) -> None`; `table(rows, columns=None, digits=1) -> str`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_descriptive.py`:

```python
import dataclasses
import json

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.eval import descriptive as ds

SPLIT = 3 * 1440.0


def test_days_since_the_sensor_are_24_hour_blocks_from_the_split():
    t = np.array([SPLIT, SPLIT + 1439, SPLIT + 1440, SPLIT + 4 * 1440 + 5])
    assert ds.day_index(t, SPLIT).tolist() == [1, 1, 2, 5]
    with pytest.raises(ValueError, match="before the split"):
        ds.day_index(np.array([SPLIT - 15]), SPLIT)


def test_a_report_states_mean_time_above_180_and_time_in_range():
    assert ds.glucose_report([100.0, 200.0, 60.0, 180.0]) == {"mean": 135.0, "tar": 25.0, "tir": 50.0}
    for empty in (lambda: ds.glucose_report([]), lambda: ds.estimated_report([], 20.0)):
        with pytest.raises(ValueError, match="no readings"):
            empty()


def test_a_flat_estimate_at_180_is_above_it_half_the_time_once_its_spread_is_counted():
    est = np.full(96, 180.0)
    assert ds.glucose_report(est)["tar"] == 0.0  # counting crossings of a smooth estimate undercounts
    r = ds.estimated_report(est, sigma=30.0)
    assert abs(r["tar"] - 50.0) < 1e-9 and abs(r["tir"] - 50.0) < 0.02 and r["mean"] == 180.0
    assert ds.estimated_report(est, sigma=0.0) == ds.glucose_report(est)


def test_the_spread_recovers_the_time_above_180_that_a_smooth_estimate_misses():
    rng = np.random.default_rng(0)
    smooth = 150.0 + 30.0 * np.sin(np.linspace(0, 20 * np.pi, 4000))
    truth = smooth + rng.normal(0.0, 25.0, smooth.size)
    true = ds.glucose_report(truth)
    assert abs(ds.estimated_report(smooth, 25.0)["tar"] - true["tar"]) < 2.0
    assert abs(ds.glucose_report(smooth)["tar"] - true["tar"]) > 5.0


def test_the_spread_around_the_daily_shape_is_measured_on_days_the_shape_has_not_seen():
    rng = np.random.default_rng(1)
    clock = np.arange(0, 4 * 1440, 15)
    g = 140.0 + rng.normal(0.0, 10.0, clock.size)
    assert g.std() < ds.profile_sigma(clock, g) < g.std() + 1.0  # a little above the noise, never below it
    one_day = clock < 1440  # no other day to learn from: the spread about that day's mean, not zero
    assert abs(ds.profile_sigma(clock[one_day], g[one_day]) - g[one_day].std()) < 1e-9


def test_daily_rows_score_each_day_with_enough_readings():
    t = SPLIT + np.arange(0, 2 * 1440 + 20 * 15, 15.0)  # two full days and five hours of a third
    truth = np.full(t.size, 150.0)
    est = truth + np.where(t >= SPLIT + 1440, 10.0, 0.0)
    rows = ds.daily_rows(t, SPLIT, truth, {"shadow": est})
    assert [r["day"] for r in rows] == [1, 2] and rows[0]["n"] == 96  # the short third day is not scored
    assert rows[0]["shadow_rmse"] == 0.0 and abs(rows[1]["shadow_rmse"] - 10.0) < 1e-9
    assert rows[1]["shadow_mean"] == 160.0 and ds.day_report(rows[1]) == {
        "mean": 150.0,
        "tar": 0.0,
        "tir": 100.0,
    }


def test_aging_says_how_far_a_day_is_from_the_report():
    report = {"mean": 150.0, "tar": 20.0, "tir": 78.0}
    near = ds.aging({"mean": 162.0, "tar": 31.0, "tir": 68.0}, report)
    assert near == {"dmean": 12.0, "abs_dmean": 12.0, "moved": 0.0, "abs_dtar": 11.0, "abs_dtir": 10.0}
    assert ds.aging({"mean": 125.0, "tar": 20.0, "tir": 78.0}, report)["moved"] == 1.0  # 25 below also counts


def test_day_zero_is_one_day_of_the_wear_against_its_other_days():
    t = np.arange(0, 3 * 1440, 15.0)
    steady = ds.inside_the_wear(t, np.full(t.size, 150.0))
    assert steady["abs_dmean"] == 0.0 and steady["moved"] == 0.0
    third_high = np.where(t >= 2 * 1440, 180.0, 150.0)
    floor = ds.inside_the_wear(t, third_high)
    assert abs(floor["abs_dmean"] - 20.0) < 1e-9  # 15, 15 and 30 mg/dL: each day against the other two
    assert abs(floor["moved"] - 1 / 3) < 1e-9
    assert ds.inside_the_wear(t[:96], np.full(96, 150.0)) is None  # one day has no other day


def _per(n=10):
    return pd.DataFrame({"shadow": np.linspace(8, 12, n), "stale": np.linspace(10, 14, n)}, index=range(n))


def test_paired_summary_is_over_patients_and_ignores_a_patient_without_both():
    s = ds.paired_summary(_per(), "shadow", "stale")
    assert s["n_patients"] == 10 and s["median_diff"] == -2.0 and s["frac_better"] == 1.0 and s["p"] < 0.05
    assert s["diff_lo"] == s["diff_hi"] == -2.0 and s["median"] == 10.0 and s["median_against"] == 12.0
    per = _per()
    per.loc[0, "stale"] = np.nan
    assert ds.paired_summary(per, "shadow", "stale")["n_patients"] == 9
    empty = ds.paired_summary(per.iloc[:0], "shadow", "stale")
    assert empty == {"of": "shadow", "against": "stale", "alternative": "less", "n_patients": 0}
    worse = ds.paired_summary(_per(), "stale", "shadow", "greater")  # the same question asked the other way
    assert worse["median_diff"] == 2.0 and worse["p"] == s["p"] and worse["frac_better"] == 0.0
    with pytest.raises(ValueError, match="alternative"):
        ds.paired_summary(_per(), "shadow", "stale", "two-sided")


def _days():
    rows = []
    for p in range(8):
        for d in range(0, 5):
            if d == 4 and p >= 3:
                continue  # only three patients reach day 4
            rows.append(
                {
                    "patient_id": f"p{p}",
                    "rec_id": f"r{p}",
                    "day": d,
                    "control_rmse": 20.0 + 2.0 * d + p,
                    "twin_rmse": 19.0 + 2.0 * d + p,
                    "abs_dmean": 10.0 + (8.0 if d >= 3 else 0.0),
                    "moved": float(d >= 3 and p < 4),
                }
            )
    return pd.DataFrame(rows)


def test_days_are_summarised_over_patients_and_thin_days_get_no_comparison():
    by_day = {r["day"]: r for r in ds.summarise_days(_days(), (("twin_rmse", "control_rmse"),))}
    assert by_day[1]["n_patients"] == 8 and by_day[1]["control_rmse"] == 25.5
    assert by_day[1]["twin_rmse_vs_control_rmse"]["median_diff"] == -1.0
    assert by_day[3]["share_moved"] == 0.5 and "moved" not in by_day[3]
    assert by_day[4]["n_patients"] == 3 and "twin_rmse_vs_control_rmse" not in by_day[4]
    assert by_day[1]["share_of_cohort"] == 1.0 and by_day[4]["share_of_cohort"] == 3 / 8


def test_two_recordings_of_one_patient_count_once_per_day():
    df = pd.concat([_days(), _days().assign(rec_id="again", control_rmse=0.0)], ignore_index=True)
    day1 = next(r for r in ds.summarise_days(df) if r["day"] == 1)
    assert day1["n_patients"] == 8 and day1["control_rmse"] == 25.5 / 2


def test_the_slope_is_taken_inside_each_patient():
    s = ds.slope_per_day(_days(), "control_rmse")
    assert s["n_patients"] == 8 and abs(s["median_slope"] - 2.0) < 1e-9 and s["frac_rising"] == 1.0
    two_days = _days()[
        _days()["day"].isin([0, 1, 2])
    ]  # day 0 is not a day since the sensor: two days are too few
    assert ds.slope_per_day(two_days, "control_rmse") == {"column": "control_rmse", "n_patients": 0}


def test_each_day_is_read_against_the_same_patients_day_zero():
    rows = ds.excess_over_day_zero(_days(), "abs_dmean")
    by_day = {r["day"]: r for r in rows}
    assert sorted(by_day) == [1, 2, 3]  # day 4 has three patients
    assert by_day[1]["median_diff"] == 0.0 and by_day[3]["median_diff"] == 8.0
    assert by_day[3]["alternative"] == "greater" and by_day[3]["p"] < 0.05  # has it aged? yes, by day 3
    assert ds.excess_over_day_zero(_days()[_days()["day"] >= 1], "abs_dmean") == []


def test_a_second_pass_must_reproduce_the_committed_numbers():
    committed = {"n_patients": 29, "control_rmse": 36.708231}
    assert ds.differences({"n_patients": 29, "control_rmse": 36.7082312, "extra": 1.0}, committed) == []
    bad = ds.differences({"n_patients": 28, "control_rmse": 36.9}, committed)
    assert len(bad) == 2 and "committed 29, found 28" in bad[0]
    assert len(ds.differences({}, committed)) == 2


def test_the_pooled_sensor_line_needs_development_pairs():
    rec = make_recording(days=4, seed=1)
    with pytest.raises(ValueError, match="pooled sensor map"):
        ds.pooled_line([], 3.0)
    with pytest.raises(ValueError, match="pooled sensor map"):
        ds.pooled_line([rec], 3.0)  # a recording without fingersticks gives no pair
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)
    intercept, slope = ds.pooled_line([dataclasses.replace(rec, fingersticks=sticks)], 3.0)
    assert abs(slope - 1.0) < 1e-9 and abs(intercept) < 1e-6  # these fingersticks read the sensor exactly


def test_test_patients_are_read_only_on_committed_code():
    ds.check_committed("")
    with pytest.raises(SystemExit, match="uncommitted"):
        ds.check_committed(" M src/chhaya/eval/expiry.py")
    with pytest.raises(SystemExit, match="git"):
        ds.check_committed(None)


def test_outputs_are_strict_json_and_a_table_leaves_nested_values_out(tmp_path):
    result = {"n": np.int64(3), "ok": np.bool_(True), "nan": float("nan"), "rows": [{"day": 1, "x": 1.26}]}
    ds.write_outputs(tmp_path, result, "# report\n", {"commit": "abc"})
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved == {"n": 3, "ok": True, "nan": None, "rows": [{"day": 1, "x": 1.26}]}
    assert json.loads((tmp_path / "provenance.json").read_text(encoding="utf-8")) == {"commit": "abc"}
    text = ds.table([{"day": 1, "x": 1.26, "pair": {"p": 0.5}}])
    assert "1.3" in text and "pair" not in text and ds.table([]) == "(no rows)"
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_descriptive.py -q`
Expected: collection error, `ImportError: cannot import name 'descriptive' from 'chhaya.eval'`

- [ ] **Step 3: Implement**

Create `src/chhaya/eval/descriptive.py`:

```python
"""Shared pieces of the descriptive outputs of Milestone 3: the second pass of section F, expiry, the band.

Days since the sensor, the three numbers a sensor report states, paired summaries over patients, and the
guards of a pass that reads test patients again. Nothing here carries a bar. How the registered words were
turned into these functions is fixed in docs/PREREGISTRATION.md, "Note to Amendment 3, descriptive outputs".
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from chhaya.config import SEED
from chhaya.eval.baselines import lodo_average_day
from chhaya.eval.fingersticks import _interval, calibration_pairs
from chhaya.eval.gate2 import _clean, _git, _paired_p
from chhaya.eval.metrics import rmse, time_in_ranges
from chhaya.twin.assimilate import pooled_map

DAY_MIN = 1440
REPORT_KEYS = ("mean", "tar", "tir")  # mg/dL, then percentage points twice
MIN_DAY_READINGS = 48  # a day counts when at least half of its 15-minute slots hold a reading
MIN_DAY_PATIENTS = 6  # below this a day keeps its medians and gets no paired comparison
MIN_SLOPE_DAYS = 3
MOVED_MGDL = 20.0  # the registered size of a drift: the mean has moved by more than this
NOT_SUMMARISED = ("day", "n", "k_days", "dev", "moved")


def day_index(t, split: float) -> np.ndarray:
    """Days since the sensor came off, in 24-hour blocks from the split: 1 for the first 24 hours."""
    t = np.asarray(t, dtype=float)
    if t.size and t.min() < split:
        raise ValueError("a reading from before the split has no day since the sensor")
    return ((t - split) // DAY_MIN).astype(int) + 1


def glucose_report(g) -> dict[str, float]:
    """What a sensor report states about a period: mean glucose, percent of time above 180 and within 70-180."""
    g = np.asarray(g, dtype=float)
    if g.size == 0:
        raise ValueError("no readings: a report needs at least one")
    r = time_in_ranges(g)
    return {"mean": float(g.mean()), "tar": r["tar"], "tir": r["tir"]}


def estimated_report(est, sigma: float) -> dict[str, float]:
    """The same three numbers from an estimated trace whose error has spread `sigma` (mg/dL).

    An estimate is a smoothed mean, so counting how often it crosses 180 undercounts the time above 180. Each
    value is the centre of a normal distribution and the probabilities are averaged. Without a spread this is
    the plain count.
    """
    est = np.asarray(est, dtype=float)
    if not sigma > 0.0:
        return glucose_report(est)
    if est.size == 0:
        raise ValueError("no readings: a report needs at least one")
    above = norm.sf((180.0 - est) / sigma)
    below = norm.cdf((70.0 - est) / sigma)
    return {
        "mean": float(est.mean()),
        "tar": float(100.0 * above.mean()),
        "tir": float(100.0 * (1.0 - above - below).mean()),
    }


def profile_sigma(clock_min, g) -> float:
    """Spread of sensor readings around the daily shape built without their own day (mg/dL).

    `clock_min` counts minutes from midnight of the first day. The shape is half the average day of the other
    days, half the mean: the control of sections F and M.
    """
    clock_min = np.asarray(clock_min, dtype=int)
    g = np.asarray(g, dtype=float)
    seen = 0.5 * lodo_average_day(clock_min // DAY_MIN, clock_min, g) + 0.5 * float(g.mean())
    return rmse(seen, g)


def aging(now: dict, report: dict) -> dict[str, float]:
    """How far a period's own report (`now`) lies from an older `report` of the same patient."""
    d = now["mean"] - report["mean"]
    return {
        "dmean": float(d),
        "abs_dmean": float(abs(d)),
        "moved": float(abs(d) > MOVED_MGDL),
        "abs_dtar": float(abs(now["tar"] - report["tar"])),
        "abs_dtir": float(abs(now["tir"] - report["tir"])),
    }


def day_report(row: dict) -> dict[str, float]:
    """The report of the day a `daily_rows` row describes."""
    return {k: row[f"day_{k}"] for k in REPORT_KEYS}


def daily_rows(t, split: float, truth, estimates: dict, min_readings: int = MIN_DAY_READINGS) -> list[dict]:
    """One row per day since the sensor that holds enough readings.

    Each row has the day's own report (`day_mean`, `day_tar`, `day_tir`) and, for every estimate, its RMSE
    against the hidden readings of that day and its mean over them.
    """
    t, truth = np.asarray(t, dtype=float), np.asarray(truth, dtype=float)
    day = day_index(t, split)
    rows = []
    for d in np.unique(day):
        m = day == d
        if m.sum() < min_readings:
            continue
        row = {"day": int(d), "n": int(m.sum())}
        row.update({f"day_{k}": v for k, v in glucose_report(truth[m]).items()})
        for name, est in estimates.items():
            est = np.asarray(est, dtype=float)
            row[f"{name}_rmse"] = rmse(est[m], truth[m])
            row[f"{name}_mean"] = float(est[m].mean())
        rows.append(row)
    return rows


def inside_the_wear(t, g, min_readings: int = MIN_DAY_READINGS) -> dict[str, float] | None:
    """Day 0: how far one day of the wear lies from the report of its other days, averaged over its days.

    This is what "not aged at all" looks like for this patient, so a later day is read against it. None when
    the wear does not hold two days with enough readings.
    """
    t, g = np.asarray(t, dtype=float), np.asarray(g, dtype=float)
    block = (t // DAY_MIN).astype(int)
    rows = []
    for b in np.unique(block):
        m = block == b
        if m.sum() >= min_readings and (~m).sum() >= min_readings:
            rows.append(aging(glucose_report(g[m]), glucose_report(g[~m])))
    if not rows:
        return None
    return {k: float(np.mean([r[k] for r in rows])) for k in rows[0]}


def paired_summary(per: pd.DataFrame, a: str, b: str, alternative: str = "less") -> dict:
    """Column `a` against column `b` over patients: both medians and the median paired difference a - b.

    Below zero means `a` is the smaller error. The interval is a 95 % percentile bootstrap over patients and
    the p-value a one-sided signed-rank test, as everywhere in Amendment 3: that `a` is smaller ("less"), or,
    where the question is whether something got worse, that it is larger ("greater"). No bar hangs on it.
    """
    if alternative not in ("less", "greater"):
        raise ValueError(f"alternative must be 'less' or 'greater', got {alternative!r}")
    both = per[[a, b]].dropna()
    out: dict = {"of": a, "against": b, "alternative": alternative, "n_patients": int(len(both))}
    if both.empty:
        return out
    diff = both[a] - both[b]
    lo, hi = _interval(diff)
    out.update(
        {
            "median": float(both[a].median()),
            "median_against": float(both[b].median()),
            "median_diff": float(diff.median()),
            "diff_lo": lo,
            "diff_hi": hi,
            "frac_better": float((diff < 0).mean()),
            "p": _paired_p(diff if alternative == "less" else -diff),
        }
    )
    return out


def summarise_days(df: pd.DataFrame, pairs: tuple[tuple[str, str], ...] = ()) -> list[dict]:
    """Per day since the sensor: patients, the median of every numeric column over patients, paired comparisons.

    Recordings of one patient are averaged first. `moved` becomes `share_moved`, the share of patients whose
    daily mean lies more than 20 mg/dL from the report. A day with fewer than MIN_DAY_PATIENTS patients keeps
    its medians and gets no paired comparison.
    """
    out = []
    for d, g in df.groupby("day"):
        per = g.groupby("patient_id").mean(numeric_only=True)
        row: dict = {"day": int(d), "n_patients": int(len(per))}
        row.update({c: float(per[c].median()) for c in per.columns if c not in NOT_SUMMARISED})
        if "moved" in per.columns:
            row["share_moved"] = float(per["moved"].mean())
        if len(per) >= MIN_DAY_PATIENTS:
            for a, b in pairs:
                row[f"{a}_vs_{b}"] = paired_summary(per, a, b)
        out.append(row)
    most = max((r["n_patients"] for r in out), default=0)
    for row in out:  # a day that few patients reach is read with care: it holds whoever is left
        row["share_of_cohort"] = row["n_patients"] / most
    return out


def slope_per_day(df: pd.DataFrame, col: str) -> dict:
    """Change of `col` per day since the sensor inside each patient: a least-squares slope each, then the median.

    Recordings end at different lengths, so a curve of daily medians mixes ageing with who is still there. A
    slope inside each patient does not. Day 0 (inside the wear) is left out.
    """
    later = df[df["day"] >= 1].dropna(subset=[col])
    per = later.groupby(["patient_id", "day"])[col].mean().reset_index()
    slopes = [
        float(np.polyfit(g["day"], g[col], 1)[0])
        for _, g in per.groupby("patient_id")
        if len(g) >= MIN_SLOPE_DAYS
    ]
    out: dict = {"column": col, "n_patients": len(slopes)}
    if not slopes:
        return out
    s = pd.Series(slopes, dtype=float)
    lo, hi = _interval(s)
    out.update(
        {
            "median_slope": float(s.median()),
            "slope_lo": lo,
            "slope_hi": hi,
            "frac_rising": float((s > 0).mean()),
        }
    )
    return out


def excess_over_day_zero(df: pd.DataFrame, col: str) -> list[dict]:
    """For each day since the sensor, `col` on that day against the same patient's day 0 (inside the wear).

    The question is whether the report has aged, so the test is one-sided the other way: larger than day 0.
    """
    wide = df.dropna(subset=[col]).groupby(["patient_id", "day"])[col].mean().unstack("day")
    if 0 not in wide.columns:
        return []
    out = []
    for d in [c for c in wide.columns if c >= 1]:
        per = pd.DataFrame({"then": wide[d], "inside": wide[0]})
        if per.dropna().shape[0] >= MIN_DAY_PATIENTS:
            out.append({"day": int(d), "column": col, **paired_summary(per, "then", "inside", "greater")})
    return out


def pooled_line(dev_recs: list, k_days: float) -> tuple[float, float]:
    """The pooled line of the sensor map, from development recordings' calibration pairs.

    The same line the confirmatory fingerstick run fitted. No test patient may be among `dev_recs`.
    """
    pairs = [calibration_pairs(r, k_days) for r in dev_recs]
    n = sum(len(p) for p in pairs)
    if n < 2:
        raise ValueError(f"{n} development calibration pairs: the pooled sensor map cannot be fitted")
    cal = pd.concat(pairs, ignore_index=True)
    return pooled_map(cal["cbg"], cal["cgm"])


def differences(found: dict, committed: dict, tol: float = 1e-6) -> list[str]:
    """Which committed numbers a second computation does not reproduce. Empty: same estimator, same cohort."""
    out = []
    for key, want in committed.items():
        got = found.get(key)
        same = got is not None and want is not None and abs(float(got) - float(want)) <= tol
        if not same:
            out.append(f"{key}: committed {want}, found {got}")
    return out


def check_committed(src_status: str | None) -> None:
    """A pass over test patients runs on committed code, or not at all."""
    if src_status is None:
        raise SystemExit(
            "git is not available, so the code that reads the test patients cannot be identified"
        )
    if src_status:
        raise SystemExit("uncommitted changes under src/: commit them before reading the test patients")


def provenance(confirm: bool, **settings) -> dict:
    status = _git("status", "--porcelain", "--", "src")
    return {
        "commit": _git("rev-parse", "--short", "HEAD"),
        "uncommitted_changes_in_src": None if status is None else bool(status),
        "confirm": confirm,
        "seed": SEED,
        **settings,
    }


def _plain(value):
    """numpy integers and booleans are not JSON; their Python values are."""
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"{type(value).__name__} is not JSON serialisable")


def write_outputs(out_dir: Path, result: dict, report: str, prov: dict | None = None) -> None:
    """summary.json (strict JSON), report.md and, when given, provenance.json. Aggregates only."""
    out_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_clean(result), indent=2, allow_nan=False, default=_plain)
    (out_dir / "summary.json").write_text(text, encoding="utf-8")
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    if prov is not None:
        (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2, default=_plain), encoding="utf-8")


def table(rows: list[dict], columns: list[str] | None = None, digits: int = 1) -> str:
    """A markdown table of flat rows; nested values (paired comparisons) are left to the summary file."""
    flat = [{k: v for k, v in r.items() if not isinstance(v, dict | list)} for r in rows]
    df = pd.DataFrame(flat)
    if df.empty:
        return "(no rows)"
    df = df[[c for c in (columns or list(df.columns)) if c in df.columns]]
    return df.round(digits).to_markdown(index=False)
```

- [ ] **Step 4: Run, lint, commit**

Run: `uv run pytest tests/test_descriptive.py -q`
Expected: 17 passed

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/descriptive.py tests/test_descriptive.py
git commit -m "feat: shared pieces of the descriptive outputs (days since the sensor, report numbers, guards)"
```

---

### Task 2: The second pass of section F

**Files:**
- Create: `src/chhaya/eval/fingersticks_report.py`
- Test: `tests/test_fingersticks_report.py`
- Not modified: `src/chhaya/eval/fingersticks.py`, `src/chhaya/twin/assimilate.py`. This pass imports `estimates` and `FilterConfig` as they are.

**Interfaces:**
- Consumes: everything Task 1 produces; from `chhaya.eval.fingersticks`: `estimates(rec, k_days, cfg, pooled, rule="all") -> dict` (keys used: `t`, `control`, `live`, `hindsight`, `ft`, `cbg`, `map`), `why_not(rec, k_days) -> str | None`, `REGISTERED_K = (3.0, 5.0)`, `REGISTERED_FILTER = (120.0, False)`; `chhaya.eval.gate3.refuse_second_run(out_dir)`.
- Produces: `stated(rec, k_days, pooled) -> (reports, e)`; `recording_rows(rec, k_days, pooled) -> (row, days) | None`; `block_for(recs, k_days, pooled) -> dict`; `run(scored, dev_recs, k_list, out_dir, confirmatory, committed=None) -> dict`; `SOURCES`, `CHECKED`; the commands `python -m chhaya.eval.fingersticks_report [--confirm]`.
- Committed numbers it must reproduce: `results/fingersticks/shanghai/summary.json` (with `--confirm`) and `results/fingersticks/shanghai-dev-tau120/summary.json` (without), keys `by_k[i].rules.all.{n_patients, control_rmse, live_median_diff, hindsight_median_diff}`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_fingersticks_report.py`:

```python
import dataclasses
import json

import numpy as np
import pytest
from conftest import make_recording

from chhaya.eval import fingersticks_report as fr
from chhaya.eval.descriptive import REPORT_KEYS, pooled_line

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(shift: float, every_min: int = 240, days: int = 7, seed: int = 11):
    """After day 3 the patient's glucose runs `shift` mg/dL higher. Fingersticks read the sensor exactly."""
    rec = make_recording(days=days, seed=seed)
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= SPLIT
    cgm.loc[late, "glucose_mgdl"] = np.clip(cgm.loc[late, "glucose_mgdl"] + shift, 40, 400)
    sticks = cgm[cgm["t_min"] % every_min == 0].reset_index(drop=True)
    return dataclasses.replace(rec, cgm=cgm, fingersticks=sticks)


def _cohort(n: int = 7, shift: float = 40.0):
    rec = _recording(shift, days=8)
    return [dataclasses.replace(rec, rec_id=f"r{i}", patient_id=f"p{i}") for i in range(n)]


def test_when_the_patient_has_changed_the_shadow_states_the_report_better_than_the_old_one():
    row, days = fr.recording_rows(_recording(40.0), 3, POOLED)
    assert row["stale_mean_err"] > 30.0 and row["stale_mean_err"] == row["abs_dmean"] and row["moved"] == 1.0
    assert row["hindsight_mean_err"] < row["stale_mean_err"] - 20.0
    assert row["hindsight_tar_err"] < row["stale_tar_err"]
    assert [d["day"] for d in days] == [1, 2, 3, 4]
    assert all(d["hindsight_rmse"] < d["control_rmse"] - 5.0 for d in days)
    assert all(d["hindsight_mean_err"] < d["abs_dmean"] for d in days)


def test_when_nothing_changed_the_old_report_is_still_right():
    row, _ = fr.recording_rows(_recording(0.0), 3, POOLED)
    assert row["stale_mean_err"] < 8.0 and row["moved"] == 0.0 and row["stale_tir_err"] < 8.0


def test_no_stated_report_reads_a_hidden_sensor_value():
    rec = _recording(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    a, _ = fr.stated(rec, 3, POOLED)
    b, _ = fr.stated(dataclasses.replace(rec, cgm=cgm), 3, POOLED)
    assert set(a) == set(fr.SOURCES)
    for source in fr.SOURCES:
        assert a[source] == pytest.approx(b[source]), source


def test_testing_frequency_is_recorded_per_recording():
    row, _ = fr.recording_rows(_recording(0.0, every_min=240), 3, POOLED)
    assert row["sticks_per_day"] == 6.0 and row["sticks_per_day_hidden"] == 6.0 and row["n_sticks"] == 24


def test_a_recording_outside_the_cohort_is_not_scored(rec):
    assert fr.recording_rows(rec, 3, POOLED) is None  # no fingersticks at all
    assert fr.block_for([rec], 3.0, POOLED) == {"k_days": 3.0, "n_patients": 0}


def test_the_summary_compares_every_source_and_two_recordings_of_a_patient_count_once():
    recs = _cohort()
    recs.append(dataclasses.replace(recs[0], rec_id="again"))
    block = fr.block_for(recs, 3.0, POOLED)
    assert block["n_patients"] == 7 and block["recordings"] == 8
    for key in REPORT_KEYS:
        assert set(block[key]["errors"]) == set(fr.SOURCES)
        assert block[key]["hindsight_vs_stale"]["n_patients"] == 7
    assert block["mean"]["hindsight_vs_stale"]["median_diff"] < -20.0
    assert block["aged"]["share_moved"] == 1.0 and block["density"]["sticks_per_day"]["median"] == 6.0
    assert [d["day"] for d in block["by_day"]] == [1, 2, 3, 4, 5]
    assert block["by_day"][0]["hindsight_rmse_vs_control_rmse"]["median_diff"] < 0
    assert {s["column"] for s in block["slopes"]} == {"control_rmse", "hindsight_rmse", "abs_dmean"}


def _committed(recs, k_list=(3.0, 5.0)):
    """What the run being repeated would have written: by_k[i].rules.all, as chhaya.eval.fingersticks does."""
    by_k = []
    for k in k_list:
        block = fr.block_for(recs, k, pooled_line(recs, k))
        by_k.append({"k_days": k, "rules": {"all": {key: block[key] for key in fr.CHECKED}}})
    return {"by_k": by_k}


def test_the_pass_is_written_only_when_it_reproduces_the_run_it_repeats(tmp_path):
    recs = _cohort()
    committed = _committed(recs)
    result = fr.run(recs, recs, [3.0, 5.0], tmp_path / "ok", True, committed)
    assert result["by_k"][0]["density_dev"]["sticks_per_day"]["median"] == 6.0
    saved = json.loads((tmp_path / "ok" / "summary.json").read_text(encoding="utf-8"))
    assert saved["confirmatory"] is True and len(saved["by_k"]) == 2
    text = (tmp_path / "ok" / "report.md").read_text(encoding="utf-8")
    assert "second time" in text and "p0" not in text and "r0" not in text  # aggregates only

    committed["by_k"][1]["rules"]["all"]["control_rmse"] += 0.01  # the second k, after the first passed
    with pytest.raises(SystemExit, match="does not reproduce"):
        fr.run(recs, recs, [3.0, 5.0], tmp_path / "bad", True, committed)
    assert not (tmp_path / "bad").exists()  # nothing is written, not even the k that matched


def test_a_committed_run_at_another_k_is_not_accepted_as_the_same_run(tmp_path):
    recs = _cohort()
    with pytest.raises(SystemExit, match="k = 5"):
        fr.run(recs, recs, [3.0], tmp_path, False, _committed(recs, (5.0,)))


def test_a_development_run_carries_no_second_density_block(tmp_path):
    recs = _cohort()
    result = fr.run(recs, recs, [3.0], tmp_path, False)
    assert result["confirmatory"] is False and "density_dev" not in result["by_k"][0]
    assert "Not confirmatory" in (tmp_path / "report.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_fingersticks_report.py -q`
Expected: collection error, `ImportError: cannot import name 'fingersticks_report' from 'chhaya.eval'`

- [ ] **Step 3: Implement**

Create `src/chhaya/eval/fingersticks_report.py`:

```python
"""Experiment F, second pass: what the frozen fingerstick estimator says at the level a doctor reads.

Amendment 3, section F lists, besides F1 and F2: error in mean glucose, time above 180 and time in range over
the hidden window against the stale sensor report and the plain fingerstick average, and error by day since the
sensor came off. The confirmatory run deferred them and said so (note of 8 Oct); how each is computed is fixed
in the note on the descriptive outputs. Descriptive: no bar, no verdict.

`estimates` and `FilterConfig` are used exactly as committed for the confirmatory run. Before anything is
written, this pass must reproduce that run's cohort size, control error and both paired differences.

Usage: python -m chhaya.eval.fingersticks_report             (development patients)
       python -m chhaya.eval.fingersticks_report --confirm   (test patients, once)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import (
    MIN_DAY_PATIENTS,
    REPORT_KEYS,
    aging,
    check_committed,
    daily_rows,
    day_report,
    differences,
    estimated_report,
    glucose_report,
    paired_summary,
    pooled_line,
    profile_sigma,
    provenance,
    slope_per_day,
    summarise_days,
    table,
    write_outputs,
)
from chhaya.eval.fingersticks import (
    REGISTERED_FILTER,
    REGISTERED_K,
    estimates,
    why_not,
)
from chhaya.eval.gate2 import _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.eval.metrics import rmse
from chhaya.twin.assimilate import FilterConfig

# who states the report of the hidden window: the old sensor report, the fingersticks alone, the estimates
SOURCES = ("stale", "sticks", "sticks_raw", "shape", "live", "hindsight", "hindsight_count")
COMPARISONS = (
    ("hindsight", "stale"),
    ("hindsight", "sticks"),
    ("hindsight", "shape"),
    ("live", "stale"),
    ("sticks", "stale"),
)
DAY_COLS = [
    "patient_id",
    "day",
    "control_rmse",
    "live_rmse",
    "hindsight_rmse",
    "abs_dmean",
    "dmean",
    "moved",
    "abs_dtar",
    "hindsight_mean_err",
]
DAY_PAIRS = (
    ("live_rmse", "control_rmse"),
    ("hindsight_rmse", "control_rmse"),
    ("hindsight_mean_err", "abs_dmean"),
)
CHECKED = ("n_patients", "control_rmse", "live_median_diff", "hindsight_median_diff")
FOLDER = RESULTS_DIR / "fingersticks"
# the runs this pass must reproduce: the confirmatory one, and the frozen design on development patients
COMMITTED = {
    True: FOLDER / "shanghai" / "summary.json",
    False: FOLDER / "shanghai-dev-tau120" / "summary.json",
}


def stated(rec: Recording, k_days: float, pooled: tuple[float, float]) -> tuple[dict, dict]:
    """The report of the hidden window as each source states it, and the estimates behind the last four.

    No hidden sensor reading is used: the stale report and the spread come from the calibration window, the
    fingerstick averages from the fingersticks, the estimates from `estimates` as committed.
    """
    e = estimates(rec, k_days, FilterConfig(), pooled)
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    assert (e["t"] >= split).all() and (e["ft"] >= split).all(), "something from before the split is scored"
    sigma = profile_sigma(rec.start.hour * 60 + rec.start.minute + t[cal], g[cal])
    a, b = e["map"]
    reports = {
        "stale": glucose_report(g[cal]),
        "sticks": glucose_report(a + b * e["cbg"]),  # on the sensor's scale, by the line the estimator uses
        "sticks_raw": glucose_report(e["cbg"]),  # as a logbook would average them
        "shape": estimated_report(e["control"], sigma),
        "live": estimated_report(e["live"], sigma),
        "hindsight": estimated_report(e["hindsight"], sigma),
        "hindsight_count": glucose_report(e["hindsight"]),  # no spread: the plain count, for comparison
    }
    return reports, {**e, "sigma": sigma}


def recording_rows(
    rec: Recording, k_days: float, pooled: tuple[float, float]
) -> tuple[dict, list[dict]] | None:
    """The report-level row and the by-day rows of a recording in the cohort of section F; None outside it."""
    if why_not(rec, k_days) is not None:
        return None
    reports, e = stated(rec, k_days, pooled)
    split = k_days * 1440.0
    truth = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)[rec.cgm["t_min"].to_numpy(dtype=float) >= split]
    true, stale = glucose_report(truth), reports["stale"]
    ids = {"rec_id": rec.rec_id, "patient_id": rec.patient_id, "k_days": k_days}
    row = {
        **ids,
        "n_sticks": len(e["ft"]),
        "sticks_per_day": len(rec.fingersticks) / (rec.n_min / 1440.0),
        "sticks_per_day_hidden": len(e["ft"]) / ((rec.n_min - split) / 1440.0),
        "sigma": e["sigma"],
        "control_rmse": rmse(e["control"], truth),
        "live_rmse": rmse(e["live"], truth),
        "hindsight_rmse": rmse(e["hindsight"], truth),
        **aging(true, stale),
    }
    for name, r in reports.items():
        row.update({f"{name}_{key}_err": abs(r[key] - true[key]) for key in REPORT_KEYS})
    days = []
    shown = {name: e[name] for name in ("control", "live", "hindsight")}
    for d in daily_rows(e["t"], split, truth, shown):
        err = abs(d["hindsight_mean"] - d["day_mean"])
        days.append({**ids, **d, **aging(day_report(d), stale), "hindsight_mean_err": err})
    return row, days


def density(per: pd.DataFrame) -> dict:
    """How often the cohort tests, and whether the patients who test more gain more from the live estimate."""
    out: dict = {}
    for col in ("sticks_per_day", "sticks_per_day_hidden"):
        q = per[col].quantile([0.0, 0.25, 0.5, 0.75, 1.0]).to_numpy()
        out[col] = dict(zip(("min", "q25", "median", "q75", "max"), (float(v) for v in q), strict=True))
    gain = per["live_rmse"] - per["control_rmse"]
    testable = len(per) >= MIN_DAY_PATIENTS and np.ptp(per["sticks_per_day_hidden"]) > 0 and np.ptp(gain) > 0
    rho = spearmanr(per["sticks_per_day_hidden"], gain) if testable else None
    out["spearman_density_vs_live_gain"] = float(rho.statistic) if rho else float("nan")
    out["spearman_p"] = float(rho.pvalue) if rho else float("nan")
    return out


def summarise(df: pd.DataFrame) -> dict:
    """Patient-level medians (recordings of one patient are averaged first) and paired comparisons."""
    per = df.groupby("patient_id").mean(numeric_only=True)
    out: dict = {
        "n_patients": int(len(per)),
        "recordings": int(df["rec_id"].nunique()),
        "control_rmse": float(per["control_rmse"].median()),
        "live_median_diff": float((per["live_rmse"] - per["control_rmse"]).median()),
        "hindsight_median_diff": float((per["hindsight_rmse"] - per["control_rmse"]).median()),
        "aged": {
            "abs_dmean": float(per["abs_dmean"].median()),
            "dmean": float(per["dmean"].median()),
            "share_moved": float(per["moved"].mean()),
            "abs_dtar": float(per["abs_dtar"].median()),
            "abs_dtir": float(per["abs_dtir"].median()),
        },
        "density": density(per),
    }
    for key in REPORT_KEYS:
        block: dict = {"errors": {name: float(per[f"{name}_{key}_err"].median()) for name in SOURCES}}
        for a, b in COMPARISONS:
            block[f"{a}_vs_{b}"] = paired_summary(per, f"{a}_{key}_err", f"{b}_{key}_err")
        out[key] = block
    return out


def block_for(recs: list[Recording], k_days: float, pooled: tuple[float, float]) -> dict:
    """Everything reported at one k for one set of recordings."""
    got = [x for x in (recording_rows(r, k_days, pooled) for r in recs) if x is not None]
    if not got:
        return {"k_days": k_days, "n_patients": 0}
    df = pd.DataFrame([row for row, _ in got])
    days = pd.DataFrame([d for _, ds in got for d in ds])
    block = {"k_days": k_days, **summarise(df), "by_day": [], "slopes": []}
    if len(days):
        block["by_day"] = summarise_days(days[DAY_COLS], DAY_PAIRS)
        block["slopes"] = [slope_per_day(days, c) for c in ("control_rmse", "hindsight_rmse", "abs_dmean")]
    return block


def _report(result: dict) -> str:
    lines = ["# Fingersticks, second pass: the report a doctor reads", ""]
    lines.append(
        "Test patients, read a second time after F1 and F2 were known. Descriptive: no bar."
        if result["confirmatory"]
        else "Development patients. Not confirmatory."
    )
    lines += [
        "",
        f"Filter: `{result['filter']}` (frozen). Errors are absolute, medians over patients: mean glucose in "
        "mg/dL, time above 180 and time in range in percentage points. `stale` is the report of the calibration "
        "days; `sticks` the average of the hidden fingersticks on the sensor's scale and `sticks_raw` as read; "
        "`shape` the daily shape alone; `hindsight_count` counts crossings of the estimate with no spread.",
    ]
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days", ""]
        if not block["n_patients"]:
            lines.append("No recording in the cohort.")
            continue
        aged, dens = block["aged"], block["density"]
        lines += [
            f"{block['n_patients']} patients, {block['recordings']} recordings. Since the calibration days the "
            f"mean moved by a median of {aged['abs_dmean']:.1f} mg/dL (signed {aged['dmean']:+.1f}); "
            f"{100 * aged['share_moved']:.0f} % of patients moved more than 20.",
            "",
            f"Fingersticks per day: {dens['sticks_per_day']['median']:.1f} over the recording "
            f"(quartiles {dens['sticks_per_day']['q25']:.1f} to {dens['sticks_per_day']['q75']:.1f}), "
            f"{dens['sticks_per_day_hidden']['median']:.1f} in the hidden window.",
            "",
            table([{"source": s, **{k: block[k]["errors"][s] for k in REPORT_KEYS}} for s in SOURCES], digits=2),
            "",
            table(
                [
                    {"what": key, **block[key][f"{a}_vs_{b}"]}
                    for key in REPORT_KEYS
                    for a, b in COMPARISONS
                    if block[key][f"{a}_vs_{b}"]["n_patients"]
                ],
                digits=3,
            ),
            "",
            "By day since the sensor came off (RMSE against the hidden sensor, mg/dL):",
            "",
            table(block["by_day"], ["day", "n_patients", "control_rmse", "live_rmse", "hindsight_rmse", "abs_dmean",
                                    "share_moved", "hindsight_mean_err"], digits=2),
        ]  # fmt: skip
    return "\n".join(lines) + "\n"


def run(
    scored: list[Recording],
    dev_recs: list[Recording],
    k_list: list[float],
    out_dir: Path,
    confirmatory: bool,
    committed: dict | None = None,
) -> dict:
    """Score `scored` at each k; the pooled line of the sensor map always comes from `dev_recs`.

    With `committed` (the summary of the run this pass repeats), nothing is written unless the cohort size,
    the control error and both paired differences come out the same at every k.
    """
    result = {"confirmatory": confirmatory, "filter": FilterConfig()._asdict(), "by_k": []}
    for i, k in enumerate(k_list):
        pooled = pooled_line(dev_recs, k)
        block = block_for(scored, k, pooled)
        if committed is not None:
            want = committed["by_k"][i]
            if want["k_days"] != k:
                raise SystemExit(f"the committed run has k = {want['k_days']:g} where this pass has {k:g}")
            bad = differences(block, {key: want["rules"]["all"][key] for key in CHECKED})
            if bad:
                raise SystemExit(
                    f"this pass does not reproduce the committed run at k = {k:g}, so it is not the frozen "
                    "estimator and nothing was written: " + "; ".join(bad)
                )
        if confirmatory and block["n_patients"]:
            block["density_dev"] = block_for(dev_recs, k, pooled).get("density")
        result["by_k"].append(block)
    write_outputs(out_dir, result, _report(result))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="read the test patients; this is done once")
    args = ap.parse_args()
    out_dir = FOLDER / ("shanghai-report" if args.confirm else "shanghai-dev-report")
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        cfg = FilterConfig()
        if (cfg.tau_min, cfg.slow) != REGISTERED_FILTER:
            raise SystemExit(f"the code defaults are not the frozen design {REGISTERED_FILTER}")
        refuse_second_run(out_dir)
    path = COMMITTED[args.confirm]
    if args.confirm and not path.exists():
        raise SystemExit(f"{path} is missing: the confirmatory run this pass repeats cannot be checked")
    committed = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    assert args.confirm or all(is_dev_patient(r.patient_id) for r in scored)
    run(scored, dev_recs, list(REGISTERED_K), out_dir, args.confirm, committed)
    prov = provenance(args.confirm, k=list(REGISTERED_K), reproduces=str(path) if committed else None)
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run, lint, check that nothing frozen moved, commit**

Run: `uv run pytest tests/test_fingersticks_report.py tests/test_fingersticks.py tests/test_assimilate.py -q`
Expected: all pass (9 new)

Run: `git diff --stat b79bc80 -- src/chhaya/eval/fingersticks.py src/chhaya/twin/assimilate.py`
Expected: no output. `b79bc80` is the commit of the confirmatory fingerstick run.

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/fingersticks_report.py tests/test_fingersticks_report.py
git commit -m "feat: second pass of the fingerstick experiment (report-level errors, error by day, testing frequency)"
```

---
### Task 3: Reveal traces

**Files:**
- Create: `src/chhaya/eval/traces.py`
- Test: `tests/test_traces.py`
- Not modified: `src/chhaya/eval/reveal.py`, anything under `src/chhaya/twin/`.

**Interfaces:**
- Consumes: `chhaya.eval.reveal.run_reveal(rec, k_days, n_members=200) -> Reveal | None` (fields used: `k_days`, `t_test`, `truth`, `twin`, `lo`, `hi`, `shrunk`, `day`, `cal_t`, `cal_truth`, `metrics`), `why_skipped(rec, k_days)`, `chhaya.eval.gate2.load(dataset)`, `differences` from Task 1.
- Produces: a trace is a `dict` with keys `rec_id`, `patient_id`, `dataset`, `group`, `k_days` and the arrays `t`, `truth`, `twin`, `lo`, `hi`, `shrunk`, `day`, `cal_t`, `cal_truth`. `TRACE_DIR`, `GATE2_TEST`, `split_of(patient_id) -> "dev" | "test"`, `save_trace(trace, root=TRACE_DIR) -> Path`, `load_traces(dataset, split, k_days, root=TRACE_DIR) -> list[dict]`, `gate2_differences(traces, metrics, tol=1e-6) -> list[str]`, `require_gate2(traces, metrics_path=GATE2_TEST) -> None`, `build(recs, k_list, n_members=200, jobs=1, root=TRACE_DIR) -> DataFrame`; the command `python -m chhaya.eval.traces --split {dev,test}`. `tests/test_traces.py` also provides `fake_trace(patient_id, k_days=3.0, days=3, off=5.0, group="t2d")`, which Task 4's tests import.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_traces.py`:

```python
import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.eval import traces as tc
from chhaya.eval.metrics import coverage, rmse
from chhaya.eval.reveal import run_reveal


def _dev_and_test_ids():
    ids = [f"synth-{i}" for i in range(40)]
    return next(i for i in ids if tc.split_of(i) == "dev"), next(i for i in ids if tc.split_of(i) == "test")


def fake_trace(
    patient_id: str, k_days: float = 3.0, days: int = 3, off: float = 5.0, group: str = "t2d"
) -> dict:
    """A trace with no fit behind it: the estimate sits `off` above the truth inside a band of +-10."""
    t = k_days * 1440 + np.arange(0, days * 1440, 15.0)
    truth = 140.0 + 20.0 * np.sin(2 * np.pi * t / 1440)
    cal_t = np.arange(0, k_days * 1440, 15.0)
    twin = truth + off
    return {
        "rec_id": patient_id,
        "patient_id": patient_id,
        "dataset": "cgmacros",
        "group": group,
        "k_days": k_days,
        "t": t,
        "truth": truth,
        "twin": twin,
        "lo": twin - 10.0,
        "hi": twin + 10.0,
        "shrunk": truth + 2 * off,
        "day": truth + 4 * off,
        "cal_t": cal_t,
        "cal_truth": 140.0 + 20.0 * np.sin(2 * np.pi * cal_t / 1440),
    }


def test_a_trace_comes_back_as_it_was_saved_and_only_from_its_own_split(tmp_path):
    dev, test = _dev_and_test_ids()
    for pid in (dev, test):
        tc.save_trace(fake_trace(pid), tmp_path)
        tc.save_trace(fake_trace(pid, k_days=5.0), tmp_path)
    got = tc.load_traces("cgmacros", "dev", 3.0, tmp_path)
    assert [tr["patient_id"] for tr in got] == [dev] and got[0]["k_days"] == 3.0 and got[0]["group"] == "t2d"
    assert np.array_equal(got[0]["twin"], fake_trace(dev)["twin"]) and isinstance(got[0]["rec_id"], str)
    assert [tr["patient_id"] for tr in tc.load_traces("cgmacros", "test", 5.0, tmp_path)] == [test]
    assert tc.load_traces("cgmacros", "dev", 7.0, tmp_path) == []
    with pytest.raises(ValueError, match="split"):
        tc.load_traces("cgmacros", "all", 3.0, tmp_path)


def test_a_test_patients_file_in_the_development_folder_is_refused(tmp_path):
    dev, test = _dev_and_test_ids()
    wrong = tmp_path / "cgmacros" / "dev" / f"{test}-k3.npz"
    wrong.parent.mkdir(parents=True)
    np.savez_compressed(wrong, **fake_trace(test))
    with pytest.raises(ValueError, match="other split"):
        tc.load_traces("cgmacros", "dev", 3.0, tmp_path)


def _gate2_rows(traces):
    return pd.DataFrame(
        [
            {
                "rec_id": tr["rec_id"],
                "k_days": int(tr["k_days"]),
                "twin_rmse": rmse(tr["twin"], tr["truth"]),
                "twin_cov80": coverage(tr["truth"], tr["lo"], tr["hi"]),
            }
            for tr in traces
        ]
    )


def test_traces_must_give_back_what_gate2_committed():
    traces = [fake_trace("a"), fake_trace("b", off=7.0)]
    metrics = _gate2_rows(traces)
    assert tc.gate2_differences(traces, metrics) == []
    moved = metrics.assign(twin_rmse=metrics["twin_rmse"] + 0.01)
    assert (
        len(tc.gate2_differences(traces, moved)) == 2
        and "twin_rmse" in tc.gate2_differences(traces, moved)[0]
    )
    missing = tc.gate2_differences(traces[:1], metrics)
    assert missing == ["b k=3: scored by the Gate 2 run, no trace"]
    extra = tc.gate2_differences(traces, metrics.iloc[:1])
    assert extra == ["b k=3: not scored by the Gate 2 run"]
    failed = pd.concat([metrics, pd.DataFrame([{"rec_id": "c", "k_days": 3, "twin_rmse": np.nan}])])
    assert tc.gate2_differences(traces, failed) == []  # a recording Gate 2 could not score needs no trace
    other_k = pd.concat([metrics, _gate2_rows([fake_trace("a", k_days=7.0)])])
    assert tc.gate2_differences(traces, other_k) == []  # a k that was not traced is not asked for


@pytest.mark.slow
def test_building_traces_saves_what_the_reveal_estimated_and_indexes_what_it_could_not(tmp_path):
    rec = make_recording(days=6, seed=3)
    index = tc.build([rec], [4.0, 6.0], n_members=20, root=tmp_path)
    assert index["k_days"].tolist() == [4.0, 6.0] and index["skipped"].notna().tolist() == [False, True]
    (tr,) = tc.load_traces("synthetic", tc.split_of(rec.patient_id), 4.0, tmp_path)
    out = run_reveal(rec, 4.0, n_members=20)
    assert np.array_equal(tr["twin"], out.twin) and np.array_equal(tr["lo"], out.lo)
    assert tr["t"].min() >= 4 * 1440 and tr["cal_t"].max() < 4 * 1440
    assert abs(rmse(tr["twin"], tr["truth"]) - index["twin_rmse"].iloc[0]) < 1e-9
    assert tc.load_traces("synthetic", tc.split_of(rec.patient_id), 6.0, tmp_path) == []


def test_a_fit_that_fails_keeps_its_row(tmp_path, monkeypatch, rec):
    def boom(rec, k, n_members=200):
        raise RuntimeError("no convergence")

    monkeypatch.setattr(tc, "run_reveal", boom)
    index = tc.build([rec], [3.0], root=tmp_path)
    assert index["error"].tolist() == ["no convergence"] and not list(tmp_path.rglob("*.npz"))
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_traces.py -q`
Expected: collection error, `ImportError: cannot import name 'traces' from 'chhaya.eval'`

- [ ] **Step 3: Implement**

Create `src/chhaya/eval/traces.py`:

```python
"""Reveal traces: the hidden readings beside the estimate and its band, one file per recording and k.

Expiry by day and the band recalibration need every hidden reading; the Gate 2 results folder keeps one row
per recording. Per-reading arrays are patient data, not aggregates (rule 6), so they are written under
DATA_DIR/derived/traces, which git ignores, and never under results/. Development and test patients go to
separate folders and a reader names the split it wants, so a development run cannot open a test file.

The estimator is `run_reveal` with its defaults, exactly as Gate 2 ran it. `gate2_differences` checks that:
a trace must give back the error and the coverage the Gate 2 results folder holds for that recording.

Usage: python -m chhaya.eval.traces --dataset cgmacros --split dev --k 3 5 --jobs 6
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import DATA_DIR, RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import differences
from chhaya.eval.gate2 import load
from chhaya.eval.metrics import coverage, rmse
from chhaya.eval.reveal import Reveal, run_reveal, why_skipped

TRACE_DIR = DATA_DIR / "derived" / "traces"
GATE2_TEST = RESULTS_DIR / "gate2" / "cgmacros-test" / "metrics.csv"
ARRAYS = ("t", "truth", "twin", "lo", "hi", "shrunk", "day", "cal_t", "cal_truth")
SPLITS = ("dev", "test")


def split_of(patient_id: str) -> str:
    return "dev" if is_dev_patient(patient_id) else "test"


def trace_of(rec: Recording, out: Reveal) -> dict:
    """What later passes need from one reveal. `day` is the average-day baseline, `shrunk` the control."""
    return {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "dataset": rec.dataset,
        "group": str(rec.static.get("group")),
        "k_days": float(out.k_days),
        "t": np.asarray(out.t_test, dtype=float),
        "truth": out.truth,
        "twin": out.twin,
        "lo": out.lo,
        "hi": out.hi,
        "shrunk": out.shrunk,
        "day": out.day,
        "cal_t": np.asarray(out.cal_t, dtype=float),
        "cal_truth": out.cal_truth,
    }


def trace_path(trace: dict, root: Path = TRACE_DIR) -> Path:
    name = f"{trace['rec_id']}-k{trace['k_days']:g}.npz"
    return root / trace["dataset"] / split_of(trace["patient_id"]) / name


def save_trace(trace: dict, root: Path = TRACE_DIR) -> Path:
    path = trace_path(trace, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **trace)
    return path


def load_traces(dataset: str, split: str, k_days: float, root: Path = TRACE_DIR) -> list[dict]:
    """Every cached trace of one split at one k. Only that split's folder is opened."""
    if split not in SPLITS:
        raise ValueError(f"split must be one of {SPLITS}, got {split!r}")
    out = []
    for path in sorted((root / dataset / split).glob(f"*-k{k_days:g}.npz")):
        with np.load(path, allow_pickle=False) as z:
            tr = {k: (z[k].item() if z[k].ndim == 0 else z[k]) for k in z.files}
        if split_of(tr["patient_id"]) != split:
            raise ValueError(f"{path} holds a patient of the other split")
        out.append(tr)
    return out


def gate2_differences(traces: list[dict], metrics: pd.DataFrame, tol: float = 1e-6) -> list[str]:
    """Where these traces and a Gate 2 metrics table disagree. Empty: the traces are the estimator Gate 2 scored.

    Checked per recording and k: the estimate's RMSE and the coverage of its 80 % band. A recording Gate 2
    scored at one of these k and that has no trace is a difference too.
    """
    scored = metrics[metrics["twin_rmse"].notna()]
    want = {(r.rec_id, float(r.k_days)): r for r in scored.itertuples()}
    out, seen = [], set()
    for tr in traces:
        key = (tr["rec_id"], float(tr["k_days"]))
        if key not in want:
            out.append(f"{key[0]} k={key[1]:g}: not scored by the Gate 2 run")
            continue
        seen.add(key)
        found = {
            "twin_rmse": rmse(tr["twin"], tr["truth"]),
            "twin_cov80": coverage(tr["truth"], tr["lo"], tr["hi"]),
        }
        committed = {c: getattr(want[key], c) for c in found}
        out += [f"{key[0]} k={key[1]:g} {d}" for d in differences(found, committed, tol)]
    ks = {float(tr["k_days"]) for tr in traces}
    out += [
        f"{r} k={k:g}: scored by the Gate 2 run, no trace" for r, k in want if k in ks and (r, k) not in seen
    ]
    return out


def require_gate2(traces: list[dict], metrics_path: Path = GATE2_TEST) -> None:
    """Stop a pass over test patients whose traces are not the estimator the confirmatory Gate 2 run scored."""
    if not metrics_path.exists():
        raise SystemExit(f"{metrics_path} is missing: the traces cannot be checked against the Gate 2 run")
    bad = gate2_differences(traces, pd.read_csv(metrics_path))
    if bad:
        raise SystemExit(
            "the traces do not reproduce the Gate 2 run; nothing was written:\n" + "\n".join(bad)
        )


def _work(rec: Recording, k_list: list[float], n_members: int, root: Path) -> list[dict]:
    """All (recording, k) index rows for one recording. Top-level so worker processes can import it."""
    rows = []
    for k in k_list:
        base = {
            "rec_id": rec.rec_id,
            "patient_id": rec.patient_id,
            "k_days": k,
            "error": None,
            "skipped": None,
        }
        try:
            out = run_reveal(rec, k, n_members=n_members)
        except (RuntimeError, ValueError) as err:
            rows.append({**base, "error": str(err)})  # a failed fit keeps its row (rule 4)
            continue
        if out is None:
            rows.append({**base, "skipped": why_skipped(rec, k)})
            continue
        save_trace(trace_of(rec, out), root)
        rows.append({**base, "twin_rmse": out.metrics["twin_rmse"], "twin_cov80": out.metrics["twin_cov80"]})
    return rows


def build(
    recs: list[Recording], k_list: list[float], n_members: int = 200, jobs: int = 1, root: Path = TRACE_DIR
) -> pd.DataFrame:
    """Run the reveal for every recording and k, save the traces, return one index row each."""
    work = partial(_work, k_list=k_list, n_members=n_members, root=root)
    if jobs > 1:
        with ProcessPoolExecutor(jobs) as pool:
            per_rec = list(pool.map(work, recs))
    else:
        per_rec = [work(rec) for rec in recs]
    return pd.DataFrame([row for rows in per_rec for row in rows])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="cgmacros")
    ap.add_argument("--split", choices=SPLITS, required=True)
    ap.add_argument("--k", type=float, nargs="+", default=[3.0, 5.0])
    ap.add_argument("--members", type=int, default=200)
    ap.add_argument("--jobs", type=int, default=1, help="worker processes; results do not depend on it")
    args = ap.parse_args()
    recs = [r for r in load(args.dataset) if split_of(r.patient_id) == args.split]
    index = build(recs, args.k, args.members, args.jobs)
    folder = TRACE_DIR / args.dataset
    folder.mkdir(parents=True, exist_ok=True)
    index.to_csv(folder / f"index-{args.split}.csv", index=False)
    done = index["twin_rmse"].notna() if "twin_rmse" in index.columns else pd.Series(False, index=index.index)
    print(
        f"{int(done.sum())} traces written under {folder / args.split}; "
        f"{int(index['skipped'].notna().sum())} skipped, {int(index['error'].notna().sum())} failed"
    )
    if args.dataset == "cgmacros" and args.split == "test" and GATE2_TEST.exists():
        metrics = pd.read_csv(GATE2_TEST)
        bad = [d for k in args.k for d in gate2_differences(load_traces("cgmacros", "test", k), metrics)]
        print(
            "Reproduces the Gate 2 run."
            if not bad
            else "DOES NOT reproduce the Gate 2 run:\n" + "\n".join(bad)
        )


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run, lint, commit**

Run: `uv run pytest tests/test_traces.py -q`
Expected: 5 passed (one of them fits a twin and takes a few seconds)

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/traces.py tests/test_traces.py
git commit -m "feat: reveal traces cached outside results, split by patient, checked against Gate 2"
```

- [ ] **Step 5: Start the development traces in the background**

```bash
uv run python -m chhaya.eval.traces --dataset cgmacros --split dev --k 3 5 --jobs 6
```

This fits 25 development patients at two calibration lengths: about 14 minutes with 6 workers. Say so, start it in the background and go on to Task 4. Expected last line: `50 traces written under ...; 0 skipped, 0 failed`.

---

### Task 4: Expiry by day and the case series

**Files:**
- Create: `src/chhaya/eval/expiry.py`
- Test: `tests/test_expiry.py`

**Interfaces:**
- Consumes: Task 1 (`aging`, `daily_rows`, `day_index`, `day_report`, `excess_over_day_zero`, `glucose_report`, `inside_the_wear`, `profile_sigma`, `slope_per_day`, `summarise_days`, `table`, `write_outputs`, `provenance`, `check_committed`); Task 3 (`load_traces`, `require_gate2`; `fake_trace` in the tests); `chhaya.eval.events.drug_flags(agents) -> dict` (key `r_insulin`); `chhaya.eval.reveal.why_skipped`; `chhaya.eval.gate3.refuse_second_run`.
- Produces: `daily_shape(rec, until=None) -> np.ndarray` (48 half-hour bins), `shape_at(shape, rec, t) -> np.ndarray`, `profile_rows(rec, k_days) -> list[dict] | None`, `trace_rows(trace) -> list[dict]`, `shanghai_block(recs, k_days) -> dict`, `cgmacros_block(traces, k_days) -> dict`, `repeat_cases(recs) -> list[dict]`, `cases_block(recs) -> dict`; the commands `python -m chhaya.eval.expiry {shanghai,cgmacros,cases} [--confirm]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_expiry.py`:

```python
import dataclasses

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording
from test_traces import fake_trace

from chhaya.eval import expiry as ex
from chhaya.eval.fingersticks import estimates
from chhaya.twin.assimilate import FilterConfig

SPLIT = 3 * 1440


def _drifting(shift: float, from_day: int = 5, days: int = 8, seed: int = 11):
    """From day `from_day` on the patient's glucose runs `shift` mg/dL higher."""
    rec = make_recording(days=days, seed=seed)
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= from_day * 1440
    cgm.loc[late, "glucose_mgdl"] = np.clip(cgm.loc[late, "glucose_mgdl"] + shift, 40, 400)
    return dataclasses.replace(rec, cgm=cgm)


def _cohort(n: int = 7):
    rec = _drifting(40.0)
    return [dataclasses.replace(rec, rec_id=f"r{i}", patient_id=f"p{i}") for i in range(n)]


def test_the_daily_shape_is_the_control_that_section_f_scored():
    rec = dataclasses.replace(_drifting(0.0), start=pd.Timestamp("2026-01-01 09:37"))
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)
    e = estimates(dataclasses.replace(rec, fingersticks=sticks), 3, FilterConfig(), (0.0, 1.0))
    mine = ex.shape_at(ex.daily_shape(rec, SPLIT), rec, e["t"])
    assert np.array_equal(mine, e["control"])


def test_a_shape_is_read_by_the_clock_of_the_recording_it_is_applied_to():
    rec = dataclasses.replace(make_recording(days=2), start=pd.Timestamp("2026-03-01 09:00"))
    bins = np.arange(48.0)
    assert ex.shape_at(bins, rec, [0, 30, 900]).tolist() == [18.0, 19.0, 0.0]


def test_the_shape_is_built_before_the_split_only():
    rec = _drifting(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    assert np.array_equal(
        ex.daily_shape(rec, SPLIT), ex.daily_shape(dataclasses.replace(rec, cgm=cgm), SPLIT)
    )
    assert not np.array_equal(ex.daily_shape(rec, SPLIT), ex.daily_shape(rec))
    with pytest.raises(ValueError, match="no sensor reading"):
        ex.daily_shape(rec, 0.0)


def test_the_profile_is_true_until_the_patient_changes_and_wrong_after():
    rows = {r["day"]: r for r in ex.profile_rows(_drifting(40.0, from_day=5), 3)}
    assert sorted(rows) == [0, 1, 2, 3, 4, 5]  # day 0 is inside the wear; days 1 and 2 are before the change
    assert rows[0]["moved"] == 0.0 and rows[1]["moved"] == 0.0 and rows[2]["moved"] == 0.0
    assert rows[3]["moved"] == 1.0 and rows[3]["dmean"] > 30.0
    assert rows[3]["control_rmse"] > rows[1]["control_rmse"] + 15.0
    assert (
        rows[1]["control_rmse"] < rows[0]["control_rmse"] + 5.0
    )  # unaged, it errs no more than inside the wear


def test_a_recording_too_short_to_hide_a_day_is_counted_with_its_reason():
    short = make_recording(days=3, seed=2)
    assert ex.profile_rows(short, 3) is None
    block = ex.shanghai_block([*_cohort(), short], 3.0)
    assert block["n_patients"] == 7 and block["recordings"] == 7
    assert block["skipped"] == {"too short to hold out a day after calibration": 1}
    assert ex.shanghai_block([short], 3.0) == {"k_days": 3.0, "n_patients": 0, "skipped": block["skipped"]}


def test_each_later_day_is_read_against_day_zero_of_the_same_patient():
    block = ex.shanghai_block(_cohort(), 3.0)
    by_day = {r["day"]: r for r in block["by_day"]}
    assert (
        by_day[0]["n_patients"] == 7 and by_day[3]["share_moved"] == 1.0 and by_day[1]["share_moved"] == 0.0
    )
    zero = {(r["column"], r["day"]): r for r in block["against_day_zero"]}
    assert zero[("abs_dmean", 4)]["median_diff"] > 25.0 and abs(zero[("abs_dmean", 1)]["median_diff"]) < 8.0
    assert {column for column, _ in zero} == {"abs_dmean"}  # day 0 is no yardstick for the point error
    slope = next(s for s in block["slopes"] if s["column"] == "abs_dmean")
    assert slope["n_patients"] == 7 and slope["median_slope"] > 5.0


def test_trace_rows_score_the_twin_its_control_and_its_band_by_day():
    rows = {r["day"]: r for r in ex.trace_rows(fake_trace("p1", off=5.0))}
    assert sorted(rows) == [0, 1, 2, 3] and "twin_rmse" not in rows[0]  # day 0 has no estimate to score
    assert rows[2]["twin_rmse"] == pytest.approx(5.0) and rows[2]["control_rmse"] == pytest.approx(10.0)
    assert rows[2]["avgday_rmse"] == pytest.approx(20.0) and rows[2]["cov80"] == 1.0
    assert (
        rows[2]["twin_mean_err"] == pytest.approx(5.0)
        and rows[2]["abs_dmean"] < 1e-9
        and rows[2]["group"] == "t2d"
    )
    outside = fake_trace("p2", off=15.0)  # 15 above the truth, band of +-10: the truth is never inside
    assert {r["cov80"] for r in ex.trace_rows(outside) if r["day"] > 0} == {0.0}


def test_the_cgmacros_block_pairs_the_twin_with_its_control_and_counts_groups():
    traces = [fake_trace(f"p{i}", off=5.0 + 0.1 * i, group="t2d" if i < 3 else "healthy") for i in range(8)]
    block = ex.cgmacros_block(traces, 3.0)
    day1 = next(r for r in block["by_day"] if r["day"] == 1)
    assert day1["n_patients"] == 8 and day1["twin_rmse_vs_control_rmse"]["frac_better"] == 1.0
    assert (
        day1["twin_mean_err_vs_abs_dmean"]["median_diff"] > 0
    )  # here the stale report's mean is the better one
    assert block["groups"] == {"healthy": 5, "t2d": 3}
    assert [r["n_patients"] for r in block["by_day_t2d"]] == [3, 3, 3, 3]
    assert ex.cgmacros_block([], 3.0) == {"k_days": 3.0, "n_patients": 0}


def _again(first, days_later: int, shift: float, **changes):
    cgm = first.cgm.assign(glucose_mgdl=np.clip(first.cgm["glucose_mgdl"] + shift, 40, 400))
    start = first.start + pd.Timedelta(days=days_later)
    return dataclasses.replace(
        first, rec_id=f"{first.rec_id}-later{days_later}", start=start, cgm=cgm, **changes
    )


def test_the_case_series_applies_the_first_wears_profile_to_each_later_wear():
    first = dataclasses.replace(
        make_recording(days=6, seed=4), static={"agents": "metformin", "group": "t2d"}
    )
    pump = pd.DataFrame({"t_min": [10.0], "drug": ["Novolin R"], "dose": [np.nan], "route": ["csii"]})
    later = _again(first, 40, 30.0, doses=pump, static={"agents": "metformin, acarbose", "group": "t2d"})
    much_later = _again(first, 150, 0.0)
    alone = make_recording(days=6, seed=5)
    rows = ex.repeat_cases([later, alone, much_later, first])  # any order; the earliest wear is the reference
    assert [r["days_between_starts"] for r in rows] == [40.0, 150.0]
    a, b = rows
    assert a["days_since_first_sensor"] == 34.0 and a["first_wear_days"] == 6.0
    assert a["moved"] == 1.0 and 25.0 < a["dmean"] <= 30.0
    assert (
        a["old_profile_rmse"] > a["fresh_profile_rmse"] + 10.0
    )  # a new wear would describe this patient better
    assert (a["insulin_first"], a["insulin_later"], a["pump_later"], a["agents_changed"]) == (
        False,
        True,
        True,
        True,
    )
    assert (
        b["moved"] == 0.0
        and b["agents_changed"] is False
        and b["old_profile_rmse"] < a["old_profile_rmse"] - 10.0
    )
    assert (
        abs(b["old_profile_rmse"] - b["first_wear_rmse"]) < 6.0
    )  # nothing changed: as good as inside the first wear

    block = ex.cases_block([first, later, much_later, alone])
    assert (block["n_patients"], block["n_cases"], block["n_moved"], block["n_treatment_changed"]) == (
        1,
        2,
        1,
        1,
    )
    assert ex.cases_block([alone]) == {"n_patients": 0, "n_cases": 0, "cases": []}


def test_reports_say_what_they_are_and_by_day_reports_name_no_patient():
    result = {"confirmatory": False, "by_k": [ex.shanghai_block(_cohort(), 3.0), ex.shanghai_block([], 5.0)]}
    text = ex._by_day_report(
        "Expiry by day: ShanghaiT2DM", "note", result, ["day", "n_patients", "control_rmse"]
    )
    assert (
        "Not confirmatory" in text
        and "No recording could be run" in text
        and "p0" not in text
        and "r0" not in text
    )
    first = make_recording(days=6, seed=4)
    cases = {"confirmatory": True, **ex.cases_block([first, _again(first, 40, 30.0)])}
    assert "case series" in ex._cases_report(cases) and "no test" in ex._cases_report(cases)
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_expiry.py -q`
Expected: collection error, `ImportError: cannot import name 'expiry' from 'chhaya.eval'`

- [ ] **Step 3: Implement**

Create `src/chhaya/eval/expiry.py`:

```python
"""Expiry: how fast one sensor wear stops describing the patient (Amendment 3, "Descriptive, no bar").

Three outputs, none with a bar. How each is computed is fixed in the note on the descriptive outputs in
docs/PREREGISTRATION.md.

  shanghai   the daily shape from the first k days against each later day: the profile alone, no fingersticks,
             every recording that can be run (wider than the cohort of section F)
  cgmacros   the same by day for the twin, its control and its band, from cached reveal traces
  cases      the Shanghai patients recorded again weeks later: the first wear's profile on the later wear

Day 0 in every by-day table is "inside the wear": one day of the calibration window against its other days.
It is built from k - 1 days where a later day is read against k, so it slightly overstates how wrong an unaged
report is. For the report's mean that is a few percent and each later day is compared with it; for the point
error of the shape it is larger, so there the slope inside each patient is the measure and day 0 is context.

Usage: python -m chhaya.eval.expiry {shanghai,cgmacros,cases} [--confirm]
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline
from chhaya.eval.descriptive import (
    aging,
    check_committed,
    daily_rows,
    day_index,
    day_report,
    excess_over_day_zero,
    glucose_report,
    inside_the_wear,
    profile_sigma,
    provenance,
    slope_per_day,
    summarise_days,
    table,
    write_outputs,
)
from chhaya.eval.events import drug_flags
from chhaya.eval.gate2 import _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.eval.metrics import rmse
from chhaya.eval.reveal import why_skipped
from chhaya.eval.traces import load_traces, require_gate2

BIN = 30
K_LIST = (3.0, 5.0)
FOLDER = RESULTS_DIR / "expiry"
INSULIN_ROUTES = {"sc", "iv", "csii"}
PROFILE_COLS = [
    "patient_id",
    "rec_id",
    "day",
    "control_rmse",
    "abs_dmean",
    "dmean",
    "moved",
    "abs_dtar",
    "abs_dtir",
]
TWIN_COLS = [
    "patient_id",
    "rec_id",
    "day",
    "twin_rmse",
    "control_rmse",
    "avgday_rmse",
    "cov80",
    "twin_mean_err",
    "abs_dmean",
    "dmean",
    "moved",
    "abs_dtar",
]
TWIN_PAIRS = (("twin_rmse", "control_rmse"), ("twin_rmse", "avgday_rmse"), ("twin_mean_err", "abs_dmean"))


def _clock0(rec: Recording) -> int:
    return rec.start.hour * 60 + rec.start.minute


def daily_shape(rec: Recording, until: float | None = None) -> np.ndarray:
    """Half the patient's average day, half their mean, in 48 half-hour bins of clock time.

    Built from sensor readings before minute `until` (all of them when None). This is the control of section F.
    """
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    m = np.ones(t.size, dtype=bool) if until is None else t < until
    if not m.any():
        raise ValueError(f"{rec.rec_id}: no sensor reading before minute {until}")
    centres = np.arange(0, 1440, BIN) + BIN // 2
    return 0.5 * average_day_baseline((_clock0(rec) + t[m]) % 1440, g[m], centres, BIN) + 0.5 * float(
        g[m].mean()
    )


def shape_at(shape: np.ndarray, rec: Recording, t) -> np.ndarray:
    """A daily shape read at minutes `t` of recording `rec`, by that recording's own clock."""
    return shape[((_clock0(rec) + np.asarray(t, dtype=float)) % 1440).astype(int) // BIN]


def profile_rows(rec: Recording, k_days: float) -> list[dict] | None:
    """By-day rows of one recording for the profile alone; None when it cannot be run at k (Gate 2 rule).

    Day 0 is inside the wear. From day 1 on only the hidden readings are scored, against a shape and a report
    that were built before the split.
    """
    if why_skipped(rec, k_days) is not None:
        return None
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    stale = glucose_report(g[cal])
    control = shape_at(daily_shape(rec, split), rec, t[~cal])
    ids = {"rec_id": rec.rec_id, "patient_id": rec.patient_id, "k_days": k_days}
    rows = []
    floor = inside_the_wear(t[cal], g[cal])
    if floor is not None:
        rows.append({**ids, "day": 0, "control_rmse": profile_sigma(_clock0(rec) + t[cal], g[cal]), **floor})
    for d in daily_rows(t[~cal], split, g[~cal], {"control": control}):
        rows.append(
            {**ids, "day": d["day"], "control_rmse": d["control_rmse"], **aging(day_report(d), stale)}
        )
    return rows


def trace_rows(tr: dict) -> list[dict]:
    """By-day rows of one cached reveal trace: the twin, its control, the average day and the band."""
    split = float(tr["k_days"]) * 1440.0
    stale = glucose_report(tr["cal_truth"])
    ids = {
        "rec_id": tr["rec_id"],
        "patient_id": tr["patient_id"],
        "k_days": float(tr["k_days"]),
        "group": tr["group"],
    }
    rows = []
    floor = inside_the_wear(tr["cal_t"], tr["cal_truth"])
    if floor is not None:
        rows.append({**ids, "day": 0, **floor})
    day = day_index(tr["t"], split)
    inside = (tr["truth"] >= tr["lo"]) & (tr["truth"] <= tr["hi"])
    shown = {"twin": tr["twin"], "control": tr["shrunk"], "avgday": tr["day"]}
    for d in daily_rows(tr["t"], split, tr["truth"], shown):
        rows.append(
            {
                **ids,
                "day": d["day"],
                **{f"{name}_rmse": d[f"{name}_rmse"] for name in shown},
                "cov80": float(inside[day == d["day"]].mean()),
                "twin_mean_err": abs(d["twin_mean"] - d["day_mean"]),
                **aging(day_report(d), stale),
            }
        )
    return rows


def day_block(
    days: pd.DataFrame,
    k_days: float,
    cols: list[str],
    pairs: tuple = (),
    slopes: tuple = (),
    zero: tuple = (),
) -> dict:
    """Everything reported by day at one k: the table, the slope inside each patient, each day against day 0."""
    if days.empty:
        return {"k_days": k_days, "n_patients": 0}
    days = days.reindex(columns=[*cols, *(c for c in days.columns if c not in cols)])
    return {
        "k_days": k_days,
        "n_patients": int(days["patient_id"].nunique()),
        "recordings": int(days["rec_id"].nunique()),
        "by_day": summarise_days(days[cols], pairs),
        "slopes": [slope_per_day(days, c) for c in slopes],
        "against_day_zero": [row for c in zero for row in excess_over_day_zero(days, c)],
    }


def shanghai_block(recs: list[Recording], k_days: float) -> dict:
    skipped = Counter(w for w in (why_skipped(r, k_days) for r in recs) if w)
    rows = [row for r in recs for row in (profile_rows(r, k_days) or [])]
    slopes = ("control_rmse", "abs_dmean")
    block = day_block(pd.DataFrame(rows), k_days, PROFILE_COLS, (), slopes, ("abs_dmean",))
    return {**block, "skipped": dict(skipped)}


def cgmacros_block(traces: list[dict], k_days: float) -> dict:
    days = pd.DataFrame([row for tr in traces for row in trace_rows(tr)])
    slopes = ("twin_rmse", "control_rmse", "cov80", "abs_dmean")
    block = day_block(days, k_days, TWIN_COLS, TWIN_PAIRS, slopes, ("abs_dmean",))
    if len(days):
        t2d = days[days["group"] == "t2d"]
        block["groups"] = {str(g): int(n) for g, n in days.groupby("group")["patient_id"].nunique().items()}
        block["by_day_t2d"] = summarise_days(t2d.reindex(columns=TWIN_COLS), TWIN_PAIRS) if len(t2d) else []
    return block


def treatment(rec: Recording) -> dict:
    """What the files say about treatment during one wear. Compared across wears, never used as a predictor."""
    routes = set(rec.doses["route"]) if len(rec.doses) else set()
    listed = drug_flags(rec.static.get("agents"))["r_insulin"] == 1.0
    return {"insulin": bool(listed or routes & INSULIN_ROUTES), "pump": "csii" in routes}


def repeat_cases(recs: list[Recording]) -> list[dict]:
    """One row per later wear of a patient recorded more than once: the first wear's profile on the later wear.

    `old_profile_rmse` is the first wear's daily shape against the later wear's readings. Two yardsticks sit
    beside it: `fresh_profile_rmse`, the later wear's own shape built without the day being scored (what a new
    sensor wear would give), and `first_wear_rmse`, the same inside the first wear. A case series: no test.
    """
    by_patient: dict[str, list[Recording]] = {}
    for r in recs:
        by_patient.setdefault(r.patient_id, []).append(r)
    rows = []
    for pid, wears in sorted(by_patient.items()):
        if len(wears) < 2:
            continue
        first, *later = sorted(wears, key=lambda r: r.start)
        t1 = first.cgm["t_min"].to_numpy(dtype=float)
        g1 = first.cgm["glucose_mgdl"].to_numpy(dtype=float)
        shape, report = daily_shape(first), glucose_report(g1)
        before = treatment(first)
        agents = str(first.static.get("agents") or "").strip().lower()
        for rec in later:
            t = rec.cgm["t_min"].to_numpy(dtype=float)
            g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
            now = treatment(rec)
            between = (rec.start - first.start) / pd.Timedelta(days=1)
            rows.append(
                {
                    "patient_id": pid,
                    "dev": is_dev_patient(pid),
                    "later_rec": rec.rec_id,
                    "days_between_starts": float(between),
                    "days_since_first_sensor": float(between - first.n_min / 1440.0),
                    "first_wear_days": first.n_min / 1440.0,
                    "later_wear_days": rec.n_min / 1440.0,
                    "old_profile_rmse": rmse(shape_at(shape, rec, t), g),
                    "fresh_profile_rmse": profile_sigma(_clock0(rec) + t, g),
                    "first_wear_rmse": profile_sigma(_clock0(first) + t1, g1),
                    **aging(glucose_report(g), report),
                    "insulin_first": before["insulin"],
                    "insulin_later": now["insulin"],
                    "pump_first": before["pump"],
                    "pump_later": now["pump"],
                    "agents_changed": agents != str(rec.static.get("agents") or "").strip().lower(),
                }
            )
    return rows


def cases_block(recs: list[Recording]) -> dict:
    rows = repeat_cases(recs)
    if not rows:
        return {"n_patients": 0, "n_cases": 0, "cases": []}
    df = pd.DataFrame(rows)
    changed = (
        df["agents_changed"]
        | (df["insulin_first"] != df["insulin_later"])
        | (df["pump_first"] != df["pump_later"])
    )
    return {
        "n_patients": int(df["patient_id"].nunique()),
        "n_cases": int(len(df)),
        "old_profile_rmse": float(df["old_profile_rmse"].median()),
        "fresh_profile_rmse": float(df["fresh_profile_rmse"].median()),
        "first_wear_rmse": float(df["first_wear_rmse"].median()),
        "abs_dmean": float(df["abs_dmean"].median()),
        "n_moved": int(df["moved"].sum()),
        "n_treatment_changed": int(changed.sum()),
        "cases": rows,
    }


def _by_day_report(title: str, note: str, result: dict, columns: list[str]) -> str:
    lines = [f"# {title}", "", note, ""]
    lines.append(
        "Test patients. Descriptive: no bar."
        if result["confirmatory"]
        else "Development patients. Not confirmatory."
    )
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days", ""]
        if not block["n_patients"]:
            lines.append("No recording could be run.")
            continue
        lines += [f"{block['n_patients']} patients, {block['recordings']} recordings.", ""]
        lines += [table(block["by_day"], columns, digits=2), "", "Change per day inside each patient:", ""]
        lines += [table(block["slopes"], digits=2), "", "Each day against the same patient's day 0:", ""]
        lines.append(table(block["against_day_zero"], digits=3))
        if block.get("skipped"):
            lines += ["", "Not run: " + "; ".join(f"{v} ({k})" for k, v in block["skipped"].items())]
    return "\n".join(lines) + "\n"


def _cases_report(result: dict) -> str:
    lines = [
        "# Expiry: patients recorded again (case series)",
        "",
        "The first wear's daily shape against the later wear. `fresh_profile_rmse` is what a new wear's own shape "
        "gives. A case series of a handful of patients under changing treatment: no test, no interval.",
        "",
        "All re-recorded patients."
        if result["confirmatory"]
        else "Development patients only. Not confirmatory.",
        "",
        f"{result['n_cases']} later wears of {result['n_patients']} patients.",
        "",
    ]
    lines.append(table(result["cases"]))
    return "\n".join(lines) + "\n"


def run(what: str, confirm: bool, out_dir: Path) -> dict:
    """Load what the output needs, compute, write. Test patients are loaded only with `confirm`."""
    split = "test" if confirm else "dev"
    if what == "cgmacros":
        result = {"confirmatory": confirm, "by_k": []}
        for k in K_LIST:
            traces = load_traces("cgmacros", split, k)
            if not traces:
                raise SystemExit(
                    f"no {split} traces at k = {k:g}: run python -m chhaya.eval.traces --split {split}"
                )
            if confirm:
                require_gate2(traces)
            result["by_k"].append(cgmacros_block(traces, k))
        note = "The twin (`twin`), its control with no meals (`control`) and the raw average day, by day since the sensor."
        cols = [
            "day",
            "n_patients",
            "twin_rmse",
            "control_rmse",
            "avgday_rmse",
            "cov80",
            "abs_dmean",
            "share_moved",
        ]
        report = _by_day_report("Expiry by day: CGMacros", note, result, cols)
    else:
        from chhaya.data.shanghai import load_all

        recs = load_all()
        if what == "shanghai":
            recs = [r for r in recs if is_dev_patient(r.patient_id) != confirm]
            result = {"confirmatory": confirm, "by_k": [shanghai_block(recs, k) for k in K_LIST]}
            note = "The daily shape of the first k days against each later day; no fingersticks are read."
            cols = ["day", "n_patients", "control_rmse", "abs_dmean", "dmean", "share_moved", "abs_dtar"]
            report = _by_day_report("Expiry by day: ShanghaiT2DM", note, result, cols)
        else:
            # nothing is fitted across patients here, so the registered case series uses all of them
            recs = recs if confirm else [r for r in recs if is_dev_patient(r.patient_id)]
            result = {"confirmatory": confirm, **cases_block(recs)}
            report = _cases_report(result)
    write_outputs(out_dir, result, report, provenance(confirm, output=what, k=list(K_LIST)))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["shanghai", "cgmacros", "cases"])
    ap.add_argument(
        "--confirm", action="store_true", help="read the test patients; this is done once per output"
    )
    args = ap.parse_args()
    out_dir = FOLDER / (args.what if args.confirm else f"{args.what}-dev")
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        refuse_second_run(out_dir)
    run(args.what, args.confirm, out_dir)
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run, lint, commit**

Run: `uv run pytest tests/test_expiry.py -q`
Expected: 10 passed

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/expiry.py tests/test_expiry.py
git commit -m "feat: expiry by day on both datasets and the case series of re-recorded patients"
```

---

### Task 5: Band recalibration

**Files:**
- Create: `src/chhaya/eval/calibrate.py`
- Test: `tests/test_calibrate.py`

**Interfaces:**
- Consumes: Task 1 (`MIN_DAY_READINGS`, `day_index`, `check_committed`, `provenance`, `table`, `write_outputs`); Task 3 (`load_traces`, `require_gate2`); `chhaya.eval.gate2.COVERAGE_BAND = (0.70, 0.90)`.
- Produces: `rescale(trace, factor) -> (lo, hi)` (the function the dashboard's artifact build will call), `prepare(trace) -> dict` (keys `patient_id`, `need`, `day`), `fit_factor(items) -> float`, `fit_by_day(items) -> dict[str, float]`, `prefer_by_day(gaps, inside, fitted) -> bool`, `choose(items) -> dict` (the design: keys `design`, `factor`, `by_day`, `left_out_day_gap`, `left_out_patients_within`, `n_patients`, `target`), `evaluate(items, design) -> dict`, `transfers(block) -> bool`, `run(items_by_k, confirmatory, design=None) -> dict`; `results/calibrate/cgmacros-dev/band.json`; the commands `python -m chhaya.eval.calibrate [--confirm]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_calibrate.py`:

```python
import numpy as np
import pytest

from chhaya.eval import calibrate as cb
from chhaya.eval.metrics import coverage


def _trace(
    patient_id: str, spread: float, k_days: float = 5.0, days: int = 5, seed: int = 0, grow: float = 0.0
):
    """A band drawn for an error of 10 mg/dL around an estimate whose real error is `spread`.

    With `grow`, the real error rises by that share per day since the sensor while the band stays as drawn.
    """
    rng = np.random.default_rng(seed)
    t = k_days * 1440 + np.arange(0, days * 1440, 15.0)
    twin = 140.0 + 20.0 * np.sin(2 * np.pi * t / 1440)
    day = (t - k_days * 1440) // 1440
    truth = twin + rng.normal(0.0, spread, t.size) * (1.0 + grow * day)
    half = 1.2816 * 10.0  # the 10th and 90th percentiles of a normal error of 10
    return {"patient_id": patient_id, "k_days": k_days, "t": t, "truth": truth, "twin": twin,
            "lo": twin - half, "hi": twin + half}  # fmt: skip


def _items(spread: float = 10.0, n: int = 12, **kw):
    return [cb.prepare(_trace(f"p{i}", spread, seed=i, **kw)) for i in range(n)]


def test_the_factor_a_reading_needs_is_the_factor_at_which_the_rescaled_band_reaches_it():
    tr = _trace("p", 14.0)
    item = cb.prepare(tr)
    for f in (0.7, 1.0, 1.6):
        lo, hi = cb.rescale(tr, f)
        assert np.mean(item["need"] <= f) == coverage(tr["truth"], lo, hi)
    assert cb.rescale(tr, 1.0)[0] == pytest.approx(tr["lo"]) and cb.rescale(tr, 1.0)[1] == pytest.approx(
        tr["hi"]
    )
    assert item["day"].min() == 1 and item["day"].max() == 5


def test_a_band_that_is_too_narrow_is_widened_to_cover_80_percent():
    items = _items(spread=14.0)  # the real error is 1.4 times what the band was drawn for
    before = cb.patient_coverage(items).mean()
    f = cb.fit_factor(items)
    after = cb.patient_coverage(items, {"design": "single", "factor": f}).mean()
    assert before < 0.68 and 1.3 < f < 1.5 and abs(after - 0.80) < 0.01
    assert 0.6 < cb.fit_factor(_items(spread=7.0)) < 0.8  # and one that is too wide is narrowed
    assert abs(cb.fit_factor(_items(spread=10.0)) - 1.0) < 0.05
    with pytest.raises(ValueError, match="no trace"):
        cb.fit_factor([])


def test_two_recordings_of_one_patient_count_once():
    items = _items(spread=10.0, n=3)
    twice = [*items, {**items[0], "need": items[0]["need"] * 3.0}]
    cov = cb.patient_coverage(twice)
    assert len(cov) == 3 and cov["p0"] < cb.patient_coverage(items)["p0"]


def test_a_band_with_no_width_cannot_divide_by_zero():
    tr = _trace("p", 10.0)
    flat = {**tr, "lo": tr["twin"].copy(), "hi": tr["twin"].copy()}
    item = cb.prepare(flat)
    assert np.isfinite(item["need"]).all() and np.mean(item["need"] <= 2.0) < 0.01


def test_a_factor_per_day_is_fitted_only_for_days_enough_patients_reach():
    items = _items(spread=10.0, grow=0.25)  # the error grows a quarter per day; the drawn band does not
    by_day = cb.fit_by_day(items)
    assert list(by_day) == ["1", "2", "3", "4", "5"] and by_day["1"] < by_day["3"] < by_day["5"]
    assert cb.fit_by_day(items[:9]) == {}  # nine patients are too few for any day
    short = [*items[:9], *(cb.prepare(_trace(f"s{i}", 10.0, days=2, seed=50 + i)) for i in range(3))]
    assert list(cb.fit_by_day(short)) == ["1", "2"]  # only nine patients reach day 3
    many = [*(cb.prepare(_trace(f"m{i}", 10.0, seed=70 + i)) for i in range(14)),
            *(cb.prepare(_trace(f"e{i}", 10.0, days=2, seed=90 + i)) for i in range(6))]  # fmt: skip
    assert list(cb.fit_by_day(many)) == [
        "1",
        "2",
    ]  # 14 of 20 reach day 3: enough heads, too few of the cohort
    design = {"design": "by_day", "by_day": {"1": 1.0, "2": 1.5}}
    f = cb.factors(items[0], design)
    assert f[0] == 1.0 and f[-1] == 1.5  # days past the last fitted day use the last factor


def test_the_per_day_design_is_chosen_only_when_it_helps_patients_left_out():
    growing = cb.choose(_items(spread=10.0, grow=0.25))
    gap = growing["left_out_day_gap"]
    assert growing["design"] == "by_day" and growing["n_patients"] == 12
    assert (
        gap["single"] > 0.06 and gap["by_day"] < gap["single"] - cb.MIN_GAIN
    )  # day 1 too wide, day 5 too narrow
    assert growing["left_out_patients_within"] == {"single": 12, "by_day": 12}  # per patient both look fine
    steady = cb.choose(_items(spread=14.0))
    assert (
        steady["design"] == "single" and 1.3 < steady["factor"] < 1.5
    )  # no real gain: the single factor stays
    assert abs(steady["left_out_day_gap"]["single"] - steady["left_out_day_gap"]["by_day"]) < cb.MIN_GAIN
    few = cb.choose(_items(spread=14.0, n=8))
    assert few["design"] == "single" and few["by_day"] == {} and np.isnan(few["left_out_day_gap"]["by_day"])


def test_a_factor_per_day_must_not_lose_on_the_number_the_registration_reports():
    closer = {"single": 0.030, "by_day": 0.002}
    assert cb.prefer_by_day(closer, {"single": 12, "by_day": 12}, fitted=True) is True
    assert (
        cb.prefer_by_day(closer, {"single": 17, "by_day": 14}, fitted=True) is False
    )  # fewer patients within
    assert cb.prefer_by_day({"single": 0.030, "by_day": 0.015}, {"single": 12, "by_day": 13}, True) is False
    assert cb.prefer_by_day(closer, {"single": 12, "by_day": 12}, fitted=False) is False
    assert (
        cb.prefer_by_day({"single": 0.03, "by_day": float("nan")}, {"single": 8, "by_day": 0}, False) is False
    )


def test_the_recalibrated_band_is_used_only_if_it_transfers_to_held_out_patients():
    def block(before, after, n_before, n_after):
        return {"before": {"mean_coverage": before, "patients_within": n_before},
                "after": {"mean_coverage": after, "patients_within": n_after}}  # fmt: skip

    assert cb.transfers(block(0.87, 0.80, 10, 13)) is True
    assert cb.transfers(block(0.83, 0.74, 10, 12)) is False  # further from 80 % than it was
    assert cb.transfers(block(0.87, 0.80, 10, 9)) is False  # closer on average, fewer patients within


def test_the_evaluation_reports_patients_within_70_to_90_before_and_after():
    items = _items(spread=14.0)
    out = cb.evaluate(items, {"design": "single", "factor": cb.fit_factor(items), "by_day": {}})
    assert (
        out["n_patients"] == 12 and out["before"]["patients_within"] < out["after"]["patients_within"] == 12
    )
    assert out["before"]["mean_coverage"] < 0.68 and abs(out["after"]["mean_coverage"] - 0.80) < 0.01
    assert [d["day"] for d in out["by_day"]] == [1, 2, 3, 4, 5] and out["by_day"][0]["n_patients"] == 12


def test_test_patients_only_report_a_design_fixed_beforehand():
    dev = {5.0: _items(spread=14.0), 3.0: _items(spread=14.0, k_days=3.0, days=7)}
    chosen = cb.run(dev, confirmatory=False)
    assert chosen["confirmatory"] is False and [b["k_days"] for b in chosen["by_k"]] == [5.0, 3.0]
    # held-out patients whose band was right as drawn: widening it for them is a step away from target
    test = {5.0: _items(spread=10.0), 3.0: _items(spread=10.0, k_days=3.0, days=7)}
    reported = cb.run(test, confirmatory=True, design=chosen["design"])
    assert reported["design"] == chosen["design"]  # nothing is refitted on the patients being reported
    assert chosen["use_recalibrated_band"] is None and reported["use_recalibrated_band"] is False
    # so a cohort that differs from the development one ends up off target, and the report says so
    assert reported["by_k"][0]["after"]["mean_coverage"] > 0.88
    text = cb._report(reported)
    assert "fixed on development patients" in text and "did not transfer" in text and "p0" not in text
    assert "in-sample" in cb._report(chosen)
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_calibrate.py -q`
Expected: collection error, `ImportError: cannot import name 'calibrate' from 'chhaya.eval'`

- [ ] **Step 3: Implement**

Create `src/chhaya/eval/calibrate.py`:

```python
"""Band recalibration (Amendment 3, "Descriptive, no bar").

The 80 % band of the reveal is widened or narrowed about the estimate by one factor, or by one factor per day
since the sensor. The factor and the choice between the two designs come from CGMacros development patients;
test patients only report: mean coverage, and how many patients fall within 70 to 90 %. The estimator and the
Gate 2 results are not touched: the factor is applied to cached traces, and later by the dashboard.

Usage: python -m chhaya.eval.calibrate             (development patients: choose, write band.json)
       python -m chhaya.eval.calibrate --confirm   (test patients, once, with the band.json on disk)
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR
from chhaya.eval.descriptive import (
    MIN_DAY_READINGS,
    check_committed,
    day_index,
    provenance,
    table,
    write_outputs,
)
from chhaya.eval.gate2 import COVERAGE_BAND, _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.eval.traces import load_traces, require_gate2

TARGET = 0.80
GRID = np.round(np.arange(0.50, 2.0001, 0.01), 2)  # the factors tried
MIN_FACTOR_PATIENTS = 10  # a day needs this many development patients to get its own factor ...
MIN_DAY_SHARE = 0.8  # ... and this share of them: later days hold whoever is left, at the end of their wear
MIN_GAIN = (
    0.02  # a factor per day must bring each day's coverage this much closer to target, or it is not used
)
PRIMARY_K = 5.0  # the Gate 2 setting; the factor is chosen there
ALSO_K = 3.0  # reported with the same factor
EPS = 1e-6
FOLDER = RESULTS_DIR / "calibrate"
BAND = FOLDER / "cgmacros-dev" / "band.json"
UNCHANGED = {"design": "single", "factor": 1.0, "by_day": {}}


def half_widths(tr: dict) -> tuple[np.ndarray, np.ndarray]:
    """How far the band reaches below and above the estimate. Never zero, so a factor always means something."""
    return np.maximum(tr["twin"] - tr["lo"], EPS), np.maximum(tr["hi"] - tr["twin"], EPS)


def rescale(tr: dict, factor) -> tuple[np.ndarray, np.ndarray]:
    """The band with both half-widths multiplied by `factor` (one number, or one value per reading)."""
    down, up = half_widths(tr)
    return tr["twin"] - factor * down, tr["twin"] + factor * up


def prepare(tr: dict) -> dict:
    """Per hidden reading: the factor at which the band just reaches it, and its day since the sensor."""
    down, up = half_widths(tr)
    off = tr["truth"] - tr["twin"]
    return {
        "patient_id": str(tr["patient_id"]),
        "need": np.where(off >= 0, off / up, -off / down),
        "day": day_index(tr["t"], float(tr["k_days"]) * 1440.0),
    }


def factors(item: dict, design: dict):
    """The factor each reading of `item` gets under `design`; days past the last fitted day use the last one."""
    if design["design"] == "single":
        return design["factor"]
    by_day = {int(d): f for d, f in design["by_day"].items()}
    last = max(by_day)
    return np.array([by_day[min(int(d), last)] for d in item["day"]])


def patient_coverage(items: list[dict], design: dict = UNCHANGED) -> pd.Series:
    """Share of hidden readings inside the band, per patient (recordings of one patient are averaged)."""
    rows = [
        {"patient_id": i["patient_id"], "cov": float(np.mean(i["need"] <= factors(i, design)))} for i in items
    ]
    return pd.DataFrame(rows).groupby("patient_id")["cov"].mean()


def fit_factor(items: list[dict]) -> float:
    """The factor whose mean coverage over patients is closest to 80 %; of two equally close, the one nearer 1."""
    if not items:
        raise ValueError("no trace to fit a band factor on")
    # coverage of every recording at every factor of the grid, then patients, then the cohort
    curves = pd.DataFrame(
        [np.mean(i["need"][:, None] <= GRID[None, :], axis=0) for i in items],
        index=[i["patient_id"] for i in items],
    )
    miss = np.abs(curves.groupby(level=0).mean().mean(axis=0).to_numpy() - TARGET)
    best = min(range(GRID.size), key=lambda j: (round(float(miss[j]), 9), abs(float(GRID[j]) - 1.0)))
    return float(GRID[best])


def on_day(item: dict, d: int) -> dict | None:
    """The readings of one day since the sensor, or None when that day holds too few."""
    m = item["day"] == d
    if m.sum() < MIN_DAY_READINGS:
        return None
    return {"patient_id": item["patient_id"], "need": item["need"][m], "day": item["day"][m]}


def fit_by_day(items: list[dict]) -> dict[str, float]:
    """One factor per day since the sensor, for the consecutive days that most of the cohort reaches.

    Recordings end at different lengths. A late day holds the few patients still recording, on the last days
    of their sensor, so a factor fitted there would describe who is left, not how the band ages.
    """
    n_patients = len({i["patient_id"] for i in items})
    enough = max(MIN_FACTOR_PATIENTS, int(np.ceil(MIN_DAY_SHARE * n_patients)))
    out: dict[str, float] = {}
    d = 1
    while True:
        sub = [s for s in (on_day(i, d) for i in items) if s is not None]
        if len({s["patient_id"] for s in sub}) < enough:
            return out
        out[str(d)] = fit_factor(sub)
        d += 1


def within(cov: pd.Series) -> int:
    return int(((cov >= COVERAGE_BAND[0]) & (cov <= COVERAGE_BAND[1])).sum())


def day_gap(by_day: pd.DataFrame) -> float:
    """How far the coverage of each day lies from 80 %, averaged over days (0.05 is five points)."""
    return float((by_day.groupby("day")["cov"].mean() - TARGET).abs().mean())


def prefer_by_day(gaps: dict, inside: dict, fitted: bool) -> bool:
    """Whether the factor per day replaces the single factor, from what both did on patients left out.

    It has more freedom, so it must earn its place twice: each day's coverage at least MIN_GAIN closer to
    target, and no fewer patients within 70 to 90 %, which is the number the registration reports.
    """
    closer = fitted and gaps["single"] - gaps["by_day"] >= MIN_GAIN
    return bool(closer and inside["by_day"] >= inside["single"])


def choose(items: list[dict]) -> dict:
    """Fit both designs on development patients and pick one, leaving each patient out in turn.

    One factor already brings a patient's coverage over the whole hidden window to target; what a factor per
    day can add is a band that is right on day 1 and still right on day 5. So for patients left out of the
    fit both are measured: how far each day's coverage lies from 80 %, and how many patients fall within
    70 to 90 %. `prefer_by_day` decides. The factors written are then fitted on all development patients.
    """
    patients = sorted({i["patient_id"] for i in items})
    by_day = fit_by_day(items)
    inside = {"single": 0, "by_day": 0}
    cells: dict[str, list[dict]] = {"single": [], "by_day": []}
    for p in patients:
        rest = [i for i in items if i["patient_id"] != p]
        held = [i for i in items if i["patient_id"] == p]
        designs = {
            "single": {"design": "single", "factor": fit_factor(rest)},
            "by_day": {"design": "by_day", "by_day": fit_by_day(rest)},
        }
        for name, design in designs.items():
            if name == "by_day" and not design["by_day"]:
                continue
            inside[name] += within(patient_coverage(held, design))
            for d in by_day:  # the same days for both designs
                sub = [s for s in (on_day(i, int(d)) for i in held) if s is not None]
                if sub:
                    cells[name].append({"day": int(d), "cov": float(patient_coverage(sub, design).iloc[0])})
    gaps = {name: day_gap(pd.DataFrame(rows)) if rows else float("nan") for name, rows in cells.items()}
    return {
        "design": "by_day" if prefer_by_day(gaps, inside, bool(by_day)) else "single",
        "factor": fit_factor(items),
        "by_day": by_day,
        "left_out_day_gap": gaps,
        "left_out_patients_within": inside,
        "n_patients": len(patients),
        "target": TARGET,
    }


def evaluate(items: list[dict], design: dict) -> dict:
    """Coverage before and after the recalibration: mean over patients, range, patients within 70 to 90 %."""
    out: dict = {"n_patients": len({i["patient_id"] for i in items})}
    for name, d in (("before", UNCHANGED), ("after", design)):
        cov = patient_coverage(items, d)
        out[name] = {
            "mean_coverage": float(cov.mean()),
            "min": float(cov.min()),
            "max": float(cov.max()),
            "patients_within": within(cov),
        }
    by_day = []
    for d in sorted({int(x) for i in items for x in np.unique(i["day"])}):
        sub = [s for s in (on_day(i, d) for i in items) if s is not None]
        if sub:
            by_day.append(
                {
                    "day": d,
                    "n_patients": len({s["patient_id"] for s in sub}),
                    "before": float(patient_coverage(sub).mean()),
                    "after": float(patient_coverage(sub, design).mean()),
                }
            )
    out["by_day"] = by_day
    return out


def _report(result: dict) -> str:
    design = result["design"]
    lines = ["# Band recalibration", ""]
    lines.append(
        "Test patients; the factor was fixed on development patients. Descriptive: no bar."
        if result["confirmatory"]
        else "Development patients: the factor is chosen here, so its coverage below is in-sample."
    )
    chosen = (
        f"one factor, {design['factor']:.2f}"
        if design["design"] == "single"
        else f"per day, {design['by_day']}"
    )
    lines += [
        "",
        f"Design: {chosen}. On development patients left out of the fit, distance of each day's coverage from "
        f"80 %: {design['left_out_day_gap']}; patients within 70 to 90 %: {design['left_out_patients_within']}.",
    ]
    if result["confirmatory"]:
        verdict = "is used" if result["use_recalibrated_band"] else "is not used: it did not transfer"
        lines += ["", f"On these patients, at k = {PRIMARY_K:g}: the recalibrated band {verdict}."]
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days ({block['n_patients']} patients)", ""]
        rows = [{"band": name, **block[name]} for name in ("before", "after")]
        lines += [table(rows, digits=3), "", table(block["by_day"], digits=3)]
    return "\n".join(lines) + "\n"


def transfers(block: dict) -> bool:
    """Whether the recalibrated band is the one to show, judged on the patients it was not fitted on.

    Yes only if its mean coverage is no further from 80 % than the band as Gate 2 scored it and no fewer
    patients fall within 70 to 90 %. Otherwise the band stays as it was and the result says so.
    """
    before, after = block["before"], block["after"]
    no_further = abs(after["mean_coverage"] - TARGET) <= abs(before["mean_coverage"] - TARGET)
    return bool(no_further and after["patients_within"] >= before["patients_within"])


def run(items_by_k: dict[float, list[dict]], confirmatory: bool, design: dict | None = None) -> dict:
    """Report every k under one design. Without a design (development) it is chosen here, on the primary k."""
    if design is None:
        design = choose(items_by_k[PRIMARY_K])
    by_k = [{"k_days": k, **evaluate(items, design)} for k, items in items_by_k.items()]
    primary = next(b for b in by_k if b["k_days"] == PRIMARY_K)
    # only held-out patients can say whether the factor transfers; on development patients it is in-sample
    use = transfers(primary) if confirmatory else None
    return {"confirmatory": confirmatory, "design": design, "use_recalibrated_band": use, "by_k": by_k}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="report on the test patients; this is done once")
    args = ap.parse_args()
    out_dir = FOLDER / ("cgmacros" if args.confirm else "cgmacros-dev")
    split = "test" if args.confirm else "dev"
    design = None
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        refuse_second_run(out_dir)
        if not BAND.exists():
            raise SystemExit(f"{BAND} is missing: choose the band on development patients first")
        design = json.loads(BAND.read_text(encoding="utf-8"))
    items_by_k = {}
    for k in (PRIMARY_K, ALSO_K):
        traces = load_traces("cgmacros", split, k)
        if not traces:
            raise SystemExit(
                f"no {split} traces at k = {k:g}: run python -m chhaya.eval.traces --split {split}"
            )
        if args.confirm:
            require_gate2(traces)
        items_by_k[k] = [prepare(tr) for tr in traces]
    result = run(items_by_k, args.confirm, design)
    write_outputs(out_dir, result, _report(result), provenance(args.confirm, k=[PRIMARY_K, ALSO_K]))
    if not args.confirm:
        BAND.write_text(json.dumps(result["design"], indent=2), encoding="utf-8")
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the whole suite, lint, commit**

Run: `uv run pytest tests/test_calibrate.py -q`
Expected: 10 passed

Run: `uv run pytest -q`
Expected: 265 passed, in about four and a half minutes (`uv run pytest -q -m "not slow"` is the quick one).

Run: `git diff --name-status bdafe69 HEAD -- src`
Expected: five lines, each starting with `A`. No existing source file has been modified (`bdafe69` is the commit this plan was written on).

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/calibrate.py tests/test_calibrate.py
git commit -m "feat: band recalibration chosen on development patients, with a rule for whether it is used"
```

---

### Task 6: Development runs and independent review

**Files:**
- Create: `results/fingersticks/shanghai-dev-report/`, `results/expiry/shanghai-dev/`, `results/expiry/cases-dev/`, `results/expiry/cgmacros-dev/`, `results/calibrate/cgmacros-dev/` (each: `summary.json`, `report.md`, `provenance.json`; the last also `band.json`)
- Modify: `docs/PREREGISTRATION.md` only if Step 2 or Step 3 says so (one dated line appended, nothing edited)

- [ ] **Step 1: The five development runs**

The development traces of Task 3, Step 5 must have finished.

```bash
uv run python -m chhaya.eval.fingersticks_report
uv run python -m chhaya.eval.expiry shanghai
uv run python -m chhaya.eval.expiry cases
uv run python -m chhaya.eval.expiry cgmacros
uv run python -m chhaya.eval.calibrate
```

Each takes seconds. The first one stops with "does not reproduce the committed run" if the estimator is not the frozen one; that would be a defect to find, not a message to work around.

- [ ] **Step 2: Compare with what the registration note says was seen**

The note of Task 0 lists what the scratch runs showed. From the five reports, check these and nothing else:

| Output | Must read |
|---|---|
| Second pass, k = 3 | 24 patients; mean error `stale` 14.83, `hindsight` 12.10; time above 180 `stale` 8.76, `hindsight` 9.91 (9.79 after the review fix to the spread; see the addendum to the note); Spearman -0.67 |
| Expiry, Shanghai, k = 3 | 49 patients on day 1; `abs_dmean` 10.8 on day 0; slope of `abs_dmean` 0.56 (0.28 to 1.40) |
| Case series | 3 later wears of 3 patients; one with `moved` = 1 |
| Expiry, CGMacros | 25 patients; at k = 3 the twin is closer than its control on days 1 to 7 and further on days 8 and 9 |
| Band | design "single", factor 0.78; mean coverage 0.874 before |

If every line matches, go on. If one differs, the committed code is not the code the note describes: find out why before anything else, and append one dated line to the note saying what differed and why. Do not edit the note's text.

- [ ] **Step 3: Independent review**

Dispatch an independent code review on the five new modules (`descriptive`, `fingersticks_report`, `traces`, `expiry`, `calibrate`) with this question, verbatim:

> Find any path by which (a) a sensor reading from after the split reaches a stated report, a daily shape, a stale report, a spread, a surprise, an alarm score or a band factor; (b) a test patient's data reaches a band factor or its design choice, an alarm threshold or the pooled sensor map; (c) a pass with `--confirm` could write results from an estimator or cohort other than the committed one; (d) a statistic is taken over recordings where Amendment 3 says patients, or over readings where it says patients; (e) a by-day number mixes patients with different days in a way the report does not disclose. For each finding give the file, the line and a failing test.

Dispatch a code review on the same files. Fix what they find, test first, one commit per finding. A finding that changes a number in Step 2's table means the development runs are repeated and the note gets a dated line.

The staleness modules do not exist yet; they are reviewed in Task 8.

- [ ] **Step 4: Freeze the band and commit the development results**

`results/calibrate/cgmacros-dev/band.json` is the design the test pass will read. Commit it with the other development folders before any test patient is read:

```bash
git add results/fingersticks/shanghai-dev-report results/expiry results/calibrate docs/PREREGISTRATION.md
git commit -m "results: development runs of the descriptive outputs; band design frozen on development patients"
```

---

### Task 7: The passes over test patients, one record each

Each pass is run once. Whatever it prints is the result. Order is priority order: if the day ends early, what is done is the more important part.

**Files:**
- Create: `results/fingersticks/shanghai-report/`, `results/expiry/shanghai/`, `results/expiry/cases/`, `results/expiry/cgmacros/`, `results/calibrate/cgmacros/`
- Create: `docs/decisions/<date>-fingersticks-report.md`, `docs/decisions/<date>-expiry.md`, `docs/decisions/<date>-band.md`
- Modify: `docs/plans/2026-10-02-chhaya-roadmap.md` (Status table, row M3), `docs/PROGRESS.md`

- [ ] **Step 1: Second pass of section F**

`git status --porcelain -- src` prints nothing, then:

```bash
uv run python -m chhaya.eval.fingersticks_report --confirm
```

It first reproduces 29 patients, control 36.708, live -2.793 and in hindsight -9.495 at k = 3 (and the k = 5 figures), then writes `results/fingersticks/shanghai-report/`.

- [ ] **Step 2: Record it**

Write `docs/decisions/<date>-fingersticks-report.md` with these sections, in this order:

1. **What this is.** The declared second pass; frozen estimator; reproduced the confirmatory run before writing; descriptive, no bar; command and commit.
2. **How far the report had aged** (k = 3 and k = 5): median distance of the hidden window's mean from the stale report's, signed median, share of patients beyond 20 mg/dL.
3. **The three numbers of the report**: for mean, time above 180 and time in range, the median error of the stale report, the fingerstick average (on the sensor's scale and as read), the shape alone, the live and the in-hindsight estimate; then each registered comparison with its interval, share of patients and p.
4. **Error by day**: the table, and the slopes inside each patient. Say which days fewer than 80 % of the cohort reach.
5. **How often these patients test**: quartiles for test and development cohorts and the Spearman correlation. State plainly whether it supports the guess in the fingerstick record of 8 Oct (test patients gained more because they test more).
6. **What it means.** Three sentences at most, each with its number. If the rebuilt report does not beat the stale report on a number, say "did not beat", with both figures. If the plain count of crossings does better than the spread on time above 180, say so.
7. **What a reader should weigh.** A three-day report stands in for a fourteen-day one; supervised care; this pass read the test patients a second time after F1 was known.
8. **The claim to quote.** One sentence of this shape, with the numbers that came out:
   "On N held-out Shanghai patients, in the D days after a three-day sensor report, that report missed the mean glucose the sensor then showed by a median of A mg/dL; the report rebuilt from fingersticks missed it by B (median paired difference C, 95 % interval L to U) and was [closer than / no closer than] the plain fingerstick average on time above 180 (E against F points)."

Update the fingerstick record's last bullet of "What it means" only by adding a pointer to this record; do not edit its numbers. Update the roadmap Status row M3 and `docs/PROGRESS.md` (the clause table and "The claims to quote").

```bash
git add results/fingersticks/shanghai-report docs
git commit -m "results: second pass of the fingerstick experiment on held-out patients (report-level, by day)"
```

- [ ] **Step 3: Expiry, Shanghai by day and the case series**

```bash
uv run python -m chhaya.eval.expiry shanghai --confirm
uv run python -m chhaya.eval.expiry cases --confirm
```

- [ ] **Step 4: Expiry, CGMacros by day**

Build the test traces (20 patients, two calibration lengths, about 12 minutes with 6 workers; start it in the background and say so):

```bash
uv run python -m chhaya.eval.traces --split test --confirm --jobs 6
```

`git status --porcelain -- src` must print nothing first: the command refuses uncommitted code, and it takes no `--k` or `--members` for test patients. Expected last line: `Reproduces the Gate 2 run.` Otherwise it stops with an error that lists every recording that differs; the cause has to be found before anything else is run. Unlike the passes below it may be repeated: the traces are a cache of numbers that are already committed.

```bash
uv run python -m chhaya.eval.expiry cgmacros --confirm
```

- [ ] **Step 5: Record expiry**

Write `docs/decisions/<date>-expiry.md`:

1. **What this is.** Three descriptive outputs; commands, commits, cohorts with counts and what was skipped and why.
2. **Shanghai, by day** (k = 3, then k = 5): the table with day 0; the slope of the distance from the report's mean inside each patient with its interval; each day against day 0; the share of patients beyond 20 mg/dL on day 0, day 3, day 7 and the last day that 80 % of the cohort reaches. State the direction (the signed median: under supervised care glucose is expected to fall).
3. **CGMacros, by day**: the twin against its control on each day, with intervals; band coverage by day; the type 2 group. **Read only the days that at least 80 % of the cohort reaches as evidence about days since the sensor.** On development patients the later days were the last days of the sensor for the few patients still recording, and both the twin's advantage and the band's coverage fell there at k = 3 and at k = 5 on the same day of the wear. Say whether the test patients show the same.
4. **Case series**: the table of nine later wears; for each, days since the first sensor, the old shape's error beside the fresh shape's, whether the mean moved by more than 20 mg/dL, and treatment at both wears. Counts only as a summary: "J of 9 later wears had moved; K of those J had a treatment change". No test.
5. **What it means for "how long the report stays true".** One paragraph. The honest forms are: "the report's mean drifts by about X mg/dL per day (interval), so after D days a typical patient is Y from it", or "no ageing was detectable within the days observed".
6. **What it means for the Gate 2 sentence.** The current claim says the meal log's gain "lasts about five days". If the test patients show the gain on every day that most of the cohort reaches, at k = 3 as far as day 7, that clause is wrong as worded: write the corrected sentence here, and change it in `docs/PROGRESS.md` and `docs/PROJECT_GUIDE.md` with a pointer to this record. The Gate 2 record itself is not edited.
7. **What a reader should weigh.** Three-day and five-day reports stand in for a fourteen-day one; supervised care with treatment being adjusted; day 0 uses k - 1 days; two wears are two sensors; a case series of eight patients.
8. **The claim to quote**, of this shape:
   "On N held-out Shanghai patients a day's mean glucose lay a median of A mg/dL from a three-day sensor report's mean inside the wear and B on day 7; inside each patient that distance grew by S mg/dL per day (95 % interval L to U), and P % of patients had moved by more than 20 mg/dL by day 7. In eight patients recorded again 12 to 168 days later, J of nine later wears had moved by more than 20 mg/dL."

Run the clinical-wording review on sections 5 and 8 of this record before committing: the wording must not read as advice on when a given patient should wear a sensor.

```bash
git add results/expiry docs docs/PROJECT_GUIDE.md
git commit -m "results: expiry by day on held-out patients and the case series of re-recorded patients"
```

- [ ] **Step 6: Band**

```bash
uv run python -m chhaya.eval.calibrate --confirm
```

- [ ] **Step 7: Record the band**

Write `docs/decisions/<date>-band.md`:

1. **What this is**, with the design chosen on development patients (from `band.json`: the factor, both left-out figures for both designs) and the rule that chose it.
2. **Test patients, k = 5**: mean coverage, range and patients within 70 to 90 %, before and after; coverage by day before and after. The same at k = 3.
3. **Whether the recalibrated band is used**: the line the report prints, which applies the rule registered in the note. If it is not used, the sentence is "the recalibration did not transfer to held-out patients (coverage X before, Y after); the band is shown as Gate 2 scored it".
4. **What it means**: the band is calibrated on average and not per patient; give the range.
5. **The claim to quote**: "On N held-out participants the 80 % band covered X % of hidden readings (Y % after a factor of F chosen on development patients), and M of N participants fell within 70 to 90 % (M2 after): calibrated on average, not per patient."

```bash
git add results/calibrate docs
git commit -m "results: band recalibration on held-out patients"
```

---

### Task 8: The staleness alarm, only if the checkpoint is met

**Checkpoint, Sat 10 Oct, 16:00.** Start this task only if the three commits of Task 7 exist. Otherwise skip to Task 9 and use its "not done" sentence.

**Files:**
- Create: `src/chhaya/twin/staleness.py`, `src/chhaya/eval/staleness.py`
- Test: `tests/test_staleness.py`
- Create: `results/staleness/shanghai-dev/`, `results/staleness/shanghai/`, `docs/decisions/<date>-staleness.md`

**Interfaces:**
- Consumes: Task 1 (`MOVED_MGDL`, `check_committed`, `pooled_line`, `profile_sigma`, `provenance`, `table`, `write_outputs`); `chhaya.eval.fingersticks.estimates` (keys used: `z`, the surprises on the sensor's scale in time order; `ft`; `cbg`; `map`), `why_not`, `REGISTERED_K`; `chhaya.twin.assimilate.FilterConfig().obs_sd`.
- Produces: `chhaya.twin.staleness`: `KAPPA = 0.5`, `surprise_scale(profile_sd, fingerstick_sd) -> float`, `cusum(z, kappa=KAPPA) -> np.ndarray`, `first_alarm(t, stat, threshold) -> float | None` (the three functions the dashboard's artifact build will call). `chhaya.eval.staleness`: `score_recording(rec, k_days, pooled) -> dict | None`, `threshold(scores, drifted, rate=0.10) -> float`, `boot_auroc(df, n_boot=2000, seed=SEED) -> dict`, `alarms(rows, name, h) -> dict`, `run(scored, dev_recs, k_list, confirmatory, n_boot=2000) -> dict`; the commands `python -m chhaya.eval.staleness [--confirm]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_staleness.py`:

```python
import dataclasses

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.eval import staleness as st
from chhaya.twin.staleness import cusum, first_alarm, surprise_scale

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(shift: float, from_day: int = 3, seed: int = 11, pid: str | None = None):
    """Eight days; from `from_day` on glucose runs `shift` higher. Fingersticks every 4 hours read the sensor."""
    rec = make_recording(days=8, seed=seed)
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= from_day * 1440
    cgm.loc[late, "glucose_mgdl"] = np.clip(cgm.loc[late, "glucose_mgdl"] + shift, 40, 400)
    sticks = cgm[cgm["t_min"] % 240 == 0].reset_index(drop=True)
    pid = pid or f"synth-{seed}-{shift:g}"
    return dataclasses.replace(rec, cgm=cgm, fingersticks=sticks, rec_id=pid, patient_id=pid)


def test_the_sum_ignores_noise_and_grows_on_a_run_of_surprises_on_one_side():
    rng = np.random.default_rng(0)
    noise = rng.normal(0.0, 1.0, 60)
    assert cusum(noise).max() < 6.0
    assert cusum(noise + 1.5)[-1] > 40.0 and cusum(noise - 1.5)[-1] > 40.0  # up or down
    assert cusum([3.0, -3.0, 3.0, -3.0]).max() == 2.5  # alternating surprises cancel
    assert cusum([]).size == 0


def test_the_alarm_time_is_the_first_fingerstick_above_the_threshold():
    stat = cusum(np.r_[np.zeros(5), np.full(10, 2.0)])
    assert first_alarm(np.arange(15.0), stat, 4.0) == 7.0  # 1.5 a reading: above 4 at the third
    assert first_alarm(np.arange(15.0), stat, 99.0) is None
    assert surprise_scale(20.0, 15.0) == 25.0


def test_a_patient_who_changed_scores_far_above_one_who_did_not():
    changed, same = (
        st.score_recording(_recording(40.0), 3, POOLED),
        st.score_recording(_recording(0.0), 3, POOLED),
    )
    assert changed["drifted"] and not same["drifted"] and changed["drift"] > 30.0
    assert changed["score"] > 3.0 * same["score"] and changed["plain"] > same["plain"] + 20.0
    assert changed["days"].min() >= 0.0 and changed["stat"].size == changed["days"].size
    down = st.score_recording(_recording(-40.0), 3, POOLED)
    assert down["drifted"] and down["drift"] < -20.0 and down["score"] > 3.0 * same["score"]


def test_the_alarm_never_reads_a_hidden_sensor_value_and_the_label_does():
    rec = _recording(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    a, b = (
        st.score_recording(rec, 3, POOLED),
        st.score_recording(dataclasses.replace(rec, cgm=cgm), 3, POOLED),
    )
    assert a["score"] == b["score"] and a["plain"] == b["plain"] and np.array_equal(a["stat"], b["stat"])
    assert a["drift"] != b["drift"]


def test_a_recording_without_fingersticks_is_outside_the_cohort(rec):
    assert st.score_recording(rec, 3, POOLED) is None


def test_the_threshold_lets_at_most_one_in_ten_quiet_recordings_alarm():
    scores = np.arange(1.0, 21.0)  # twenty recordings that did not drift
    drifted = np.zeros(20, dtype=bool)
    h = st.threshold(scores, drifted)
    assert h == 19.0 and np.mean(scores > h) == 0.05
    assert st.threshold(np.r_[scores, 500.0], np.r_[drifted, True]) == 19.0  # a drifted one does not set it
    assert np.mean(np.arange(11.0) > st.threshold(np.arange(11.0), np.zeros(11, dtype=bool))) <= 0.10
    with pytest.raises(ValueError, match="without drift"):
        st.threshold([1.0], [True])


def _rows():
    rows = []
    for i in range(12):
        hot = i < 5
        stat = np.full(8, 9.0 if hot else 1.0) * np.linspace(0.25, 1.0, 8)
        rows.append({"rec_id": f"r{i}", "patient_id": f"p{i}", "drift": 30.0 if hot else 2.0, "drifted": hot,
                     "score": float(stat.max()), "n_sticks": 8, "plain": 5.0 + (0.1 * i if hot else 0.0),
                     "days": np.arange(1.0, 9.0), "stat": stat})  # fmt: skip
    return rows


def test_alarms_report_sensitivity_false_alarms_and_days_to_alarm():
    out = st.alarms(_rows(), "score", 4.0)
    assert out["sensitivity"] == 1.0 and out["false_alarm_rate"] == 0.0 and out["n_alarms"] == 5
    assert out["median_days_to_alarm"] == 3.0  # 9 x 0.25, 0.357, 0.464: above 4 at the third fingerstick
    none = st.alarms(_rows(), "score", 99.0)
    assert none["sensitivity"] == 0.0 and np.isnan(none["median_days_to_alarm"])
    assert "median_days_to_alarm" not in st.alarms(_rows(), "plain", 5.05)


def test_auroc_intervals_resample_patients_and_skip_one_class_resamples():
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("days", "stat")} for r in _rows()])
    out = st.boot_auroc(df, n_boot=300)
    assert out["score"]["auroc"] == 1.0 and out["score"]["lo"] == 1.0
    assert out["diff"]["difference"] == pytest.approx(1.0 - out["plain"]["auroc"])
    assert 0 < out["n_resamples_used"] <= 300
    one_class = st.boot_auroc(df.assign(drifted=False), n_boot=50)
    assert np.isnan(one_class["score"]["auroc"]) and one_class["n_resamples_used"] == 0


def test_thresholds_come_from_development_recordings_and_test_recordings_only_report():
    dev = [_recording(0.0, seed=s) for s in range(20, 28)] + [_recording(40.0, seed=s) for s in (30, 31)]
    test = [_recording(0.0, seed=s) for s in range(40, 44)] + [
        _recording(45.0, seed=s) for s in range(50, 53)
    ]
    result = st.run(test, dev, [3.0], confirmatory=True, n_boot=200)
    block = result["by_k"][0]
    assert block["n_recordings"] == 7 and block["n_drifted"] == 3 and block["n_drifted_down"] == 0
    assert block["development"] == {"n_recordings": 10, "n_without_drift": 8}
    assert block["auroc"]["score"]["auroc"] == 1.0 and block["score"]["sensitivity"] == 1.0
    assert block["auroc_of_fingerstick_count"] == 0.5  # every recording here tests equally often
    assert block["score"]["false_alarm_rate"] <= 0.25 and block["score"]["median_days_to_alarm"] < 2.0
    again = st.run(
        test, dev[:8], [3.0], confirmatory=True, n_boot=50
    )  # no development recording drifted: fine
    assert again["by_k"][0]["score"]["threshold"] == block["score"]["threshold"]
    text = st._report(result)
    assert "set on development recordings" in text and "synth" not in text  # aggregates only
    empty = st.run(
        [make_recording(days=8)], dev, [3.0], confirmatory=True, n_boot=50
    )  # no fingersticks: no cohort
    assert empty["by_k"][0]["n_recordings"] == 0 and "No recording in the cohort" in st._report(empty)
    with pytest.raises(ValueError, match="pooled sensor map"):
        st.run(test, [], [3.0], confirmatory=True)
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_staleness.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'chhaya.twin.staleness'`

- [ ] **Step 3: Implement the detector**

Create `src/chhaya/twin/staleness.py`:

```python
"""Staleness alarm: has the patient moved away from the profile their last sensor wear gave?

A cumulative sum of standardised fingerstick surprises against the frozen profile (Amendment 3, "Staleness
alarm"). A surprise is how far a fingerstick, put on the sensor's scale, lies from the daily shape at that
clock time. One odd reading is not a drift; a run of readings on the same side is.
"""

from __future__ import annotations

import numpy as np

KAPPA = 0.5  # allowance per fingerstick, in standard deviations: half of the one-SD shift the sum looks for


def surprise_scale(profile_sd: float, fingerstick_sd: float) -> float:
    """Standard deviation of a surprise when nothing has changed: the shape's own spread plus the meter's."""
    return float(np.hypot(profile_sd, fingerstick_sd))


def cusum(z, kappa: float = KAPPA) -> np.ndarray:
    """After each fingerstick, the larger of the upward and the downward cumulative sum of the surprises `z`.

    Each sum adds the surprise less the allowance and is never below zero, so readings near the profile pull
    it back down. `z` must be in time order.
    """
    z = np.asarray(z, dtype=float)
    out = np.empty(z.size)
    up = down = 0.0
    for i, v in enumerate(z):
        up = max(0.0, up + v - kappa)
        down = max(0.0, down - v - kappa)
        out[i] = max(up, down)
    return out


def first_alarm(t, stat, threshold: float) -> float | None:
    """The time of the first fingerstick at which the sum is above the threshold; None when it never is."""
    hit = np.flatnonzero(np.asarray(stat, dtype=float) > threshold)
    return float(np.asarray(t, dtype=float)[hit[0]]) if hit.size else None
```

- [ ] **Step 4: Implement the experiment**

Create `src/chhaya/eval/staleness.py`:

```python
"""The staleness alarm on real drift (Amendment 3, "Staleness alarm" and the note on the descriptive outputs).

A recording has drifted when its hidden-window sensor mean differs from its calibration mean by more than
20 mg/dL. The alarm reads fingersticks only. Its threshold is set on development recordings so that at most
10 % of those that did not drift would alarm; test recordings then report AUROC, sensitivity, false alarms and
days to alarm. Beside it, the plainest thing a doctor could do: the fingerstick average against the report's
mean, with a threshold set the same way. Descriptive: no bar.

Usage: python -m chhaya.eval.staleness             (development recordings; the threshold is in-sample)
       python -m chhaya.eval.staleness --confirm   (test recordings, once)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from chhaya.config import RESULTS_DIR, SEED, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.descriptive import (
    MOVED_MGDL,
    check_committed,
    pooled_line,
    profile_sigma,
    provenance,
    table,
    write_outputs,
)
from chhaya.eval.fingersticks import REGISTERED_K, estimates, why_not
from chhaya.eval.gate2 import _git
from chhaya.eval.gate3 import refuse_second_run
from chhaya.twin.assimilate import FilterConfig
from chhaya.twin.staleness import cusum, first_alarm, surprise_scale

FALSE_ALARMS = 0.10
N_BOOT = 2000
SCORES = ("score", "plain")  # the cumulative sum, and the fingerstick average against the report's mean
FOLDER = RESULTS_DIR / "staleness"


def score_recording(rec: Recording, k_days: float, pooled: tuple[float, float]) -> dict | None:
    """Drift label and alarm statistics of one recording in the cohort of section F; None outside it.

    The label reads the hidden sensor. Nothing else does: the surprises come from `estimates` as committed,
    and their scale and the report's mean from the calibration window.
    """
    if why_not(rec, k_days) is not None:
        return None
    e = estimates(rec, k_days, FilterConfig(), pooled)
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    cal = t < split
    scale = surprise_scale(
        profile_sigma(rec.start.hour * 60 + rec.start.minute + t[cal], g[cal]), FilterConfig().obs_sd
    )
    stat = cusum(e["z"] / scale)
    a, b = e["map"]
    drift = float(g[~cal].mean() - g[cal].mean())
    return {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "drift": drift,
        "drifted": bool(abs(drift) > MOVED_MGDL),
        "score": float(stat.max()) if stat.size else 0.0,
        "plain": abs(float(np.mean(a + b * e["cbg"])) - float(g[cal].mean())) if e["cbg"].size else 0.0,
        "n_sticks": int(e["ft"].size),
        "days": (e["ft"] - split) / 1440.0,  # when each fingerstick was taken, in days since the sensor
        "stat": stat,
    }


def threshold(scores, drifted, rate: float = FALSE_ALARMS) -> float:
    """The smallest observed score that at most `rate` of the recordings without drift lie above."""
    quiet = np.asarray(scores, dtype=float)[~np.asarray(drifted, dtype=bool)]
    if quiet.size == 0:
        raise ValueError("no recording without drift: a false-alarm rate cannot be set")
    return float(np.quantile(quiet, 1.0 - rate, method="higher"))


def _auroc(y, s) -> float:
    y = np.asarray(y, dtype=int)
    return float(roc_auc_score(y, s)) if 0 < y.sum() < y.size else float("nan")


def boot_auroc(df: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """AUROC of both scores and of their difference, with 95 % intervals from resampling patients.

    A resample in which every recording drifted, or none did, has no AUROC and is left out; the number of
    resamples used is returned.
    """
    y = df["drifted"].to_numpy(dtype=int)
    s = {name: df[name].to_numpy(dtype=float) for name in SCORES}
    patient = df["patient_id"].to_numpy()
    groups = [np.flatnonzero(patient == u) for u in pd.unique(patient)]
    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {"score": [], "plain": [], "diff": []}
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        if 0 < y[idx].sum() < idx.size:
            a, b = _auroc(y[idx], s["score"][idx]), _auroc(y[idx], s["plain"][idx])
            draws["score"].append(a), draws["plain"].append(b), draws["diff"].append(a - b)
    point = {name: _auroc(y, s[name]) for name in SCORES}
    point["diff"] = point["score"] - point["plain"]
    out: dict = {"n_resamples_used": len(draws["diff"])}
    for name, values in draws.items():
        lo, hi = np.percentile(values, [2.5, 97.5]) if values else (float("nan"), float("nan"))
        out[name] = {
            "auroc" if name != "diff" else "difference": point[name],
            "lo": float(lo),
            "hi": float(hi),
        }
    return out


def alarms(rows: list[dict], name: str, h: float) -> dict:
    """What a threshold does on a set of recordings: who alarms, and for the cumulative sum, when."""
    y = np.array([r["drifted"] for r in rows], dtype=bool)
    fired = np.array([r[name] > h for r in rows], dtype=bool)
    out = {
        "threshold": h,
        "sensitivity": float(fired[y].mean()) if y.any() else float("nan"),
        "false_alarm_rate": float(fired[~y].mean()) if (~y).any() else float("nan"),
        "n_alarms": int(fired.sum()),
    }
    if name == "score":
        when = [first_alarm(r["days"], r["stat"], h) for r, yes in zip(rows, y & fired, strict=True) if yes]
        out["median_days_to_alarm"] = float(np.median(when)) if when else float("nan")
    return out


def block_for(rows: list[dict], thresholds: dict[str, float], k_days: float, n_boot: int = N_BOOT) -> dict:
    """Everything reported at one k for one set of scored recordings."""
    if not rows:
        return {"k_days": k_days, "n_recordings": 0}
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("days", "stat")} for r in rows])
    return {
        "k_days": k_days,
        "n_recordings": int(len(df)),
        "n_patients": int(df["patient_id"].nunique()),
        "n_drifted": int(df["drifted"].sum()),
        "n_drifted_down": int((df["drift"] < -MOVED_MGDL).sum()),
        "median_abs_drift": float(df["drift"].abs().median()),
        "auroc": boot_auroc(df, n_boot),
        # a sum over more fingersticks can only grow: how much of the separation is just more testing?
        "auroc_of_fingerstick_count": _auroc(df["drifted"], df["n_sticks"]),
        **{name: alarms(rows, name, thresholds[name]) for name in SCORES},
    }


def run(
    scored: list[Recording],
    dev_recs: list[Recording],
    k_list: list[float],
    confirmatory: bool,
    n_boot: int = N_BOOT,
) -> dict:
    """Thresholds from development recordings, then `scored` under them. The pooled map is the development one."""
    result = {"confirmatory": confirmatory, "false_alarm_target": FALSE_ALARMS, "by_k": []}
    for k in k_list:
        pooled = pooled_line(dev_recs, k)
        dev = [row for row in (score_recording(r, k, pooled) for r in dev_recs) if row]
        if not dev:
            result["by_k"].append({"k_days": k, "n_recordings": 0})
            continue
        drifted = [r["drifted"] for r in dev]
        thresholds = {name: threshold([r[name] for r in dev], drifted) for name in SCORES}
        rows = [row for row in (score_recording(r, k, pooled) for r in scored) if row]
        block = block_for(rows, thresholds, k, n_boot)
        block["development"] = {"n_recordings": len(dev), "n_without_drift": int(len(dev) - sum(drifted))}
        result["by_k"].append(block)
    return result


def _report(result: dict) -> str:
    lines = ["# Staleness alarm on real drift", ""]
    lines.append(
        "Test recordings; thresholds were set on development recordings. Descriptive: no bar."
        if result["confirmatory"]
        else "Development recordings: the thresholds are set on these same recordings, so this is in-sample."
    )
    lines += [
        "",
        "`score` is the cumulative sum of fingerstick surprises against the frozen profile; `plain` is the "
        "fingerstick average against the report's mean. Drift: the hidden sensor mean more than 20 mg/dL from the "
        "calibration mean.",
    ]
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days", ""]
        if not block["n_recordings"]:
            lines.append("No recording in the cohort.")
            continue
        au = block["auroc"]
        lines += [
            f"{block['n_recordings']} recordings of {block['n_patients']} patients; {block['n_drifted']} drifted "
            f"({block['n_drifted_down']} downwards). Thresholds from {block['development']['n_without_drift']} "
            "development recordings without drift.",
            "",
            table(
                [
                    {
                        "alarm": name,
                        "auroc": au[name]["auroc"],
                        "lo": au[name]["lo"],
                        "hi": au[name]["hi"],
                        **block[name],
                    }
                    for name in SCORES
                ],
                digits=3,
            ),
            "",
            f"AUROC difference, cumulative sum minus plain: {au['diff']['difference']:.3f} "
            f"({au['diff']['lo']:.3f} to {au['diff']['hi']:.3f}); {au['n_resamples_used']} resamples used. "
            f"AUROC of the number of fingersticks alone: {block['auroc_of_fingerstick_count']:.3f}.",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test recordings; this is done once")
    args = ap.parse_args()
    out_dir: Path = FOLDER / ("shanghai" if args.confirm else "shanghai-dev")
    if args.confirm:
        check_committed(_git("status", "--porcelain", "--", "src"))
        refuse_second_run(out_dir)
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    result = run(scored, dev_recs, list(REGISTERED_K), args.confirm)
    write_outputs(out_dir, result, _report(result), provenance(args.confirm, k=list(REGISTERED_K)))
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run, lint, commit**

Run: `uv run pytest tests/test_staleness.py -q`
Expected: 9 passed

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/twin/staleness.py src/chhaya/eval/staleness.py tests/test_staleness.py
git commit -m "feat: staleness alarm on fingerstick surprises, thresholds from development recordings"
```

- [ ] **Step 6: Development run and review**

```bash
uv run python -m chhaya.eval.staleness
```

Must read, at k = 3: 25 recordings of 24 patients, 8 drifted (7 downwards), thresholds from 17 recordings without drift; AUROC `plain` 0.728. The AUROC of `score` was 0.735 before the review fix to the spread, which is the scale of a surprise, so it may differ in the second decimal: record what the committed code gives and append one dated line to the note with both figures. Any other difference is handled as in Task 6, Step 2.

The code blocks above were written before the reviews of Task 6. Three things to follow from the reviewed code instead: build the provenance before computing and pass it to `write_outputs` (as `expiry.run` does), so nothing is written after `summary.json`; `paired_summary` now reports `frac_larger` for a "greater" comparison; `profile_sigma` leaves the scored day out of both halves of the shape. None of these changes a signature the staleness modules use.

Dispatch an independent code review on both staleness modules: "Find any path by which a hidden sensor reading reaches a surprise, a score or a threshold; any path by which a test recording reaches a threshold; and any way the AUROC could be inflated by recording length or by the number of fingersticks beyond what `auroc_of_fingerstick_count` discloses." Dispatch a code review. Fix, test first. Commit `results/staleness/shanghai-dev`.

- [ ] **Step 7: The pass over test recordings, and its record**

`git status --porcelain -- src` prints nothing, then, once:

```bash
uv run python -m chhaya.eval.staleness --confirm
```

Write `docs/decisions/<date>-staleness.md`: what this is; recordings, patients, how many drifted and in which direction; the table for the cumulative sum and the plain fingerstick average (AUROC with interval, threshold, sensitivity, false-alarm rate, days to alarm); the AUROC difference with its interval; the AUROC of the fingerstick count; k = 5. Then what it means, in this order of honesty: if the interval for the AUROC includes 0.5, the sentence is "the alarm was not shown to separate drifted from stable recordings"; if the difference from the plain average includes 0, "it was not shown to do better than comparing the fingerstick average with the report". What a reader should weigh: about thirty recordings; the label and the score look back over the same window; supervised care, where most drift is downwards under treatment; thresholds from 17 recordings. The claim to quote:

"On N held-out recordings, D of which drifted by more than 20 mg/dL, an alarm on fingerstick surprises separated drifted from stable recordings with AUROC A (95 % interval L to U), against B for the plain fingerstick average; at a threshold set for 10 % false alarms on development recordings it caught S % with F % false alarms, a median of T days after the sensor came off."

Run the clinical-wording review on the record: the alarm must be described as a prompt to consider a new sensor wear, never as a finding about the patient's glucose and never as advice on treatment.

```bash
git add results/staleness docs
git commit -m "results: staleness alarm on held-out recordings"
```

---

### Task 9: Close Milestone 3

**Files:**
- Modify: `docs/plans/2026-10-02-chhaya-roadmap.md`, `docs/PROGRESS.md`, `docs/PROJECT_GUIDE.md`, `README.md`, `docs/specs/2026-10-04-chhaya-m3-design.md`

- [ ] **Step 1: Roadmap and progress**

In the roadmap Status table set M3 to done, with one clause per output and its record. In `docs/PROGRESS.md`: the milestone table; "Start here" now points at Milestone 4 (artifact build first; it reads `chhaya.eval.traces`, `chhaya.eval.calibrate.rescale` and, if Task 8 ran, `chhaya.twin.staleness`); the clause table ("How long it stays true", "When to wear a sensor again"); add each record's claim to "The claims to quote".

- [ ] **Step 2: docs/PROJECT_GUIDE.md**

Add the seven modules to the Architecture block, the new commands to Commands, and move "Plan 4's descriptive outputs" from "Not yet verified" to the run list with one sentence per record. If Task 7, Step 5 corrected "lasts about five days", correct it in the Gate 2 paragraph too.

- [ ] **Step 3: The design's limits and the README's command list**

In the design spec, "Known limits we will state": replace "Hidden windows are at most about ten days, plus eight patients re-recorded up to 168 days later" with the measured sentence from the expiry record. In `README.md` add the commands that regenerate the four outputs.

- [ ] **Step 4: Whatever was cut**

Use these sentences, in the README limits and in the roadmap:

- Staleness cut: "The staleness alarm was built [or: was not built] and has not been tested on held-out recordings. The dashboard shows days since the sensor and no alarm."
- Band cut: "The 80 % band is calibrated on average (0.83 on held-out patients) and not per patient (0.60 to 0.99). It was not recalibrated."
- Expiry by day cut: "Error by day since the sensor was not computed. The case series of eight re-recorded patients is the only evidence beyond ten days."

- [ ] **Step 5: Final check and commit**

```bash
uv run pytest -q
uv run ruff check src tests && uv run ruff format --check src tests
git diff --name-status bdafe69 HEAD -- src
git add docs docs/PROJECT_GUIDE.md README.md
git commit -m "docs: Milestone 3 closed; progress map, verified facts and commands after Plan 4"
```

Expected: every test passes (274 with Task 8, 265 without), ruff is clean, and the third command lists only added files (`A`).

---

## Self-review, done when this plan was written

- **Spec coverage.** Section F's deferred outputs: Task 2 (report-level errors against the stale report and the fingerstick average, error by day, and fingersticks per day, which the first run did not record). Expiry by day on both datasets: Tasks 3 and 4. The case series of the eight re-recorded patients: Task 4. Band, one factor or one per day, chosen on development patients, coverage and patients within 70 to 90 % on test patients: Task 5. Staleness with the registered label, sum, 10 % threshold and four reported quantities: Task 8. Two commands per experiment, a leakage test per builder, aggregates only: every task.
- **Leakage tests, one per builder:** `test_no_stated_report_reads_a_hidden_sensor_value`, `test_the_shape_is_built_before_the_split_only`, `test_the_alarm_never_reads_a_hidden_sensor_value_and_the_label_does`, `test_a_trace_comes_back_as_it_was_saved_and_only_from_its_own_split`, `test_test_patients_only_report_a_design_fixed_beforehand`.
- **Names across tasks** were checked by running the code: the plan's blocks are the files that passed.
- **Known gaps, accepted.** `main()` of each module and `expiry.run` load real data and are covered by the development runs of Task 6, not by unit tests. Day 0 uses k - 1 days. The case series cannot separate ageing from treatment change or from a new sensor. The staleness score grows with the number of fingersticks; the report discloses how well that number alone separates.

## Changes made by the reviews of Task 6 (8 Oct 2026)

two independent code reviews read the five modules of Tasks 1 to 5. Neither found a path by which a sensor reading from after the split, or a test patient, reaches an estimate, a shape, a spread or a fitted value. They found the defects below. Each was fixed with a test that failed first; commits `d4df1a0` and `e4e0076`. No test patient had been read.

| Finding | Where | What changed |
|---|---|---|
| The "unchanged" band was not Gate 2's band when an estimate lay outside its own band (the half-widths were clipped at a small positive number) | `calibrate.py` | Half-widths are signed, so a factor of 1 is the band exactly as scored; `evaluate` compares "before" with Gate 2's coverage per recording and stops if they differ. On the development traces the estimate is never outside its band, so no number moved |
| `traces --split test` ran the estimator on test patients with no guard, and only printed whether it reproduced Gate 2 | `traces.py` | It needs `--confirm`, committed code and the registered settings, and stops with an error unless Gate 2 is reproduced. It may be repeated: it is a cache of committed numbers |
| The Gate 2 check passed when there was no trace at a calibration length | `traces.py` | `require_gate2(traces, k_days)` names the k it asks for; every recording Gate 2 scored at that k must have a trace |
| The test pass of the band read an uncommitted, rewritable `band.json` | `calibrate.py` | It reads only a file that git tracks and that has not changed, and records its hash; the file is strict JSON |
| The spread around the daily shape left the scored day out of the average day but not out of the mean | `descriptive.py` | Both halves leave the day out, as the note says. Development figures that moved are in the addendum to the note |
| `share_of_cohort` was relative to the best-attended day and was missing from the report tables | `descriptive.py`, both reports | It is over every patient with a row, and the tables show it |
| A "has it grown" comparison reported the share that had shrunk as `frac_better` | `descriptive.py` | It reports `frac_larger` |
| A results folder could be left with a summary and no provenance; a provenance file held an absolute local path | `descriptive.py`, `fingersticks_report.py` | All three files are serialised before any is written, the summary last; paths are relative to the repository |
| A recording a build could no longer trace kept the trace of an earlier build; nothing recorded what built the traces | `traces.py` | The old file is removed; each build writes its commit and settings, and the passes that read traces copy them into their provenance |
| The case series summary did not say its counts are over wears | `expiry.py` | It says so |

The staleness modules of Task 8 were reviewed the same way after they were built (commit `7adc06c`): the
threshold rule was one rank too high when the number of quiet development recordings is a multiple of ten; the
test for "thresholds come from development recordings" could not fail; the effect of recording length was only
partly disclosed, so the same sum over the first two days and an interval for the AUROC of the fingerstick count
are now reported beside the alarm; and three guards were added (no patient both scored and used for thresholds,
registered filter constants only, a pass closed by any file of an earlier one). The second addendum to the
registration note records it, with the development figures. **The code blocks of Task 8 above show the files as
first committed; the repository is the source of truth.**

Not changed, with the reason: `pooled_line` does not itself refuse a test patient's recording (every caller builds its list with `is_dev_patient`, and the synthetic tests pass arbitrary patient names); `differences` treats a missing committed number as a difference (it fails safe); in `choose`, a fold too small for a factor per day is left out of that design's count only (the bias is toward the single factor).
