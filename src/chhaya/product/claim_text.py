"""Each result's claim to quote, copied whole from its decision record.

Wording only: no number here is computed. `tests/test_product_claims.py` compares every entry with its record,
so a record and the screen cannot drift apart. Gate 2 is its record's sentence followed by the clause the
expiry record corrected ("lasts about five days" is not shown anywhere).
"""

TEXT = {
    "gate2": (
        "On 19 held-out patients, 5 days after the sensor comes off, Chhaya's estimate is 1.4 mg/dL (6 %) "
        "closer to the hidden sensor than the patient's own average day (p = 4e-05) and about 0.35 mg/dL "
        "closer than a control that uses no meals (p = 0.04). The gain comes from the meal log and is "
        "small. It was not seen to fade with days since the sensor: with three days of calibration the "
        "median favours the twin over its control on each of the seven following days (0.4 to 2.0 mg/dL; "
        "the interval excludes zero on three of them; 19 held-out participants), and it reverses only on "
        "the last days of the recording, which fewer than half of the participants reach."
    ),
    "label": (
        "Of 64 sensor readings below 70 mg/dL with a fingerstick within 10 minutes, 8 (12.5 %) were "
        "confirmed, and 0 of 9 at night; of 809 sensor readings above 180, 732 (90.5 %) were confirmed."
    ),
    "gate3": (
        "On 47 held-out Shanghai patients (1,205 meals, 39 % followed by an excursion above 180 mg/dL), a "
        "model fusing the record, the sensor week and fingersticks predicted the excursion at meal time "
        "with AUPRC 0.60, which was not better than any single stream (fingersticks only: 0.64) nor than "
        "the patient's own excursion rate from the sensor week (0.59; difference 0.01, 95 % interval "
        "-0.09 to 0.14); with the sensor on, the same model reaches 0.76."
    ),
    "prior": (
        "On 20 held-out CGMacros patients with one day of sensor data, giving the twin the record's "
        "fasting glucose as its prior changed the error of the estimate by a median of 0.02 mg/dL (p = "
        "0.16), and with three or more days by nothing measurable: the record, as it enters the twin "
        "today, is not worth any sensor days."
    ),
    "sticks": (
        "On 29 held-out Shanghai patients, calibrated on three days of sensor data, fingersticks taken "
        "afterwards brought the running estimate 2.8 mg/dL closer to the hidden sensor than the patient's "
        "daily shape alone (median paired RMSE difference; 95 % interval 1.6 to 4.7; 86 % of patients; p "
        "= 4e-06) and 9.5 mg/dL closer in hindsight (interval 4.6 to 12.1); with one fingerstick a day "
        "the running gain was 0.3 mg/dL."
    ),
    "report": (
        "Descriptive, no bar; a plain baseline beats our estimator. On 29 held-out Shanghai patients "
        "under supervised care who were tested about six times a day, with the hidden sensor as the "
        "yardstick, a three-day sensor report missed the mean sensor glucose of the following days (up to "
        "eleven) by a median of 13.0 mg/dL. Chhaya's report rebuilt in hindsight from those fingersticks "
        "missed it by 8.9 (median paired difference 3.4, 95 % interval 1.6 to 8.9, 83 % of patients), but "
        "was no closer than the plain average of the same fingersticks converted to the sensor's scale by "
        "a line learned during the wear (6.4). The share of those converted readings above 180 mg/dL and "
        "within 70 to 180 was also closer to the sensor's time above 180 and time in range (3.1 against "
        "8.8 points; 5.0 against 15.2). As read from the meter the same average lay 18.3 mg/dL from the "
        "sensor's mean; sensor-scale figures are not meter values. Lower testing frequencies were not "
        "measured, and this is not a recommendation to test at any frequency."
    ),
    "expiry": (
        'Descriptive, no bar; "report" means mean glucose only, and a three-day report stands in for a '
        "fourteen-day one. On 47 held-out Shanghai patients under supervised care with treatment being "
        "adjusted, a day's mean sensor glucose lay a median of 13.5 mg/dL from a three-day sensor "
        "report's mean inside the wear and 11 to 16 on the four days after it; inside each patient that "
        "distance grew by 1.0 mg/dL per day (95 % interval 0.7 to 2.6) over at most eleven days, with "
        "glucose moving downward. On 19 held-out free-living CGMacros participants (7 with type 2 "
        "diabetes; medication not recorded) no growth was detected over seven days (0.1 mg/dL per day, "
        "interval -0.8 to 0.8). In a case series of eight Shanghai patients recorded again (nine later "
        "wears, five beginning within three days of the first sensor coming off and four 33 to 154 days "
        "after it), four wears in three patients had a mean more than 20 mg/dL lower, all four with a "
        "change of treatment in the files; of the five that had not moved, four had no change and one "
        "had, and the old daily profile fitted them no worse than a fresh one. No test; not a rule for "
        "when a patient should wear a sensor."
    ),
    "band": (
        "On 19 held-out participants the 80 % band held 83.5 % of hidden readings on average and between "
        "60 % and 98.5 % for an individual, with 10 of 19 participants within 70 to 90 %. A recalibration "
        "factor chosen on development patients (0.78) moved the average to 75.7 %, further from 80 % than "
        "before, so it is not used: the band is calibrated on average, not per patient."
    ),
    "stale": (
        "Descriptive, no bar; a plain baseline does as well. On 32 held-out Shanghai recordings (29 "
        "patients under supervised care, tested about six times a day, for up to eleven days after a "
        "three-day sensor report), 11 of which drifted by more than 20 mg/dL in mean sensor glucose (9 "
        "downward, 2 upward), a running sum of fingerstick surprises, used only as a prompt to consider a "
        "new sensor wear, separated drifted from stable recordings with AUROC 0.82 (95 % interval 0.63 to "
        "0.98), against 0.82 (0.61 to 0.97) for the plain fingerstick average compared with the report's "
        "mean (difference 0.00, interval -0.16 to 0.18): it was not shown to do better than that "
        "comparison. At a threshold set on development recordings so that at most 10 % of stable ones "
        "would raise it, the prompt was raised in 7 of 11 drifted recordings (64 %) and 2 of 21 stable "
        "ones (10 %); in those 7, a median of 2.6 days after the split. With a five-day report (24 "
        "recordings, 6 drifted) it was not shown to separate them (0.67, interval 0.35 to 0.92). The "
        "label and the score look back over the same days. It is not a finding about a patient's glucose, "
        "not advice on treatment and not a rule for when to wear a sensor, and it was not tested in "
        "outpatient care, at lower testing frequencies or over longer periods."
    ),
    "stickband": (
        "Descriptive, no bar. On 29 held-out Shanghai patients under supervised care, calibrated on three "
        "days of sensor data and tested about six times a day, a band built from the fingerstick filter's "
        "own spread and each patient's spread during the sensor wear, with nothing fitted, held 83.6 % of "
        "hidden sensor readings around the running estimate (49.9 % to 98.9 % for an individual; 12 of 29 "
        "patients within 70 to 90 %) and 86.1 % around the estimate in hindsight (56.7 % to 100 %), at a "
        "half-width of about 45 mg/dL. It is calibrated on average, not per patient, and it is wide."
    ),
}
