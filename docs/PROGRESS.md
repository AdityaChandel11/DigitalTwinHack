# Progress map (read this first in a new chat)

Last updated: 8 Oct 2026. Project: Chhaya, team SynapseX (IIT Kanpur), solo. Deadline 20 Oct 2026, 19:00 IST;
internal deadline 18 Oct; feature freeze 15 Oct; **science stops at midnight on 10 Oct**.
Claude is the teammate: propose, push back, name the model and effort before each task (README developer guide).
When the next task names a different model, Claude stops and waits for the switch.

## Where we are

| Milestone | State |
|---|---|
| M1 Data truth | Done. Gate 1 GO |
| M2 Core twin and the reveal | Done and closed. Gate 2 GO on the corrected run |
| M3 Evidence | **Plans 2 and 3 done.** Label check done. Gate 3 NOT PASSED. Record prior NOT PASSED. **Fingersticks PASS (F1, F2).** Plan 4: second pass of F, expiry, band and the staleness alarm **all done on held-out patients, 8 Oct** (descriptive, no bar). Only Task 9, the closing of the docs, is left |
| M4 Product (three screens, one decision) | Not started |
| M5 Ship (README, deck, 20-minute video, submit by noon 20 Oct) | Not started |

## Start here

1. **GitHub.** `main` is on GitHub at `bdafe69` (all of 8 Oct up to the progress map). Plan 4 lives on the branch
   `claude/plan-4-expiry-band-staleness-048969`, pushed 8 Oct, not yet merged into `main`. Merge it after Task 9.
   Never run any `--confirm` command from a checkout that lacks the results folders of earlier passes: the
   once-only guards read the folder in the checkout you run from.
2. **Plan 4, what is left**: [docs/superpowers/plans/2026-10-08-chhaya-plan-4-expiry-band-staleness.md](superpowers/plans/2026-10-08-chhaya-plan-4-expiry-band-staleness.md).
   Tasks 0 to 8 were done on 8 Oct (registration note, seven modules, independent reviews, four passes over
   held-out patients with one record each: `docs/decisions/2026-10-08-fingersticks-report.md`, `-expiry.md`,
   `-band.md`, `-staleness.md`). The staleness pass was run once (`results/staleness/shanghai/`, commit
   `1595e71`); `--confirm` is now refused for it from any checkout that has that folder.
   - **Next: Task 9** (Sonnet 5.5, medium) closes Milestone 3: the seven modules and the new commands in
     CLAUDE.md, the README command list, the design's limits, the roadmap. Nothing was cut, so none of the
     "not done" sentences of its Step 4 is used; the README limits take the staleness record's caveats
     instead. **End Task 9's report with the reminder to merge to `main` and push** (see "Waiting on the
     team lead").
   - **For the team lead to decide before Milestone 4:** whether "and when to wear a sensor again" stays in
     the headline as worded. What stands behind it is the expiry record ("not a rule for when a patient
     should wear a sensor") and a prompt that, in the product's own use case (an outpatient, weeks after a
     fourteen-day report, testing less often), is outside everything tested and so is shown on the Evidence
     screen only. On the patient screen it appears only inside the tested range (profile from three or five
     sensor days, at least 4.6 fingersticks a day, first raised by day 11); otherwise "not computed". See the
     staleness record's "Consequences for the product". Claude's suggestion: reword the clause to "and what
     we measured about when the report stops being true", or keep it and say on the first screen that the
     prompt is evidence, not a feature.
   - **What the four results change for the product** (Milestone 4; wording reviewed by
     `healthcare-reviewer`, exact screen text in each record's "Consequences for the product"): the staleness
     output is a prompt to consider a new sensor wear, never called an alarm, never a finding about glucose or
     a reason to change or keep treatment, shown only inside the tested range and beside the plain comparison
     it did not beat, with "no prompt does not mean the report still holds" and "not computed" as visible as
     the prompt; the report
     since the sensor is an estimated, "sensor-equivalent" mean and share of fingerstick readings above 180,
     from the plain fingerstick average converted to the sensor's scale, beside the same figures as read from
     the meter, not from the estimator; no time in range and no time below range from any source; days since
     the sensor is a fact with no threshold and no per-day figure beside it; a recorded treatment change is
     shown with the case-series counts and "no recorded change does not mean the report still holds"; the
     clinic list has no default ranking by the treatment flag; the band is drawn as Gate 2 scored it.
3. Before quoting any Clarke zone figure: `clarke_zones` matches the widely used reference implementation but
   has not been checked against the figure in the 1987 paper. Say in the README that the Clarke grid is used.

## What was done, in order (details in docs/decisions/)

1. Concept chosen in docs/WAR_ROOM.md. Core twin built and tested (128 tests).
2. Gate 1 GO: 106 usable Shanghai recordings; 65 of 109 on insulin.
3. Gate 2: first run NO-GO, inputs fixed, blend added; GO on 20 held-out patients; break test; corrected re-run
   on 4 Oct, still GO (19 patients, one skipped by the coverage guard).
4. Research round, 4 Oct: sensor lows in Shanghai are 12 % confirmed by fingerstick, so the overnight-low
   fallback was withdrawn; the headline was changed; Amendment 3 fixes the Milestone 3 bars.
5. 7 Oct: roadmap rebuilt, Plans 2 and 3 written.
6. 8 Oct, Plan 2: label check regenerated by a repo command (matches the 4 Oct counts). Gate 3 code reviewed
   twice, a dated note added to Amendment 3, then the one confirmatory run: **NOT PASSED**.
7. 8 Oct, Plan 3: `--prior` and `--tag` on Gate 2; two sweeps at k = 1 to 7; record prior **NOT PASSED**.
   Fingerstick experiment built, reviewed twice (the reviews caught a same-minute reading, a one-value leak
   into the sensor map and an inexact smoother, all fixed before the test run), filter frozen on development
   patients with a dated note, then the one confirmatory run: **F1 and F2 PASS**.
8. 8 Oct: headline revised (the excursion clause removed, "which readings not to believe" added).
9. 8 Oct, Plan 4: a third dated note to Amendment 3 fixed how the descriptive outputs are computed, before
   their code. Five modules built with no change to any existing source file; two independent reviews found
   no leakage and ten defects, all fixed test-first and recorded in an addendum to the note. Then one pass
   each over held-out patients: the second pass of section F (a plain baseline beats our estimator at report
   level), expiry (these data do not give a number of days; "lasts about five days" corrected) and the
   band (the recalibration did not transfer).
10. 8 Oct, Plan 4, Task 8: the staleness alarm built, reviewed twice (the reviews fixed the threshold rule and
    added the two-day sum and three guards; second addendum to the note), run on development recordings, then
    the one pass over 32 held-out recordings: it separated drifted from stable recordings (AUROC 0.82) and
    was not shown to do better than comparing the fingerstick average with the report (also 0.82). The record's
    wording was reviewed by `healthcare-reviewer`; its findings moved the prompt to the Evidence screen in
    the product's own use case.

## What Chhaya is now (the headline)

One sensor wear turned into the patient's shadow: **how long that sensor report stays true, which of its
readings not to believe, what keeps it true, and when to wear a sensor again**, with an honest band. Every
number is scored once on held-out patients against a bar written beforehand, misses published. It does not
replace a sensor and has no low-glucose alarm and no meal alert.

What stands behind each clause today:

| Clause | Evidence | State |
|---|---|---|
| How long it stays true | Expiry by day on both datasets; case series of eight re-recorded patients | Done. These data do not give a number of days: about 1 mg/dL per day, downward, over at most eleven days in supervised care; no ageing detected over a week in free-living participants; and in nine repeat wears of eight patients the four whose mean had moved all had a treatment change in the files. Not a rule for when to wear a sensor |
| With an honest band | Gate 2 coverage; band recalibration | Done. 83.5 % on average, 60 to 98.5 % per patient; the recalibration did not transfer and is not used |
| Which readings not to believe | Label check: 8 of 64 sensor lows confirmed, 732 of 809 highs | Done |
| What keeps it true | Meal log (Gate 2); fingersticks (F1, F2); second pass of F at report level | Both pass. At report level a plain baseline wins: the fingerstick average converted to the sensor's scale beats our estimate. Measured at about six fingersticks a day only |
| When to wear a sensor again | Staleness alarm on 32 held-out recordings | Done. A prompt, not a rule: it told moved from unmoved reports (AUROC 0.82, interval 0.63 to 0.98; raised in 7 of 11 drifted and 2 of 21 stable recordings) and was not shown to do better than comparing the fingerstick average with the report (0.82). Supervised care, about six fingersticks a day, at most eleven days, 9 of 11 drifts downward; not tested where the product would be used, so in the product's use case it is on the Evidence screen only. **This clause of the headline is the weakest; see "Start here"** |
| Fusion of record and sensor | Gate 3 (M1) and record prior (P1) | Both missed: built and measured, no gain |

## The claims to quote (and nothing bigger)

- **Gate 2:** on 19 held-out patients, 5 days after the sensor comes off, Chhaya's estimate is 1.4 mg/dL (6 %)
  closer to the hidden sensor than the patient's own average day (p = 4e-05) and about 0.35 mg/dL closer than a
  control that uses no meals (p = 0.04). The gain comes from the meal log and is small. **Corrected 8 Oct**
  (the Gate 2 record said "lasts about five days"): it was not seen to fade with days since the sensor;
  with three days of calibration the median favours the twin over its control on each of the seven
  following days (0.4 to 2.0 mg/dL; the interval excludes zero on three of them; 19 held-out participants),
  and it reverses only on the last days of the recording, which fewer than half of the participants reach.
  (`docs/decisions/2026-10-08-expiry.md`)
- **Label check:** of 64 sensor readings below 70 mg/dL with a fingerstick within 10 minutes, 8 (12.5 %) were
  confirmed, and 0 of 9 at night; of 809 sensor readings above 180, 732 (90.5 %) were confirmed.
  (`python -m chhaya.data.audit`)
- **Fingersticks (passed):** on 29 held-out Shanghai patients, calibrated on three days of sensor data,
  fingersticks taken afterwards brought the running estimate 2.8 mg/dL closer to the hidden sensor than the
  patient's daily shape alone (median paired RMSE difference; 95 % interval 1.6 to 4.7; 86 % of patients;
  p = 4e-06) and 9.5 mg/dL closer in hindsight (interval 4.6 to 12.1); with one fingerstick a day the running
  gain was 0.3 mg/dL.
- **Fingersticks at report level** (`docs/decisions/2026-10-08-fingersticks-report.md`): descriptive, no
  bar; a plain baseline beats our estimator. On 29 held-out Shanghai patients under supervised care who
  were tested about six times a day, with the hidden sensor as the yardstick, a three-day sensor report
  missed the mean sensor glucose of the following days (up to eleven) by a median of 13.0 mg/dL. Chhaya's
  report rebuilt in hindsight from those fingersticks missed it by 8.9 (median paired difference 3.4, 95 %
  interval 1.6 to 8.9, 83 % of patients), but was no closer than the plain average of the same fingersticks
  converted to the sensor's scale by a line learned during the wear (6.4). The share of those converted
  readings above 180 mg/dL and within 70 to 180 was also closer to the sensor's time above 180 and time in
  range (3.1 against 8.8 points; 5.0 against 15.2). As read from the meter the same average lay 18.3 mg/dL
  from the sensor's mean; sensor-scale figures are not meter values. Lower testing frequencies were not
  measured, and this is not a recommendation to test at any frequency.
- **Expiry** (`docs/decisions/2026-10-08-expiry.md`): descriptive, no bar; "report" means mean glucose
  only, and a three-day report stands in for a fourteen-day one. On 47 held-out Shanghai patients under
  supervised care with treatment being adjusted, a day's mean sensor glucose lay a median of 13.5 mg/dL
  from a three-day sensor report's mean inside the wear and 11 to 16 on the four days after it; inside each
  patient that distance grew by 1.0 mg/dL per day (95 % interval 0.7 to 2.6) over at most eleven days, with
  glucose moving downward. On 19 held-out free-living CGMacros participants (7 with type 2 diabetes;
  medication not recorded) no growth was detected over seven days (0.1 mg/dL per day, interval -0.8 to
  0.8). In a case series of eight Shanghai patients recorded again (nine later wears, five beginning within
  three days of the first sensor coming off and four 33 to 154 days after it), four wears in three patients
  had a mean more than 20 mg/dL lower, all four with a change of treatment in the files; of the five that
  had not moved, four had no change and one had, and the old daily profile fitted them no worse than a
  fresh one. No test; not a rule for when a patient should wear a sensor.
- **Band (descriptive, no bar; the recalibration did not transfer):** on 19 held-out participants the 80 %
  band held 83.5 % of hidden readings on average and between 60 % and 98.5 % for an individual, with 10 of
  19 participants within 70 to 90 %. A recalibration factor chosen on development patients (0.78) moved the
  average to 75.7 %, further from 80 % than before, so it is not used: the band is calibrated on average,
  not per patient. (`docs/decisions/2026-10-08-band.md`)
- **Staleness alarm** (`docs/decisions/2026-10-08-staleness.md`): descriptive, no bar; a plain baseline does
  as well. On 32 held-out Shanghai recordings (29 patients under supervised care, tested about six times a
  day, for up to eleven days after a three-day sensor report), 11 of which drifted by more than 20 mg/dL in
  mean sensor glucose (9 downward, 2 upward), a running sum of fingerstick surprises, used only as a prompt
  to consider a new sensor wear, separated drifted from stable recordings with AUROC 0.82 (95 % interval
  0.63 to 0.98), against 0.82 (0.61 to 0.97) for the plain fingerstick average compared with the report's
  mean (difference 0.00, interval -0.16 to 0.18): it was not shown to do better than that comparison. At a
  threshold set on development recordings so that at most 10 % of stable ones would raise it, the prompt was
  raised in 7 of 11 drifted recordings (64 %) and 2 of 21 stable ones (10 %); in those 7, a median of 2.6
  days after the split. With a five-day report (24 recordings, 6 drifted) it was not shown to separate them
  (0.67, interval 0.35 to 0.92). The label and the score look back over the same days. It is not a finding
  about a patient's glucose, not advice on treatment and not a rule for when to wear a sensor, and it was
  not tested in outpatient care, at lower testing frequencies or over longer periods.
- **Gate 3 (missed its bars):** on 47 held-out Shanghai patients (1,205 meals, 39 % followed by an excursion
  above 180 mg/dL), a model fusing the record, the sensor week and fingersticks predicted the excursion at meal
  time with AUPRC 0.60, which was not better than any single stream (fingersticks only: 0.64) nor than the
  patient's own excursion rate from the sensor week (0.59; difference 0.01, 95 % interval -0.09 to 0.14); with
  the sensor on, the same model reaches 0.76.
- **Record prior (missed its bar):** on 20 held-out CGMacros patients with one day of sensor data, giving the
  twin the record's fasting glucose as its prior changed the error of the estimate by a median of 0.02 mg/dL
  (p = 0.16), and with three or more days by nothing measurable: the record, as it enters the twin today, is
  not worth any sensor days.
- **Fusion, in one sentence:** we fused the record and the sensor two ways and measured both; once a sensor
  week exists the record added nothing detectable. What adds something is the meal log and fingersticks.

Two things a reader must be told with the fingerstick claim: the filter was chosen on development patients by
a criterion other than the plan's written rule (dated note in the registration, before the test run), and the
estimate is still about 22 % off the next fingerstick where a real sensor is about 12 %.

## Where things are

- Rules and conventions: CLAUDE.md. Roadmap, calendar and the twelve failure guards:
  docs/superpowers/plans/2026-10-02-chhaya-roadmap.md. Design: docs/superpowers/specs/2026-10-04-chhaya-m3-design.md.
- Bars, amendments and the two dated notes of 8 Oct: docs/PREREGISTRATION.md. Decisions: docs/decisions/
  (`2026-10-08-gate3.md`, `2026-10-08-record-prior.md`, `2026-10-08-fingersticks.md`, and the four of Plan 4:
  `-fingersticks-report.md`, `-expiry.md`, `-band.md`, `-staleness.md`).
- Code: src/chhaya/. Tests: tests/ (202 fast tests). Results: results/. Research scripts as run:
  scripts/research_2026-10-04/.
- Not committed: .claude/, .agents/, skills-lock.json (local tooling), data/ (datasets), .venv/.

## Waiting on the team lead

- **Merge the Plan 4 branch into `main` and push, right after Task 9** (you asked to be reminded: GitHub's `main`
  page shows only `bdafe69` until then; the merge is a fast-forward while `main` is still at `bdafe69`).
- Three questions to the organisers (rubric; video minimum and live Q&A; non-commercial data).
- Read the RSSDI glucose-monitoring consensus before it is cited.
- One clinician to look at the dashboard on 13 or 14 Oct.
- Whether competitor names stay in the public War Room doc.
