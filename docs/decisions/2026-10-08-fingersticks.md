# Fingersticks after the sensor comes off (section F), 8 Oct 2026

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

Two independent reviews (`mle-reviewer`, `python-reviewer`) found no path for a hidden sensor value or a test
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

To be completed after `python -m chhaya.eval.fingersticks --confirm`, run once.
