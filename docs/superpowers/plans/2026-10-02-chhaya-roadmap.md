# Chhaya roadmap — 2 Oct to 20 Oct 2026

The concept was chosen in [docs/WAR_ROOM.md](../../WAR_ROOM.md) and revised on 4 Oct
([plan revision](../../decisions/2026-10-04-plan-revision.md), [design](../specs/2026-10-04-chhaya-m3-design.md)).
This document is the build order: five milestones, what each must put on screen, and the guards against the
ways this can fail. Pass bars live in [docs/PREREGISTRATION.md](../../PREREGISTRATION.md) (Amendment 3 for
everything from Milestone 3 on).

Task-level plans:

- Plan 1, core twin (done): [2026-10-02-chhaya-plan-1-core-twin.md](2026-10-02-chhaya-plan-1-core-twin.md)
- Plan 2, label check and the excursion experiment: [2026-10-07-chhaya-plan-2-excursions.md](2026-10-07-chhaya-plan-2-excursions.md)
- Plan 3, record prior and fingersticks: [2026-10-07-chhaya-plan-3-prior-and-fingersticks.md](2026-10-07-chhaya-plan-3-prior-and-fingersticks.md)
- Plan 4, second pass of the fingerstick experiment, expiry, band, staleness: [2026-10-08-chhaya-plan-4-expiry-band-staleness.md](2026-10-08-chhaya-plan-4-expiry-band-staleness.md)
- The Milestone 4 and 5 plans are written the day each starts.

## Status (update this table whenever a milestone step finishes)

Last updated: 8 Oct 2026.

| # | Milestone | Status | Evidence |
|---|---|---|---|
| M1 | Data truth | **Done.** Gate 1 is GO | `docs/decisions/2026-10-03-gate1.md` |
| M2 | Core twin and the reveal | **Done and closed.** Gate 2 is GO on the corrected run: 21.9 vs 23.3 mg/dL against the average day at k = 5 (p = 4e-05), 0.35 mg/dL against the physiology-free control (p = 0.04) | `docs/decisions/2026-10-04-gate2-corrected.md`, `results/gate2/cgmacros-test/` |
| M3 | Evidence: label check, excursions, fusion, fingersticks | **In progress.** 3.1 label check done: 8 of 64 sensor lows and 732 of 809 sensor highs confirmed by fingerstick. 3.2 **Gate 3 NOT PASSED** (M1, M2, M3 miss): fused sensor-off AUPRC 0.596 on 47 held-out patients, not better than any single stream nor than the personal rate (0.587; difference 0.009, interval -0.089 to 0.141); sensor on 0.760. 3.3 **P1 NOT PASSED**: the record prior changed the estimate by a median of 0.02 mg/dL at k = 1 (p = 0.16) on 20 held-out patients and by nothing from k = 3. 3.4 **F1 PASS, F2 PASS**: on 29 held-out patients fingersticks bring the running estimate 2.79 mg/dL closer to the hidden sensor than the daily shape alone (interval 1.60 to 4.69, p = 4e-06) and 9.50 closer in hindsight; 0.3 with one fingerstick a day. **M3 is complete except Plan 4 (3.5 to 3.7)** | `docs/decisions/2026-10-08-gate3.md`, `docs/decisions/2026-10-08-record-prior.md`, `results/gate3/shanghai/`, `docs/decisions/2026-10-08-fingersticks.md`, `results/fusion/`, `results/fingersticks/shanghai/`, `results/audit/label_validity.json` |
| M4 | Product | Not started | |
| M5 | Ship | Not started | |

### Decisions and changes since this roadmap was written

- Project renamed to **Chhaya**. Team SynapseX, IIT Kanpur, solo.
- The estimate is an equal-weight blend of the physiology and the patient's own average day (chosen on
  development patients). After the first Gate 2 run every claim is made on held-out test patients only.
- **4 Oct: the headline changed.** Chhaya is "the shadow of one sensor wear: how long that report stays true,
  what keeps it true, and when to wear a sensor again". It does not claim to replace a sensor.
- **4 Oct: the overnight-low module is withdrawn**, as a headline and as a fallback. In Shanghai, 12 % of sensor
  readings below 70 mg/dL were confirmed by a fingerstick taken at the same moment.
- **4 Oct: the adverse event is a post-meal excursion** above 180 mg/dL, predicted at meal time on Shanghai.
- **4 Oct: cut** the Shanghai food table, insulin kinetics, oral drug terms, the cross-patient corrector,
  meal-shape tuning, walk what-ifs, time-in-range claims and the "inside sensor noise" line.
- Three working days were lost between 4 and 7 Oct. The calendar below is rebuilt from 7 Oct and the cut order
  is stricter.
- **8 Oct: Gate 3 did not pass; failures 1 and 3 of the table below are triggered.** Responses as written
  there: the result is published with its bars; the stream switch shows the measured numbers; the dashboard
  shows risk bands, not probabilities (M3 missed); there is no meal alert. The record-prior result is the
  second fusion test. **Headline revised the same day:** the clause "predicts post-meal excursions without
  the sensor" is removed (the sensor week's own excursion rate does as well as any model) and "which of its
  readings not to believe" is added (the label check).
- **8 Oct: the record prior did not help (P1 missed), so both registered fusion tests are null.** The record
  prior is one lab value on one parameter; a learned record-to-parameter map was never built and is not being
  built now. Fusion is described as built and measured, not as a gain. The "sensor-days-saved table" of 3.3
  exists and says there is no saving; the dashboard shows no such figure.
- **8 Oct: fingersticks pass (F1, F2).** The filter (fade over 120 minutes, no slow level) was chosen on
  development patients by the median paired difference, not by the plan's rule of lowest cohort-median RMSE;
  the departure is in a dated note to Amendment 3, written before the test run. "Fingersticks already taken"
  is read strictly (before the minute). The report-level outputs of section F are a declared second pass in
  Plan 4 with the estimator frozen. Product: the retrospective reconstruction is the feature with the
  strongest evidence; the gain needs several fingersticks a day.
- **8 Oct: Plan 4 written.** It adds seven modules and changes no existing source file. Its readings of the
  registered text are in a third dated note to Amendment 3, committed before its code: time above 180 from an
  estimate uses a normal spread measured on calibration days; a day since the sensor is a 24-hour block from
  the split; each later day is read against "day 0" (one day of the wear against its other days); the band
  factor per day must be reached by 80 % of the cohort and must not leave fewer patients within 70 to 90 %;
  the recalibrated band is shown only if it transfers to held-out patients. Per-reading reveal traces are
  cached under the data folder, never under `results/`.
- 8 Oct: a dated note to Amendment 3 fixes how section M was coded (plain share for M2, and seven smaller
  readings of the text), written before the test run. `--confirm` on Gate 3 is pinned to the registered
  settings and refuses a second run.

## What wins this

Judging is on "technical implementation and real-world healthcare impact". No rubric is published. The best
public entries already have real data, ablations with intervals, conformal bands, React front ends and CI, so
those are the floor. What only we can show:

1. **The reveal, with an honest band.** A real patient's hidden glucose, the shadow's estimate, then the real
   trace on top. No other entry runs without the sensor.
2. **Evidence that was allowed to fail.** Bars committed before each run; a fallback we withdrew because our own
   check showed its labels were wrong; nulls published next to passes. No other public entry pre-registers.
3. **Labels checked against fingersticks.** We can say which sensor events are real and refuse to alarm on the
   ones that are not.
4. **Fusion that is measured.** A stream switch on the dashboard that shows the measured accuracy of record
   only, sensor history only, fingersticks only and fused, on held-out patients.

There is no large effect hidden in the open data: meal logs add about 2 %, fingersticks 3 to 8 % in an
exploratory look. We win on measuring the truth better and packaging it better, not on a big number.

## Calendar (rebuilt 7 Oct)

| Date | Work | Ends with |
|---|---|---|
| Wed 7 Oct | Plan 2, Tasks 1 to 3: label check, record fields, meal table | Label check in `results/audit/` |
| Thu 8 Oct | Plan 2, Tasks 4 and 5: excursion experiment, development run, then the one confirmatory run | **Gate 3** decision record |
| Fri 9 Oct | Plan 3: record prior runs (in the background) and the fingerstick experiment | Decision records for P and F |
| Sat 10 Oct | Plan 4: expiry and case series, band recalibration; staleness only if both are done by 16:00 | **Science stops at midnight** |
| Sun 11 – Wed 14 Oct | **M4 Product**: artifact build, three screens, record JSON, demo patient. Clinician review 13 or 14 Oct | Dashboard runs offline |
| Thu 15 Oct | **Feature freeze.** Safety review of every screen, clean-clone test on a second folder | Freeze tag |
| Fri 16 Oct | README, architecture PDF, model card, TRIPOD+AI checklist, video script | |
| Sat 17 – Sun 18 Oct | Deck; record and upload the video | **Internal deadline, 18 Oct** |
| Mon 19 Oct | Slack: re-record, fix links, second clean-clone | |
| Tue 20 Oct, 12:00 | Submit | 7 hours before the portal closes |

## M3 — Evidence (7 to 10 Oct)

Definitions and bars: Amendment 3. Cut from the bottom; the first four are not cuttable.

| # | Deliverable | Plan | Accepted when | If time runs out |
|---|---|---|---|---|
| 3.1 | **Label check.** Sensor against fingerstick agreement as a repo command | Plan 2, Task 1 | `results/audit/label_validity.json` regenerates; the below-70 and above-180 figures appear in the README | Not cuttable |
| 3.2 | **Excursion experiment (Gate 3).** Post-meal above 180 at meal time; record, sensor history, fingersticks, fused, sensor on, personal rate | Plan 2, Tasks 2 to 5 | Confirmatory run done once; M1 and M2 reported with intervals; leakage test green | Not cuttable: it is the brief's adverse event and its fusion ablation |
| 3.3 | **Record as prior.** Reveal at k = 1, 3, 5, 7 with and without the record | Plan 3, Tasks 1 and 2 | P1 reported; the sensor-days-saved table exists | Not cuttable: two background runs |
| 3.4 | **Fingersticks.** Live and in-hindsight estimates, thinning, accuracy against the fingerstick beside a real sensor's | Plan 3, Tasks 3 to 6 | Filter design frozen on development patients before the test run; F1 and F2 reported | Not cuttable; the thinning table can be dropped |
| 3.5 | **Expiry.** Error by day since the sensor; the eight re-recorded patients as a case series | Plan 4 | One figure and one table, labelled case series | Keep the case series, drop the by-day figure |
| 3.6 | **Band recalibration** | Plan 4 | Test coverage and patients within 70 to 90 % reported | Cut second; state "calibrated on average, not per patient" |
| 3.7 | **Staleness alarm on real drift** | Plan 4 | AUROC with interval on test recordings | Cut first; the dashboard then shows days since the sensor only, and the README says the alarm is untested |

Every experiment gets a decision record (`docs/decisions/<date>-<topic>.md`) and a row in the Status table in the
same commit as its results.

## M4 — Product (11 to 15 Oct)

One decision on screen: is the last sensor report still valid, where in the day is the problem, should the
patient wear a sensor again.

| # | Deliverable | Accepted when |
|---|---|---|
| 4.1 | **Artifact build.** `python -m chhaya.build` writes one JSON bundle per patient to `artifacts/`: profile, band, reveal arrays, excursion probabilities per arm, days since sensor, what-ifs | The dashboard starts with the network unplugged and never fits a model |
| 4.2 | **Patient screen.** Last sensor report beside today's shadow with its band; reveal switch; days since the sensor; where-in-the-day strip; stream switch that changes the probability and shows that arm's measured accuracy | A clinician reads the state of the patient in under 10 seconds; no estimate without band and the word "estimated"; a sensor low reads "sensor low, unconfirmed" |
| 4.3 | **Clinic list.** Patients ordered by days since sensor and share of meals predicted above 180, one-line reason | |
| 4.4 | **Evidence screen.** Every results table with its bar, the label check, limits, provenance | Every figure matches `results/` |
| 4.5 | **Meal what-if** on the virtual patient | Labelled "simulation"; no dose, drug or walk options; no recommendation text |
| 4.6 | **Record as FHIR-shaped JSON** and the synthetic demo patient "Mrs. R." | Labelled synthetic on screen; the genetic-marker field is synthetic and off in every experiment |
| 4.7 | **Figures**: reveal (hero), stream ablation, record-prior curve, fingerstick accuracy beside a sensor, label check, expiry | Each regenerated by one script from `results/` |
| 4.8 | **Front end.** One page served by one local command. Decide on 13 Oct at 18:00: if the custom page does not show the patient screen end to end, switch to Streamlit that evening | One command starts it; a recorded walkthrough is in the repo |

Limits banner on every screen. Run `healthcare-reviewer` on every screen on 15 Oct.

## M5 — Ship (16 to 20 Oct)

| Item | Note |
|---|---|
| README | First screen: the reveal, four numbers with their bars, what Chhaya is not. Then team, problem, method, results, limits, licences, how to run. Developer guide removed |
| One command | `python -m chhaya.reproduce` regenerates every number quoted anywhere, and CI runs the fast tests |
| Model card and TRIPOD+AI checklist | In `docs/`; every item answered or marked not applicable with a reason |
| Data licences | `DATA_LICENSES.md`: ShanghaiT2DM CC BY 4.0, CGMacros CC BY-NC-SA 4.0 (non-commercial), nothing redistributed |
| Architecture diagram | PDF, from the module map in CLAUDE.md |
| Deck | PDF, following the video script |
| Video | At least 20 minutes. Script 16 Oct, record 17 and 18 Oct, unlisted link in the README |
| War Room doc | Competitor names removed if the team lead confirms |
| AI assistance | One honest sentence in the README; the team lead can explain every equation live |
| Clean-clone test | Fresh clone in a second folder: sync, download, audit, smoke runs, dashboard starts |
| Submission | Repo public; folder `SynapseX_IITK`; by 12:00 on 20 Oct |

## Twelve ways this fails, and the guard against each

| # | Failure | Guard, already in the plan | Trigger | Response when triggered |
|---|---|---|---|---|
| 1 | A confirmatory run loses its bar | Bars are in Amendment 3; the README template has a "missed its bar" row from the start | Any bar fails | Publish it with the bar. The headline does not depend on any single bar passing |
| 2 | The excursion event is too common or too rare to discriminate | 250 mg/dL threshold and "meals that start at or below 180" are pre-declared secondary analyses | Development-run event rate above 85 % or below 10 % | Report the primary as registered and lead with the pre-declared secondary on screen, saying so |
| 3 | Fusion does not beat the best single stream | The stream switch shows measured numbers either way | M1 fails | Say "fusion did not beat the best single stream, by this much"; keep the record-prior result as the second fusion test |
| 4 | Leakage in a feature builder | A test per builder: change hidden sensor readings, assert non-sensor features are unchanged; `--confirm` required to touch test patients | Leakage test red | Fix before any run; a run made with leakage is void and recorded as void |
| 5 | A clinician says the lows are not real | The label check is a repo command and a front-page finding; no low alarm exists | — | Already answered by our own data |
| 6 | Dataset licence challenged | Shanghai CC BY 4.0 read on Figshare; CGMacros non-commercial stated; nothing redistributed; `DATA_LICENSES.md` | Organiser objects to non-commercial data | Shanghai-only results stand alone (excursions, fingersticks, label check) |
| 7 | Science eats the product days | Science stops at midnight on 10 Oct; cut order is fixed (3.7, 3.6, 3.5) | Anything in 3.1 to 3.4 open on 10 Oct at 16:00 | Drop 3.5 to 3.7 that hour; unfinished items become a "not done" line in the README |
| 8 | The custom front end is not ready | Streamlit fallback with a fixed decision time | 13 Oct, 18:00 | Switch that evening; no further front-end work beyond the three screens |
| 9 | The video takes two days longer than planned | Script on 16 Oct; two recording days; 19 Oct is slack; the recorded walkthrough doubles as demo footage | Not uploaded by 18 Oct, 22:00 | Use 19 Oct; cut the deck to the video's slides |
| 10 | The reveal looks like an average day on screen | The hero figure shows the band and its measured coverage, the average day in grey and the hidden trace; the claim beside it is the measured one | Hero figure review on 14 Oct | Lead with coverage ("83 % of hidden readings inside the 80 % band") and the expiry curve, not with closeness |
| 11 | Clean clone fails on another machine | Clean-clone test on 15 Oct and again on 19 Oct; pinned `uv.lock`; download script with checksums | Either test fails | Fix that day; nothing else ships first |
| 12 | A judge reads a small number before the framing | README first screen states what the shadow is and is not before any number; each number sits beside its comparator and bar | README review on 16 Oct | Rewrite the first screen until a cold reader can say what Chhaya does not claim |

Standing risks with no full guard: no Indian data; supervised hospital care in Shanghai; hidden windows of at
most about ten days; a solo builder. Each is stated in the README limits section.

## Tasks only the team lead can do

| When | Task |
|---|---|
| Now | Send the organisers three questions: is there a rubric with weights; is the 20-minute video a minimum, and is Phase 2 a live Q&A; is open data under a non-commercial licence acceptable when fetched by script |
| Now | Read the RSSDI glucose-monitoring consensus before it is cited: https://journals.sagepub.com/doi/10.1177/30502071241293567 |
| By 12 Oct | Arrange one clinician to look at the dashboard on 13 or 14 Oct; ask permission to quote them |
| 16 Oct | Decide whether competitor names stay in the public War Room doc |
| 17 – 18 Oct | Record the video; be able to explain the model, the split and every bar without notes |

## How the work splits across sessions

The contract between tracks is `Recording` (data to model) and the artifact bundle (model to dashboard).
Science sessions execute Plans 2 to 4 task by task with tests first. Product sessions start from synthetic
artifacts on 11 Oct so they do not wait on late science.
