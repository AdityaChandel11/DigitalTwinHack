# Gate 2, corrected re-run, 4 Oct 2026

**Verdict: GO, unchanged. The effect against a fair control is unchanged too: about 0.35 mg/dL.**

This is the one re-run that Amendment 2 of `docs/PREREGISTRATION.md` allowed: the held-out test split, with the
input corrections and guards of that amendment and no change to any estimator setting. The registered run stays
in `results/gate2/cgmacros-test-registered/`; this run is in `results/gate2/cgmacros-test/`.

Command: `python -m chhaya.eval.gate2 --dataset cgmacros --split test --k 3 5 7 --jobs 6`
Provenance: commit `985b2ad`, no uncommitted changes under `src/`, seed 20261002, blend 0.5, 200 members.

## Primary, k = 5 days

| | Registered run | Corrected run |
|---|---|---|
| Patients scored | 20 | 19 (018 skipped: its calibration window is 15 % covered) |
| Failed fits | 0 | 0 |
| Chhaya RMSE, median over patients (mg/dL) | 22.5 | 21.9 |
| Average day RMSE | 24.2 | 23.3 |
| P1: median difference, share better, p | -1.48, 90 %, 3.1e-05 | -1.36, 89 %, 3.6e-05 |
| Physiology-free control RMSE | 22.55 (from the break test) | 22.3 |
| Against the control: median difference, share better, p | -0.39, 70 %, 0.03 | -0.35, 63 %, 0.036 |
| P2: time-in-range error, Chhaya / average day (points) | 4.7 / 3.4 | 6.0 / 3.5 |
| P3: 80 % band coverage, mean (range over patients) | 0.83 | 0.83 (0.60 to 0.99) |
| Two-sensor RMSE where both recorded | 38.8 (inflated, see break test) | 35.1 |

## Other calibration lengths

| k | Patients | Chhaya | Average day | Control | Against the control: difference, share better, p |
|---|---|---|---|---|---|
| 3 | 19 | 23.8 | 27.6 | 24.0 | -0.48, 58 %, 0.057 |
| 5 | 19 | 21.9 | 23.3 | 22.3 | -0.35, 63 %, 0.036 |
| 7 | 18 | 22.0 | 22.1 | 21.7 | -0.57, 78 %, 0.001 |

## What it means

- P1, P2 and P3 pass as registered, and the new guard (at most 10 % failed fits) passes. Gate 2 stays GO.
- The corrections moved every estimator by under 1 mg/dL and did not change the ordering.
- Against the physiology-free control the gain is 0.35 to 0.57 mg/dL (about 2 %), significant at k = 5 and
  k = 7 and not at k = 3. This is the honest size of what the meal-driven physiology adds.
- Time in range remains a weakness: the patient's own average day estimates it better (3.5 against 6.0 points).
  P2 passes only because its bar cannot discriminate (Amendment 2, item 8).
- The band is calibrated on average and not per patient: coverage runs from 0.60 to 0.99.

## The claim to quote

On 19 held-out patients, 5 days after the sensor comes off, Chhaya's estimate is 1.4 mg/dL (6 %) closer to the
hidden sensor than the patient's own average day (p = 4e-05) and about 0.35 mg/dL closer than a control that uses
no meals (p = 0.04). This replaces the sentence in `2026-10-03-break-test.md`; everything else in that record
stands.
