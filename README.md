# Chhaya

**One glucose-sensor wear, turned into the patient's shadow.**

Chhaya (Hindi for "shadow") is a Type 2 diabetes digital twin for the months when no sensor is worn. It tells
a doctor how long a sensor report stays true, which of its readings not to believe, what keeps it true, and
what we measured about when the report stops being true. Every number below was scored once, on patients the
model had never seen, against a bar written beforehand. The misses are published beside the passes.

Entry to the Happiest Health **Digital Twin Challenge 2026** · Team **SynapseX**, IIT Kanpur (solo) ·
submission folder `SynapseX_IITK`

## The problem, and the one experiment

A continuous glucose sensor in India costs about Rs 4,200 for 14 days, so almost nobody with Type 2 diabetes
wears one all year. A patient wears it once, gets a report, and is treated from that report for months. Nobody
tells the doctor how old the report has become.

Chhaya personalises a physiological glucose-insulin model to the patient from their health record (the prior)
and one sensor wear (the evidence). The whole project is built around one experiment that can be checked:

> Calibrate on k days of sensor data, hide the rest, estimate the hidden days without the sensor, then reveal
> the real trace on top.

## What we measured

On held-out patients, each scored once. This table is a summary; the full wording of each claim, with its
caveats, is in the next section, and that wording is the one to quote.

| | Result | Bar written beforehand | Outcome |
|---|---|---|---|
| **The reveal** | Five days after the sensor comes off, the estimate is 1.4 mg/dL (6 %) closer to the hidden sensor than the patient's own average day (p = 4e-05, 19 participants). The gain comes from the meal log and is small | Closer than the average day, p < 0.05 | **Passed** |
| **Which readings not to believe** | 8 of 64 sensor lows were confirmed by a fingerstick taken within 10 minutes; 732 of 809 sensor highs were | none | Descriptive |
| **Fingersticks keep the report truer** | 2.8 mg/dL closer to the hidden sensor as fingersticks arrive, 9.5 in hindsight, 0.3 with one a day (29 patients) | Closer than the daily shape alone, p < 0.05 | **Passed** |
| **Post-meal excursions without the sensor** | Fusing the record, the sensor week and fingersticks reaches AUPRC 0.60. The patient's own excursion rate reaches 0.59, fingersticks alone 0.64 (47 patients) | Fusion beats every single stream and the personal rate | **Missed** |
| **The record as the twin's prior** | It changed the error by 0.02 mg/dL with one day of sensor data (p = 0.16, 20 participants) | Lower error with the record, p < 0.05 | **Missed** |
| **Fingersticks at report level** | Our rebuilt report missed mean glucose by 8.9 mg/dL. The plain fingerstick average on the sensor's scale missed by 6.4; the stale three-day report by 13.0 | none | Descriptive: a plain baseline beats us |
| **How long a report stays true** | About 1 mg/dL per day, downward, over at most eleven days in supervised care; none detected over a week in free-living participants. These data do not give a number of days | none | Descriptive |
| **The 80 % band** | It held 83.5 % of hidden readings on average and 60 % to 98.5 % for an individual. A recalibration did not transfer and is not used | none | Descriptive |
| **A prompt to consider a new sensor wear** | It told drifted from stable reports with AUROC 0.82 (interval 0.63 to 0.98). Comparing the fingerstick average with the report did as well (0.82) | none | Descriptive: a plain baseline does as well |

Nine bars were written before the runs: five passed and four were missed. Five further results are
descriptive and have no bar. Bars and their dated amendments: [docs/PREREGISTRATION.md](docs/PREREGISTRATION.md).

**Fusion, in one sentence:** we fused the record and the sensor two ways and measured both; once a sensor week
exists the record added nothing detectable. What adds something is the meal log and fingersticks.

### The claims in full

<details>
<summary><b>The reveal</b> (Gate 2, passed)</summary>

On 19 held-out patients, 5 days after the sensor comes off, Chhaya's estimate is 1.4 mg/dL (6 %) closer to the
hidden sensor than the patient's own average day (p = 4e-05) and about 0.35 mg/dL closer than a control that
uses no meals (p = 0.04). The gain comes from the meal log and is small. It was not seen to fade with days
since the sensor; with three days of calibration the median favours the twin over its control on each of the
seven following days (0.4 to 2.0 mg/dL; the interval excludes zero on three of them; 19 held-out
participants), and it reverses only on the last days of the recording, which fewer than half of the
participants reach.

Records: [Gate 2, corrected run](docs/decisions/2026-10-04-gate2-corrected.md),
[expiry](docs/decisions/2026-10-08-expiry.md). Time in range is not a strength of the estimate and is never
shown from it.
</details>

<details>
<summary><b>Which readings not to believe</b> (label check, descriptive)</summary>

Of 64 sensor readings below 70 mg/dL with a fingerstick within 10 minutes, 8 (12.5 %) were confirmed, and 0 of
9 at night; of 809 sensor readings above 180, 732 (90.5 %) were confirmed.

Regenerate: `python -m chhaya.data.audit`. This is why Chhaya has no low-glucose estimate and why a sensor low
on its screens reads "sensor low, unconfirmed".
</details>

<details>
<summary><b>Fingersticks</b> (passed)</summary>

On 29 held-out Shanghai patients, calibrated on three days of sensor data, fingersticks taken afterwards
brought the running estimate 2.8 mg/dL closer to the hidden sensor than the patient's daily shape alone
(median paired RMSE difference; 95 % interval 1.6 to 4.7; 86 % of patients; p = 4e-06) and 9.5 mg/dL closer in
hindsight (interval 4.6 to 12.1); with one fingerstick a day the running gain was 0.3 mg/dL.

To be told with it: the filter was chosen on development patients by a criterion other than the plan's written
rule (dated note in the registration, before the test run), and the estimate is still about 22 % off the next
fingerstick where a real sensor is about 12 %. Record: [fingersticks](docs/decisions/2026-10-08-fingersticks.md).
</details>

<details>
<summary><b>Post-meal excursions without the sensor</b> (Gate 3, missed its bars)</summary>

On 47 held-out Shanghai patients (1,205 meals, 39 % followed by an excursion above 180 mg/dL), a model fusing
the record, the sensor week and fingersticks predicted the excursion at meal time with AUPRC 0.60, which was
not better than any single stream (fingersticks only: 0.64) nor than the patient's own excursion rate from the
sensor week (0.59; difference 0.01, 95 % interval -0.09 to 0.14); with the sensor on, the same model reaches
0.76.

Record: [Gate 3](docs/decisions/2026-10-08-gate3.md). There is no meal alert.
</details>

<details>
<summary><b>The record as the twin's prior</b> (missed its bar)</summary>

On 20 held-out CGMacros patients with one day of sensor data, giving the twin the record's fasting glucose as
its prior changed the error of the estimate by a median of 0.02 mg/dL (p = 0.16), and with three or more days
by nothing measurable: the record, as it enters the twin today, is not worth any sensor days.

Record: [record prior](docs/decisions/2026-10-08-record-prior.md).
</details>

<details>
<summary><b>Fingersticks at report level</b> (descriptive; a plain baseline beats our estimator)</summary>

On 29 held-out Shanghai patients under supervised care who were tested about six times a day, with the hidden
sensor as the yardstick, a three-day sensor report missed the mean sensor glucose of the following days (up to
eleven) by a median of 13.0 mg/dL. Chhaya's report rebuilt in hindsight from those fingersticks missed it by
8.9 (median paired difference 3.4, 95 % interval 1.6 to 8.9, 83 % of patients), but was no closer than the
plain average of the same fingersticks converted to the sensor's scale by a line learned during the wear
(6.4). The share of those converted readings above 180 mg/dL and within 70 to 180 was also closer to the
sensor's time above 180 and time in range (3.1 against 8.8 points; 5.0 against 15.2). As read from the meter
the same average lay 18.3 mg/dL from the sensor's mean; sensor-scale figures are not meter values. Lower
testing frequencies were not measured, and this is not a recommendation to test at any frequency.

Record: [fingersticks at report level](docs/decisions/2026-10-08-fingersticks-report.md).
</details>

<details>
<summary><b>How long a report stays true</b> (expiry, descriptive)</summary>

"Report" means mean glucose only, and a three-day report stands in for a fourteen-day one. On 47 held-out
Shanghai patients under supervised care with treatment being adjusted, a day's mean sensor glucose lay a
median of 13.5 mg/dL from a three-day sensor report's mean inside the wear and 11 to 16 on the four days after
it; inside each patient that distance grew by 1.0 mg/dL per day (95 % interval 0.7 to 2.6) over at most eleven
days, with glucose moving downward. On 19 held-out free-living CGMacros participants (7 with type 2 diabetes;
medication not recorded) no growth was detected over seven days (0.1 mg/dL per day, interval -0.8 to 0.8). In
a case series of eight Shanghai patients recorded again (nine later wears, five beginning within three days of
the first sensor coming off and four 33 to 154 days after it), four wears in three patients had a mean more
than 20 mg/dL lower, all four with a change of treatment in the files; of the five that had not moved, four
had no change and one had, and the old daily profile fitted them no worse than a fresh one. No test; not a
rule for when a patient should wear a sensor.

Record: [expiry](docs/decisions/2026-10-08-expiry.md).
</details>

<details>
<summary><b>The 80 % band</b> (descriptive; the recalibration did not transfer)</summary>

On 19 held-out participants the 80 % band held 83.5 % of hidden readings on average and between 60 % and
98.5 % for an individual, with 10 of 19 participants within 70 to 90 %. A recalibration factor chosen on
development patients (0.78) moved the average to 75.7 %, further from 80 % than before, so it is not used: the
band is calibrated on average, not per patient.

Record: [band](docs/decisions/2026-10-08-band.md).
</details>

<details>
<summary><b>A prompt to consider a new sensor wear</b> (descriptive; a plain baseline does as well)</summary>

On 32 held-out Shanghai recordings (29 patients under supervised care, tested about six times a day, for up to
eleven days after a three-day sensor report), 11 of which drifted by more than 20 mg/dL in mean sensor glucose
(9 downward, 2 upward), a running sum of fingerstick surprises, used only as a prompt to consider a new sensor
wear, separated drifted from stable recordings with AUROC 0.82 (95 % interval 0.63 to 0.98), against 0.82
(0.61 to 0.97) for the plain fingerstick average compared with the report's mean (difference 0.00, interval
-0.16 to 0.18): it was not shown to do better than that comparison. At a threshold set on development
recordings so that at most 10 % of stable ones would raise it, the prompt was raised in 7 of 11 drifted
recordings (64 %) and 2 of 21 stable ones (10 %); in those 7, a median of 2.6 days after the split. With a
five-day report (24 recordings, 6 drifted) it was not shown to separate them (0.67, interval 0.35 to 0.92).
The label and the score look back over the same days. It is not a finding about a patient's glucose, not
advice on treatment and not a rule for when to wear a sensor, and it was not tested in outpatient care, at
lower testing frequencies or over longer periods.

Record: [staleness](docs/decisions/2026-10-08-staleness.md).
</details>

## What Chhaya is not

- It does not replace a sensor. Against the next fingerstick the estimate is about 22 % off where a real
  sensor is about 12 %.
- It has no low-glucose estimate and raises nothing on lows: in the open data most sensor lows were not
  confirmed by a fingerstick.
- It recommends no dose. The dashboard only simulates a meal the doctor enters.
- It shows no time in range from an estimate, and no HbA1c from fingersticks.
- It does not claim that fusing the record with the sensor improves anything we measured.
- It gives no rule for when a patient should wear a sensor again.

## How it works

```mermaid
flowchart LR
  R[Health record] -->|sets the prior| T(Twin: glucose-insulin model,<br/>seven personal parameters)
  W[One sensor wear] -->|is the evidence| T
  T --> S[Shadow: estimated glucose<br/>with an 80 % band]
  M[Meal log] --> S
  A[The patient's own average day] --> S
  F[Fingersticks] --> S
  F --> P[Prompt to consider<br/>a new sensor wear]
  S --> D[Dashboard: clinic list,<br/>patient, evidence]
  P --> D
```

- **The twin** is the published E-DES glucose-insulin model with a circadian term, in JAX, with seven personal
  parameters. The record sets their prior; the sensor wear is the likelihood. Calibration is a MAP fit with a
  Laplace ensemble for the band.
- **The estimate is a blend**: half physiology, which knows what was eaten today, and half the patient's own
  average day, which knows the habits a meal log misses.
- **Fingersticks** nudge the estimate through a filter whose effect fades over about two hours, and feed a
  running comparison with the sensor wear's daily pattern.
- **Split by patient, never by row.** One half of the patients tunes every setting; the other half is scored
  once, by a command that needs `--confirm`. Every evaluation asserts that scored readings lie after the
  calibration split, and every feature builder has a test that changes the hidden sensor and checks that
  nothing else moves.

Why this concept and what the other entries do: [docs/WAR_ROOM.md](docs/WAR_ROOM.md). Where the project
stands today: [docs/PROGRESS.md](docs/PROGRESS.md).

## Run it

```bash
uv sync
uv run pytest -q                                           # about 30 seconds
uv run python -m chhaya.data.download shanghai cgmacros    # 3.7 MB + 627 MB, checksum-verified
uv run python -m chhaya.data.audit                         # dataset counts and the label check
uv run python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7
```

Each later result has one command. It reads held-out patients only with `--confirm`, once, on committed code;
the results are in `results/`.

```bash
uv run python -m chhaya.eval.gate3 --confirm                 # post-meal excursions: missed its bars
uv run python -m chhaya.eval.fusion                          # the record as the twin's prior: missed
uv run python -m chhaya.eval.fingersticks --confirm          # fingersticks after the sensor: passed
uv run python -m chhaya.eval.fingersticks_report --confirm   # the same, at the level of a sensor report
uv run python -m chhaya.eval.expiry shanghai --confirm       # also: cgmacros, cases
uv run python -m chhaya.eval.calibrate --confirm             # the band's recalibration: did not transfer
uv run python -m chhaya.eval.staleness --confirm             # the prompt to consider a new sensor wear
```

### The dashboard

Three screens (clinic list, patient, evidence), offline, from pre-computed files. It is being built now:
[design](docs/superpowers/specs/2026-10-08-chhaya-m4-product-design.md),
[plan](docs/superpowers/plans/2026-10-11-chhaya-plan-5-product.md). The design mocks run today, with a
synthetic patient:

```bash
python -m http.server 8765 --directory docs/superpowers/specs/m4-mocks
```

Then open `http://localhost:8765`.

## Limits

No Indian data. Shanghai is supervised care with treatment being adjusted. Hidden windows are at most eleven
days, plus eight patients recorded again up to 168 days later (a case series, not a rule). The effect of the
physiology is about 2 %. The prompt was not shown to do better than comparing the fingerstick average with the
report, and was not tested in outpatient care. The band is calibrated on average, not per patient. The model
has no exogenous insulin, no drug kinetics and no counter-regulation. The Clarke error grid used in the
fingerstick experiment is the widely used reference implementation, not checked against the 1987 figure.

## Data and licences

Code: MIT. Datasets are downloaded by the user and never redistributed; only derived aggregates are in this
repository.

- **ShanghaiT2DM**: 100 patients with Type 2 diabetes, 109 recordings, supervised care. CC BY 4.0 (Zhao et
  al., Scientific Data 2023).
- **CGMacros**: 45 free-living participants. CC BY-NC-SA 4.0, non-commercial use only (PhysioNet,
  doi 10.13026/3z8q-x658).

## Repository map

- `src/chhaya/` the package: data loaders, the twin (model, calibration), evaluation
- `tests/` the test suite; synthetic patients with known true parameters
- `results/` every reported number, as written by the commands above
- `docs/PREREGISTRATION.md` the bars, fixed before each run, with dated amendments
- `docs/decisions/` one record per result, each with its "claim to quote"
- `docs/superpowers/` the roadmap, designs and task-level plans
- `CLAUDE.md` the project's rules and conventions

Built with Claude (Anthropic) as a programming and review assistant, working under the rules in `CLAUDE.md`.
