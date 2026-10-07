# Plan revision, 4 Oct 2026

A second red-team round before Milestone 3: the corrected Gate 2 re-run, counts on the Shanghai files, three
exploratory probes on Shanghai development patients, a scan of public competing entries, and a re-check of
dataset sources. It changes the headline, withdraws the fallback, and replaces the Milestone 3 list.

Evidence: `results/gate2/cgmacros-test/` (confirmatory) and `scripts/research_2026-10-04/` (exploratory; see the
README there). Bars for everything that follows are in Amendment 3 of `docs/PREREGISTRATION.md`.

## What was found

### Confirmatory

1. **Gate 2 stays GO after the corrected re-run**, with the same small effect: 0.35 mg/dL against the
   physiology-free control at k = 5 (p = 0.036). Record: `2026-10-04-gate2-corrected.md`.

### Counts on the real files (labels and availability; all Shanghai patients)

2. **Sensor lows in ShanghaiT2DM are mostly not capillary lows.** All 3,268 fingersticks have a sensor reading
   within 10 minutes. Where the sensor reads below 70 mg/dL (64 pairs, 21 patients) the fingerstick is also below
   70 in 8 (12 %); its median is 94. With a flat sensor trace (38 pairs) it is 13 %, so this is not lag. At night
   (00:00 to 06:00) it is 0 of 9. Only 18 fingersticks are below 70. This matches published behaviour of the
   same sensor family (see Sources).
3. **Sensor highs are real.** Above 180: 809 sensor flags, 732 confirmed (90 %). Above 250: 202, 175 (87 %).
   The sensor reads low, and more so at high glucose: -8 mg/dL at 100 to 180, -20 at 180 to 250, -35 above 250.
   Overall MARD 12.8 %. The per-patient offset has a spread of 16 mg/dL across patients.
4. **Overnight lows are also too few.** 97 nights with a sustained sensor low in 41 of 100 patients; in the
   test split 40 nights in 16 patients, 62 % of them in five people.
5. **The setting is supervised care.** Insulin pumps in 35 of 109 recordings, intravenous insulin in 6,
   fingersticks at seven fixed clock times, weighed food. The paper never says inpatient or outpatient (read in
   full on 4 Oct). The sensor mean falls by more than 20 mg/dL between the first and last three days in 29 % of
   recordings of 8 days or more, and rises by that much in 5 %.
6. **Fingersticks are plentiful but uneven.** Median 2.4 a day; 46 recordings have 4 or more a day, 15 have
   none. A cohort with at least one a day and two hidden days: 59 recordings at k = 3 (34 test), 46 at k = 5.
7. **Eight patients were recorded again** 12 to 168 days later (nine extra recordings): a small real long-gap set.
8. **The record is rich**: fasting and 2-hour glucose, C-peptide and insulin, HbA1c, glycated albumin, lipids,
   kidney function, complications, agents. The sheet's "Hypoglycemia (yes/no)" column is not defined as prior
   history, so it is never used as a predictor.

### Exploratory, Shanghai development patients only (20 to 24 patients; not quotable)

9. **Reading by reading, fingersticks add little to the patient's own daily shape.** At k = 5 with about four
   real fingersticks a day: control 32.6 mg/dL; a random-walk level fed by fingersticks is worse (34.8); a
   decaying deviation is slightly better live (32.3, better in 75 %) and in hindsight (31.0, better in 90 %).
   A perfect daily level correction would reach only 26.4, so the remaining error is within the day.
10. **One sensor wear is worth more than fingersticks alone.** The patient's own profile (32.6) beats
    fingersticks carried forward (43.4), interpolated (37.4), and fingersticks on a population shape for a
    patient who never wore a sensor (39.3).
11. **Against the fingerstick itself the shadow is not a sensor.** Real sensor: MARD about 13 %, 75 % of
    readings within 15 mg/dL or 15 %. Shadow: about 20 %, 41 to 47 %.
12. **At the level of the report** (mean, time above 180, time in range over about eight hidden days), shape
    plus fingersticks does not beat the stale sensor report, because the report has barely aged in a week. It
    does beat the plain fingerstick average on time above 180 (3.5 against 7.6 to 12.6 points).

### Sources and field

13. **Licences.** ShanghaiT2DM is CC BY 4.0 on its Figshare page (read in a browser; a 2025 survey paper says
    it has no licence, which is wrong or out of date). CGMacros is CC BY-NC-SA 4.0. No open T2D dataset with
    both a record and wearables is better than these two (21 datasets listed by the Glucose-ML project; the
    large ones are controlled access).
14. **Competing entries are stronger than the War Room doc assumed.** Of 19 public entries with a real README,
    the best have real data, ablations with bootstrap intervals, conformal bands, React and FastAPI front ends
    and CI. None runs without the sensor. None mentions pre-registration. None of the five read in detail
    checks sensor labels against fingersticks.

## Decisions

| # | Decision | Because |
|---|---|---|
| 1 | **The overnight-low module is withdrawn**, as a headline and as the Gate 2 fallback. No low-glucose model is trained on sensor lows. | Findings 2 and 4 |
| 2 | **The headline changes** from "keeps estimating your glucose after the sensor comes off" to "how long one sensor report stays true, what keeps it true, and when to wear a sensor again". | Findings 1, 9, 11, 12 |
| 3 | **The adverse event is a post-meal excursion** (sensor above 180 mg/dL for 15 minutes within 2 hours of a meal), predicted at meal time on Shanghai, without the sensor and with it. | The brief's own example; label is valid (finding 3); about 3,800 meals |
| 4 | **Fusion is measured twice**: as an ablation in the event model (record, sensor history, fingersticks, fused) and as the record prior switched on and off in the twin at k = 1 to 7. | The brief's central requirement |
| 5 | **Fingersticks are reported for what they do**: a small live gain, a larger one in hindsight, and accuracy against the fingerstick itself next to a real sensor's. | Findings 9 and 11 |
| 6 | **Cut from Milestone 3**: Shanghai food table, insulin kinetics, oral drug terms, cross-patient corrector, meal-shape tuning, walk what-ifs, any time-in-range claim, the "inside sensor noise" line. | About 2 % effect with known meals; activity adds 0.03 mg/dL; the average day estimates time in range better |
| 7 | **The dashboard is built around one decision**: is the last sensor report still valid, where in the day is the problem, should the patient wear a sensor again. | Follows from decision 2 |
| 8 | **Competitor names come out of the public War Room doc before submission** (to be confirmed by the team lead). | Naming and criticising other student teams in a public repo is a risk with judges |

## Not verified

- The RSSDI glucose-monitoring consensus (intermittent sensor use in India) could not be read by our tools. It
  must be read before it is cited: https://journals.sagepub.com/doi/10.1177/30502071241293567
- Sample sizes for the NHANES accelerometry cohort (the rejected alternative) remain from memory.
- The competitor tallies come from keyword matching on READMEs and are approximate; five entries were read.

## Sources

- Shanghai datasets: https://pmc.ncbi.nlm.nih.gov/articles/PMC9849330/ and
  https://figshare.com/articles/dataset/Diabetes_Datasets-ShanghaiT1DM_and_ShanghaiT2DM/20444397
- Sensor over-reading of lows: https://pmc.ncbi.nlm.nih.gov/articles/PMC6154245/ and
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9639390/
- Glucose-ML dataset list: https://www.glucose-ml-project.com/
- Time-in-range consensus targets: https://pmc.ncbi.nlm.nih.gov/articles/PMC6973648/
- TRIPOD+AI: https://pmc.ncbi.nlm.nih.gov/articles/PMC11019967/
