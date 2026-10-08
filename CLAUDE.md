# Chhaya — project guide for Claude

Chhaya (Hindi for "shadow") is our entry to the Happiest Health **Digital Twin Challenge 2026**: a Type 2 diabetes
digital twin that turns one sensor wear into the patient's shadow. It tells the doctor **how long that sensor report
stays true, which of its readings not to believe, what keeps it true (meal log, fingersticks), and when to wear a
sensor again**, with an honest band, and every claim is scored once on held-out patients against a bar written
beforehand, misses published. It does not claim to replace a sensor, to alarm on lows, or to predict post-meal
excursions better than the sensor week already does (headline revised 4 Oct and again 8 Oct after Gate 3; see
`docs/decisions/2026-10-04-plan-revision.md` and `docs/decisions/2026-10-08-gate3.md`).

- **Team:** SynapseX, IIT Kanpur. Solo participant; submission folder `SynapseX_IITK`.
- **Where we are and what is next: [docs/PROGRESS.md](docs/PROGRESS.md). Read it first.**
- **Submission closes 20 Oct 2026, 19:00 IST.** We submit by 12:00 that day. Feature freeze is 15 Oct. Science
  stops at midnight on 10 Oct.
- **Why this concept, and what everyone else is building:** [docs/WAR_ROOM.md](docs/WAR_ROOM.md) (read Phase 6).
- **What to build, in order, with gates:** [docs/superpowers/plans/2026-10-02-chhaya-roadmap.md](docs/superpowers/plans/2026-10-02-chhaya-roadmap.md).
- **Design from Milestone 3 on:** [docs/superpowers/specs/2026-10-04-chhaya-m3-design.md](docs/superpowers/specs/2026-10-04-chhaya-m3-design.md).
- **Task-level plans:** [Plan 2, excursions](docs/superpowers/plans/2026-10-07-chhaya-plan-2-excursions.md) and
  [Plan 3, record prior and fingersticks](docs/superpowers/plans/2026-10-07-chhaya-plan-3-prior-and-fingersticks.md)
  are done. **Being executed:** [Plan 4, second pass of F, expiry, band, staleness](docs/superpowers/plans/2026-10-08-chhaya-plan-4-expiry-band-staleness.md).
- **The brief itself:** [docs/brief/Digital_Twin_Challenge_2026_Content.txt](docs/brief/Digital_Twin_Challenge_2026_Content.txt).

## Working agreement (solo project: Claude is the teammate)

- Act as a teammate, not an order-taker: propose, push back with reasons, and make the call on routine
  trade-offs. Ask only when a choice is irreversible or genuinely the user's.
- **Before each task, say which model and effort to use**, using the table in README.md (Developer guide).
  Default to the cheapest model that is safe; escalate after one failed attempt. Say when to switch.
- Keep reports short: what changed, what was verified, what is next.
- **Keep the plan current.** When a step finishes or a decision is made, update the Status section of the
  roadmap and, for a gate, write `docs/decisions/<date>-<topic>.md`. Docs and code change in the same commit.
- The user's time is the scarcest resource. Never leave a long command running without saying so.

## The one claim

> Calibrate on k days of sensor data, hide the rest, estimate the hidden days without the sensor, then
> reveal the real trace on top.

Everything in the repo exists to make that experiment true, measurable and demoable. Sensor-on spike
forecasting is a **baseline table**, never the headline — at least four competing entries are already
"GlucoTwin" classifiers. Do not name anything Gluco* or Glyco*.

## Rules that are not negotiable

These are what separate us from entries that validate a model on their own simulator. Breaking one
silently is worse than a bad number.

1. **No leakage.** In the hidden window the twin may use meals, band data and (later) fingersticks — never
   CGM. Every evaluation asserts that scored timestamps lie after the calibration split. Every feature builder
   has a test that changes the hidden sensor readings and asserts the non-sensor features do not move.
   Test patients are scored once per experiment, by a command that needs `--confirm`.
2. **Split by patient, never by row.** `chhaya.config.is_dev_patient()` is the only split. Population
   settings (priors, slow-down coefficients, band recalibration, any learned corrector) are tuned on dev
   patients and reported on test patients.
3. **Pass bars are written before the run.** They live in `docs/PREREGISTRATION.md`. Changing a bar after
   seeing a result means adding a dated amendment that says so, not editing the number.
4. **Report what happened.** A failed fit is a row with an `error`, not a dropped patient. A result that
   misses its bar is published with the bar. Where a plain baseline beats the twin, say so.
5. **Never draw an estimate without its uncertainty band**, and label it "estimated". No dose
   recommendations anywhere — only simulations of options the doctor entered.
6. **Datasets are never committed or redistributed.** CGMacros is CC BY-NC-SA. They are fetched by
   `python -m chhaya.data.download` into `data/` (git-ignored). Only derived aggregates go in `results/`.
7. **Synthetic is labelled synthetic** — in code, in files, on screen. The demo patient "Mrs. R." and any
   genetic-marker field are synthetic; neither open dataset has genotypes.
8. **A number goes on a slide only if a command in this repo regenerates it.** Facts tagged `[memory]` in
   the War Room doc must be re-checked before they are quoted.

## Commands

```bash
uv sync                                         # create the environment from pyproject.toml
uv run pytest -q                                # full suite, ~30 s; twin fits are marked `slow`
uv run pytest -q -m "not slow"                  # seconds
uv run ruff check src tests && uv run ruff format src tests
uv run python -m chhaya.data.download shanghai cgmacros   # 3.7 MB + 627 MB, checksum-verified
uv run python -m chhaya.data.audit              # Gate 1 -> results/audit/
uv run python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7   # Gate 2 -> results/gate2/
uv run python -m chhaya.eval.gate2 --dataset cgmacros --limit 5   # smoke run
```

## Architecture

```
src/chhaya/
  config.py        paths (CHHAYA_DATA_DIR), SEED, is_dev_patient()
  units.py         mg/dL <-> mmol/L, GMI, HbA1c and insulin unit conversions
  data/
    schema.py      Recording — the only type that crosses module boundaries
    download.py    fetch + checksum + unpack
    cgmacros.py    loader -> Recording   (45 people; Libre + Dexcom, Fitbit, meal macros)
    shanghai.py    loader -> Recording   (100 T2D; Libre, fingersticks, diet text, drugs, labs)
    files.py       file search that ignores macOS archive debris
    audit.py       dataset counts, Gate 1
  twin/
    model.py       the ODE: E-DES core + circadian + exercise, in JAX
    inputs.py      Recording -> Inputs arrays
    priors.py      population prior; record-informed prior (static data enters here)
    fit.py         MAP calibration + Laplace ensemble
    clock.py       per-patient offset between the meal log and the sensor clock
  eval/
    metrics.py     RMSE, MARD, TIR/TAR/TBR error, GMI error, band coverage
    baselines.py   mean; the patient's own average day (the bar to beat, and half of the blend)
    reveal.py      the hide-and-reveal experiment; estimate = blend of physiology and average day
    gate2.py       cohort run (--split dev|test, --jobs), pre-registered verdict, report
```

Data flows one way: **loader → `Recording` → `build_inputs` → `fit_twin` → `simulate_ensemble` →
metrics**. Loaders know file formats; nothing downstream does. The dashboard (later) reads only
pre-computed artifacts — nothing is fitted live in a demo.

**The estimate is a blend.** Half physiology (knows what was eaten today), half the patient's own average
day (knows the habits the meal log misses). Their errors are only partly correlated, so the blend beats
both. `RevealConfig` holds the switches; its defaults are the configuration chosen on dev patients.

**Fusion is Bayesian, not concatenation.** The health record sets the prior over the twin's seven
personal parameters; sensor data is the likelihood. That sentence is the answer to the brief's "fusion of
two data streams" and to "why is this a twin and not a classifier". **Measured effect: nil.** Today the record
sets one parameter's prior (basal glucose, from fasting glucose), and on held-out patients it changed the
estimate by 0.02 mg/dL at k = 1 (P1 missed, `docs/decisions/2026-10-08-record-prior.md`). Gate 3's fusion bar
(M1) missed too. Describe fusion as built and measured, never as a gain.

## Conventions

- **Units.** Storage, metrics and anything a human reads: **mg/dL**. Inside the ODE: **mmol/L**, mU/L,
  minutes, mg of gut glucose. Convert only through `chhaya.units`. `Recording.validate()` rejects glucose
  outside 20–600 mg/dL, which catches an unconverted mmol/L column.
- **Time.** `t_min` = integer minutes since `Recording.start`. The ODE steps at 1 minute (RK4). Clock
  time of day is `start.hour*60 + start.minute + t_min`.
- **Parameters.** The twin's personal vector `z` has 7 unconstrained entries, order fixed by
  `model.THETA_NAMES`: absorption rate, insulin-mediated fraction of basal disposal, beta-cell
  responsiveness, basal glucose, dawn amplitude, exercise sensitivity, meal-logging bias. `unpack()`
  maps `z` to physical values. Fasting insulin `ib` comes from the record and is not fitted.
- **JAX.** `jax_enable_x64` is switched on in `model.py`; import that module before creating arrays.
  Keep `simulate` pure. A new array *shape* triggers a recompile (≈0.3 s) — fine per patient, not per step.
- **Determinism.** Seeds come from `config.SEED`. A function that samples takes a `seed` argument.
- **Tests.** Test-first. Synthetic recordings come from `tests/conftest.py::make_recording`, which runs
  the twin with known parameters — so recovery tests have ground truth. Real-data tests are marked
  `data` and skipped by default. Assert on behaviour a clinician or judge would care about, with numbers.
- **Style.** `ruff format` (110 cols) and `ruff check` must be clean. Comments explain why, not what.

## What is verified, and what is not yet

Verified on 2 Oct 2026 against the sources:

- **CGMacros column names** (from its data dictionary): `Timestamp, Libre GL, Dexcom GL, HR,
  Calories (Activity), Mets, Meal Type, Calories, Carbs, Protein, Fat, Fiber, Amount Consumed,
  Image Path`. `Mets` is stored ×10. Body weight is in pounds, height in inches. There is **no sleep
  column and no medication data**; sleep must be derived from HR/METs and labelled as derived.
- **ShanghaiT2DM**: 100 patients, 109 recordings of 3–14 days, Libre every 15 min, mean TIR 77.7 %.
  Diet is **free text of weighed foods** (Chinese and English) — it needs a food-to-macros table before
  the twin can use it. HbA1c is in mmol/mol. It has **no wearable activity data**.
- **Model equations and constants**: the published E-DES reference implementation.
- **The prototype**: the core in Plan 1 was run before the plan was written — steady state exact,
  parameter recovery on synthetic data, 67 tests green, 200-member ensemble over 10 days in about 3 s.

Verified on real files, 3 Oct 2026 (see `docs/decisions/2026-10-03-gate1.md`): Shanghai headers match the
loader; its diet text is English, one food per line; 65 of 109 Shanghai recordings are on insulin. CGMacros
files vary (11 of 45 lack METs; the loader derives them from activity calories); its healthy group spends
22.8 % of time below 70 mg/dL, so its lows are mostly sensor artefacts. Gate 1 is GO.

**Gate 2 is GO and closed** (corrected run, 4 Oct 2026, `docs/decisions/2026-10-04-gate2-corrected.md`; what it
means is in `docs/decisions/2026-10-03-break-test.md`): on 19 held-out CGMacros patients, 5 days after the sensor
comes off, Chhaya is 1.4 mg/dL (6 %) closer to the hidden sensor than the patient's average day (21.9 vs 23.3,
p = 4e-05) but only about 0.35 mg/dL closer than a physiology-free control (p = 0.04). The gain comes from the
meal log and activity adds nothing measurable. Time-in-range is not a strength. Quote only the sentence in the
"claim to quote" section of the corrected-run record, **except its clause "lasts about five days", which the
expiry record of 8 Oct corrects**: the gain is small and was not seen to fade with days since the sensor (with
three days of calibration the median favours the twin on each of the seven following days; the interval excludes
zero on three of them) and it reverses only on the last days of the recording
(`docs/decisions/2026-10-08-expiry.md`).

Found on 4 Oct 2026 by scratch scripts (`scripts/research_2026-10-04/`), **not quotable until Plan 2, Task 1
regenerates them** (`docs/decisions/2026-10-04-plan-revision.md`):

- **Sensor lows in Shanghai are mostly not capillary lows**: of 64 sensor readings below 70 mg/dL with a
  fingerstick within 10 minutes, 8 (12 %) were confirmed; at night 0 of 9. Sensor highs are real (above 180: 90 %
  confirmed). So there is **no low-glucose model and no overnight-low fallback**; a sensor low on screen reads
  "sensor low, unconfirmed".
- Shanghai is supervised care (pumps in 35 of 109 recordings, IV insulin in 6, seven fixed fingerstick times a
  day). The paper never says inpatient or outpatient. The sensor reads 8 to 35 mg/dL below the fingerstick,
  more at high glucose.
- The sheet's "Hypoglycemia (yes/no)" column is not defined as prior history: never a predictor.
- Exploratory, development patients only: fingersticks add little reading by reading; the patient's own sensor
  profile beats fingersticks alone; against the fingerstick the shadow is about 20 % off where a real sensor is
  about 13 %.
- ShanghaiT2DM is CC BY 4.0 on its Figshare page (read 4 Oct).

Not yet verified:

- How many snacks go unlogged in CGMacros (snacks that are logged carry the label `snack`).
- Whether the E-DES Michaelis constant (0.63 mmol/L) suits T2D; it is a population setting to revisit on
  dev patients.

Run on 8 Oct 2026 on held-out patients, one decision record each in `docs/decisions/2026-10-08-*.md`:
**Gate 3 missed** (fusing record, sensor week and fingersticks predicts a post-meal excursion no better than
any single stream or the patient's own rate); **the record prior missed** (P1; 0.02 mg/dL at k = 1);
**fingersticks passed** (F1 and F2: 2.8 mg/dL closer as they arrive, 9.5 in hindsight, 0.3 with one a day).
The label check is regenerated by `python -m chhaya.data.audit` and matches the 4 Oct counts above, which are
now quotable. Quote only the "claim to quote" sentence of each record.

Also run on 8 Oct 2026 on held-out patients (Plan 4; descriptive, no bar; one record each; wording reviewed by
`healthcare-reviewer`): **fingersticks at report level** (`2026-10-08-fingersticks-report.md`): in supervised-care
patients tested about six times a day the rebuilt report missed the sensor's mean by 8.9 mg/dL where the stale
three-day report missed by 13.0, but **the plain fingerstick average converted to the sensor's scale missed by 6.4
and beats our estimate on all three report numbers**; time in range from an estimate is not usable; lower testing
frequencies were not measured; sensor-scale figures are not meter values. **Expiry** (`2026-10-08-expiry.md`):
these data do not give a number of days: about 1 mg/dL per day, downward, over at most eleven days in supervised
care; no ageing detected over a week in free-living participants; in nine repeat wears of eight patients the four
whose mean had moved all had a treatment change in the files (three patients; a case series, not a rule). **Band**
(`2026-10-08-band.md`): 83.5 % coverage on average, 60 to 98.5 % per patient; the recalibration factor (0.78) did
not transfer and is not used. **Staleness alarm** (`2026-10-08-staleness.md`): on 32 held-out recordings, 11
drifted by more than 20 mg/dL (9 downward), a running sum of fingerstick surprises separated drifted from stable
recordings with AUROC 0.82 (interval 0.63 to 0.98) and **was not shown to do better than comparing the fingerstick
average with the report** (also 0.82); at its development threshold it was raised in 7 of 11 drifted and 2 of 21
stable recordings; with a five-day report it was not shown to separate them. It is a prompt to consider a new
sensor wear, never called an alarm on screen, never a finding about glucose, advice on treatment or a rule for
when to wear a sensor. It was not tested in outpatient care, at lower testing frequencies or beyond eleven days,
so in the product's own use case it is shown on the Evidence screen only. Quote only each record's "claim to quote",
whole: its caveats are part of it.
- What the RSSDI glucose-monitoring consensus says about intermittent sensor use; read it before citing it.

Known model gaps: no counter-regulation (deep hypoglycaemia dynamics are not trustworthy), no drug
kinetics, no exogenous insulin, one absorption curve per meal.

## Environment gotchas (Windows)

- The working tree is inside OneDrive, which is signed out on this machine (dormant), so no sync workaround is
  needed. The git directory is at `C:/dev/DigitalTwinHack.git` (`.git` is a pointer file). Datasets go to
  `./data` (git-ignored); override with `CHHAYA_DATA_DIR` if needed.
- **Always pass `encoding="utf-8"`** when reading or writing text. The default is cp1252 and it corrupts
  the Chinese diet text and column headers.
- Python 3.13, `uv` 0.12. **Docker is not installed** — do not plan around it.
- In the Bash tool, long heredocs containing apostrophes fail to parse. Write files with the Write tool.

## Skills and agents to reach for

| When | Use |
|---|---|
| Any new feature or behaviour change | `superpowers:brainstorming`, then `superpowers:writing-plans` |
| Writing code | `superpowers:test-driven-development` |
| A test fails or a number looks wrong | `superpowers:systematic-debugging` |
| Before saying "done", "passes" or "fixed" | `superpowers:verification-before-completion` |
| Experiment design, leakage, "is this result real?" | `scientific-critical-thinking`, `statistical-analysis` |
| Baselines, splits, evaluation, reproducibility | `mle-workflow`, `scikit-learn`; `shap` for the baseline forecaster |
| First look at a new file or column | `exploratory-data-analysis` |
| Figures for README, deck, video | `scientific-visualization`, `dataviz` |
| README, limitations, method write-up | `scientific-writing` |
| The deck | `pptx-deck:create-deck` |
| After any change under `src/` | `python-reviewer` agent |
| After any change to model, fitting or evaluation | `mle-reviewer` agent |
| After anything clinical or patient-facing (dashboard copy, alerts, thresholds) | `healthcare-reviewer` agent |

`pymc`, `statsmodels`, `aeon`, `polars` and `pyhealth` are installed but not on the critical path; use
them only if a task in the plan calls for it.

## Decisions

- Decided: project name **Chhaya**; team **SynapseX**, IIT Kanpur; `docs/WAR_ROOM.md` is public.
- Not committed (kept local): `.claude/`, `.agents/`, `skills-lock.json`.
- Still open: questions for the organisers (top 10 or top 5 after Phase 1; is "minimum 20-minute video"
  correct; is there a scoring rubric).
