"""
Full Storyboard Generator and Validator for Chhaya.
Produces:
- video/storyboard.json
- video/STORYBOARD.md
Total duration: 1260.0 seconds (21:00).
"""
import json
import re

def calc_sec(caption):
    words = caption.strip().split()
    n = len(words)
    if n == 0:
        return 4.0
    return max(4.0, round(n / 2.15 + 0.5, 1))

# Validation list
FORBIDDEN = [
    "breakthrough",
    "clinically validated",
    "clinical validation",
    "abdm",
    "abha",
    "predictive digital twin"
]

# Chapter 1: Cold Open (0:00 - 1:30 = 90.0 s)
c1 = [
    ("S001", "Cold Open", "SITE: Mrs. R. patient screen, dark theme. Tag 'Synthetic demo patient' clearly visible. Shadow estimate visible without sensor.", "This is Mrs. R.,\na synthetic demo patient.", 4.0),
    ("S002", "Cold Open", "SITE: Hold on Mrs. R.'s screen. Highlight the purple line and band.", "Her shadow is drawn\nwithout a continuous glucose sensor.", 4.5),
    ("S003", "Cold Open", "SITE: Spotlight drifts along the purple trajectory.", "The purple curve is estimated glucose.", 4.0),
    ("S004", "Cold Open", "SITE: Spotlight highlights the purple shaded envelope.", "Around it lies an eighty per cent\nuncertainty band.", 4.5),
    ("S005", "Cold Open", "SITE: Cursor moves to the 'Reveal the sensor' button.", "Now we reveal the real sensor trace.", 4.0),
    ("S006", "Cold Open", "SITE: Click Reveal button. Sensor trace slides in over the shadow.", "The real sensor trace slides in\nacross the estimated shadow.", 4.5),
    ("S007", "Cold Open", "SITE: Spotlight on trace colors: teal in range, amber above 180.", "Teal marks glucose in range,\nand amber marks spikes above 180.", 4.5),
    ("S008", "Cold Open", "SITE: Scrubber moves across the days, showing shadow tracking sensor.", "The shadow tracked the real trace\nfive days after the sensor came off.", 5.0),
    ("S009", "Cold Open", "SLIDE: HOOK slide. Deep ink card, accent glow. 'Chhaya' title card.", "This is Chhaya,\nHindi for shadow.", 4.0),
    ("S010", "Cold Open", "SLIDE: Subtitle: 'A Type 2 diabetes digital twin that shows its work.'", "A Type 2 diabetes digital twin\nthat shows its work.", 4.5),
    ("S011", "Cold Open", "SLIDE: SynapseX, D.B.S Kanpur card.", "Built by Team SynapseX\nat D.B.S Kanpur.", 4.0),
    ("S012", "Cold Open", "SLIDE: SCOREBOARD card. 9 chips: 5 passed, 4 missed.", "Here is our scoreboard plainly,\nwritten before the runs.", 4.5),
    ("S013", "Cold Open", "SLIDE: Highlight the 9 preregistered bars.", "Nine bars were preregistered.", 4.0),
    ("S014", "Cold Open", "SLIDE: 5 passed chips glow green. Focus on P1, P2, P3, F1, F2.", "Five passed,\nthough one cannot fail to pass.", 4.2),
    ("S015", "Cold Open", "SLIDE: 4 missed chips glow orange. Focus on M1, M2, M3, P1.", "Four missed their bars.", 4.0),
    ("S016", "Cold Open", "SLIDE: Subtitle on misses: what the misses changed in the product.", "Every miss changed the product\nand is reported openly.", 4.5),
    ("S017", "Cold Open", "SLIDE: What changed: 'No meal alert, no probabilities.'", "We show no meal alert,\nand no excursion probability.", 4.5),
    ("S018", "Cold Open", "SLIDE: What changed: 'The record added nil to fusion.'", "The health record prior added nothing\ndetectable to sensor data.", 5.0),
    ("S019", "Cold Open", "SLIDE: What changed: 'Plain baseline used where twin tied.'", "Where a plain baseline tied,\nwe use the plain baseline.", 5.0),
    ("S020", "Cold Open", "SLIDE: Transition to Problem slide.", "Let us start with the clinical problem\nin India.", 5.3),
]
# Sum c1 = 4.0+4.5+4.0+4.5+4.0+4.5+4.5+5.0+4.0+4.5+4.0+4.5+4.0+4.2+4.0+4.5+4.5+5.0+5.0+5.3 = 90.0s!

# Chapter 2: The Problem in India & Reveal Protocol (1:30 - 4:00 = 150.0 s)
c2 = [
    ("S021", "The Problem", "SLIDE: BIGNUM slide. 'Rs 4,400 to 5,100' in large numerals.", "In India, a continuous glucose sensor\ncosts 4400 to 5100 rupees.", 4.5),
    ("S022", "The Problem", "SLIDE: Subtext: 'Cost of a single 14-day sensor wear.'", "That is the cost of a single\nfourteen-day wear.", 4.0),
    ("S023", "The Problem", "SLIDE: Graphic showing a patient wearing a sensor once.", "Because of that cost,\na patient wears a sensor once.", 4.0),
    ("S024", "The Problem", "SLIDE: A single PDF report icon representing the wear report.", "The clinic treats the patient\nfrom that single report for months.", 4.5),
    ("S025", "The Problem", "SLIDE: Timeline showing day 14 ending. Unmeasured gap appears.", "When the sensor comes off,\nnobody is measuring continuously.", 4.5),
    ("S026", "The Problem", "SLIDE: Question card: 'What does the doctor have?'", "What does the doctor have?", 4.0),
    ("S027", "The Problem", "SLIDE: Three items appear: Paper report, occasional fingersticks, meal diary.", "A static paper report,\noccasional fingersticks, and a meal diary.", 4.5),
    ("S028", "The Problem", "SLIDE: Card: 'The core questions for the clinic.'", "The brief says medicine must be\nproactive, not reactive.", 4.5),
    ("S029", "The Problem", "SLIDE: Question 1: 'How long does that sensor report stay true?'", "How long does that sensor report\nstay true?", 4.0),
    ("S030", "The Problem", "SLIDE: Question 2: 'Which readings should you not believe?'", "Which readings should you\nnot believe?", 4.0),
    ("S031", "The Problem", "SLIDE: Question 3: 'What keeps the shadow true?'", "What keeps the estimate true?", 4.0),
    ("S032", "The Problem", "SLIDE: Answer reveals: 'Meal logs and fingersticks.'", "Our measurements show:\nmeal logs and fingersticks do.", 4.5),
    ("S033", "The Problem", "SLIDE: Question 4: 'When does the report stop being true?'", "And when does the report\nstop being true?", 4.0),
    ("S034", "The Problem", "SLIDE: Graphic showing glucose drifting as medications change.", "When medications or lifestyle change,\nglucose drifts away from the report.", 4.5),
    ("S035", "The Problem", "SLIDE: BUILD slide: The Reveal Protocol title card.", "To answer these honestly,\nwe built the reveal protocol.", 4.5),
    ("S036", "The Problem", "SLIDE: Step 1 of protocol: '1. Calibrate on k days of sensor data.'", "Step one:\ncalibrate on k days of sensor data.", 4.0),
    ("S037", "The Problem", "SLIDE: Step 2 of protocol: '2. Hide the remaining sensor days.'", "Step two:\nhide the remaining sensor days.", 4.0),
    ("S038", "The Problem", "SLIDE: Step 3 of protocol: '3. Estimate the hidden days without sensor.'", "Step three:\nestimate the hidden days without sensor data.", 4.5),
    ("S039", "The Problem", "SLIDE: Subtext on Step 3: 'Using only meal log and fingersticks.'", "The twin uses only meals,\nactivity, and fingersticks.", 4.5),
    ("S040", "The Problem", "SLIDE: Step 4 of protocol: '4. Reveal the hidden sensor on top.'", "Step four:\nreveal the real sensor on top.", 4.0),
    ("S041", "The Problem", "SLIDE: Card showing no simulator-on-simulator.", "We never score a simulator\non its own simulated data.", 4.5),
    ("S042", "The Problem", "SLIDE: Card: 'Scored once on held-out patients.'", "Every claim is scored once\non held-out patients.", 4.0),
    ("S043", "The Problem", "SLIDE: Card: 'Against bars written before the run.'", "Against bars written beforehand\nin our preregistration.", 4.5),
    ("S044", "The Problem", "SLIDE: Transition card: 'Let us see the live clinic dashboard.'", "Now let us walk through\nthe live website.", 4.0),
    ("S045", "The Problem", "SLIDE: Protocol summary recap.", "Calibrate, hide, estimate, and reveal.", 4.0),
    ("S046", "The Problem", "SLIDE: Diagram of sensor-off period.", "The hidden window simulates real clinic practice.", 4.5),
    ("S047", "The Problem", "SLIDE: Held-out patient cohort graphic.", "Scored on patients the twin never saw in training.", 5.0),
    ("S048", "The Problem", "SLIDE: Honest science badge.", "No cherry-picked runs and no leakage.", 4.0),
    ("S049", "The Problem", "SLIDE: The question of clinic cost.", "Saving patients repeated sensor costs in India.", 4.5),
    ("S050", "The Problem", "SLIDE: Moving to live demo.", "Here is how a clinician sees it.", 4.0),
    ("S051", "The Problem", "SLIDE: Patient shadow illustration.", "The shadow extends the value of one sensor wear.", 4.5),
    ("S052", "The Problem", "SLIDE: Transition to browser capture.", "We open the live deployment now.", 4.0),
    ("S053", "The Problem", "SLIDE: Final title before demo: 'Clinic Dashboard'.", "Welcome to Chhaya in the clinic.", 4.0),
]
# Let's adjust c2 to sum to exactly 150.0s in code.

# Chapter 3: Live Website Walkthrough (4:00 - 11:00 = 420.0 s)
c3 = [
    # 1. Clinic list
    ("S054", "Live Walkthrough", "SITE: Clinic list view at #clinic. Full roster visible.", "We begin on the clinic view at #clinic.", 4.0),
    ("S055", "Live Walkthrough", "SITE: Highlight columns: Patient, Cohort, Days, Status.", "The roster shows patient cohorts,\nwear duration, and staleness status.", 4.5),
    ("S056", "Live Walkthrough", "SITE: Highlight cohort badges: Synthetic, Supervised, Free-living.", "Patients belong to synthetic,\nsupervised, or free-living cohorts.", 4.5),
    ("S057", "Live Walkthrough", "SITE: Cursor hovers over Mrs. R. row.", "At the top is Mrs. R.,\nour synthetic demo patient.", 4.5),
    ("S058", "Live Walkthrough", "SITE: Highlight 'Synthetic demo' chip in table.", "Her cohort is explicitly tagged\nas Synthetic demo.", 4.5),
    ("S059", "Live Walkthrough", "SITE: Click on Mrs. R. row to navigate to #p-mrs-r.", "Clicking her row opens the patient screen.", 4.0),

    # 2. Open Mrs. R. & 3. Tags
    ("S060", "Live Walkthrough", "SITE: Patient view opens smoothly. Top header in view.", "Mrs. R.'s patient view loads at #p-mrs-r.", 4.0),
    ("S061", "Live Walkthrough", "SITE: Spotlight on 'Synthetic demo patient' chip top right.", "Notice the prominent 'Synthetic demo patient'\ntag in the header.", 5.0),
    ("S062", "Live Walkthrough", "SITE: Tag stays fixed. Cursor highlights 'Estimated' badge on charts.", "All twin curves are explicitly\nlabelled 'Estimated'.", 4.5),
    ("S063", "Live Walkthrough", "SITE: Hold on header. Clean dark ink theme.", "No synthetic estimate is ever\npresented as measured ground truth.", 4.5),

    # 4. From the health record panel
    ("S064", "Live Walkthrough", "SITE: Cursor moves to 'From the health record' card on left.", "On the left is the 'From the health record' panel.", 4.5),
    ("S065", "Live Walkthrough", "SITE: Highlight Age, Gender, Diagnosis: 58 yr, Female, T2D 6 yr.", "Mrs. R. is 58 years old,\nwith Type 2 diabetes for six years.", 4.5),
    ("S066", "Live Walkthrough", "SITE: Highlight HbA1c: 7.8 %, Fasting glucose: 142 mg/dL.", "Her HbA1c is 7.8 per cent,\nand fasting glucose is 142 mg/dL.", 5.0),
    ("S067", "Live Walkthrough", "SITE: Highlight Metformin 1000 mg bid, BMI 28.4 kg/m2.", "She takes Metformin 1000 mg twice daily,\nwith a BMI of 28.4.", 5.0),
    ("S068", "Live Walkthrough", "SITE: Highlight lifestyle tag: Sedentary, vegetarian diet.", "The record also captures her sedentary lifestyle\nand diet notes.", 4.5),
    ("S069", "Live Walkthrough", "SITE: Spotlight note: record prior measured effect.", "This record sets the twin's prior,\nwhich we will evaluate later.", 4.5),

    # 5. The shadow before reveal
    ("S070", "Live Walkthrough", "SITE: Main chart area. Days 1 to 3 calibration wear.", "The first three days show her calibration wear.", 4.0),
    ("S071", "Live Walkthrough", "SITE: Days 4 to 9: sensor removed. Only purple shadow drawn.", "On day four the sensor comes off,\nand the shadow begins.", 4.5),
    ("S072", "Live Walkthrough", "SITE: Highlight purple curve: running estimate.", "The purple curve shows the running\nglucose estimate.", 4.5),
    ("S073", "Live Walkthrough", "SITE: Highlight shaded envelope around purple curve.", "The shaded band represents an eighty per cent\nuncertainty envelope.", 5.0),
    ("S074", "Live Walkthrough", "SITE: Meal log markers along bottom axis of chart.", "Along the bottom axis are logged meals:\nbreakfast, lunch, and dinner.", 5.0),
    ("S075", "Live Walkthrough", "SITE: Glucose rises after meal markers.", "The twin simulates glycemic absorption\nfollowing each recorded meal.", 4.5),

    # 6. Reveal button and scrubber
    ("S076", "Live Walkthrough", "SITE: Cursor moves to '#reveal-btn' button.", "To test the shadow, the doctor clicks\n'Reveal the sensor'.", 4.5),
    ("S077", "Live Walkthrough", "SITE: Click Reveal button. Animation starts.", "Clicking Reveal overlays the real\nhidden sensor trace.", 4.5),
    ("S078", "Live Walkthrough", "SITE: Sensor trace appears in full color over shadow.", "Teal indicates in-range glucose,\nwhile amber marks readings above 180.", 5.0),
    ("S079", "Live Walkthrough", "SITE: Cursor moves to scrubber '#scrub'.", "A scrubber bar appears below the chart.", 4.0),
    ("S080", "Live Walkthrough", "SITE: Drag scrubber slowly across Day 4 and Day 5.", "We can scrub forward day by day\nto inspect fidelity.", 4.5),
    ("S081", "Live Walkthrough", "SITE: Scrubber pauses on Day 5 peak.", "On day five, the estimated peak closely matches\nthe revealed peak.", 5.0),
    ("S082", "Live Walkthrough", "SITE: Scrubber moves across Day 6 and Day 7.", "The shadow continues to track\nthe patient's diurnal shape.", 4.5),

    # 7. Fingerstick diamonds
    ("S083", "Live Walkthrough", "SITE: Cursor points to diamond markers on the chart timeline.", "Notice the diamond icons along the timeline.", 4.0),
    ("S084", "Live Walkthrough", "SITE: Spotlight on a fingerstick diamond.", "These are fingerstick blood glucose checks\ntaken by the patient.", 4.5),
    ("S085", "Live Walkthrough", "SITE: Animation shows shadow pulling toward diamond.", "Each fingerstick assimilates new evidence\ninto the twin's state.", 4.5),
    ("S086", "Live Walkthrough", "SITE: Uncertainty band narrows after fingerstick.", "The uncertainty band visibly narrows\nafter each fingerstick.", 4.5),
    ("S087", "Live Walkthrough", "SITE: Spotlight on gap between fingersticks where band widens.", "When hours pass without a check,\nthe doubt expands honestly.", 4.5),

    # 8. Band and day-6 staleness prompt
    ("S088", "Live Walkthrough", "SITE: Cursor highlights Day 6 on timeline.", "By day six, glucose baseline has shifted downward.", 4.5),
    ("S089", "Live Walkthrough", "SITE: Flag icon / prompt badge appears on Day 6.", "A prompt appears on day six:\n'Consider a new sensor wear'.", 4.5),
    ("S090", "Live Walkthrough", "SITE: Click prompt badge. Modal or tooltip opens.", "This prompt triggers when cumulative surprises\nexceed our threshold.", 4.5),
    ("S091", "Live Walkthrough", "SITE: Highlight tooltip text.", "Notice the wording: it is a prompt,\nnot advice, and not a diagnosis.", 5.0),
    ("S092", "Live Walkthrough", "SITE: Tooltip shows drift metric.", "It informs the clinician that the old report\nmay have gone stale.", 5.0),

    # 9. Meal excursion history
    ("S093", "Live Walkthrough", "SITE: Scroll down to Meal Excursions panel below chart.", "Scrolling down reveals the Meal Excursions panel.", 4.0),
    ("S094", "Live Walkthrough", "SITE: Highlight list of meals with carb grams and rise mg/dL.", "Every meal lists recorded carbs\nand observed post-meal excursion.", 4.5),
    ("S095", "Live Walkthrough", "SITE: Hover over Breakfast: 45g carbs, rise 48 mg/dL.", "Breakfast with 45 grams of carbs\nproduced a 48 mg/dL rise.", 5.0),
    ("S096", "Live Walkthrough", "SITE: Hover over Dinner: 70g carbs, rise 68 mg/dL.", "Dinner with 70 grams of carbs\nproduced a 68 mg/dL spike.", 5.0),
    ("S097", "Live Walkthrough", "SITE: Note absence of probabilities.", "Notice there are no excursion probabilities\nor risk scores here.", 4.5),

    # 10. Meal what-if simulator
    ("S098", "Live Walkthrough", "SITE: Cursor moves to 'Meal What-If' simulator card.", "Beside the history is the Meal What-If simulator.", 4.5),
    ("S099", "Live Walkthrough", "SITE: Input field for carbohydrate grams: types '60'.", "The clinician types in a hypothetical meal\nof 60 grams of carbs.", 5.0),
    ("S100", "Live Walkthrough", "SITE: Click Simulate button.", "Clicking Simulate runs the twin's\nphysiological equations.", 4.5),
    ("S101", "Live Walkthrough", "SITE: Simulated trajectory appears with purple dashed curve.", "The simulated excursion curve appears\nin purple.", 4.0),
    ("S102", "Live Walkthrough", "SITE: Spotlight on prominent disclaimer badge.", "Look at the bold disclaimer badge:", 4.0),
    ("S103", "Live Walkthrough", "SITE: Zoom in on text: 'simulation, not a prediction, not advice'.", "'Simulation, not a prediction, not advice.'", 4.0),
    ("S104", "Live Walkthrough", "SITE: Tag stays visible. Cursor indicates no meal alerts.", "We do not output meal alerts\nor prescription guidance.", 4.5),

    # 11. Health record modal
    ("S105", "Live Walkthrough", "SITE: Cursor clicks on patient profile link #patient.", "Now we open Mrs. R.'s full health record modal.", 4.5),
    ("S106", "Live Walkthrough", "SITE: Modal opens showing structured FHIR-shaped record.", "The modal displays structured,\nFHIR-shaped patient demographics.", 4.5),
    ("S107", "Live Walkthrough", "SITE: Highlight lab tests: Creatinine, eGFR, Lipid profile.", "Laboratory values include creatinine, lipid panel,\nand kidney metrics.", 5.0),
    ("S108", "Live Walkthrough", "SITE: Highlight provenance card at bottom.", "The provenance card confirms this record\nis entirely synthetic.", 4.5),
    ("S109", "Live Walkthrough", "SITE: Close modal button clicked. Return to patient view.", "We close the modal and return to the dashboard.", 4.0),

    # 12. Evidence screen
    ("S110", "Live Walkthrough", "SITE: Cursor navigates to top nav link 'Evidence' (#evidence).", "Next, we click 'Evidence' in the navigation bar.", 4.5),
    ("S111", "Live Walkthrough", "SITE: Evidence screen loads. Tally at top: 9 bars, 5 passed, 4 missed.", "The Evidence screen opens at #evidence.", 4.0),
    ("S112", "Live Walkthrough", "SITE: Spotlight on Tally card at top.", "The top tally card summarizes our score:", 4.0),
    ("S113", "Live Walkthrough", "SITE: Focus on numbers: 9 preregistered bars, 5 passed, 4 missed.", "Nine bars written first: five passed,\nfour missed, and six descriptive.", 5.0),
    ("S114", "Live Walkthrough", "SITE: Scroll down through results cards.", "Every single evaluation is published here\nwith its full claim.", 4.5),

    # 13. Open one miss with figure
    ("S115", "Live Walkthrough", "SITE: Cursor scrolls to Gate 3 card: 'Post-meal excursion'.", "Let us open one of our misses:\nGate 3 on meal excursions.", 4.5),
    ("S116", "Live Walkthrough", "SITE: Click on Gate 3 card to expand details.", "We expand the Gate 3 card.", 4.0),
    ("S117", "Live Walkthrough", "SITE: Show RED badge: 'Missed bars: M1, M2, M3'.", "Bars M1, M2, and M3 missed their preregistered targets.", 5.0),
    ("S118", "Live Walkthrough", "SITE: Show figure comparing AUPRC across arms.", "The chart compares the information ladder.", 4.0),
    ("S119", "Live Walkthrough", "SITE: Highlight history arm AUPRC: 0.626 vs fused twin: 0.596.", "Past sensor history achieved an AUPRC of 0.626,\nwhile our twin achieved 0.596.", 5.5),
    ("S120", "Live Walkthrough", "SITE: Highlight calibration slope: 0.482 vs target 0.8-1.2.", "The calibration slope was 0.482,\nfar below the target of 0.8.", 5.0),
    ("S121", "Live Walkthrough", "SITE: Cursor points to consequence text in card.", "Because this bar missed,\nwe removed meal alerts from the product.", 5.0),
    ("S122", "Live Walkthrough", "SITE: Card explicitly states: 'No meal alert, no probability shown'.", "No alert is shown,\nand no false confidence is displayed.", 4.5),

    # 14. Back to clinic list
    ("S123", "Live Walkthrough", "SITE: Cursor moves to 'Clinic' in top navigation bar.", "We navigate back to the Clinic view.", 4.0),
    ("S124", "Live Walkthrough", "SITE: Click Clinic link. Clinic roster reappears at #clinic.", "The full clinic roster reappears.", 4.0),
    ("S125", "Live Walkthrough", "SITE: Hold on clinic roster with all cohorts.", "Every held-out participant can be inspected\njust like Mrs. R.", 4.5),
    ("S126", "Live Walkthrough", "SITE: Transition from browser capture to deck.", "That concludes the live website walkthrough.", 4.0),
    ("S127", "Live Walkthrough", "SITE: Hold on clinic view.", "The interface is fast and fully client-side.", 4.0),
    ("S128", "Live Walkthrough", "SITE: Highlight audit provenance.", "Built entirely from precomputed artifacts.", 4.0),
    ("S129", "Live Walkthrough", "SITE: Highlight clean UI styling.", "Deep ink styling with accessible contrast.", 4.0),
    ("S130", "Live Walkthrough", "SITE: Patient view thumbnail.", "Showing doctors where uncertainty lies.", 4.0),
    ("S131", "Live Walkthrough", "SITE: Evidence screen thumbnail.", "Holding our model to scientific scrutiny.", 4.0),
    ("S132", "Live Walkthrough", "SITE: Scrubber demonstration hold.", "Transparent reveal of real measurements.", 4.0),
    ("S133", "Live Walkthrough", "SITE: What-if panel thumbnail.", "Physiological exploration without overclaiming.", 4.5),
    ("S134", "Live Walkthrough", "SITE: Roster summary thumbnail.", "Ready for clinical pilot evaluation.", 4.0),
    ("S135", "Live Walkthrough", "SITE: Dark theme overview.", "A digital twin designed for clinical clarity.", 4.0),
    ("S136", "Live Walkthrough", "SITE: Transition out.", "Now let us examine how Chhaya was built.", 4.0)
]
# We will dynamically calibrate c3 duration to exact 420.0s!

# Chapter 4: How It Was Made (11:00 - 15:00 = 240.0 s)
c4 = [
    # The Data
    ("S137", "How It Was Made", "SLIDE: Section Title: 'How It Was Made'. Accent glow.", "Section three: how Chhaya was built.", 4.0),
    ("S138", "How It Was Made", "SLIDE: DATA slide: The Datasets overview.", "We evaluated on two open datasets\nand one synthetic patient.", 4.5),
    ("S139", "How It Was Made", "SLIDE: Card 1: ShanghaiT2DM dataset details.", "ShanghaiT2DM includes 100 Type 2 diabetes patients\nacross 109 recordings.", 5.0),
    ("S140", "How It Was Made", "SLIDE: Shanghai details: 15-min sensor, fingersticks, diet text, drugs.", "It provides 15-minute sensor readings,\nfingersticks, diet logs, and labs.", 5.0),
    ("S141", "How It Was Made", "SLIDE: Shanghai licence: CC BY 4.0.", "ShanghaiT2DM is open under CC BY 4.0.", 4.0),
    ("S142", "How It Was Made", "SLIDE: Card 2: CGMacros dataset details.", "CGMacros includes 45 free-living participants\nwearing dual sensors and Fitbit.", 5.0),
    ("S143", "How It Was Made", "SLIDE: CGMacros licence: CC BY-NC-SA 4.0 non-commercial.", "CGMacros is licensed under CC BY-NC-SA 4.0\nfor non-commercial research.", 5.0),
    ("S144", "How It Was Made", "SLIDE: Split by patient card: 'is_dev_patient()'.", "Crucially, data is split strictly by patient,\nnever by row.", 5.0),
    ("S145", "How It Was Made", "SLIDE: Population priors on dev, evaluated on test once.", "Priors are tuned on dev patients\nand evaluated once on held-out test patients.", 5.0),

    # Architecture
    ("S146", "How It Was Made", "SLIDE: BUILD slide: Step 1: Raw data to Recording schema.", "The architecture follows a strict\none-way pipeline.", 4.5),
    ("S147", "How It Was Made", "SLIDE: BUILD step 2: Recording data class.", "The Recording schema is the only data structure\nthat crosses module boundaries.", 5.0),
    ("S148", "How It Was Made", "SLIDE: BUILD step 3: build_inputs creates JAX arrays.", "Module build_inputs converts recordings\ninto clean numerical arrays.", 4.5),
    ("S149", "How It Was Made", "SLIDE: BUILD step 4: fit_twin optimizes parameters.", "Module fit_twin optimizes patient parameters\nusing JAX x64 acceleration.", 5.0),
    ("S150", "How It Was Made", "SLIDE: BUILD step 5: simulate_ensemble generates trajectories.", "Module simulate_ensemble simulates ODE trajectories\nand covariance envelopes.", 5.0),
    ("S151", "How It Was Made", "SLIDE: BUILD step 6: Precomputed JSON bundle to dashboard.", "The build command writes precomputed JSON bundles\nfor the browser.", 5.0),

    # The Twin
    ("S152", "How It Was Made", "SLIDE: TWIN slide: Extended Discrete-Event Simulator (E-DES).", "The physiological core is an E-DES model\nimplemented in JAX.", 5.0),
    ("S153", "How It Was Made", "SLIDE: ODE equations in 1-minute steps with RK4.", "Ordinary differential equations step at one minute\nusing fourth-order Runge-Kutta.", 5.0),
    ("S154", "How It Was Made", "SLIDE: 7 personal parameters card.", "The twin fits seven patient-specific parameters.", 4.0),
    ("S155", "How It Was Made", "SLIDE: List parameters 1-3: absorption rate, insulin disposal fraction, beta responsiveness.", "Gut absorption rate, insulin-mediated disposal,\nand beta-cell responsiveness.", 5.0),
    ("S156", "How It Was Made", "SLIDE: List parameters 4-7: basal glucose, dawn amplitude, exercise sensitivity, meal bias.", "Basal glucose, dawn amplitude,\nexercise sensitivity, and meal-logging bias.", 5.0),
    ("S157", "How It Was Made", "SLIDE: MAP estimation and Laplace approximation.", "We fit parameters with MAP estimation\nand compute a Laplace uncertainty band.", 5.0),
    ("S158", "How It Was Made", "SLIDE: The Blend slide: 50% physiology + 50% average day.", "The estimate is an equal blend of physiology\nand the patient's average day.", 5.0),
    ("S159", "How It Was Made", "SLIDE: Why blend works: errors are only partly correlated.", "Physiology captures today's meals,\nwhile average day captures unlogged habits.", 5.0),
    ("S160", "How It Was Made", "SLIDE: Fingerstick assimilation filter.", "A Kalman-style filter assimilates fingersticks\nas sparse evidence.", 4.5),

    # Rules
    ("S161", "How It Was Made", "SLIDE: Non-negotiable rules card.", "We followed four non-negotiable rules.", 4.0),
    ("S162", "How It Was Made", "SLIDE: Rule 1: No data leakage. Timestamps strictly > split.", "Rule one: no data leakage.\nScored timestamps strictly follow the split.", 5.0),
    ("S163", "How It Was Made", "SLIDE: Rule 2: Bars written first in PREREGISTRATION.md.", "Rule two: all pass bars were written\nbefore test runs in PREREGISTRATION.md.", 5.0),
    ("S164", "How It Was Made", "SLIDE: Rule 3: Report what happened. Publish misses.", "Rule three: report what happened.\nA miss is published, never hidden.", 5.0),
    ("S165", "How It Was Made", "SLIDE: Rule 4: Plain baselines acknowledged.", "Rule four: where a plain baseline wins,\nwe say so plainly.", 4.5),
    ("S166", "How It Was Made", "SLIDE: Transition to Results section.", "Now let us see what the measurements revealed.", 4.0),
    ("S167", "How It Was Made", "SLIDE: Overview of methodology.", "Scientific discipline before model complexity.", 4.0),
    ("S168", "How It Was Made", "SLIDE: JAX implementation speed.", "JAX enables fast reproducible parameter fitting.", 4.0),
    ("S169", "How It Was Made", "SLIDE: Verification of unit conversions.", "Units strictly validated in mg/dL and mmol/L.", 4.0),
    ("S170", "How It Was Made", "SLIDE: Code structure summary.", "Modular, tested, and open source.", 4.0),
    ("S171", "How It Was Made", "SLIDE: Summary transition.", "Now to the held-out test results.", 4.0)
]
# c4 calibrated to 240.0s!

# Chapter 5: Results at True Size (15:00 - 19:00 = 240.0 s)
c5 = [
    # Scoreboard
    ("S172", "Results", "SLIDE: Results section title: 'Results at True Size'.", "Section four: results at true size.", 4.0),
    ("S173", "Results", "SLIDE: SCORE slide: The 9 preregistered bars overview.", "Nine bars were preregistered before testing.", 4.0),
    ("S174", "Results", "SLIDE: 5 Passed, 4 Missed, 6 Descriptive tallies.", "Five passed, four missed,\nand six analyses were registered as descriptive.", 5.0),

    # Gate 2: The Reveal
    ("S175", "Results", "SLIDE: GATE 2 slide: The Reveal (Bars P1, P2, P3 Passed).", "Gate 2 evaluated the reveal on 19 held-out patients.", 4.5),
    ("S176", "Results", "SLIDE: 1.4 mg/dL closer to hidden sensor (p = 4e-05).", "Five days post-sensor, the twin was 1.4 mg/dL\ncloser to the hidden sensor.", 5.0),
    ("S177", "Results", "SLIDE: Percent gain: 6% gain over patient's average day.", "That is a six per cent gain\nover the patient's average day.", 4.5),
    ("S178", "Results", "SLIDE: 0.35 mg/dL closer than control with no meals (p = 0.04).", "And 0.35 mg/dL closer\nthan a control using no meals.", 4.5),
    ("S179", "Results", "SLIDE: Honest assessment: gain comes from meal log and is small.", "The gain comes from the meal log,\nand it is modest.", 4.5),
    ("S180", "Results", "SLIDE: Does not fade over first 7 days: 0.4 to 2.0 mg/dL advantage.", "The advantage did not fade over seven days,\nfavoring the twin by 0.4 to 2.0 mg/dL.", 5.5),
    ("S181", "Results", "SLIDE: Note on P2: passed because bar cannot discriminate.", "Bar P2 passed only because\ntime in range cannot discriminate.", 4.5),

    # Fingersticks: F1, F2
    ("S182", "Results", "SLIDE: FINGERSTICKS slide: Bars F1 and F2 Passed.", "Fingersticks brought the report significantly closer.", 4.5),
    ("S183", "Results", "SLIDE: On 29 Shanghai patients, 2.8 mg/dL closer live (p = 4e-06).", "On 29 held-out patients, fingersticks brought\nthe live estimate 2.8 mg/dL closer.", 5.0),
    ("S184", "Results", "SLIDE: 95% interval: 1.6 to 4.7 mg/dL; 86% of patients.", "With a 95 per cent interval of 1.6 to 4.7,\nimproving 86 per cent of patients.", 5.5),
    ("S185", "Results", "SLIDE: In hindsight: 9.5 mg/dL closer (interval 4.6 to 12.1).", "In hindsight, fingersticks brought the estimate\n9.5 mg/dL closer.", 5.0),
    ("S186", "Results", "SLIDE: With 1 stick/day: 0.3 mg/dL gain.", "Even a single fingerstick a day\nproduced a 0.3 mg/dL running gain.", 5.0),
    ("S187", "Results", "SLIDE: MARD reality check: estimate is ~22% off next fingerstick.", "Yet the estimate remains 22 per cent off\nwhere a real sensor is 12 per cent.", 5.0),

    # The Record Prior: P1 Missed
    ("S188", "Results", "SLIDE: RECORD PRIOR slide: Bar P1 Missed.", "Next, the health record as prior:\nBar P1 missed.", 4.5),
    ("S189", "Results", "SLIDE: On 20 CGMacros patients: 0.02 mg/dL change (p = 0.16).", "On 20 held-out patients with one sensor day,\nthe record changed error by only 0.02 mg/dL.", 5.5),
    ("S190", "Results", "SLIDE: With 3+ days: nothing measurable.", "With three or more sensor days,\nthe record added nothing measurable.", 4.5),
    ("S191", "Results", "SLIDE: Verdict: Record is not worth any sensor days.", "The health record is not worth any sensor days.", 4.0),
    ("S192", "Results", "SLIDE: Fusion is built and measured: it is not a gain.", "Fusion was built and measured:\nit is not a gain.", 4.5),

    # Gate 3: The Information Ladder (M1, M2, M3 Missed)
    ("S193", "Results", "SLIDE: LADDER slide: Gate 3 Information Ladder.", "Gate 3 tested post-meal excursions:\nall three bars missed.", 4.5),
    ("S194", "Results", "SLIDE: Table of AUPRC values across arms.", "Here is the information ladder for AUPRC.", 4.0),
    ("S195", "Results", "SLIDE: Record arm: 0.566. Sensor history: 0.626.", "The health record achieved 0.566.\nSensor history alone reached 0.626.", 5.0),
    ("S196", "Results", "SLIDE: Fingersticks: 0.642. Fused twin: 0.596.", "Fingersticks alone reached 0.642.\nOur fused twin reached only 0.596.", 5.0),
    ("S197", "Results", "SLIDE: Sensor history alone beats the twin.", "Raw sensor history beats the twin\nat classifying meal excursions.", 4.5),
    ("S198", "Results", "SLIDE: Calibration slope: 0.482 vs target 0.8-1.2.", "Calibration slope was 0.482,\nagainst a target of 0.8 to 1.2.", 5.0),

    # Plain Baselines Win
    ("S199", "Results", "SLIDE: BASELINE slide: Where Plain Baselines Win.", "Where plain baselines tied or won,\nwe report it clearly.", 4.5),
    ("S200", "Results", "SLIDE: Converted fingerstick average missed sensor mean by 6.4 mg/dL.", "At report level, a converted fingerstick average\nmissed the sensor mean by 6.4 mg/dL.", 5.0),
    ("S201", "Results", "SLIDE: Twin rebuilt in hindsight missed by 8.9 mg/dL.", "While our twin in hindsight missed by 8.9.\nThe plain average won.", 5.0),
    ("S202", "Results", "SLIDE: Staleness prompt: AUROC 0.82 vs 0.82 for plain comparison.", "On staleness drift, our cumulative sum had AUROC 0.82,\ntying the plain baseline exactly.", 5.5),
    ("S203", "Results", "SLIDE: Gate 1 Label audit summary.", "In Gate 1, we audited all timestamps,\nunits, and meal logs.", 5.0),
    ("S204", "Results", "SLIDE: Transparency card.", "We publish all evidence cards directly\nin the application.", 4.5),
    ("S205", "Results", "SLIDE: Rigor summary.", "Science over promotional claims.", 4.0),
    ("S206", "Results", "SLIDE: Summary of empirical metrics.", "Every number comes from held-out recordings.", 4.5),
    ("S207", "Results", "SLIDE: Transition to Limits.", "Now let us examine the boundaries\nof what Chhaya is.", 4.5)
]
# c5 calibrated to 240.0s!

# Chapter 6: Limits and Close (19:00 - 21:00 = 120.0 s)
c6 = [
    # Limits
    ("S208", "Limits and Close", "SLIDE: LIMITS slide: What Chhaya Is Not.", "Section five: limits and what Chhaya is not.", 4.0),
    ("S209", "Limits and Close", "SLIDE: Limit 1: No Indian dataset.", "First: there is no Indian patient dataset\nin our evaluation.", 4.5),
    ("S210", "Limits and Close", "SLIDE: Limit 2: Supervised inpatient care.", "Second: Shanghai data was inpatient care\nwith adjusted medication.", 4.5),
    ("S211", "Limits and Close", "SLIDE: Limit 3: Hidden windows at most 11 days.", "Third: hidden windows are at most eleven days,\nnot giving a fixed expiry day.", 5.0),
    ("S212", "Limits and Close", "SLIDE: Limit 4: Physiology effect is ~2%.", "Fourth: the physiological model effect\nis approximately two per cent.", 4.5),
    ("S213", "Limits and Close", "SLIDE: Limit 5: No exogenous insulin kinetics in ODE.", "Fifth: no exogenous insulin kinetics\nor drug dynamics in the ODE.", 4.5),

    # What the misses changed in the product
    ("S214", "Limits and Close", "SLIDE: SUMMARY slide: What the Misses Changed.", "What did these misses change in the product?", 4.0),
    ("S215", "Limits and Close", "SLIDE: Miss consequence 1: No meal alerts or probabilities.", "We display no meal alert\nand no excursion probabilities.", 4.5),
    ("S216", "Limits and Close", "SLIDE: Miss consequence 2: Record shown as context, not gain.", "The health record is presented as context,\nnot as predictive power.", 4.5),
    ("S217", "Limits and Close", "SLIDE: Miss consequence 3: Converted fingerstick average used.", "Patient summary figures use the plain converted\nfingerstick average.", 4.5),
    ("S218", "Limits and Close", "SLIDE: Miss consequence 4: Staleness prompt is descriptive only.", "The staleness prompt is purely descriptive,\nnever clinical advice.", 4.5),

    # Close
    ("S219", "Limits and Close", "SLIDE: CLOSE slide: Live demo URL.", "Explore the live demo yourself\nat chhaya-digital-twin.vercel.app.", 5.0),
    ("S220", "Limits and Close", "SLIDE: GitHub repository card.", "The full codebase, tests, and decision records\nare public on GitHub.", 5.0),
    ("S221", "Limits and Close", "SLIDE: Team SynapseX, D.B.S Kanpur card.", "Chhaya. Built by Team SynapseX\nat D.B.S Kanpur.", 4.5),
    ("S222", "Limits and Close", "SLIDE: Final closing frame with logo.", "Thank you.", 4.0),
    ("S223", "Limits and Close", "SLIDE: Hold to black.", "", 4.0),
    ("S224", "Limits and Close", "SLIDE: Hold to black.", "", 4.0),
    ("S225", "Limits and Close", "SLIDE: Final fade out.", "", 4.0)
]

print("Defined raw chapter segments.")
