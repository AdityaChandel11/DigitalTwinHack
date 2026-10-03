# War Room — Digital Twin Challenge 2026 (Happiest Health)

Convened 2 Oct 2026. Submission closes 20 Oct 2026, 7:00 PM IST — **18 days from today**.

**How to read this.** If you have five minutes, read Phase 6 and the Appendix. Everything before that is the reasoning, so you can argue with it.

**What was checked live vs. recalled.** I had web search and used it. Claims marked **[verified]** were checked today against the source listed at the bottom. Claims marked **[memory]** are from my own knowledge and could be stale — check them before they go on a slide.

**No candidate idea was supplied**, so nothing here is defending a sunk cost.

---

## Phase 0 — Interrogate the Brief

### What is literally being asked

A proof-of-concept that does four things, all mandatory:

1. Picks **one** chronic or lifestyle condition prevalent in India.
2. **Fuses two streams**: static EHR-like data (demographics, diagnoses, labs, genetic markers) and dynamic wearable/IoT time series (HRV, CGM, sleep, steps).
3. Produces a **working algorithmic model that predicts an adverse event** ahead of time.
4. Presents a **conceptual dashboard showing how a doctor interacts with the virtual patient**.

Data must be anonymized, open-source, or synthetic. Deliverable is a public GitHub repo with README, architecture diagram, deck, license, and a video of **at least 20 minutes**.

### The real problem behind the stated one

The brief describes a prediction task. The disease underneath is different: an Indian diabetologist or physician makes treatment decisions every three months on one HbA1c number and a handful of fingersticks, with no view of what happened in between. The organiser's own definition says a twin works "by simulating a patient's unique physiology" to "personalize treatment protocols". A classifier that outputs "spike in 2 hours" simulates nothing and personalises nothing. Most teams will build the classifier and call it a twin.

### Stakeholders

| Who | What they want | Would they resist? |
|---|---|---|
| Treating doctor (primary user) | A better titration decision in a 4–5 minute consult | Yes, if it adds screens, alerts, or liability |
| Patient | Fewer scary events, fewer costs, less logging | Yes, if it needs daily effort or a ₹4,000 sensor every fortnight |
| Family/caregiver of elderly patient | Not finding a parent unconscious at 4 a.m. | No |
| Clinic chain / Happiest Health | A differentiated service line, patient retention | No — this is who would deploy it |
| Sensor makers | Selling a sensor every 14 days | Yes, to anything that reduces sensor use |
| Regulator (CDSCO, DPDP) | No unvalidated software making dosing calls | Yes, if it looks like a medical device making claims |

### What the organiser actually wants to see

- Happiest Health is Ashok Soota's healthcare group: knowledge/media, diagnostics, and clinics. It launched **Happiest Endocrinology** clinics in July 2026 and ran a nutrition summit in August 2026 **[verified]**. A metabolic twin is squarely on-brand, and they are a plausible first deployer.
- Winners are announced on a summit stage titled "Reimagining and Reforming Healthcare in India". The top 5 need to be stage-worthy stories about India, not leaderboard entries.
- Phase 2 is judged on "technical implementation **and real-world healthcare impact**". Those are the two axes.
- **No official scoring rubric is published** that I could find **[verified — searched, found none]**. The rubric in Phase 6 is inferred from the brief's wording.

### The ideas everyone else will pitch

This is not a guess. Teams' repos for this exact challenge are public on GitHub, and I read them today **[verified]**:

| Team / repo | Condition | Data | Model | Reported |
|---|---|---|---|---|
| AlgoAura "GlucoTwin" (MERI) | T2D spike, 2 h | Synthetic only | GBDT hand-written in TypeScript | ROC-AUC 0.98 on its own generator |
| GlucoStudio "GlycoTwin" (VIT Bhopal) | T2D spike, 2 h | Synthetic only | XGBoost + SHAP, Streamlit | ROC-AUC 0.90 |
| ChipUP (Chennai Inst. of Tech.) | T2D spike, 2 h | Synthetic only | XGBoost, HTML mockup | ROC-AUC ~0.77 |
| RUSHI-KOLLA "GlucoTwin" | T2D spike, 60 min | **Real** (CGMacros) + Synthea | LightGBM | RMSE@60 25.7 mg/dL, AUROC 0.95 |
| **AMRIT_VIT "T2D Digital Twin"** (VIT) | T2D spike, 2 h + what-if | Synthetic ODE cohort, **validated on real Shanghai T2DM and CGMacros** | LightGBM + personalised ODE twin, 47 Indian dishes, triage view, 75 tests | PR-AUC 0.85; 60-min MAE 14.1 synthetic, 18.7 on real Shanghai |
| CardioTwin India (Amity) | CV risk | Synthetic only | Logistic regression | Pipeline metrics only |
| BioTwin Omni | ICU-style crises | Synthetic scenarios | Rules + "multi-agent consensus" | No numeric validation |
| Others seen by title | MediTwin (multi-disease), HealthJEPA, a 7-day deterioration "glycotwin", two more "GlucoTwin"s | — | — | — |

So the default pitches are:

1. **"GlucoTwin": T2D glucose-spike classifier, XGBoost/LightGBM, synthetic data, Streamlit, SHAP bars.** This is the modal entry. At least four repos are literally named GlucoTwin or GlycoTwin.
2. The same thing with an LSTM/Transformer.
3. A cardiovascular risk score on synthetic HR/HRV.
4. A multi-disease "whole body" platform with agents.
5. T2D spike prediction **plus a what-if simulator**. I expected this to be the differentiator. It is already built, and built well, by AMRIT_VIT.

### Constraints hidden in the wording

- **"Predicting a sudden glucose spike 2 hours in advance"** is the brief's own example, so judges will accept it — but glucose two hours out is dominated by a meal that hasn't been eaten yet. Any model claiming high accuracy at 2 h is either being told about the meal or is evaluated on synthetic data where meals are regular.
- **"Consumer wearables"** — yet a CGM is not a consumer wearable for an Indian T2D patient. One 14-day FreeStyle Libre sensor costs ₹4,200–4,437, about ₹50,000 a year **[verified]**. The brief quietly assumes hardware that 99% of India's 101 million people with diabetes **[verified: ICMR-INDIAB]** will not wear continuously.
- **"How a doctor would interact"** — the user is the doctor, not the patient. Patient-facing coaching apps are off-brief.
- **Async judging.** Phase 1 is a repo and a video, reviewed by people working through a large pile. The "first 15 seconds" is the README's first screen and the video's first minute.
- **Two inconsistencies to raise with the organisers now:** the page says both "top 10" and "top 5" are selected after Phase 1; and "minimum 20-minute video" is unusual enough that it's worth confirming it isn't meant to be a maximum.

### Assumptions I'm proceeding on

1. The team can write Python, fit ODE models, and build a web dashboard.
2. Judging weights clinical relevance and technical rigour about equally, with a tie-break on the India story.
3. Datasets that need a signed data-use agreement are out. There are 18 days left.

---

## Phase 1 — Recon

### What already exists

**Commercial**

- **Twin Health ("Whole Body Digital Twin")** — an Indian-origin company that already sells exactly this phrase. RCT in India, 319 participants; 18-month sustained T2D remission in 64.3% of completers in the twin arm; a JACC: Advances paper on hypertension in the same cohort **[verified]**. Any jury member in Indian digital health knows this company. It relies on CGM plus a sensor kit plus human coaching.
- **January AI** — "virtual CGM". After roughly 14 days of sensor wear, it predicts glucose curves without a sensor from food logs, heart rate and activity; its white paper reports 13.0% error **[verified]**. US consumer wellness, closed source, not physician-facing, not aimed at medicated T2D.
- **Ultrahuman, HealthifyMe, Fitterfly, BeatO, Sugar.fit** — Indian CGM-plus-coaching programmes **[memory]**. All need the sensor on.

**Research / open source**

- **ReplayBG** — open-source digital-twin framework: fits a physiological ODE to CGM + insulin + meals with MCMC, then replays counterfactuals. **Type 1 only**; a Python port exists (`py-replay-bg`) **[verified]**. T1D models treat insulin as an external input. T2D patients still secrete their own, so the model structure doesn't transfer directly.
- **E-DES (Eindhoven Diabetes Education Simulator)** — compact physiology model (4 compartments, ~12–14 parameters) covering healthy, T1D and T2D; in BioModels, MATLAB reference **[verified]**. A realistic starting structure for T2D.
- **UVA/Padova and Dalla Man meal models, Padova T2D simulator, `simglucose`** **[memory]** — heavier, mostly T1D-oriented.
- 2025–26 literature on hybrid mechanistic-plus-ML diabetes twins and counterfactuals (GlyTwin, simulation-based-inference twins, PhysioSeq2Seq) is active, and almost all of it is T1D **[verified]**.

**Open data that pairs both streams in real patients**

| Dataset | People | Static ("EHR") | Dynamic | Access |
|---|---|---|---|---|
| **ShanghaiT2DM** | 100 T2D, 109 recordings, 3–14 days | Age, BMI, duration, complications, HbA1c, fasting + 2 h glucose/insulin/C-peptide, eGFR, creatinine, lipids, hypoglycaemia history | Libre CGM every 15 min, **capillary fingersticks**, weighed food records, **drug and insulin doses with timestamps** | Open, CC BY 4.0 **[verified]** |
| **CGMacros** | 45 (15 healthy, 16 pre-diabetes, 14 T2D), 10 days | Demographics, HbA1c, fasting glucose and insulin, lipids, microbiome | **Two CGMs at once** (Libre Pro + Dexcom G6 Pro), **Fitbit Sense** (HR, steps, METs), meal macros with photos, standardised breakfasts and lunches | Open, CC BY-NC-SA 4.0; no medication data **[verified]** |
| HUPA-UCM | 25 T1D, 14+ days | Minimal | Libre 2, Fitbit Ionic (HR, steps, sleep), insulin, carbs | Open, CC BY-NC-ND **[verified]** |
| D1NAMO | 9 T1D + 20 healthy, 3–4 days | Minimal | CGM, ECG, breathing, accelerometer, food photos | Open (Zenodo) **[verified]** |

For hypertension, heart failure, AF and sleep apnea, I know of **no open dataset pairing wearables with clinical records and labelled adverse events that can be downloaded without an application** **[memory]**. Aurora-BP, MESA and All of Us all gate access.

### Where existing attempts fail

- **Student entries:** trained and tested on their own synthetic generator. The model rediscovers the rules the team wrote. AMRIT_VIT's README says this outright, calling it "circularity".
- **What-if simulators:** validated only on synthetic data. AMRIT_VIT states that only synthetic data allows their check. Nobody has tested a counterfactual on real patients.
- **EHR fusion is cosmetic.** AMRIT_VIT's own ablation found that once you have hours of CGM history, the record adds almost nothing to spike prediction. That is an honest and important finding. It means the brief's central requirement — fusion — is not actually earning its place in anyone's spike model.
- **Every single entry needs a CGM running forever.** None works when the sensor is off. None uses fingersticks.
- **Commercial twins** need the sensor, the kit and the coach. Cost is the adoption ceiling.

### The table-stakes bar

To not look naive next to the best public entry, a submission must have: real-data validation on Shanghai and/or CGMacros; patient-wise splits; a persistence baseline; calibrated probabilities; a what-if panel with Indian foods; a clinician dashboard; tests; a candid limitations section. That is the floor now, not the differentiator.

---

## Phase 2 — Divergent Ideation

Twenty concepts, one line each, before judging any.

1. **Spike Sentinel** — gradient-boosted 2-hour spike classifier on synthetic CGM + EHR. (The default.)
2. **Rehearsal Twin** — personalised ODE twin; the doctor tries meal, dose and walk what-ifs before prescribing.
3. **Calibrate-Once Twin** — one 14-day sensor personalises a mechanistic twin; the sensor comes off and the twin keeps running on meals, a fitness band and occasional fingersticks, and says when it has gone stale.
4. **Night Watch** — a bedtime forecast of overnight hypoglycaemia for patients on sulfonylureas or insulin, with kidney function, age and drug as mechanistic modifiers.
5. **Titration Frontier** — for each candidate dose change the twin simulates two weeks and plots time-in-range gained against time-below-range risked; the doctor picks a point on the curve.
6. **Upvas Twin** — simulates a planned religious fast (Ramadan, Navratri, Ekadashi) for a medicated patient and shows the hypo window and the dose re-timing that removes it.
7. **Drift Sentinel** — borrowed from jet-engine health monitoring: track the twin's fitted insulin-sensitivity parameter day by day and alarm on parameter drift (infection, steroids, lapsed adherence) before glucose visibly worsens.
8. **Missed-Dose Detective** — infers non-adherence from the signature of the gap between twin and reality after scheduled dose times.
9. **Thali Twin** — ranks a patient's own staple dishes by their personal predicted response; rice-to-ragi swaps, mapped to Indian food composition tables.
10. **Dipper Twin** (hypertension) — predicts nocturnal non-dipping and morning BP surge from sleep, heart rate and a home cuff; what-if on moving the dose to bedtime.
11. **Decompensation Twin** (heart failure) — weight, resting HR, HRV and steps give a 7-day warning of fluid overload.
12. **Over-treatment Twin** — for elderly patients on antihypertensives: predicts orthostatic drops and falls from HR response to standing and step patterns.
13. **AF-Onset Twin** — irregular-rhythm burden from a wrist sensor combined with stroke-risk factors from the record.
14. **Autonomic Twin** — detects cardiac autonomic neuropathy in long-standing diabetes from overnight HRV; flags silent-MI risk.
15. **Heat-Wave Twin** — adds a third stream, local wet-bulb temperature, to drugs in the record (diuretics, SGLT2 inhibitors) and HR drift to predict dehydration and kidney injury.
16. **No-Smartphone Twin** — the twin lives at the clinic; the patient feeds it through missed calls, IVR and a health worker's entries.
17. **Clinic Twin** — a twin of the whole panel, not the patient: who should the clinic phone this week.
18. **Trial-in-a-Box** — twin-generated control arms for Indian diabetes drug trials.
19. **Pregnancy Twin** — gestational diabetes; models the third-trimester insulin-resistance ramp.
20. **Night-Shift Twin** — circadian insulin sensitivity against meal timing for shift workers.

---

## Phase 3 — Convergence & Scoring

N = novelty, T = technical depth, F = feasibility (18 days, open data), V = real-world viability, D = demo power, J = judging fit.

| # | Concept | N | T | F | V | D | J | Σ | Why these numbers |
|---|---|---|---|---|---|---|---|---|---|
| 3 | **Calibrate-Once Twin** | 8 | 8 | 7 | 9 | 9 | 8 | **49** | No entry works sensor-off; real fingersticks exist in Shanghai to test it; the hide-and-reveal is a built-in demo; attacks India's actual cost barrier. |
| 4 | Night Watch | 7 | 7 | 6 | 9 | 7 | 8 | 44 | Hypoglycaemia is a true adverse event and the one where the record matters; open data has few real events to validate on. |
| 5 | Titration Frontier | 7 | 8 | 5 | 8 | 8 | 8 | 44 | Matches the doctor's real decision; dose counterfactuals are hard to validate on observational data. |
| 2 | Rehearsal Twin | 4 | 8 | 7 | 7 | 8 | 9 | 43 | Strong fit, but a polished public entry already does it. Now table stakes. |
| 6 | Upvas Twin | 9 | 6 | 4 | 8 | 8 | 7 | 42 | Most India-specific idea here; zero open fasting data, so it can only be simulation. |
| 7 | Drift Sentinel | 8 | 8 | 5 | 7 | 6 | 7 | 41 | Real twin thinking; needs weeks of data per patient that open sets barely have. |
| 9 | Thali Twin | 5 | 6 | 7 | 7 | 8 | 7 | 40 | Demos well; AMRIT_VIT already ships 47 Indian dishes. |
| 11 | Decompensation Twin | 7 | 7 | 3 | 8 | 6 | 8 | 39 | Classic twin use case, thinly contested lane; no open data at all. |
| 17 | Clinic Twin | 5 | 5 | 7 | 8 | 7 | 7 | 39 | Useful view, shallow problem; better as a screen than a project. |
| 10 | Dipper Twin | 7 | 7 | 3 | 7 | 6 | 8 | 38 | Uncrowded lane; needs continuous BP that no open source gives, and cuffless BP is contested. |
| 8 | Missed-Dose Detective | 7 | 6 | 4 | 7 | 6 | 6 | 36 | Clever; no ground-truth adherence labels anywhere. |
| 19 | Pregnancy Twin | 7 | 6 | 3 | 8 | 6 | 6 | 36 | High need; no data. |
| 16 | No-Smartphone Twin | 7 | 4 | 6 | 8 | 5 | 5 | 35 | Right instinct on access; drops the wearable stream the brief requires. |
| 12 | Over-treatment Twin | 8 | 5 | 3 | 7 | 5 | 6 | 34 | Fresh angle; unvalidatable. |
| 13 | AF-Onset Twin | 4 | 6 | 5 | 6 | 6 | 7 | 34 | Detection is solved by watches; prediction evidence is thin. |
| 15 | Heat-Wave Twin | 9 | 5 | 3 | 6 | 6 | 5 | 34 | Memorable; mostly hand-waved physiology. |
| 14 | Autonomic Twin | 8 | 6 | 3 | 6 | 4 | 6 | 33 | Expert idea; slow outcome, no event to demo. |
| 20 | Night-Shift Twin | 7 | 6 | 4 | 5 | 6 | 5 | 33 | Niche user; weak adverse event. |
| 18 | Trial-in-a-Box | 6 | 7 | 4 | 6 | 3 | 3 | 29 | Wrong user; no doctor, no dashboard. |
| 1 | Spike Sentinel | 1 | 3 | 10 | 3 | 5 | 6 | 28 | What the pile is made of. |

### The argument the panel had before carrying anything forward

**Hackathon Veteran:** Leave diabetes. At least two-thirds of the pile is T2D glucose. A panel choosing five teams for a stage will want variety, and the best cardiovascular entry I can see is a logistic regression. Be the best hypertension twin and take the diversity slot.

**AI/ML Researcher:** With what data? There is no open, download-today dataset pairing wearables with records and events for hypertension or heart failure. We would be validating a simulator against itself, which is precisely the weakness we plan to attack in everyone else.

**Ruthless Critic:** And the T2D lane already contains a team that did the hybrid ODE twin, real validation, Indian dishes and triage. If we build "a better AMRIT_VIT" we are pitch number two of the same idea.

**Domain Expert:** Then stop predicting spikes. A post-meal reading of 190 is not an adverse event; no clinician would chart it as one. And notice what AMRIT_VIT's ablation showed: the record contributes nothing to spike prediction. The fusion in the brief is decorative for that task.

**Founder:** The actual barrier in India is the sensor. Nobody is addressing that.

**Resolution:** Stay in T2D because it is the only lane where claims can be tested on real patients in 18 days. Change the question the twin answers. Carry forward concepts 3, 4 and 5. Concept 2's what-if panel becomes a required component rather than the pitch.

---

## Phase 4 — Deep Dive on Finalists

### Finalist A — Calibrate-Once Twin (working title: **Chhaya**, Hindi for "shadow")

**One-liner.** Wear one glucose sensor once; the twin it trains keeps estimating your glucose for months afterwards from meals, a fitness band and the occasional fingerstick, and tells the doctor when it can no longer be trusted.

**The hook.** On screen: a real patient's week-two glucose trace is hidden. The twin, which has seen only week one, draws its estimate with an uncertainty band from that patient's meals and three fingersticks. Then the real sensor trace is revealed on top. No other team can show this, because every other model takes the sensor as input.

**Target user and scenario.** A diabetologist in a clinic that already applies one professional 14-day sensor to produce a glucose-profile report, a practice that exists in India today **[memory]**. Mrs. R., 58, eleven years of T2D, metformin plus glimepiride, HbA1c 8.6%. She wore a sensor in July. It is now October. She has been logging two fingersticks a week and wears a ₹2,000 band. The doctor has four minutes and must decide whether to raise the glimepiride. Today that decision rests on one HbA1c value.

**Core mechanism.**

1. **Ingest.** Static record as FHIR-shaped JSON: age, sex, BMI, diabetes duration, HbA1c, fasting glucose/insulin/C-peptide, eGFR, medication list. Dynamic: CGM during calibration; meal log (time, carbohydrate, protein, fat, fibre); band (heart rate, steps or METs, sleep); fingersticks.
2. **Physiological core.** A compact glucose–insulin ODE of the E-DES family: gut absorption compartments → plasma glucose; **endogenous insulin secretion that responds to glucose** (the piece T1D twins lack); an insulin-action compartment; hepatic glucose output with a circadian term; an exercise term driven by METs or heart rate; drugs as parameter modifiers, with sulfonylurea effect scaled by eGFR.
3. **Fusion as Bayes, not concatenation.** About seven parameters are patient-specific (insulin sensitivity, beta-cell responsiveness, basal output, gastric emptying, dawn amplitude, exercise sensitivity, meal-logging bias). **The record sets the prior** — HOMA-IR from fasting glucose and insulin shifts the insulin-sensitivity prior, C-peptide shifts beta-cell function, HbA1c shifts basal glucose. **The sensor fortnight is the evidence** that turns prior into posterior. Static data is the prior, dynamic data is the likelihood. That one sentence is the whole fusion story.
4. **Calibration.** Per-patient posterior via MAP plus an ensemble (upgrade to MCMC in NumPyro if time allows).
5. **Sensor-off running.** The parameter ensemble is simulated forward on logged meals and band activity. Each fingerstick is an observation that corrects the state through an ensemble Kalman update. The band widens between fingersticks and tightens at each one.
6. **Events.** From the ensemble: probability of exceeding 180 mg/dL after a logged or habitual meal in the next two hours; probability of going below 70 overnight. Checked with a reliability diagram.
7. **Staleness.** A running test on fingerstick surprises. When reality keeps landing outside the band, the dashboard says "re-calibrate — wear a sensor again" and names which parameter appears to have moved.
8. **Dashboard.** Clinic list → patient page: reconstructed 90-day daily profile with band, estimated GMI (3.31 + 0.02392 × mean glucose **[verified]**) beside the last lab HbA1c, an hour-of-day risk strip, a what-if panel, and a "last calibrated N days ago / confidence" badge.

**MVP scope.** The reveal experiment on real data: calibrate on the first *k* days, hide the rest, report error against the hidden sensor as a function of *k* and of fingersticks per day. One patient page.

**Stretch / wow.** (a) Fusion measured in sensor-days: "with the record as prior, 3 days of sensor gets the accuracy that needs 7 without it" — to be tested, not assumed. (b) CGMacros participants wore two sensors at once, so the disagreement between two physical sensors is a real noise floor to plot the sensor-less twin against. (c) Staleness detection. (d) Fasting-day simulation as a labelled, unvalidated scenario.

**Architecture.** Python 3.12; NumPy/SciPy ODE core (JAX + NumPyro optional); LightGBM for the sensor-on baseline; Synthea for the record shell and extra synthetic patients; FastAPI serving pre-computed twins from Parquet; Streamlit + Plotly for Phase 1; Docker Compose; pytest. Data: ShanghaiT2DM and CGMacros via download scripts — never redistributed, since CGMacros is non-commercial share-alike.

**Why it's different.** Every entry in Phase 0 takes CGM as model input and dies when the sensor is removed. A gradient-boosted model on CGM lags cannot do this at all; a mechanistic twin can, which is the actual reason to build one. January AI proves the idea is feasible, but it is closed, American, consumer-facing and not built for medicated T2D.

### Finalist B — Night Watch

**One-liner.** Every evening the twin tells the doctor's dashboard which medicated patients are likely to go low tonight, and why.

**Hook.** Two patients with the same evening glucose trace and the same dinner. One is 45 on metformin; the other is 68 with eGFR 42 on a sulfonylurea. Only the second twin dips below 70 at 3 a.m.

**User and scenario.** A physician with elderly patients on sulfonylureas or insulin — the most frequently prescribed class in Indian geriatric T2D prescriptions, with metformin + glimepiride the most common combination **[verified]**.

**Mechanism.** Same ODE core. The record enters as mechanism: eGFR lengthens drug action, age and duration blunt counter-regulation. Afternoon activity from the band raises overnight uptake. Output is a calibrated overnight probability at 9 p.m. plus a what-if (bedtime snack, halve the evening dose).

**MVP.** Night-level classifier on Shanghai (roughly a thousand patient-nights) compared against "was low last night" and a LightGBM baseline.

**Stretch.** T1D cohorts (HUPA-UCM) as a secondary check that band signals help.

**Why different.** It is the one adverse event where the record changes the answer, which is what the brief's fusion requirement is really asking for.

### Finalist C — Titration Frontier

**One-liner.** Before changing a dose, the doctor sees each option as a point on a benefit-versus-hypo-risk curve computed on that patient's twin.

**Hook.** Drag glimepiride from 1 mg to 2 mg: time in range rises nine points and nights-with-a-low goes from one a month to five. Drag to "add evening walk" instead: nearly the same gain, no extra lows.

**User and scenario.** The four-minute consult above.

**Mechanism.** Twin simulates 14 days of the patient's habitual meals and activity under each option, with parameter uncertainty; plots time-in-range against time-below-range.

**MVP.** Three or four options on one patient.

**Why different.** Others show a single what-if curve for a single meal. This shows the trade-off across a regimen.

---

## Phase 5 — Red Team

### Finalist A — Calibrate-Once Twin

| Objection | Attack | Response |
|---|---|---|
| **Judge** | "Another glucose twin. I've seen thirty." | The headline never says glucose prediction. It says "the twin that works after the sensor comes off" and opens on the reveal. Do not name it anything containing Gluco or Glyco. |
| **Critic** | "Sensor-off accuracy will be poor and you're hiding it." Also: "January AI did this." | **Real weakness.** Nobody knows the number until it's run. Set the pass bar in advance and publish whatever comes out, including the curve of error against fingersticks per day. A mediocre honest number on real patients is still a result no competitor has. On January: closed, US, wellness users with flat glucose; ours is open, physician-facing, medicated T2D. |
| **Critic** | "Who pays?" | A clinic that already charges for one sensor report sells a 90-day follow-up on the same sensor. The patient pays once. Happiest Health runs endocrinology clinics. |
| **Engineer** | "Fitting ODEs live on stage will hang." | Nothing is fitted live. All twins are pre-computed to Parquet; the reveal is a toggle over cached arrays. The app runs offline. Ship a recorded fallback. |
| **Domain Expert** | "Indian patients on tablets fingerstick 2–3 times a **week**, not twice a day **[verified]**. And they won't log meals." | Sweep fingerstick frequency down to zero and report the weekly-testing case explicitly. For meals, learn a habit model from the sensor fortnight (usual times and sizes) so the twin runs on "ate as usual" plus exceptions. Say plainly that accuracy degrades with logging quality. |
| **Domain Expert** | "Shanghai patients look like monitored, treated, possibly inpatient cases; physiology shifts as treatment changes." | Acknowledge. Use the seven patients with repeat recordings as a small real test of whether a twin from period one still fits period two. |
| **Domain Expert** | "Chinese and American data, not Indian." | True and unfixable in 18 days; no open Indian CGM set exists. State it, and note that Shanghai's rice-based diet and lower-BMI T2D are closer to India than US cohorts **[memory]**. |
| **Ethics** | An estimated curve could be read as a measurement and dosed on. | Never draw the line without the band; label it "estimated"; doctor-facing only; no dose recommendations, only simulations; low-glucose alerts tuned toward sensitivity; staleness badge always visible. |

### Finalist B — Night Watch

| Objection | Attack | Response |
|---|---|---|
| Judge | Narrow; sounds like an alarm feature. | Fair. It is a strong module and a weak headline. |
| Critic | Real overnight lows on sulfonylureas in open data may number only dozens. | **Real weakness, probably fatal as a standalone.** Count the events on day one. |
| Engineer | None serious; it's batch. | — |
| Domain Expert | Libre sensors over-read lows from compression during sleep **[memory]**. | Require sustained lows of 15+ minutes; say so. |
| Ethics | A false "safe tonight" is dangerous. | Report sensitivity at a fixed alert budget; never display "safe", only "no elevated risk detected". |

### Finalist C — Titration Frontier

| Objection | Attack | Response |
|---|---|---|
| Judge | Lovely chart. Is it true? | — |
| Critic | Dose counterfactuals cannot be validated on observational data. The drug-effect sizes are literature constants. | **Real weakness.** Only partial check: Shanghai records dose changes with timestamps, so within-patient before/after may exist. Otherwise label as simulation. |
| Engineer | Fine if pre-computed. | — |
| Domain Expert | Recommending doses crosses into regulated device territory. | Present as simulation of options the doctor entered, never a suggestion. |
| Ethics | Automation bias. | Show uncertainty on both axes. |

---

## Phase 6 — Verdict

### The pick: the Calibrate-Once Twin ("Chhaya")

**The single sharpest reason:** every other team's twin stops existing the moment the CGM comes off, and in India the CGM comes off after 14 days because it costs ₹4,200 a time. This is the only concept whose central claim is about that fact, and the only one that can prove its claim with a hide-and-reveal on real patients.

The second reason is structural. Sensor-off operation is something a mechanistic twin can do and a boosted-tree forecaster cannot. That gives a real answer to "why is this a twin and not a classifier?", which the brief's own definition demands.

### Runner-up: Night Watch

Lost because the open data probably contains too few real overnight lows on sulfonylureas to validate it. It is kept as the safety module inside the pick, and it is the fallback pitch if the sensor-off numbers come out unusable.

### Judging-criteria map (rubric inferred, not published)

| Likely criterion | How the pick meets it | Honest gap |
|---|---|---|
| Fusion of static + dynamic streams | Record sets the Bayesian prior, sensor and band update it; fusion value reported in sensor-days saved | The saving might turn out small; report it either way |
| Working model predicting an adverse event ahead of time | Post-meal >180 and overnight <70 probabilities, sensor-on and sensor-off, with calibration plots | Sensor-off event accuracy is unknown until run |
| Doctor dashboard | Reconstructed 90-day profile, confidence badge, risk strip, what-if | Streamlit looks like everyone's; custom front end only if shortlisted |
| Data-rule compliance | Open and synthetic only; download scripts; licences stated | CGMacros is non-commercial |
| Technical rigour | Real-patient validation, patient-wise splits, baselines, pre-stated pass bar, limitations | Small cohorts |
| India impact | Cost barrier, low fingerstick rates, clinic workflow, Indian foods | No Indian data |
| Documentation | README, architecture PDF, deck, 20-minute video, licence | Video is a big time cost |

### Build roadmap — a working demo exists at every checkpoint

| Days | Stage | Output | Gate |
|---|---|---|---|
| 1–2 (Oct 3–4) | **Data truth** | Both datasets loaded; meals converted to macros; counts of patients, days, fingersticks, low events | **Go/no-go 1:** are Shanghai's food records usable for ≥60 patients? If not, CGMacros becomes primary. |
| 3–6 | **Core** | ODE twin fitted per patient on CGMacros; sensor-on forecast vs persistence and LightGBM; first reveal plot | **Go/no-go 2 (Oct 8):** does sensor-off beat "patient's own average daily curve"? If not, switch headline to Night Watch on the same engine. |
| 7–10 | **Enhanced** | Fingerstick updates on Shanghai; record-as-prior experiment; calibration plots; dashboard with reveal toggle | Demoable end to end |
| 11–13 | **Stretch** | Staleness detector; two-sensor noise floor; what-if with Indian dishes; fasting scenario (labelled simulation) | Drop anything not done by Oct 15 |
| 14–17 (Oct 16–19) | **Polish** | README, architecture PDF, deck, 20-minute video, clean clone-and-run, tests | Feature freeze Oct 15 |
| 18 (Oct 20) | Submit by noon | — | Seven hours of slack before 7 PM |

### Kill list

1. **Sensor-off accuracy is useless.** Defuse now: define the pass bar before running anything (suggest: beats the patient's own average-day curve, and estimated time-in-range within 10 points of truth). Hold the Oct 8 gate honestly.
2. **It reads as "GlucoTwin number six".** Defuse now: the name, the README's first screen and the video's first minute are all the reveal. Spike forecasting appears only as a baseline table.
3. **Feature sprawl eats the documentation.** The video alone is 20 minutes of scripted content. Defuse now: feature freeze on Oct 15 is not negotiable; stretch items are cut, not rushed.

### Demo narrative (20-minute video)

| Minutes | Beat |
|---|---|
| 0:00–1:00 | **Hook.** "A glucose sensor in India costs ₹4,200 and lasts 14 days. Then it falls off, and every digital twin goes blind." The reveal: hidden trace, twin's estimate, real trace laid on top. |
| 1:00–3:00 | Mrs. R. and the four-minute consult. What the doctor has today: one number. |
| 3:00–7:00 | Dashboard walkthrough: 90-day reconstructed profile, confidence badge, risk strip, a what-if. |
| 7:00–12:00 | How it works: record as prior, sensor as evidence, band and fingersticks as upkeep. Architecture diagram. |
| 12:00–16:00 | **Technical highlight:** results on real patients — error vs calibration days, error vs fingersticks, the two-sensor noise floor, where a plain LightGBM beats us and why that's fine. |
| 16:00–18:00 | Limitations, stated plainly. Staleness alarm as the safety answer. |
| 18:00–20:00 | Impact close: one sensor, once; what a clinic pilot would look like. |

---

## Appendix — Submission-Ready Brief

**Title.** Chhaya — a Type 2 diabetes digital twin that keeps working after the glucose sensor comes off.

**Problem.** India has an estimated 101 million people with diabetes. A continuous glucose sensor costs about ₹4,200 for 14 days, so almost no one with T2D wears one continuously, and patients on tablets test by fingerstick only two or three times a week. Doctors titrate drugs — often sulfonylureas, which can cause dangerous lows — on a three-monthly HbA1c with no view of daily glucose. Existing digital twins assume a sensor that is always on.

**Proposed solution.** A patient wears one sensor once. During those 14 days, a physiological glucose–insulin model is personalised to them, starting from their health record and refined by sensor data. After the sensor is removed, the twin continues to estimate glucose from logged meals, fitness-band activity and sleep, and occasional fingersticks, always with an uncertainty band. It forecasts post-meal highs and overnight lows, lets the doctor test changes on the virtual patient, and raises a flag when its estimates stop matching fingersticks and a fresh sensor is needed.

**Innovation and uniqueness.** (1) Sensor-off operation, validated by hiding real sensor data and revealing it against the twin's estimate. (2) Fusion done as Bayesian inference — the record is the prior, wearable data is the evidence — with the value of the record measured in sensor-days saved. (3) A twin that reports its own staleness. Public entries to this challenge all require continuous CGM input and validate what-ifs on synthetic data only.

**Technical approach.** Compact T2D glucose–insulin ODE with endogenous insulin secretion, circadian hepatic output, exercise and drug terms. Per-patient parameter posterior from record-informed priors plus sensor data. Ensemble forward simulation with Kalman-style correction at each fingerstick. Event probabilities from the ensemble, checked for calibration. Gradient-boosted sensor-on forecaster as baseline. Validation on ShanghaiT2DM (100 patients; sensor, fingersticks, drugs, labs) and CGMacros (45 participants; two sensors, Fitbit, meal macros), with Synthea for record structure. Python, FastAPI, Streamlit, Docker.

**Feasibility and viability.** Both datasets are open and downloadable today. All twins are pre-computed, so the demo runs offline. The workflow extends one many Indian clinics already offer — a one-time professional sensor report — from 14 days of insight to 90. No new hardware beyond a low-cost band and the patient's existing glucometer.

**Impact and benefits.** For patients: one sensor purchase instead of twenty-six a year, and earlier warning of lows. For doctors: a daily glucose picture at every visit, not a single number. For clinics: a follow-up service on an existing sensor. For the field: an open, reproducible test of how far a twin can go without continuous sensing. Limits are stated: validated on Chinese and US cohorts, small samples, research prototype, not for dosing.

---

## Open items to confirm

- Ask the organisers: top 10 or top 5 after Phase 1? Is "minimum 20-minute video" correct? Is there a scoring rubric?
- Day-1 data check on Shanghai's food records and the number of real low-glucose events.
- Recheck every **[memory]** item before it appears in the deck.

## Sources checked today

Competitor repos: [AMRIT_VIT](https://github.com/shashi-bhushan-27/digitalTwinChallenge) · [AlgoAura GlucoTwin](https://github.com/Nishu15205/AlgoAura_MERI-College-of-Engineering-and-Technology) · [GlycoTwin (VIT Bhopal)](https://github.com/Abhi4621/GlycoTwin) · [ChipUP](https://github.com/reshureshumii/ChipUP_DigitalTwinChallenge) · [RUSHI-KOLLA GlucoTwin](https://github.com/RUSHI-KOLLA/Digital-Twin-Challenge) · [CardioTwin India](https://github.com/Nikunj-Shah00000/Digital-Twin-Challenge-2026) · [BioTwin Omni](https://github.com/deepshekhar555/HappiestHealth-DigitalTwin-2026)

Data: [ShanghaiT2DM paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC9849330/) · [CGMacros on PhysioNet](https://physionet.org/content/cgmacros/1.0.0/) · [HUPA-UCM](https://pmc.ncbi.nlm.nih.gov/articles/PMC11214197/) · [D1NAMO](https://explore.openaire.eu/search/dataset?pid=10.5281/zenodo.1421615)

Landscape: [Twin Health RCT, 18-month results](https://diabetesjournals.org/diabetes/article/73/Supplement_1/20-OR/154875/20-OR-Digital-Twin-DT-Technology-in-Type-2) · [Twin Health hypertension RCT](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11450914/) · [January AI virtual CGM white paper](https://blog.january.ai/blog/white-paper-virtual-blood-glucose-monitoring-prediction-machine-learning) · [ReplayBG](https://github.com/gcappon/py_replay_bg) · [E-DES in BioModels](https://www.ebi.ac.uk/biomodels/MODEL2403070001) · [Frontiers review of diabetes twins, 2026](https://www.frontiersin.org/journals/endocrinology/articles/10.3389/fendo.2026.1919404/full)

India context: [ICMR-INDIAB-17](https://researcher.manipal.edu/en/publications/metabolic-non-communicable-disease-health-report-of-india-the-icm/) · [CGM pricing in India 2026](https://medstuffs.com/cgm-price-in-india-2026-freestyle-libre-best-brands/) · [SMBG usage in India](https://www.valueinhealthjournal.com/article/S1098-3015(14)02726-0/fulltext) · [Geriatric T2D prescribing in India](https://pmc.ncbi.nlm.nih.gov/articles/PMC13032815/) · [GMI formula](https://diabetesjournals.org/care/article/41/11/2275/36593/Glucose-Management-Indicator-GMI-A-New-Term-for) · [Happiest Health clinics launch](https://aninews.in/news/business/happiest-health-announces-launch-of-speciality-clinics-happiest-paediatrics-happiest-orthopaedics-happiest-gynaecology-happiest-endocrinology-amp-your-personal-physician20260709163401/)
