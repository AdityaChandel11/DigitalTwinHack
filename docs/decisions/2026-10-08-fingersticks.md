# Fingersticks after the sensor comes off (section F), 8 Oct 2026

**Verdict: F1 PASS, F2 PASS** on 29 held-out patients (Part 2). The filter design was frozen first (Part 1).

## Part 1: the design, frozen before the test run

**Frozen design: a deviation that fades with a time constant of 120 minutes, no slow level.** It is the code
default (`FilterConfig`) and `--confirm` refuses any other. Bars, cohort and readings of the text are in
`docs/PREREGISTRATION.md`, Amendment 3, section F, and its note of 8 Oct.

### The six declared designs on development patients

Commands (each writes its own folder under `results/fingersticks/`):

```bash
python -m chhaya.eval.fingersticks --tau 60
python -m chhaya.eval.fingersticks --tau 120
python -m chhaya.eval.fingersticks --tau 240
python -m chhaya.eval.fingersticks --tau 60 --slow
python -m chhaya.eval.fingersticks --tau 120 --slow
python -m chhaya.eval.fingersticks --tau 240 --slow
```

Provenance: commit `270e6fb`, no uncommitted changes under `src/`. 24 development patients (25 recordings) at
k = 3; control RMSE 36.01 mg/dL. Live estimate, all fingersticks:

| Design | Median live RMSE | Median paired difference from control (95 % interval) | Patients better | p |
|---|---|---|---|---|
| tau 60 | 35.55 | -0.94 (-2.44 to -0.45) | 79 % | 0.00001 |
| **tau 120** | 35.25 | **-1.19** (-2.66 to -0.37) | 75 % | 0.0008 |
| tau 240 | 34.89 | -0.44 (-2.39 to 0.24) | 62 % | 0.03 |
| tau 60, slow level | **34.15** | -0.94 (-2.05 to 0.85) | 58 % | 0.13 |
| tau 120, slow level | 34.32 | -0.85 (-2.03 to 1.44) | 58 % | 0.17 |
| tau 240, slow level | 34.49 | +0.39 (-2.05 to 2.41) | 46 % | 0.43 |

### The choice, and the departure from the plan

- **The plan's rule** (7 Oct): lowest cohort-median live RMSE at k = 3, a tie within 0.1 going to the simpler
  design. It selects tau 60 with the slow level.
- **What was used:** the median paired difference from the control, with the same tie rule. It selects tau 120
  without the slow level; the runner-up is 0.25 mg/dL behind.
- **Why:** all designs share one control, so the cohort median of the RMSE separates designs only by which
  patient sits in the middle. The plan's pick helps 58 % of development patients and its interval crosses
  zero. The slow level also makes things worse than the control at k = 5 in every design that has it.
- **Who and when:** the team lead, on 8 Oct, after seeing this table and before any test patient was scored.
  It is a development-data choice and a departure from the written rule; both facts are in the dated note.
- The chosen design is also the code default from the exploration of 4 Oct.

### What the reviews changed before the freeze

Two independent reviews found no path for a hidden sensor value or a test
patient's data into an estimate, the map or a constant, and confirmed the live filter is exact. They did find:

- **A same-minute reading.** The live estimate at a minute was reading the fingerstick stamped at that minute,
  and in Shanghai every hidden fingerstick shares its row with a sensor reading. That accounted for a third to
  a half of the effect at tau 60. F1 is now judged on fingersticks stamped strictly before; the at-or-before
  variant is reported with no bar. The first table of six designs, made before this fix, favoured tau 60
  (-1.47 against -1.44); the table above replaces it.
- **A leak of one value into the sensor map.** A fingerstick just before the split was paired with the hidden
  reading just after it. Calibration pairs now use the trace cut at the split.
- **The hindsight estimate was not the smoother between fingersticks** (a blend that halved the deviation
  mid-gap). It is now exact, tested against brute-force conditioning.
- **Thinning dropped recordings silently** and "every second day" always skipped the first hidden day. Both
  fixed.
- **One-shot safety:** the primary result is written before anything else; `--confirm` asserts the frozen
  design, the registered k and committed code; verdict at k = 3 only; all five Clarke zones kept.

### Development figures for the frozen design (not confirmatory)

| | k = 3 (24 patients) | k = 5 (20 patients) |
|---|---|---|
| Live against control: median paired difference (interval), p | -1.19 (-2.66 to -0.37), 0.0008 | -0.62 (-1.16 to 0.12), 0.012 |
| Same-minute variant, no bar | -1.44, 0.00008 | -0.99, 0.001 |
| In hindsight against control | -3.69 (-7.30 to -2.05), 0.000004 | -2.70 (-4.23 to -1.65), 0.00007 |
| Two a day / one a day / every second day, live | -0.26 / -0.04 / +0.02 | -0.23 / -0.01 / -0.00 |

Against the hidden fingerstick, k = 3, medians over patients: real sensor MARD 11.8 %, 74.6 % within 15/15,
zone A 82.2 %; control MARD 19.3 %, 47.1 %, zone A 56.9 %; live MARD 19.4 %, 45.3 %, zone A 58.1 %. On
development patients the live estimate is no closer to the next fingerstick than the control is.

Sensor map at k = 3: own slope in 18 recordings, pooled slope in 5, pooled line in 2. Outside the cohort: 25
recordings with fewer than one fingerstick a day, 6 with fewer than two days after the split.

## Part 2: the confirmatory run

**Verdict: F1 PASS, F2 PASS.** On held-out patients, fingersticks taken after the sensor comes off bring the
estimate closer to the hidden sensor than the patient's daily shape alone: by 2.8 mg/dL as they arrive, and by
9.5 mg/dL in hindsight.

Command: `python -m chhaya.eval.fingersticks --confirm`, run once.
Provenance: commit `b79bc80`, no uncommitted changes under `src/`, frozen filter (tau 120 minutes, no slow
level), seed 20261002. Results: `results/fingersticks/shanghai/`.

### Primary, k = 3 days: 29 test patients, 32 recordings, all fingersticks

RMSE against the hidden sensor, median over patients. The control is the patient's daily shape with no
fingersticks: 36.7 mg/dL.

| | Median RMSE | Median paired difference from control (95 % interval) | Patients better | p | Bar |
|---|---|---|---|---|---|
| **Live** (fingersticks stamped before the minute) | 32.1 | **-2.79** (-4.69 to -1.60) | 86 % | 0.000004 | **F1: PASS** |
| **In hindsight** (all hidden fingersticks) | 27.0 | **-9.50** (-12.15 to -4.56) | 93 % | 0.0000003 | **F2: PASS** |
| Live, may read the same minute (no bar) | 30.7 | -3.95 (-5.97 to -2.27) | 86 % | 0.000001 | |

Against the control's 36.7 mg/dL, the live gain is about 8 % and the hindsight gain about 26 %.

### How many fingersticks it takes (k = 3, live; same 29 patients under every rule)

| Fingersticks kept | Median paired difference (interval) | Patients better | p | In hindsight |
|---|---|---|---|---|
| All | -2.79 (-4.69 to -1.60) | 86 % | 0.000004 | -9.50 |
| Two a day (first and last) | -0.79 (-2.02 to -0.25) | 76 % | 0.0001 | -2.27 |
| One a day | -0.32 (-0.92 to -0.03) | 69 % | 0.002 | -1.12 |
| One every second day | -0.35 (-0.81 to 0.03) | 66 % | 0.008 | -0.55 |

The gain depends on how often the patient tests. With one fingerstick a day it is a third of a mg/dL.

### k = 5 days (reported, no bar): 21 patients, 24 recordings, control 31.0 mg/dL

Live -1.08 (-5.08 to -0.40), 81 % better, p = 0.0002. In hindsight -5.70 (-11.04 to -2.42), 95 % better.
Two a day: live -0.51. One a day: live -0.19 (interval crosses zero).

### Accuracy against the hidden fingerstick, before it is used (k = 3, medians over patients)

| | MARD | Within 15 mg/dL or 15 % | Clarke zone A | Zone B | Zones C, D, E |
|---|---|---|---|---|---|
| A real sensor at that moment | 11.5 % | 71.9 % | 84.9 % | 13.3 % | 0 |
| Control (daily shape) | 22.5 % | 44.4 % | 57.1 % | 40.4 % | 0 |
| Live estimate | 21.8 % | 46.7 % | 55.6 % | 41.3 % | 0 |

Zone shares are medians over patients, so a row need not sum to 100. The zone rules match the widely used
reference implementation; the grid has not been checked against the figure in the 1987 paper.

### Cohort and map

- Sensor-scale line at k = 3: the patient's own in 26 recordings, the pooled slope in 4, the pooled line
  (sensor = 7.9 + 0.863 x fingerstick, from development patients) in 2.
- Outside the cohort at k = 3: 16 recordings with fewer than one fingerstick a day, 3 with fewer than two
  days after the split, 2 with fewer than three paired fingersticks after the split.

### What it means

- **Fingersticks keep the sensor report truer, and the claim in the headline stands.** F1 is the third of
  Amendment 3's primary bars and the only one that passed (M1 and M2 missed).
- **The strong result is the retrospective one.** At a clinic visit, with every fingerstick since the sensor
  in hand, the reconstructed trace is 9.5 mg/dL (about a quarter) closer to what a sensor would have shown.
  As a running estimate the gain is 2.8 mg/dL.
- **It needs frequent testing.** These patients were tested several times a day under supervised care (the
  cohort requires at least one a day; the exact density was not recorded by this run). At one fingerstick a
  day the live gain is 0.3 mg/dL: real, and too small to matter to a doctor.
- **The estimate is not a sensor.** Against the next fingerstick it is about 22 % off where a real sensor is
  about 12 %, and the live estimate is no better than the daily shape there (21.8 % against 22.5 %). A
  fingerstick improves the estimate for the next couple of hours along the sensor's trace; it does not make
  the next fingerstick predictable.
- **The effect is larger on test patients than on development patients** (-2.79 against -1.19 at k = 3).
  Nothing in the run explains it; the test cohort is larger (29 against 24) and fewer of its recordings were
  excluded for sparse testing (16 against 25), so its patients may simply test more often. The run did not
  record fingersticks per day, so this is a guess, to be checked in the descriptive pass of Plan 4.
  **Checked on 8 Oct** in `2026-10-08-fingersticks-report.md`: the test cohort tests about six times a day,
  the development cohort about four, and the gain rises with testing frequency inside both.

### What a reader should weigh

- The design was chosen on development patients by the median paired difference, not by the plan's written
  rule (Part 1 and the dated note). The choice was frozen before the test run and the test patients were
  scored once.
- "Already taken" is read strictly. Under the looser reading the live figure would be -3.95.
- Supervised hospital care, one country, hidden windows of at most about ten days, 29 patients.
- Report-level outputs (error in mean glucose, time above 180, time in range, error by day) are not in this
  run; they are a declared second pass with this estimator frozen.

### Consequences for the product

- **Patient screen:** the retrospective reconstruction from fingersticks is the feature with evidence behind
  it; the running estimate is shown with its band and the thinning table beside it.
- **"What keeps it true" on screen:** meal log (Gate 2, about 6 % against the average day) and fingersticks
  (this result), each with how much and at what testing frequency.
- **No per-fingerstick accuracy claim** beyond the table above.

## The claim to quote

On 29 held-out Shanghai patients, calibrated on three days of sensor data, fingersticks taken afterwards
brought the running estimate 2.8 mg/dL closer to the hidden sensor than the patient's daily shape alone
(median paired RMSE difference; 95 % interval 1.6 to 4.7; 86 % of patients; p = 4e-06) and 9.5 mg/dL closer in
hindsight (interval 4.6 to 12.1); with one fingerstick a day the running gain was 0.3 mg/dL.
