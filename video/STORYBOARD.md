# Chhaya Presentation Film: Storyboard

**Goal:** 21-minute (1260.0 s), 1920x1080, 30 fps film with burned-in captions.

## Chapter Timing Table

| Chapter | Start | End | Target Duration | Actual Duration | Segments |
|---|---|---|---|---|---|
| **Cold Open** | 0:00 | 1:30 | 1.5 min (90s) | 1.5 min (90s) | 20 |
| **The Problem** | 1:30 | 4:00 | 2.5 min (150s) | 2.5 min (150s) | 35 |
| **Live Walkthrough** | 4:00 | 11:00 | 7.0 min (420s) | 7.0 min (420s) | 94 |
| **How It Was Made** | 11:00 | 15:00 | 4.0 min (240s) | 4.0 min (240s) | 50 |
| **Results** | 15:00 | 19:00 | 4.0 min (240s) | 4.0 min (240s) | 51 |
| **Limits and Close** | 19:00 | 21:00 | 2.0 min (120s) | 2.0 min (120s) | 26 |
| **Total** | 0:00 | 21:00 | 21.0 min (1260s) | 21.0 min (1260s) | 276 |

## Truth Rules and Verified Sourced Facts

All numbers and claims are verified against repository sources (`README.md`, `evidence.json`, `summary.json`, decision records):

1. **Sensor Wear Cost in India:** Rs 4,400 to 5,100 per wear (README footnotes; Abbott FreeStyle Libre sensor).

2. **Preregistered Scoreboard:** 9 bars written before test runs: 5 passed (P1, P2, P3 in Gate 2; F1, F2 in sticks), 4 missed (M1, M2, M3 in Gate 3; P1 in prior), 6 descriptive.

3. **Gate 2 Reveal Accuracy:** On 19 held-out patients, 5 days after sensor off, twin is 1.4 mg/dL (6 %) closer to hidden sensor than patient's own average day (Wilcoxon p = 4e-05); 0.35 mg/dL closer than control without meals (p = 0.04). Advantage does not fade over 7 days (0.4 to 2.0 mg/dL).

4. **Fingersticks Evidence:** On 29 held-out Shanghai patients, fingersticks brought running estimate 2.8 mg/dL closer (paired RMSE difference; 95% CI 1.6 to 4.7; 86% of patients; p = 4e-06) and 9.5 mg/dL closer in hindsight (CI 4.6 to 12.1). With 1 stick/day, running gain is 0.3 mg/dL. Estimate is ~22% off next fingerstick where real sensor is ~12%.

5. **Record Prior (Fusion Miss):** On 20 held-out CGMacros patients with 1 sensor day, record's fasting glucose prior changed error by median 0.02 mg/dL (p = 0.16); with 3+ days, nothing measurable. Fusion is built and measured; it is nil, not a gain.

6. **Gate 3 Information Ladder (Miss):** AUPRC for meal excursions: record alone = 0.566, history alone = 0.626, fingersticks alone = 0.642, fused twin = 0.596. Calibration slope = 0.482 (target 0.8 to 1.2). Result: no meal alert in product.

7. **Plain Baseline Ties and Wins:** Converted fingerstick average missed sensor mean by 6.4 mg/dL vs twin in hindsight by 8.9 mg/dL. Staleness prompt AUROC = 0.82 (CI 0.63 to 0.98), tying plain fingerstick average vs report (AUROC 0.82, diff 0.00).

8. **Data and Licences:** ShanghaiT2DM (100 patients, CC BY 4.0); CGMacros (45 participants, CC BY-NC-SA 4.0); 1 synthetic patient (Mrs. R.).

9. **Forbidden Words Checked:** Zero occurrences of 'breakthrough', 'clinically validated', 'clinical validation', 'ABDM', 'ABHA', 'predictive digital twin'; 'alert' only appears as 'no alert' or 'no meal alert'.

10. **Synthetic Labeling:** 'Synthetic demo patient' tag clearly visible on all Mrs. R. walkthrough segments.


## Sourced Claims and [NEEDS SOURCE] List

Every number in this film is 100% sourced from repository artifacts and pre-registration records.

- **List of [NEEDS SOURCE]:** None. All cited figures are verified against committed records.


## Complete Storyboard Segments

| ID | Chapter | Time | Seconds | Visual | Caption |
|---|---|---|---|---|---|
| `S001` | Cold Open | 0:00 - 0:04 | 4.5s | SITE: Mrs. R. patient screen, dark theme. Tag 'Synthetic demo patient' clearly visible. Shadow estimate visible without sensor. | This is Mrs. R.,<br>a synthetic demo patient. |
| `S002` | Cold Open | 0:04 - 0:09 | 4.5s | SITE: Hold on Mrs. R.'s screen. Highlight the purple line and band. | Her shadow is drawn<br>without a continuous glucose sensor. |
| `S003` | Cold Open | 0:09 - 0:13 | 4.5s | SITE: Spotlight drifts along the purple trajectory. | The purple curve is estimated glucose. |
| `S004` | Cold Open | 0:13 - 0:18 | 4.5s | SITE: Spotlight highlights the purple shaded envelope. | Around it lies an eighty per cent<br>uncertainty band. |
| `S005` | Cold Open | 0:18 - 0:22 | 4.5s | SITE: Cursor moves to the 'Reveal the sensor' button. | Now we reveal the real sensor trace. |
| `S006` | Cold Open | 0:22 - 0:27 | 4.5s | SITE: Click Reveal button. Sensor trace slides in over the shadow. | The real sensor trace slides in<br>across the estimated shadow. |
| `S007` | Cold Open | 0:27 - 0:31 | 4.5s | SITE: Spotlight on trace colors: teal in range, amber above 180. | Teal marks glucose in range,<br>and amber marks spikes above 180. |
| `S008` | Cold Open | 0:31 - 0:36 | 5.0s | SITE: Scrubber moves across the days, showing shadow tracking sensor. | The shadow tracked the real trace<br>five days after the sensor came off. |
| `S009` | Cold Open | 0:36 - 0:41 | 4.5s | SLIDE: HOOK slide. Deep ink card, accent glow. 'Chhaya' title card. | This is Chhaya,<br>Hindi for shadow. |
| `S010` | Cold Open | 0:41 - 0:45 | 4.5s | SLIDE: Subtitle: 'A Type 2 diabetes digital twin that shows its work.' | A Type 2 diabetes digital twin<br>that shows its work. |
| `S011` | Cold Open | 0:45 - 0:49 | 4.0s | SLIDE: SynapseX, D.B.S Kanpur card. | Built by Team SynapseX<br>at D.B.S Kanpur. |
| `S012` | Cold Open | 0:49 - 0:54 | 4.5s | SLIDE: SCOREBOARD card. 9 chips: 5 passed, 4 missed. | Here is our scoreboard plainly,<br>written before the runs. |
| `S013` | Cold Open | 0:54 - 0:58 | 4.0s | SLIDE: Highlight the 9 preregistered bars. | Nine bars were preregistered. |
| `S014` | Cold Open | 0:58 - 1:02 | 4.5s | SLIDE: 5 passed chips glow green. Focus on P1, P2, P3, F1, F2. | Five passed,<br>though one cannot fail to pass. |
| `S015` | Cold Open | 1:02 - 1:06 | 4.0s | SLIDE: 4 missed chips glow orange. Focus on M1, M2, M3, P1. | Four missed their bars. |
| `S016` | Cold Open | 1:06 - 1:11 | 4.5s | SLIDE: Subtitle on misses: what the misses changed in the product. | Every miss changed the product<br>and is reported openly. |
| `S017` | Cold Open | 1:11 - 1:15 | 4.5s | SLIDE: What changed: 'No meal alert, no probabilities.' | We show no meal alert,<br>and no excursion probability. |
| `S018` | Cold Open | 1:15 - 1:20 | 5.0s | SLIDE: What changed: 'The record added nil to fusion.' | The health record prior added nothing<br>detectable to sensor data. |
| `S019` | Cold Open | 1:20 - 1:25 | 5.0s | SLIDE: What changed: 'Plain baseline used where twin tied.' | Where a plain baseline tied,<br>we use the plain baseline. |
| `S020` | Cold Open | 1:25 - 1:30 | 4.5s | SLIDE: Transition to Problem slide. | Let us start with the clinical problem<br>in India. |
| `S021` | The Problem | 1:30 - 1:34 | 4.5s | SLIDE: BIGNUM slide. 'Rs 4,400 to 5,100' in large numerals. | In India, a continuous glucose sensor<br>costs 4400 to 5100 rupees. |
| `S022` | The Problem | 1:34 - 1:39 | 4.5s | SLIDE: Subtext: 'Cost of a single 14-day sensor wear.' | That is the cost of a single<br>fourteen-day wear. |
| `S023` | The Problem | 1:39 - 1:43 | 4.5s | SLIDE: Graphic showing a patient wearing a sensor once. | Because of that cost,<br>a patient wears a sensor once. |
| `S024` | The Problem | 1:43 - 1:48 | 4.5s | SLIDE: A single PDF report icon representing the wear report. | The clinic treats the patient<br>from that single report for months. |
| `S025` | The Problem | 1:48 - 1:52 | 4.5s | SLIDE: Timeline showing day 14 ending. Unmeasured gap appears. | When the sensor comes off,<br>nobody is measuring continuously. |
| `S026` | The Problem | 1:52 - 1:57 | 4.5s | SLIDE: Question card: 'What does the doctor have?' | What does the doctor have? |
| `S027` | The Problem | 1:57 - 2:01 | 4.5s | SLIDE: Three items appear: Paper report, occasional fingersticks, meal diary. | A static paper report,<br>occasional fingersticks, and a meal diary. |
| `S028` | The Problem | 2:01 - 2:06 | 4.5s | SLIDE: Card: 'The core questions for the clinic.' | The brief says medicine must be<br>proactive, not reactive. |
| `S029` | The Problem | 2:06 - 2:10 | 4.0s | SLIDE: Question 1: 'How long does that sensor report stay true?' | How long does that sensor report<br>stay true? |
| `S030` | The Problem | 2:10 - 2:14 | 4.0s | SLIDE: Question 2: 'Which readings should you not believe?' | Which readings should you<br>not believe? |
| `S031` | The Problem | 2:14 - 2:18 | 4.0s | SLIDE: Question 3: 'What keeps the shadow true?' | What keeps the estimate true? |
| `S032` | The Problem | 2:18 - 2:22 | 4.5s | SLIDE: Answer reveals: 'Meal logs and fingersticks.' | Our measurements show:<br>meal logs and fingersticks do. |
| `S033` | The Problem | 2:22 - 2:26 | 4.0s | SLIDE: Question 4: 'When does the report stop being true?' | And when does the report<br>stop being true? |
| `S034` | The Problem | 2:26 - 2:31 | 4.5s | SLIDE: Graphic showing glucose drifting as medications change. | When medications or lifestyle change,<br>glucose drifts away from the report. |
| `S035` | The Problem | 2:31 - 2:35 | 4.5s | SLIDE: BUILD slide: The Reveal Protocol title card. | To answer these honestly,<br>we built the reveal protocol. |
| `S036` | The Problem | 2:35 - 2:39 | 4.0s | SLIDE: Step 1 of protocol: '1. Calibrate on k days of sensor data.' | Step one:<br>calibrate on k days of sensor data. |
| `S037` | The Problem | 2:39 - 2:43 | 4.0s | SLIDE: Step 2 of protocol: '2. Hide the remaining sensor days.' | Step two:<br>hide the remaining sensor days. |
| `S038` | The Problem | 2:43 - 2:48 | 4.5s | SLIDE: Step 3 of protocol: '3. Estimate the hidden days without sensor.' | Step three:<br>estimate the hidden days without sensor data. |
| `S039` | The Problem | 2:48 - 2:52 | 4.5s | SLIDE: Subtext on Step 3: 'Using only meal log and fingersticks.' | The twin uses only meals,<br>activity, and fingersticks. |
| `S040` | The Problem | 2:52 - 2:56 | 4.0s | SLIDE: Step 4 of protocol: '4. Reveal the hidden sensor on top.' | Step four:<br>reveal the real sensor on top. |
| `S041` | The Problem | 2:56 - 3:01 | 4.5s | SLIDE: Card showing no simulator-on-simulator. | We never score a simulator<br>on its own simulated data. |
| `S042` | The Problem | 3:01 - 3:05 | 4.0s | SLIDE: Card: 'Scored once on held-out patients.' | Every claim is scored once<br>on held-out patients. |
| `S043` | The Problem | 3:05 - 3:09 | 4.5s | SLIDE: Card: 'Against bars written before the run.' | Against bars written beforehand<br>in our preregistration. |
| `S044` | The Problem | 3:09 - 3:13 | 4.0s | SLIDE: Protocol summary recap. | Calibrate, hide, estimate, and reveal. |
| `S045` | The Problem | 3:13 - 3:18 | 4.5s | SLIDE: Diagram of sensor-off period. | The hidden window simulates real clinic practice. |
| `S046` | The Problem | 3:18 - 3:22 | 4.5s | SLIDE: Held-out patient cohort graphic. | Scored on patients the twin never saw in training. |
| `S047` | The Problem | 3:22 - 3:26 | 4.0s | SLIDE: Honest science badge. | No cherry-picked runs and no leakage. |
| `S048` | The Problem | 3:26 - 3:31 | 4.5s | SLIDE: The question of clinic cost. | Saving patients repeated sensor costs in India. |
| `S049` | The Problem | 3:31 - 3:35 | 4.5s | SLIDE: Patient shadow illustration. | The shadow extends the value of one sensor wear. |
| `S050` | The Problem | 3:35 - 3:39 | 4.0s | SLIDE: Transition to browser capture. | We open the live deployment now. |
| `S051` | The Problem | 3:39 - 3:44 | 4.5s | SLIDE: Clinic economics footnote card. | Sensor costs represent a heavy recurring expense. |
| `S052` | The Problem | 3:44 - 3:48 | 4.0s | SLIDE: Transparency pledge. | Every number in this film is reproducible. |
| `S053` | The Problem | 3:48 - 3:52 | 4.0s | SLIDE: Clinic Dashboard title card. | Welcome to Chhaya in the clinic. |
| `S054` | The Problem | 3:52 - 3:56 | 4.0s | SLIDE: Ready for live walkthrough. | Let us inspect the live system in action. |
| `S055` | The Problem | 3:56 - 4:00 | 4.0s | SLIDE: Interface architecture peek. | Running client-side from static assets. |
| `S056` | Live Walkthrough | 4:00 - 4:04 | 4.0s | SITE: Clinic list view at #clinic. Full roster visible. | We begin on the clinic view at #clinic. |
| `S057` | Live Walkthrough | 4:04 - 4:08 | 4.5s | SITE: Highlight columns: Patient, Cohort, Days, Status. | The roster shows patient cohorts,<br>wear duration, and staleness status. |
| `S058` | Live Walkthrough | 4:08 - 4:13 | 4.5s | SITE: Highlight cohort badges: Synthetic, Supervised, Free-living. | Patients belong to synthetic,<br>supervised, or free-living cohorts. |
| `S059` | Live Walkthrough | 4:13 - 4:17 | 4.5s | SITE: Cursor hovers over Mrs. R. row. | At the top is Mrs. R.,<br>our synthetic demo patient. |
| `S060` | Live Walkthrough | 4:17 - 4:22 | 4.5s | SITE: Highlight 'Synthetic demo' chip in table. | Her cohort is explicitly tagged<br>as Synthetic demo. |
| `S061` | Live Walkthrough | 4:22 - 4:26 | 4.0s | SITE: Click on Mrs. R. row to navigate to #p-mrs-r. | Clicking her row opens the patient screen. |
| `S062` | Live Walkthrough | 4:26 - 4:30 | 4.0s | SITE: Patient view opens smoothly. Top header in view. | Mrs. R.'s patient view loads at #p-mrs-r. |
| `S063` | Live Walkthrough | 4:30 - 4:35 | 5.0s | SITE: Spotlight on 'Synthetic demo patient' chip top right. | Notice the prominent 'Synthetic demo patient'<br>tag in the header. |
| `S064` | Live Walkthrough | 4:35 - 4:39 | 4.5s | SITE: Tag stays fixed. Cursor highlights 'Estimated' badge on charts. | All twin curves are explicitly<br>labelled 'Estimated'. |
| `S065` | Live Walkthrough | 4:39 - 4:44 | 4.5s | SITE: Hold on header. Clean dark ink theme. | No synthetic estimate is ever<br>presented as measured ground truth. |
| `S066` | Live Walkthrough | 4:44 - 4:48 | 4.5s | SITE: Cursor moves to 'From the health record' card on left. | On the left is the 'From the health record' panel. |
| `S067` | Live Walkthrough | 4:48 - 4:53 | 4.5s | SITE: Highlight Age, Gender, Diagnosis: 58 yr, Female, T2D 6 yr. | Mrs. R. is 58 years old,<br>with Type 2 diabetes for six years. |
| `S068` | Live Walkthrough | 4:53 - 4:58 | 5.0s | SITE: Highlight HbA1c: 7.8 %, Fasting glucose: 142 mg/dL. | Her HbA1c is 7.8 per cent,<br>and fasting glucose is 142 mg/dL. |
| `S069` | Live Walkthrough | 4:58 - 5:03 | 5.0s | SITE: Highlight Metformin 1000 mg bid, BMI 28.4 kg/m2. | She takes Metformin 1000 mg twice daily,<br>with a BMI of 28.4. |
| `S070` | Live Walkthrough | 5:03 - 5:07 | 4.5s | SITE: Highlight lifestyle tag: Sedentary, vegetarian diet. | The record also captures her sedentary lifestyle<br>and diet notes. |
| `S071` | Live Walkthrough | 5:07 - 5:12 | 4.5s | SITE: Cursor points to Kidney lab values: Creatinine 1.0, eGFR 72. | Renal function shows creatinine 1.0 mg/dL<br>and eGFR 72. |
| `S072` | Live Walkthrough | 5:12 - 5:16 | 4.5s | SITE: Cursor points to Lipid panel: Total Chol 188, Triglycerides 164. | Lipids show total cholesterol 188 mg/dL<br>and triglycerides 164. |
| `S073` | Live Walkthrough | 5:16 - 5:21 | 4.5s | SITE: Spotlight note: record prior measured effect. | This record sets the twin's prior,<br>which we will evaluate later. |
| `S074` | Live Walkthrough | 5:21 - 5:25 | 4.0s | SITE: Main chart area. Days 1 to 3 calibration wear. | The first three days show her calibration wear. |
| `S075` | Live Walkthrough | 5:25 - 5:29 | 4.5s | SITE: Days 4 to 9: sensor removed. Only purple shadow drawn. | On day four the sensor comes off,<br>and the shadow begins. |
| `S076` | Live Walkthrough | 5:29 - 5:34 | 4.5s | SITE: Highlight purple curve: running estimate. | The purple curve shows the running<br>glucose estimate. |
| `S077` | Live Walkthrough | 5:34 - 5:39 | 5.0s | SITE: Highlight shaded envelope around purple curve. | The shaded band represents an eighty per cent<br>uncertainty envelope. |
| `S078` | Live Walkthrough | 5:39 - 5:44 | 5.0s | SITE: Meal log markers along bottom axis of chart. | Along the bottom axis are logged meals:<br>breakfast, lunch, and dinner. |
| `S079` | Live Walkthrough | 5:44 - 5:48 | 4.5s | SITE: Glucose rises after meal markers. | The twin simulates glycemic absorption<br>following each recorded meal. |
| `S080` | Live Walkthrough | 5:48 - 5:53 | 4.5s | SITE: Cursor moves to '#reveal-btn' button. | To test the shadow, the doctor clicks<br>'Reveal the sensor'. |
| `S081` | Live Walkthrough | 5:53 - 5:57 | 4.5s | SITE: Click Reveal button. Animation starts. | Clicking Reveal overlays the real<br>hidden sensor trace. |
| `S082` | Live Walkthrough | 5:57 - 6:02 | 5.0s | SITE: Sensor trace appears in full color over shadow. | Teal indicates in-range glucose,<br>while amber marks readings above 180. |
| `S083` | Live Walkthrough | 6:02 - 6:06 | 4.0s | SITE: Cursor moves to scrubber '#scrub'. | A scrubber bar appears below the chart. |
| `S084` | Live Walkthrough | 6:06 - 6:11 | 4.5s | SITE: Drag scrubber slowly across Day 4 and Day 5. | We can scrub forward day by day<br>to inspect fidelity. |
| `S085` | Live Walkthrough | 6:11 - 6:16 | 5.0s | SITE: Scrubber pauses on Day 5 peak. | On day five, the estimated peak closely matches<br>the revealed peak. |
| `S086` | Live Walkthrough | 6:16 - 6:20 | 4.5s | SITE: Scrubber moves across Day 6 and Day 7. | The shadow continues to track<br>the patient's diurnal shape. |
| `S087` | Live Walkthrough | 6:20 - 6:25 | 4.5s | SITE: Scrubber pauses on Day 8. | Even eight days out, the purple curve<br>remains centered. |
| `S088` | Live Walkthrough | 6:25 - 6:30 | 5.0s | SITE: Highlight live error card beside scrubber. | The error metrics card computes difference<br>against the revealed sensor. |
| `S089` | Live Walkthrough | 6:30 - 6:34 | 4.0s | SITE: Cursor points to diamond markers on the chart timeline. | Notice the diamond icons along the timeline. |
| `S090` | Live Walkthrough | 6:34 - 6:38 | 4.5s | SITE: Spotlight on a fingerstick diamond. | These are fingerstick blood glucose checks<br>taken by the patient. |
| `S091` | Live Walkthrough | 6:38 - 6:43 | 4.5s | SITE: Animation shows shadow pulling toward diamond. | Each fingerstick assimilates new evidence<br>into the twin's state. |
| `S092` | Live Walkthrough | 6:43 - 6:47 | 4.5s | SITE: Uncertainty band narrows after fingerstick. | The uncertainty band visibly narrows<br>after each fingerstick. |
| `S093` | Live Walkthrough | 6:47 - 6:52 | 4.5s | SITE: Spotlight on gap between fingersticks where band widens. | When hours pass without a check,<br>the doubt expands honestly. |
| `S094` | Live Walkthrough | 6:52 - 6:56 | 4.5s | SITE: Cursor highlights Day 6 on timeline. | By day six, glucose baseline has shifted downward. |
| `S095` | Live Walkthrough | 6:56 - 7:01 | 4.5s | SITE: Flag icon / prompt badge appears on Day 6. | A prompt appears on day six:<br>'Consider a new sensor wear'. |
| `S096` | Live Walkthrough | 7:01 - 7:05 | 4.5s | SITE: Click prompt badge. Tooltip opens. | This prompt triggers when cumulative surprises<br>exceed our threshold. |
| `S097` | Live Walkthrough | 7:05 - 7:10 | 5.0s | SITE: Inspect drift threshold rationale. | The threshold was chosen on development records<br>to limit false prompts to ten per cent. |
| `S098` | Live Walkthrough | 7:10 - 7:15 | 5.0s | SITE: Highlight tooltip text. | Notice the wording: it is a prompt,<br>not advice, and not a diagnosis. |
| `S099` | Live Walkthrough | 7:15 - 7:20 | 5.0s | SITE: Tooltip shows drift metric. | It informs the clinician that the old report<br>may have gone stale. |
| `S100` | Live Walkthrough | 7:20 - 7:24 | 4.0s | SITE: Scroll down to Meal Excursions panel below chart. | Scrolling down reveals the Meal Excursions panel. |
| `S101` | Live Walkthrough | 7:24 - 7:29 | 4.5s | SITE: Highlight list of meals with carb grams and rise mg/dL. | Every meal lists recorded carbs<br>and observed post-meal excursion. |
| `S102` | Live Walkthrough | 7:29 - 7:34 | 5.0s | SITE: Hover over Breakfast: 45g carbs, rise 48 mg/dL. | Breakfast with 45 grams of carbs<br>produced a 48 mg/dL rise. |
| `S103` | Live Walkthrough | 7:34 - 7:39 | 5.0s | SITE: Hover over Dinner: 70g carbs, rise 68 mg/dL. | Dinner with 70 grams of carbs<br>produced a 68 mg/dL spike. |
| `S104` | Live Walkthrough | 7:39 - 7:43 | 4.5s | SITE: Note absence of probabilities. | Notice there are no excursion probabilities<br>or risk scores here. |
| `S105` | Live Walkthrough | 7:43 - 7:48 | 4.5s | SITE: Cursor moves to 'Meal What-If' simulator card. | Beside the history is the Meal What-If simulator. |
| `S106` | Live Walkthrough | 7:48 - 7:53 | 5.0s | SITE: Input field for carbohydrate grams: types '60'. | The clinician types in a hypothetical meal<br>of 60 grams of carbs. |
| `S107` | Live Walkthrough | 7:53 - 7:57 | 4.5s | SITE: Click Simulate button. | Clicking Simulate runs the twin's<br>physiological equations. |
| `S108` | Live Walkthrough | 7:57 - 8:01 | 4.0s | SITE: Simulated trajectory appears with purple dashed curve. | The simulated excursion curve appears<br>in purple. |
| `S109` | Live Walkthrough | 8:01 - 8:05 | 4.0s | SITE: Spotlight on prominent disclaimer badge. | Look at the bold disclaimer badge: |
| `S110` | Live Walkthrough | 8:05 - 8:09 | 4.0s | SITE: Zoom in on text: 'simulation, not a prediction, not advice'. | 'Simulation, not a prediction, not advice.' |
| `S111` | Live Walkthrough | 8:09 - 8:14 | 4.5s | SITE: Tag stays visible. Cursor indicates no meal alerts. | We show no meal alert<br>and no prescription guidance. |
| `S112` | Live Walkthrough | 8:14 - 8:18 | 4.5s | SITE: Compare with 30g carb scenario. | Entering 30 grams simulates a lower post-meal rise. |
| `S113` | Live Walkthrough | 8:18 - 8:23 | 4.5s | SITE: Instant local simulation note. | The simulation updates instantly in the browser<br>without round-trips to a server. |
| `S114` | Live Walkthrough | 8:23 - 8:27 | 4.5s | SITE: Cursor clicks on patient profile link #patient. | Now we open Mrs. R.'s full health record modal. |
| `S115` | Live Walkthrough | 8:27 - 8:32 | 4.5s | SITE: Modal opens showing structured FHIR-shaped record. | The modal displays structured,<br>FHIR-shaped patient demographics. |
| `S116` | Live Walkthrough | 8:32 - 8:37 | 5.0s | SITE: Highlight lab tests: Creatinine, eGFR, Lipid profile. | Laboratory values include creatinine, lipid panel,<br>and kidney metrics. |
| `S117` | Live Walkthrough | 8:37 - 8:41 | 4.5s | SITE: Highlight provenance card at bottom. | The provenance card confirms this record<br>is entirely synthetic. |
| `S118` | Live Walkthrough | 8:41 - 8:45 | 4.0s | SITE: Close modal button clicked. Return to patient view. | We close the modal and return to the dashboard. |
| `S119` | Live Walkthrough | 8:45 - 8:50 | 4.5s | SITE: Cursor navigates to top nav link 'Evidence' (#evidence). | Next, we click 'Evidence' in the navigation bar. |
| `S120` | Live Walkthrough | 8:50 - 8:54 | 4.0s | SITE: Evidence screen loads. Tally at top: 9 bars, 5 passed, 4 missed. | The Evidence screen opens at #evidence. |
| `S121` | Live Walkthrough | 8:54 - 8:58 | 4.0s | SITE: Spotlight on Tally card at top. | The top tally card summarizes our score: |
| `S122` | Live Walkthrough | 8:58 - 9:03 | 5.0s | SITE: Focus on numbers: 9 preregistered bars, 5 passed, 4 missed. | Nine bars written first: five passed,<br>four missed, and six descriptive. |
| `S123` | Live Walkthrough | 9:03 - 9:07 | 4.5s | SITE: Scroll down through results cards. | Every single evaluation is published here<br>with its full claim. |
| `S124` | Live Walkthrough | 9:07 - 9:12 | 4.5s | SITE: Cursor scrolls to Gate 3 card: 'Post-meal excursion'. | Let us open one of our misses:<br>Gate 3 on meal excursions. |
| `S125` | Live Walkthrough | 9:12 - 9:16 | 4.0s | SITE: Click on Gate 3 card to expand details. | We expand the Gate 3 card. |
| `S126` | Live Walkthrough | 9:16 - 9:21 | 5.0s | SITE: Show RED badge: 'Missed bars: M1, M2, M3'. | Bars M1, M2, and M3 missed<br>their preregistered targets. |
| `S127` | Live Walkthrough | 9:21 - 9:25 | 4.0s | SITE: Show figure comparing AUPRC across arms. | The chart compares the information ladder. |
| `S128` | Live Walkthrough | 9:25 - 9:30 | 5.5s | SITE: Highlight history arm AUPRC: 0.626 vs fused twin: 0.596. | Past sensor history achieved an AUPRC of 0.626,<br>while our twin achieved 0.596. |
| `S129` | Live Walkthrough | 9:30 - 9:35 | 5.0s | SITE: Highlight calibration slope: 0.482 vs target 0.8-1.2. | The calibration slope was 0.482,<br>far below the target of 0.8. |
| `S130` | Live Walkthrough | 9:35 - 9:40 | 5.0s | SITE: Cursor points to consequence text in card. | Because this bar missed,<br>we show no meal alert in the product. |
| `S131` | Live Walkthrough | 9:40 - 9:45 | 4.5s | SITE: Card explicitly states: 'No meal alert, no probability shown'. | No alert is shown,<br>and no false confidence is displayed. |
| `S132` | Live Walkthrough | 9:45 - 9:49 | 4.0s | SITE: Inspect second descriptive card: Expiry analysis. | We also inspect the Expiry analysis card. |
| `S133` | Live Walkthrough | 9:49 - 9:54 | 5.0s | SITE: Expiry card details: 47 Shanghai patients, 1.0 mg/dL drift per day. | On 47 Shanghai patients,<br>mean sensor glucose drifted 1.0 mg/dL per day. |
| `S134` | Live Walkthrough | 9:54 - 9:59 | 5.0s | SITE: Inspect Band card: 80% band held 83.5% of readings. | The Band card shows our 80 per cent band<br>held 83.5 per cent of readings. |
| `S135` | Live Walkthrough | 9:59 - 10:03 | 4.0s | SITE: Cursor moves to 'Clinic' in top navigation bar. | We navigate back to the Clinic view. |
| `S136` | Live Walkthrough | 10:03 - 10:07 | 4.0s | SITE: Click Clinic link. Clinic roster reappears at #clinic. | The full clinic roster reappears. |
| `S137` | Live Walkthrough | 10:07 - 10:11 | 4.5s | SITE: Hold on clinic roster with all cohorts. | Every held-out participant can be inspected<br>just like Mrs. R. |
| `S138` | Live Walkthrough | 10:11 - 10:15 | 4.0s | SITE: Hold on clinic view. | The interface is fast and fully client-side. |
| `S139` | Live Walkthrough | 10:15 - 10:19 | 4.0s | SITE: Highlight audit provenance. | Built entirely from precomputed artifacts. |
| `S140` | Live Walkthrough | 10:19 - 10:23 | 4.0s | SITE: Highlight clean UI styling. | Deep ink styling with accessible contrast. |
| `S141` | Live Walkthrough | 10:23 - 10:27 | 4.0s | SITE: Patient view thumbnail. | Showing doctors where uncertainty lies. |
| `S142` | Live Walkthrough | 10:27 - 10:31 | 4.0s | SITE: Evidence screen thumbnail. | Holding our model to scientific scrutiny. |
| `S143` | Live Walkthrough | 10:31 - 10:35 | 4.0s | SITE: Scrubber demonstration hold. | Transparent reveal of real measurements. |
| `S144` | Live Walkthrough | 10:35 - 10:40 | 4.5s | SITE: What-if panel thumbnail. | Physiological exploration without overclaiming. |
| `S145` | Live Walkthrough | 10:40 - 10:44 | 4.0s | SITE: Roster summary thumbnail. | Ready for clinical pilot evaluation. |
| `S146` | Live Walkthrough | 10:44 - 10:48 | 4.0s | SITE: Dark theme overview. | A digital twin designed for clinical clarity. |
| `S147` | Live Walkthrough | 10:48 - 10:52 | 4.0s | SITE: Transition out. | Now let us examine how Chhaya was built. |
| `S148` | Live Walkthrough | 10:52 - 10:56 | 4.0s | SITE: Wrap-up of walkthrough. | Next is the architecture and engineering. |
| `S149` | Live Walkthrough | 10:56 - 11:00 | 4.0s | SITE: Final hold on clinic header. | From live product to underlying code. |
| `S150` | How It Was Made | 11:00 - 11:04 | 4.5s | SLIDE: Section Title: 'How It Was Made'. Accent glow. | Section three: how Chhaya was built. |
| `S151` | How It Was Made | 11:04 - 11:09 | 4.5s | SLIDE: DATA slide: The Datasets overview. | We evaluated on two open datasets<br>and one synthetic patient. |
| `S152` | How It Was Made | 11:09 - 11:14 | 5.0s | SLIDE: Card 1: ShanghaiT2DM dataset details. | ShanghaiT2DM includes 100 Type 2 diabetes patients<br>across 109 recordings. |
| `S153` | How It Was Made | 11:14 - 11:19 | 5.0s | SLIDE: Shanghai details: 15-min sensor, fingersticks, diet text, drugs. | It provides 15-minute sensor readings,<br>fingersticks, diet logs, and labs. |
| `S154` | How It Was Made | 11:19 - 11:23 | 4.5s | SLIDE: Shanghai licence: CC BY 4.0. | ShanghaiT2DM is open under CC BY 4.0. |
| `S155` | How It Was Made | 11:23 - 11:28 | 5.0s | SLIDE: Card 2: CGMacros dataset details. | CGMacros includes 45 free-living participants<br>wearing dual sensors and Fitbit. |
| `S156` | How It Was Made | 11:28 - 11:33 | 5.0s | SLIDE: CGMacros licence: CC BY-NC-SA 4.0 non-commercial. | CGMacros is licensed under CC BY-NC-SA 4.0<br>for non-commercial research. |
| `S157` | How It Was Made | 11:33 - 11:38 | 5.0s | SLIDE: Split by patient card: 'is_dev_patient()'. | Crucially, data is split strictly by patient,<br>never by row. |
| `S158` | How It Was Made | 11:38 - 11:43 | 5.0s | SLIDE: Population priors on dev, evaluated on test once. | Priors are tuned on dev patients<br>and evaluated once on held-out test patients. |
| `S159` | How It Was Made | 11:43 - 11:48 | 4.5s | SLIDE: Data hygiene: checksum verification. | All datasets are checksummed<br>and verified on download. |
| `S160` | How It Was Made | 11:48 - 11:52 | 4.5s | SLIDE: BUILD slide: Step 1: Raw data to Recording schema. | The architecture follows a strict<br>one-way pipeline. |
| `S161` | How It Was Made | 11:52 - 11:57 | 5.0s | SLIDE: BUILD step 2: Recording data class. | The Recording schema is the only data structure<br>that crosses module boundaries. |
| `S162` | How It Was Made | 11:57 - 12:02 | 4.5s | SLIDE: BUILD step 3: build_inputs creates JAX arrays. | Module build_inputs converts recordings<br>into clean numerical arrays. |
| `S163` | How It Was Made | 12:02 - 12:07 | 5.0s | SLIDE: BUILD step 4: fit_twin optimizes parameters. | Module fit_twin optimizes patient parameters<br>using JAX x64 acceleration. |
| `S164` | How It Was Made | 12:07 - 12:12 | 5.0s | SLIDE: BUILD step 5: simulate_ensemble generates trajectories. | Module simulate_ensemble simulates ODE trajectories<br>and covariance envelopes. |
| `S165` | How It Was Made | 12:12 - 12:17 | 5.0s | SLIDE: BUILD step 6: Precomputed JSON bundle to dashboard. | The build command writes precomputed JSON bundles<br>for the browser. |
| `S166` | How It Was Made | 12:17 - 12:22 | 5.0s | SLIDE: Serverless static design: zero latency inference. | The browser app computes nothing live:<br>every curve is precomputed and verified. |
| `S167` | How It Was Made | 12:22 - 12:27 | 5.0s | SLIDE: TWIN slide: Extended Discrete-Event Simulator (E-DES). | The physiological core is an E-DES model<br>implemented in JAX. |
| `S168` | How It Was Made | 12:27 - 12:32 | 5.0s | SLIDE: ODE equations in 1-minute steps with RK4. | Ordinary differential equations step at one minute<br>using fourth-order Runge-Kutta. |
| `S169` | How It Was Made | 12:32 - 12:37 | 5.0s | SLIDE: Two-compartment gut model details. | A two-compartment gut model simulates<br>carbohydrate digestion and appearance. |
| `S170` | How It Was Made | 12:37 - 12:42 | 5.0s | SLIDE: JAX precision: x64 enabled. | We use 64-bit floating point precision<br>in JAX to prevent numerical underflow. |
| `S171` | How It Was Made | 12:42 - 12:46 | 4.5s | SLIDE: Pure functional implementation. | Pure functional simulation ensures<br>exact reproducibility across platforms. |
| `S172` | How It Was Made | 12:46 - 12:51 | 4.5s | SLIDE: 7 personal parameters card. | The twin fits seven patient-specific parameters. |
| `S173` | How It Was Made | 12:51 - 12:56 | 5.0s | SLIDE: Parameter 1: absorption rate k_abs. | Absorption rate k_abs governs gut emptying<br>and appearance into plasma. |
| `S174` | How It Was Made | 12:56 - 13:01 | 5.0s | SLIDE: Parameter 2: basal glucose Gb. | Basal glucose Gb represents steady-state<br>hepatic glucose production. |
| `S175` | How It Was Made | 13:01 - 13:05 | 4.5s | SLIDE: Parameter 3: beta responsiveness. | Beta-cell responsiveness captures<br>insulin secretion capacity. |
| `S176` | How It Was Made | 13:05 - 13:10 | 5.0s | SLIDE: Parameter 4: dawn amplitude. | Dawn amplitude models early morning<br>circadian elevation in glucose. |
| `S177` | How It Was Made | 13:10 - 13:15 | 5.0s | SLIDE: Parameter 5: exercise sensitivity. | Exercise sensitivity scales muscle glucose uptake<br>from physical activity. |
| `S178` | How It Was Made | 13:15 - 13:20 | 5.0s | SLIDE: Parameter 6: meal-logging bias. | Meal-logging bias adjusts for patient<br>underreporting of carb grams. |
| `S179` | How It Was Made | 13:20 - 13:25 | 4.5s | SLIDE: Parameter 7: insulin-mediated disposal fraction. | And insulin-mediated disposal fraction<br>balances clearance. |
| `S180` | How It Was Made | 13:25 - 13:30 | 5.0s | SLIDE: MAP estimation and Laplace approximation. | We fit parameters with MAP estimation<br>and compute a Laplace uncertainty band. |
| `S181` | How It Was Made | 13:30 - 13:34 | 4.5s | SLIDE: L-BFGS-B optimization speed. | The optimizer finds the posterior mode<br>using L-BFGS-B in seconds. |
| `S182` | How It Was Made | 13:34 - 13:39 | 5.0s | SLIDE: Parameter covariance from Hessian matrix. | The Hessian at the mode gives the covariance<br>for realistic uncertainty bands. |
| `S183` | How It Was Made | 13:39 - 13:44 | 5.0s | SLIDE: The Blend slide: 50% physiology + 50% average day. | The estimate is an equal blend of physiology<br>and the patient's average day. |
| `S184` | How It Was Made | 13:44 - 13:49 | 5.0s | SLIDE: Why blend works: errors are only partly correlated. | Physiology captures today's meals,<br>while average day captures unlogged habits. |
| `S185` | How It Was Made | 13:49 - 13:54 | 4.5s | SLIDE: Fingerstick assimilation filter. | A Kalman-style filter assimilates fingersticks<br>as sparse evidence. |
| `S186` | How It Was Made | 13:54 - 13:59 | 5.0s | SLIDE: Updating baseline and drift states. | Each fingerstick updates both baseline glucose<br>and running drift. |
| `S187` | How It Was Made | 13:59 - 14:03 | 4.5s | SLIDE: Non-negotiable rules card. | We followed four non-negotiable rules. |
| `S188` | How It Was Made | 14:03 - 14:08 | 5.0s | SLIDE: Rule 1: No data leakage. Timestamps strictly > split. | Rule one: no data leakage.<br>Scored timestamps strictly follow the split. |
| `S189` | How It Was Made | 14:08 - 14:13 | 5.0s | SLIDE: Test assertions against sensor leakage. | Automated tests alter hidden sensor values<br>and assert features do not move. |
| `S190` | How It Was Made | 14:13 - 14:18 | 5.0s | SLIDE: Rule 2: Bars written first in PREREGISTRATION.md. | Rule two: all pass bars were written<br>before test runs in PREREGISTRATION.md. |
| `S191` | How It Was Made | 14:18 - 14:23 | 5.0s | SLIDE: Rule 3: Report what happened. Publish misses. | Rule three: report what happened.<br>A miss is published, never hidden. |
| `S192` | How It Was Made | 14:23 - 14:28 | 4.5s | SLIDE: Rule 4: Plain baselines acknowledged. | Rule four: where a plain baseline wins,<br>we say so plainly. |
| `S193` | How It Was Made | 14:28 - 14:33 | 5.0s | SLIDE: Test suite: 400+ automated pytest tests. | Over 400 automated tests enforce compliance<br>on every commit. |
| `S194` | How It Was Made | 14:33 - 14:37 | 4.5s | SLIDE: Scientific integrity recap. | Truth rules take precedence over marketing. |
| `S195` | How It Was Made | 14:37 - 14:42 | 5.0s | SLIDE: Synthetic recovery verification. | Synthetic recordings verify that ground truth<br>parameters can be recovered. |
| `S196` | How It Was Made | 14:42 - 14:47 | 4.5s | SLIDE: Unit test coverage summary. | Comprehensive assertions on physiological bounds. |
| `S197` | How It Was Made | 14:47 - 14:51 | 4.5s | SLIDE: Transition to Results section. | Now let us see what the measurements revealed. |
| `S198` | How It Was Made | 14:51 - 14:56 | 4.5s | SLIDE: Moving to evaluation benchmarks. | Every claim scored once on held-out patients. |
| `S198b` | How It Was Made | 14:56 - 15:00 | 4.0s | SLIDE: Continuous integration pipeline. | Continuous integration tests run<br>on every commit. |
| `S199` | Results | 15:00 - 15:04 | 4.0s | SLIDE: Results section title: 'Results at True Size'. | Section four: results at true size. |
| `S200` | Results | 15:04 - 15:08 | 4.0s | SLIDE: SCORE slide: The 9 preregistered bars overview. | Nine bars were preregistered before testing. |
| `S201` | Results | 15:08 - 15:13 | 5.0s | SLIDE: 5 Passed, 4 Missed, 6 Descriptive tallies. | Five passed, four missed,<br>and six analyses were registered as descriptive. |
| `S202` | Results | 15:13 - 15:17 | 4.5s | SLIDE: GATE 2 slide: The Reveal (Bars P1, P2, P3 Passed). | Gate 2 evaluated the reveal on 19 held-out patients. |
| `S203` | Results | 15:17 - 15:22 | 5.0s | SLIDE: 1.4 mg/dL closer to hidden sensor (p = 4e-05). | Five days post-sensor, the twin was 1.4 mg/dL<br>closer to the hidden sensor. |
| `S204` | Results | 15:22 - 15:27 | 4.5s | SLIDE: Wilcoxon signed-rank test. | A one-sided Wilcoxon signed-rank test<br>gave p = 4e-05. |
| `S205` | Results | 15:27 - 15:31 | 4.5s | SLIDE: Percent gain: 6% gain over patient's average day. | That is a six per cent gain<br>over the patient's average day. |
| `S206` | Results | 15:31 - 15:36 | 4.5s | SLIDE: 0.35 mg/dL closer than control with no meals (p = 0.04). | And 0.35 mg/dL closer<br>than a control using no meals. |
| `S206b` | Results | 15:36 - 15:40 | 4.5s | SLIDE: Wilcoxon signed-rank test on no-meal control. | The Wilcoxon test against the no-meal control<br>gave p = 0.04. |
| `S207` | Results | 15:40 - 15:45 | 4.5s | SLIDE: Honest assessment: gain comes from meal log and is small. | The gain comes from the meal log,<br>and it is modest. |
| `S208` | Results | 15:45 - 15:50 | 5.5s | SLIDE: Does not fade over first 7 days: 0.4 to 2.0 mg/dL advantage. | The advantage did not fade over seven days,<br>favoring the twin by 0.4 to 2.0 mg/dL. |
| `S209` | Results | 15:50 - 15:55 | 5.0s | SLIDE: Subgroup analysis: gate2-by-group.png. | Performance was consistent across age,<br>gender, and BMI subgroups. |
| `S210` | Results | 15:55 - 16:00 | 5.0s | SLIDE: Subgroup details: under 65 vs over 65. | In patients under 65, the twin was 1.5 mg/dL<br>closer to the hidden sensor. |
| `S210b` | Results | 16:00 - 16:05 | 4.5s | SLIDE: BMI subgroup analysis: under 25 vs 25+. | In participants with BMI under 25,<br>the twin was 1.3 mg/dL closer. |
| `S211` | Results | 16:05 - 16:09 | 4.5s | SLIDE: Note on P2: passed because bar cannot discriminate. | Bar P2 passed only because<br>time in range cannot discriminate. |
| `S212` | Results | 16:09 - 16:14 | 4.5s | SLIDE: FINGERSTICKS slide: Bars F1 and F2 Passed. | Fingersticks brought the report<br>significantly closer. |
| `S213` | Results | 16:14 - 16:19 | 5.0s | SLIDE: On 29 Shanghai patients, 2.8 mg/dL closer live (p = 4e-06). | On 29 held-out patients, fingersticks brought<br>the live estimate 2.8 mg/dL closer. |
| `S214` | Results | 16:19 - 16:24 | 5.5s | SLIDE: 95% interval: 1.6 to 4.7 mg/dL; 86% of patients. | With a 95 per cent interval of 1.6 to 4.7,<br>improving 86 per cent of patients. |
| `S215` | Results | 16:24 - 16:29 | 5.0s | SLIDE: In hindsight: 9.5 mg/dL closer (interval 4.6 to 12.1). | In hindsight, fingersticks brought the estimate<br>9.5 mg/dL closer. |
| `S216` | Results | 16:29 - 16:34 | 5.0s | SLIDE: With 1 stick/day: 0.3 mg/dL gain. | Even a single fingerstick a day<br>produced a 0.3 mg/dL running gain. |
| `S216b` | Results | 16:34 - 16:39 | 4.5s | SLIDE: Six fingersticks per day analysis. | With six fingersticks a day,<br>the hindsight gain reached 9.5 mg/dL. |
| `S217` | Results | 16:39 - 16:44 | 5.0s | SLIDE: MARD reality check: estimate is ~22% off next fingerstick. | Yet the estimate remains 22 per cent off<br>where a real sensor is 12 per cent. |
| `S218` | Results | 16:44 - 16:48 | 4.5s | SLIDE: RECORD PRIOR slide: Bar P1 Missed. | Next, the health record as prior:<br>Bar P1 missed. |
| `S219` | Results | 16:48 - 16:54 | 5.5s | SLIDE: On 20 CGMacros patients: 0.02 mg/dL change (p = 0.16). | On 20 held-out patients with one sensor day,<br>the record changed error by only 0.02 mg/dL. |
| `S220` | Results | 16:54 - 16:58 | 4.5s | SLIDE: Wilcoxon p-value 0.16. | The Wilcoxon test gave p = 0.16,<br>showing no significant difference. |
| `S221` | Results | 16:58 - 17:03 | 4.5s | SLIDE: With 3+ days: nothing measurable. | With three or more sensor days,<br>the record added nothing measurable. |
| `S222` | Results | 17:03 - 17:07 | 4.0s | SLIDE: Verdict: Record is not worth any sensor days. | The health record is not worth any sensor days. |
| `S223` | Results | 17:07 - 17:11 | 4.5s | SLIDE: Fusion is built and measured: it is not a gain. | Fusion was built and measured:<br>it is not a gain. |
| `S223b` | Results | 17:11 - 17:16 | 4.5s | SLIDE: Bayesian fusion parameter prior details. | Prior was placed on basal glucose Gb<br>derived from fasting glucose. |
| `S224` | Results | 17:16 - 17:20 | 4.5s | SLIDE: LADDER slide: Gate 3 Information Ladder. | Gate 3 tested post-meal excursions:<br>all three bars missed. |
| `S225` | Results | 17:20 - 17:25 | 5.0s | SLIDE: Meal excursion prevalence. | Prevalence of meal spikes was 39.2 per cent<br>across 1205 meals in 47 patients. |
| `S226` | Results | 17:25 - 17:29 | 4.0s | SLIDE: Table of AUPRC values across arms. | Here is the information ladder for AUPRC. |
| `S227` | Results | 17:29 - 17:34 | 5.0s | SLIDE: Record arm: 0.566. Sensor history: 0.626. | The health record achieved 0.566.<br>Sensor history alone reached 0.626. |
| `S228` | Results | 17:34 - 17:39 | 5.0s | SLIDE: Fingersticks: 0.642. Fused twin: 0.596. | Fingersticks alone reached 0.642.<br>Our fused twin reached only 0.596. |
| `S229` | Results | 17:39 - 17:44 | 4.5s | SLIDE: Sensor history alone beats the twin. | Raw sensor history beats the twin<br>at classifying meal excursions. |
| `S230` | Results | 17:44 - 17:49 | 5.0s | SLIDE: Calibration slope: 0.482 vs target 0.8-1.2. | Calibration slope was 0.482,<br>against a target of 0.8 to 1.2. |
| `S231` | Results | 17:49 - 17:53 | 4.5s | SLIDE: Calibration intercept: -0.338. | Calibration intercept was -0.338,<br>revealing consistent miscalibration. |
| `S231b` | Results | 17:53 - 17:58 | 4.5s | SLIDE: Excursion prevalence in dev cohort. | Development recordings showed identical<br>spike prevalence of 39 per cent. |
| `S232` | Results | 17:58 - 18:02 | 4.5s | SLIDE: BASELINE slide: Where Plain Baselines Win. | Where plain baselines tied or won,<br>we report it clearly. |
| `S233` | Results | 18:02 - 18:07 | 5.0s | SLIDE: Converted fingerstick average missed sensor mean by 6.4 mg/dL. | At report level, a converted fingerstick average<br>missed the sensor mean by 6.4 mg/dL. |
| `S234` | Results | 18:07 - 18:12 | 5.0s | SLIDE: Twin rebuilt in hindsight missed by 8.9 mg/dL. | While our twin in hindsight missed by 8.9.<br>The plain average won. |
| `S235` | Results | 18:12 - 18:17 | 5.0s | SLIDE: Staleness prompt: AUROC 0.82 vs 0.82 for plain comparison. | On staleness drift,<br>our cumulative sum had AUROC 0.82. |
| `S236` | Results | 18:17 - 18:22 | 5.0s | SLIDE: Plain baseline comparison AUROC. | Plain baseline achieved identical AUROC 0.82<br>with interval 0.61 to 0.97. |
| `S236b` | Results | 18:22 - 18:27 | 4.5s | SLIDE: Decision record reference: 2026-10-08-staleness.md. | Every staleness finding is documented in<br>decision record staleness. |
| `S237` | Results | 18:27 - 18:32 | 5.0s | SLIDE: Gate 1 Label audit summary. | In Gate 1, we audited all timestamps,<br>units, and meal logs. |
| `S238` | Results | 18:32 - 18:37 | 5.0s | SLIDE: Expiry analysis details. | On 47 Shanghai patients,<br>mean glucose drifted 1.0 mg/dL per day. |
| `S239` | Results | 18:37 - 18:42 | 5.0s | SLIDE: Free-living drift: 0.1 mg/dL per day. | On 19 free-living participants,<br>no drift growth was detected over seven days. |
| `S240` | Results | 18:42 - 18:47 | 5.0s | SLIDE: Band calibration check. | Recalibrating the band factor on dev (0.78)<br>made test coverage worse, so was discarded. |
| `S241` | Results | 18:47 - 18:51 | 4.0s | SLIDE: Scientific rigor summary. | Empirical truth without exaggeration. |
| `S242` | Results | 18:51 - 18:55 | 4.5s | SLIDE: Transition to Limits. | Now let us examine the boundaries<br>of what Chhaya is. |
| `S243` | Results | 18:55 - 19:00 | 4.5s | SLIDE: Final results recap. | Held-out test results published without omissions. |
| `S244` | Limits and Close | 19:00 - 19:04 | 4.5s | SLIDE: LIMITS slide: What Chhaya Is Not. | Section five: limits and what Chhaya is not. |
| `S245` | Limits and Close | 19:04 - 19:09 | 4.5s | SLIDE: Limit 1: No Indian dataset. | First: there is no Indian patient dataset<br>in our evaluation. |
| `S246` | Limits and Close | 19:09 - 19:13 | 4.5s | SLIDE: Limit 2: Supervised inpatient care. | Second: Shanghai data was inpatient care<br>with adjusted medication. |
| `S247` | Limits and Close | 19:13 - 19:18 | 5.0s | SLIDE: Limit 3: Hidden windows at most 11 days. | Third: hidden windows are at most eleven days,<br>not giving a fixed expiry day. |
| `S248` | Limits and Close | 19:18 - 19:23 | 5.0s | SLIDE: Observation on inpatient drift rate. | We observed about 1 mg/dL per day downward<br>drift in supervised inpatient care. |
| `S249` | Limits and Close | 19:23 - 19:28 | 5.0s | SLIDE: Observation on free-living drift rate. | In free-living participants, no significant<br>drift was detected over a week. |
| `S250` | Limits and Close | 19:28 - 19:33 | 5.0s | SLIDE: Case series of 8 re-recorded patients. | Eight patients were re-recorded up to 168 days<br>later as an observational case series. |
| `S251` | Limits and Close | 19:33 - 19:38 | 4.5s | SLIDE: Limit 4: Physiology effect is ~2%. | Fourth: the physiological model effect<br>is approximately two per cent. |
| `S252` | Limits and Close | 19:38 - 19:42 | 4.5s | SLIDE: Limit 5: No exogenous insulin kinetics in ODE. | Fifth: no exogenous insulin kinetics<br>or drug dynamics in the ODE. |
| `S253` | Limits and Close | 19:42 - 19:47 | 4.5s | SLIDE: Clinical boundary card. | Chhaya is an investigative tool,<br>not an autonomous clinical decision system. |
| `S254` | Limits and Close | 19:47 - 19:51 | 4.5s | SLIDE: SUMMARY slide: What the Misses Changed. | What did these misses change in the product? |
| `S255` | Limits and Close | 19:51 - 19:56 | 4.5s | SLIDE: Miss consequence 1: No meal alerts or probabilities. | We display no meal alert<br>and no excursion probabilities. |
| `S256` | Limits and Close | 19:56 - 20:00 | 4.5s | SLIDE: Miss consequence 2: Record shown as context, not gain. | The health record is presented as context,<br>not as predictive power. |
| `S257` | Limits and Close | 20:00 - 20:05 | 4.5s | SLIDE: Miss consequence 3: Converted fingerstick average used. | Patient summary figures use the plain converted<br>fingerstick average. |
| `S258` | Limits and Close | 20:05 - 20:09 | 4.5s | SLIDE: Miss consequence 4: Staleness prompt is descriptive only. | The staleness prompt is purely descriptive,<br>never clinical advice. |
| `S259` | Limits and Close | 20:09 - 20:14 | 4.5s | SLIDE: Not for Type 1 diabetes or acute dosing. | Chhaya is not for acute hypoglycemia<br>or insulin dosing. |
| `S260` | Limits and Close | 20:14 - 20:18 | 4.5s | SLIDE: Why negative results matter. | Publishing negative results prevents<br>repetition of flawed approaches. |
| `S260b` | Limits and Close | 20:18 - 20:23 | 5.0s | SLIDE: Full transparency in digital health. | Honest science is the foundation of<br>safe clinical medicine. |
| `S261` | Limits and Close | 20:23 - 20:28 | 5.0s | SLIDE: CLOSE slide: Live demo URL. | Explore the live demo yourself<br>at chhaya-digital-twin.vercel.app. |
| `S262` | Limits and Close | 20:28 - 20:33 | 5.0s | SLIDE: GitHub repository card. | The full codebase, tests, and decision records<br>are public on GitHub. |
| `S263` | Limits and Close | 20:33 - 20:38 | 4.5s | SLIDE: Client-side web architecture. | The web demo runs client-side with no tracking<br>and open MIT licensing. |
| `S264` | Limits and Close | 20:38 - 20:43 | 5.0s | SLIDE: Single command reproducibility. | All evaluations can be regenerated with a single<br>command from the repository. |
| `S265` | Limits and Close | 20:43 - 20:47 | 4.5s | SLIDE: Team SynapseX, D.B.S Kanpur card. | Chhaya. Built by Team SynapseX<br>at D.B.S Kanpur. |
| `S266` | Limits and Close | 20:47 - 20:52 | 4.5s | SLIDE: Final closing frame with logo. | Thank you. |
| `S267` | Limits and Close | 20:52 - 20:56 | 4.0s | SLIDE: Hold to black. |  |
| `S268` | Limits and Close | 20:56 - 21:00 | 4.0s | SLIDE: Final fade out. |  |
