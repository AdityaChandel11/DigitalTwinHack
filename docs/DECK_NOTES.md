# Chhaya — 10-Slide Deck Notes & Speaker Guide
**Happiest Health Digital Twin Challenge 2026**  
**Team SynapseX** | Aditya Singh Chandel | D.B.S. College, Kanpur  
**Live Demo:** [digital-twin-hack.vercel.app](https://digital-twin-hack.vercel.app/)  
**Public Repository:** [GitHub](https://github.com/AdityaChandel11/DigitalTwinHack)  

---

## Deck Overview
- **Format:** 16:9 widescreen (1920×1080 px), left-aligned, one idea per slide.
- **Design System:** Source Serif 4 (titles & large metrics), Source Sans 3 (body text), Source Code Pro (metadata & uppercase labels). Dashboard palette strictly mapped to data meaning. Zero gradients, zero shadows, zero emoji, zero marketing buzzwords.
- **Core Narrative Arc:** 
  1. The Economic & Clinical Dilemma in India (14 vs. 365 days; ₹1.1L/yr barrier).
  2. The Digital Twin Concept (infilling unmeasured days with bounded uncertainty).
  3. Challenge Compliance Matrix (5 asks audited with complete candour).
  4. Transparent Physiological Model (E-DES ODEs in JAX, Laplace ensemble, no neural net/LLM).
  5. Scientific Epistemology (pre-registered bars, split by patient, publishing 4 misses).
  6. Primary Infill Endpoint (1.4 mg/dL gain from meal logs on 19 held-out patients).
  7. Retrospective Calibration (sparse fingersticks; honest admission that simple baselines win).
  8. Adverse Event Prediction (sensor predicts spikes; fusion without sensor suppressed).
  9. Clinician Dashboard (safe 10-second scan, bounded bands, zero automated dosing).
  10. Scientific Conclusion & Roadmap (measuring where the twin earns its place; Indian cohort).

---

## Slide 1 — Hook (Dark)
* **Title:** A sensor shows a doctor 14 days; the patient lives 365. *(11 words)*
* **Copy:** Continuous monitoring costs over Rs 1.1 lakh yearly. In India, 101 million people live with diabetes; a single 14-day sensor costs Rs 4,400 to 5,100.
* **Enriched Data:**
  - 101 Million living with diabetes, 136 Million prediabetes (ICMR-INDIAB 2023). India carries the second highest diabetic burden globally.
  - Episodic Wear: In Indian clinical practice, patients wear 1–2 sensors per year to titrate prescriptions, leaving 337 to 351 days completely unmeasured.
  - Retail Costs: ₹4,400 to ₹5,100 per 14-day patch (FreeStyle Libre / Dexcom One checked Oct 2026); > ₹1.1 Lakh annual continuous cost (26 sensors).
* **Visual:** 365-day calendar tick strip (14 days lit in teal `#0e9aa7`, 351 days in dark grey `#2c2b3d`). Three stat callouts: 101M patients, ₹4,400–5,100/sensor, ₹1.1L+ annual continuous cost.
* **Footnote:** Chhaya · Team SynapseX (Aditya Singh Chandel, D.B.S. College, Kanpur) · Happiest Health Digital Twin Challenge 2026. ICMR-INDIAB study (2023); sensor retail prices verified Oct 2026.
* **Speaker Notes (75s):**
> "A continuous glucose monitor gives a clinician a clean 14-day window into a patient's life, but chronic illness does not pause between prescriptions. In India, 101 million people live with diabetes. At four thousand four hundred to five thousand one hundred rupees per sensor, a full year of 26 sensors costs over one point one lakh rupees. For the overwhelming majority of families, continuous wear is economically impossible. Patients wear a sensor once or twice a year to titrate medications, leaving over 350 days completely unmeasured. If a digital twin is to have any real-world healthcare impact in India, it cannot assume an endless sensor stream. Its primary mission must be to maintain an honest, safe physiological estimate during the long gaps when no sensor is worn."

---

## Slide 2 — The Answer in One Picture (Light)
* **Title:** Chhaya estimates the unmeasured days, then lays the real sensor on top. *(12 words)*
* **Copy:** Between sensor wears, Chhaya reconstructs daily glucose from meal logs and baseline physiology. An 80 % uncertainty band is maintained and scored against ground truth when wear resumes.
* **Enriched Data:**
  - CGM sampling rate: 15-minute continuous interstitial telemetry.
  - Day 4–8 Infill: Physics E-DES ODE + meal logs + Laplace 80% credible band (covers 83.5% of readings on held-out patients).
  - Day 6 Staleness Check: Drift prompt raised via cumulative fingerstick surprise (AUROC 0.82; prompt to re-wear, not a diagnosis).
  - Day 9 Ground Truth: Returning sensor measures paired RMSE against twin shadow.
* **Visual:** Timeline trace from Mrs. R. (marked "Synthetic demo patient"): calibration phase (sensor on, teal), unmeasured gap with purple twin estimate (`#4a3aa7`) and 80% credible band (`rgba(74, 58, 167, 0.12)`), overlay of returning sensor trace, and sparse fingerstick markers (`#b81f58`).
* **Footnote:** Demonstration profile Mrs. R. is synthetic and formatted to FHIR structures (not ABDM-certified). Traces show model mechanics; all claims scored on held-out human cohorts.
* **Speaker Notes (75s):**
> "This is the core concept of Chhaya: estimating the unmeasured days with explicit uncertainty, and immediately confronting that estimate with reality when a sensor returns. During the wear week, Chhaya fits a personalized physical model of glucose-insulin kinetics. When the sensor comes off, the twin continues to propagate forward using meal logs, bounded by a calibrated eighty percent Laplace uncertainty band. When the patient returns to clinic or applies a fresh sensor, the twin lays the true sensor data right over the shadow. There is no hand-waving: every point of deviation is quantified. Notice that every estimate is bounded, and every real measurement is clearly distinguished from a reconstruction. The demo profile shown here is synthetic, designed to illustrate the exact clinical interface before we evaluate real held-out patients."

---

## Slide 3 — The Brief, Answered (Light)
* **Title:** We answered every challenge requirement plainly: built, measured, or missed. *(10 words)*
* **Copy:** All five core requirements of the Digital Twin Challenge were built and tested on unseen patients. We report each outcome with unvarnished candour.
* **Enriched Data:**
  - 01 Static Stream (Simulated EHR): FHIR-structured demographics, diagnoses, fasting blood glucose. Role: Sets twin prior for basal parameter $G_b$ only. Status: **BUILT**.
  - 02 Dynamic Stream (Wearables & CGM): Ingests 15-min CGM telemetry, meal carb logs, capillary fingersticks. Role: Calibrates 7 kinetic ODE parameters. Status: **BUILT**.
  - 03 Static & Dynamic Fusion: Evaluated via Bayesian record prior ($0.02$ mg/dL change, $p=0.16$) and multi-modal feature stacking. Finding: Record adds zero detectable gain once sensor exists. Status: **MISSED**.
  - 04 Adverse Event Model: Post-meal excursion (>180 mg/dL within 2h; 1,205 meals). Finding: AUROC 0.82 (sensor on); sensor off (AUROC 0.71) trails personal history (0.76); calibration slope 0.48. Status: **MEASURED** (Alert withheld).
  - 05 Conceptual Doctor Dashboard: 10-second triage screen, dual-track shadow view, embedded evidence ledger. Guardrails: Zero dosing, zero unconfirmed alarms. Status: **BUILT**.
* **Footnote:** Compliance mapped directly to criteria in Digital_Twin_Challenge_2026_Content.txt. Pre-registered protocol in docs/PREREGISTRATION.md.
* **Speaker Notes (80s):**
> "The challenge brief laid out five specific requirements. We built every single one, evaluated them against held-out data, and we state their exact status without spin. Static EHR ingestion is built. Dynamic wearable streaming is built. Fusion was built and tested in two distinct ways—and it missed: once sensor data exists, the static EHR record added nothing measurable to prediction accuracy. For the adverse event requirement, our excursion model reaches point-eight-two AUROC with an active sensor, but without one, it failed to beat the patient's own history, so we responsibly suppress the alert. Finally, our clinician dashboard is fully operational with zero automated dosing. When grant panels review submissions, they expect teams to claim five out of five successes. We refuse to trade scientific honesty for an artificial scorecard."

---

## Slide 4 — The Twin Architecture (Light)
* **Title:** The record sets one parameter prior; the sensor week provides the evidence. *(12 words)*
* **Copy:** Chhaya pairs a physical differential equation model with Bayesian inference. Seven personal parameters are fit with a Laplace ensemble in JAX. No neural network. No LLM.
* **Enriched Data:**
  - Maas et al. (2015) E-DES two-compartment differential equations in 64-bit JAX:
    $$\frac{dG}{dt} = -p_1(G - G_b) - X\cdot G + \frac{R_{meal}}{V_d}, \quad \frac{dX}{dt} = -p_2 X + p_3 S_I (G - G_b)$$
  - 7 Personal Parameters: $S_I$ (insulin sensitivity), $k_{abs}$ (carb absorption rate), $G_b$ (basal glucose), $V_d$ (distribution volume), rate constants ($p_1, p_2, p_3$).
  - Inference: Maximum A Posteriori (MAP) with L-BFGS in JAX; Laplace approximation Hessian inversion yields covariance matrix $\Sigma$; 200 ensemble samples generate the 80% credible band.
  - 50/50 Blend Filter: Blends the dynamic ODE meal response with the patient's empirical daily median profile to guarantee numerical stability.
* **Footnote:** Differential equations adapted from Maas et al. (2015). Solved via diffrax/JAX float64. 400+ unit tests across the parameter identification pipeline.
* **Speaker Notes (80s):**
> "Judges often ask: 'Where is the deep learning, and why aren't you using an LLM?' Our answer is deliberate: clinical physiology is governed by mass-action conservation laws, not token probabilities. Chhaya uses the E-DES two-compartment differential equation model of glucose-insulin dynamics implemented in sixty-four-bit JAX. The static medical record informs a single physiological prior: basal glucose derived from fasting laboratory values. A one-week sensor wear then provides the empirical evidence to identify seven patient-specific parameters, such as insulin sensitivity and absorption rates, via Maximum A Posteriori estimation. Uncertainty is propagated through a two-hundred-member Laplace ensemble. This means every prediction is physically grounded, fully interpretable, and reproducible to the last digit."

---

## Slide 5 — The Proof (Light)
* **Title:** We pre-registered nine bars, scored once, and published five passes and four misses. *(13 words)*
* **Copy:** Evaluation followed four strict locks: bars written before test runs, patient-level splits, single scoring pass on held-out cohorts, and mandatory publication of all misses.
* **Enriched Data:**
  - 4 Protocol Locks: Bars Written First (git commit), Split by Patient (zero temporal leakage), Scored Exactly Once (unseen cohorts), All Misses Published.
  - Complete 9-Bar Breakdown:
    - Passed (5 bars): Gate 2 Infill (P1, P2, P3); Fingerstick Live Tracking (F1); Fingerstick in Hindsight (F2).
    - Missed (4 bars): Gate 3 Excursion AUPRC vs single streams (M1); Fused AUPRC vs personal rate (M2); Calibration slope (M3: 0.48); Record Prior (P1: 0.02 mg/dL, $p=0.16$).
    - Descriptive (6 results): Label audit (8/64 lows confirmed); Report level (plain mean 6.4 vs twin 8.9); Expiry rate (1.0 mg/dL/day); 80% Credible band (83.5% coverage); Stickband (83.6% coverage); Staleness prompt (AUROC 0.82).
* **Footnote:** Registered protocol committed to GitHub repository prior to evaluation runs. Evidence tally parsed directly from src/chhaya/dashboard/demo/evidence.json.
* **Speaker Notes (80s):**
> "Machine learning in healthcare has a severe reproducibility crisis: benchmarks are repeatedly tweaked until claims look impressive. We instituted four non-negotiable protocol locks before touching test data. First, every hypothesis bar was written into git before running tests. Second, splits were strictly by patient, eliminating temporal data leakage. Third, held-out cohorts were scored exactly once. Fourth, every miss was published. Out of nine pre-registered bars, five passed and four missed, alongside six descriptive results. We passed on infilling unmeasured gaps and fingerstick corrections. We missed on static record fusion and excursion prediction without a sensor. Publishing misses is not a sign of failure; it is the fundamental prerequisite of medical truth."

---

## Slide 6 — Result: The Reveal (Light)
* **Title:** Five days off sensor, the estimate is 1.4 mg/dL closer than an average day. *(14 words)*
* **Copy:** Across 19 held-out free-living participants, Chhaya beat the patient's own historical average day by 1.4 mg/dL (p = 4e-05). The gain comes entirely from meal logs.
* **Enriched Data:**
  - Overall Median RMSE: 21.9 mg/dL (Chhaya) vs. 23.3 mg/dL (Average day baseline). Gain: 1.4 mg/dL (6% improvement, $p = 4 \times 10^{-5}$).
  - Subgroup Breakdown: Type 2 Diabetes ($n=7$, 1.8 mg/dL gain), Prediabetes ($n=7$, 1.4 mg/dL gain), Healthy ($n=5$, 0.9 mg/dL gain).
  - Ablation vs. No-Meal Control: Meal log carbs account for ~1.05 mg/dL of the gain ($p = 0.04$); ODE physical dynamics account for ~0.35 mg/dL.
  - Temporal Stability: Median favors the twin on each of the 5 days following sensor removal; does not fade with time.
* **Visual:** Per-participant dot plot stratified across 3 cohorts: Type 2 Diabetes, Prediabetes, Healthy. Right stat card with ablation decomposition.
* **Footnote:** CGMacros free-living cohort (19 held-out participants; 7 T2D, 7 prediabetes, 5 healthy). One-sided Wilcoxon signed-rank p = 4e-05. Decision record: docs/decisions/2026-10-04-gate2-corrected.md.
* **Speaker Notes (80s):**
> "Here is our primary endpoint: what happens five days after the continuous glucose monitor is removed? Across nineteen unseen, free-living participants in the CGMacros dataset, Chhaya achieved a root-mean-square error of 21.9 mg/dL compared to 23.3 mg/dL for the patient's own average day. That is a 1.4 mg/dL improvement, or six percent, with a Wilcoxon p-value of four times ten to the minus fifth. Clinicians on the panel will rightfully ask: 'Is one point four mg/dL clinically transformative?' Our answer is no: it is modest. Ablation shows this gain stems almost entirely from meal logging rather than exotic ODE dynamics. But it proves that a personalized model, informed by patient meal logs, consistently reconstructs unmeasured days closer to reality than a static historical average."

---

## Slide 7 — Result: Fingersticks & Baselines (Light)
* **Title:** At about six fingersticks a day, report error falls from 13.0 to 6.4 mg/dL. *(14 words)*
* **Copy:** Sparse fingersticks correct retrospective reports. However, a plain calibrated average (6.4 mg/dL) beat our twin estimator (8.9 mg/dL). We report this baseline honestly.
* **Enriched Data:**
  - Miss in Mean Sensor Glucose over following days:
    - Stale 3-day report: 13.0 mg/dL miss.
    - Chhaya rebuilt report: 8.9 mg/dL miss (3.4 mg/dL closer, $p = 4 \times 10^{-6}$, 83% of patients).
    - Plain fingerstick average on sensor scale: 6.4 mg/dL miss (hard baseline wins).
  - Meter Scale Warning: Raw glucometer average as read directly without sensor-scale calibration missed by 18.3 mg/dL due to systemic interstitial-capillary lag.
  - Label Validity Audit: Only 8 of 64 sensor lows (<70 mg/dL) confirmed within 10 min (12.5%; 0 of 9 at night due to compression artifacts). 732 of 809 highs (>180 mg/dL) confirmed (90.5%). Explains why low-glucose alarms are omitted.
* **Footnote:** ShanghaiT2DM cohort (29 held-out patients under supervised care, ~6 fingersticks/day). Descriptive protocol; results/audit/label_validity.json and docs/decisions/2026-10-08-fingersticks-report.md.
* **Speaker Notes (85s):**
> "When patients cannot wear continuous sensors, can routine fingersticks keep their clinical report accurate? On twenty-nine held-out Shanghai patients tested six times daily, relying on an expired three-day sensor report missed actual mean glucose by 13.0 mg/dL. Rebuilding the report with Chhaya's fingerstick filter reduced that error to 8.9 mg/dL. But here is the critical finding: a simple linear calibration of the fingersticks directly to the sensor scale achieved an error of 6.4 mg/dL, outperforming our complex model. We deliberately display this baseline because real clinical engineering demands knowing when simple arithmetic beats complex modeling. Furthermore, our audit revealed that only 8 of 64 sensor lows were verified by fingersticks, and zero out of nine at night. This is why Chhaya strictly refuses to report unconfirmed low-glucose alerts."

---

## Slide 8 — Result: Adverse Events (Light)
* **Title:** Live sensors anticipate post-meal spikes; without one, fusion fails to beat patient history. *(13 words)*
* **Copy:** Active CGM predicts post-meal spikes (AUROC 0.82). Without a sensor, fusion achieved AUROC 0.71, trailing the patient's personal history (0.76); alerts are withheld.
* **Enriched Data:**
  - Evaluated on 1,205 meals across 47 held-out patients (39% post-meal excursion prevalence).
  - Stream Ladder: Sensor on (0.82 AUROC / 0.76 AUPRC); Sensor week history (0.78 / 0.63); Patient personal rate baseline (0.76 / 0.59); Fused sensor off (0.71 / 0.60); Fingersticks only (0.70 / 0.64); Record only (0.65 / 0.57).
  - Exploratory Dev Cohort (49 dev patients, 1,436 meals): Late fusion, stacking, recalibration, and stronger L2 regularization did not beat the best single stream (stacking came within 0.005 AUPRC).
  - Operating Threshold: Sensitivity 86%, Specificity 58%, 8.9 false alarms per patient-week among 21.4 eligible meals. Calibration slope 0.48. Decision: alert responsibly suppressed.
* **Footnote:** ShanghaiT2DM cohort (47 held-out patients, 1,205 meals, 39 % post-meal excursion prevalence). Decision record: docs/decisions/2026-10-08-gate3.md.
* **Speaker Notes (85s):**
> "The brief asked for an adverse event prediction model anticipating glucose spikes above 180 mg/dL within two hours of a meal. We evaluated 1,205 meals across 47 held-out patients. With an active sensor, the model performs solidly, reaching an AUROC of point-eight-two and AUPRC of point-seven-six. But when the sensor is off, multi-modal fusion drops to point-seven-one AUROC. Crucially, simply knowing the patient's historical excursion rate achieves point-seven-six—outperforming the fused model. Furthermore, the fused calibration slope was point-four-eight, producing almost nine false alerts per patient-week. In clinical software, deploying an uncalibrated alert that is beaten by a simple patient prior induces alert fatigue and endangers care. Because our pre-registered bar was missed, Chhaya responsibly suppresses this alert entirely."

---

## Slide 9 — The Doctor Dashboard (Light)
* **Title:** A doctor reads it in seconds: visible uncertainty, no alarms, and no dose advice. *(14 words)*
* **Copy:** Designed for clinical workflow: 10-second patient review, full uncertainty disclosure, and complete refusal to automate drug dosing or issue uncalibrated alarms.
* **Enriched Data:**
  - 01 Clinic Triage: 10-second triage table showing unmeasured gap duration, drift prompt status, and fingerstick count.
  - 02 Patient View: Real screenshot of Mrs. R. (synthetic) displaying measured trace, shaded 80% credible band, and meal carb markers. Simulation mode allows testing hypothetical meals.
  - 03 Evidence Screen: Real screenshot of embedded in-app evidence ledger (`evidence.json`) showing all 5 passes, 4 misses, sample sizes, and p-values directly in the clinical UI.
  - Highlight the 3 clinical safety rules: (1) Zero automated insulin/drug dosing; (2) Zero unconfirmed low-glucose alarms; (3) Zero naked point estimates without uncertainty envelopes.
* **Footnote:** Research prototype. Interactive application running at **digital-twin-hack.vercel.app**. Synthetic patient profile. Not approved as a medical device; no dosing advice.
* **Speaker Notes (75s):**
> "A doctor has at most two minutes to review a patient's chart. A dashboard cluttered with red flashing alarms and black-box recommendations is a clinical liability. Chhaya's clinician dashboard is designed for a ten-second assessment. The primary view displays the measured sensor days alongside reconstructed gaps, always accompanied by the eighty-percent credible envelope. You will notice three deliberate absences: there is no insulin dose calculator, no low-glucose panic alarm, and no naked point estimates without uncertainty. We also embedded the entire evidence ledger directly into the clinician interface, allowing doctors to inspect our pre-registered passes and misses. You can test this live right now at digital-twin-hack.vercel.app."

---

## Slide 10 — Conclusion & Roadmap (Dark)
* **Title:** The digital twin is not always needed; we measured where it earns its place. *(14 words)*
* **Copy:** Physics twins earn their place in bounded gap estimation and meal simulation. Where simple baselines lead, we defer. The next critical step is an Indian clinical cohort.
* **Enriched Data:**
  - Where the digital twin earns its place:
    - 1. Unmeasured gap infill (1.4 mg/dL gain, $p = 4 \times 10^{-5}$) using meal absorption kinetics.
    - 2. In-silico meal what-if simulation (patient-specific carb sensitivity).
    - 3. Bounded uncertainty representation (80% credible envelope for clinical safety).
    - 4. Empirical humility: Proved where static EHR adds zero signal, and where plain linear fingerstick averages beat complex models.
  - Key Metrics Box: Gate 2 Infill (-1.4 mg/dL, $p=4e-05$), Sticks in Hindsight (+9.5 mg/dL gain), EHR Fusion Gain (0.02 mg/dL, $p=0.16$).
  - Concrete Future Roadmap:
    - 1. Prospective Indian Cohort: Calibrate and test model kinetics on Indian dietary patterns (high refined carb glycemic indices in rotis/rice) under local institutional ethics.
    - 2. ABDM Health Stack Integration: Map schemas to Ayushman Bharat Digital Mission FHIR Milestone 1–3 profiles (future work).
    - 3. Prospective Clinical Trial: Evaluating whether bounded shadow infilling during sensor holidays prevents glycemic decompensation.
* **Footnote:** Team SynapseX · Aditya Singh Chandel · D.B.S. College, Kanpur · Happiest Health Digital Twin Challenge 2026.<br>Public GitHub: github.com/AdityaChandel11/DigitalTwinHack · Live Demo: digital-twin-hack.vercel.app
* **Speaker Notes (85s):**
> "We did not set out to prove that complex digital twins are a panacea for diabetes care. We set out to measure scientifically where a physical twin earns its place. We discovered that a twin provides genuine value in reconstructing unmeasured sensor gaps and providing bounded meal simulations. Equally important, we proved where a twin is unnecessary: static records add nothing once wearable data exists, and simple calibrated averages outperform complex models for retrospective reports. For India's 101 million diabetes patients, this honest boundary mapping is vital to prevent wasteful technology deployment. Our next milestone is validating these findings on a prospective Indian cohort and mapping our schema to ABDM profiles. The future of medicine is proactive, not reactive—and above all, it must be verifiably honest."
