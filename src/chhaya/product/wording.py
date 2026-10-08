"""Every sentence of reviewed wording the dashboard shows, in one place.

Each constant is copied from the "Consequences for the product" section of a decision record, where
the clinical-wording review read it; `tests/test_product_copy.py` compares them word for word. A `{gap}` is filled by
`fill` from the patient's bundle. Change a sentence in its record first, with a review, then here.
"""

from __future__ import annotations

# the design spec's limits line, always on screen
LIMITS = (
    "Research prototype; evaluated on a Chinese cohort in supervised care and a US free-living cohort; "
    "estimates, not measurements; not for dosing."
)
SENSOR_LOW = "sensor low, unconfirmed"

# band record
BAND = (
    "80 % band; on held-out participants it held 83.5 % of readings on average and between 60 % and 98.5 % "
    "for an individual."
)

# expiry record
DAYS_NOTE = (
    "Measured over at most 11 days: about 1 mg/dL per day, downward, in supervised care with treatment being "
    "adjusted; none detected over 7 days in free-living participants (7 of 19 with type 2 diabetes). Beyond 11 "
    "days: eight patients. A cohort figure, not this patient's; not to be multiplied by the days shown."
)
TREATMENT_CHANGED = (
    "Treatment changed since the sensor. In a case series the sensor mean had moved by more than 20 mg/dL in 4 "
    "of 5 repeat wears after a change (3 of 4 patients) and in 0 of 4 without. No recorded change does not mean "
    "the report still holds."
)
LIST_NOTE = (
    "This describes how old the sensor report is, not how unwell a patient is or who should be seen first. A "
    "patient with no recorded change may still have changed."
)

# fingerstick report record
SINCE_LABEL = "sensor-equivalent, estimated from {n} fingersticks over {days} days"
SINCE_SENSOR = (
    "Sensor-equivalent, not meter values: this patient's sensor read lower than the meter. Converted with the "
    "line learned during the wear of {date}; another sensor may read differently. A share of readings taken at "
    "{times}, not time above range; nights are not sampled. In 29 supervised-care patients tested about six "
    "times a day, for up to 11 days, the median miss was 6 mg/dL (mean) and 3 points (above 180); half of "
    "patients were missed by more. Not measured with fewer fingersticks. Says nothing about low glucose. Not for "
    "dosing."
)
NOT_ESTIMATED = (
    "Time in range and low glucose since the sensor are not estimated. This screen says nothing about "
    "hypoglycaemia."
)
KEEP_FINGERSTICKS = (
    "In 29 supervised-care patients who were already tested about six times a day, the plain average of their "
    "fingersticks, converted to the sensor's scale, lay a median of 6 mg/dL from the sensor's mean over the "
    "following days; a three-day sensor report lay 13 (a fourteen-day report would be closer). Not measured at "
    "lower testing frequencies. This describes those patients; it is not a recommendation to test at any "
    "frequency."
)

# staleness record
PROMPT = (
    "The sensor report may be out of date. A running comparison of fingersticks with the daily pattern of the "
    "sensor wear of {dates} crossed its preset threshold on {date}. This concerns the report, not this patient's "
    "glucose. Consider whether a new sensor wear is due."
)
PROMPT_ABOUT = (
    "A prompt to consider a new sensor wear. It is not a finding about this patient's glucose and not a reason "
    "to change or to keep treatment. In 32 recordings of supervised-care patients tested about six times a day, "
    "for up to 11 days, it was raised in 7 of 11 whose sensor mean had moved by more than 20 mg/dL and in 2 of 21 "
    "where it had not. It was not shown to tell the two apart better than comparing the fingerstick average with "
    "the report's mean. In 9 of those 11 the mean had moved downward, in patients whose treatment was being "
    "adjusted by staff; 2 moved upward. Whether the prompt is raised when glucose rises is not known. It does "
    "not say which way. Not tested in outpatient care, with fewer fingersticks or over longer periods. It "
    "neither indicates nor rules out low glucose. Not a rule for when to wear a sensor."
)
PROMPT_NONE = (
    "No prompt does not mean the report still holds, nor that glucose is unchanged or in range. 4 of 11 "
    "recordings whose sensor mean had moved raised none."
)
PROMPT_NOT_COMPUTED = "Not computed: {reason}. Not a recommendation to test at any frequency."
NOT_COMPUTED_REASONS = {
    "few_sticks": "fewer fingersticks than in the tested recordings",
    "wear_length": "a sensor wear of a length that was not tested",
    "too_late": "more than 11 days since the sensor",
}
LIST_NOTE_PROMPT = "A patient with no prompt may still have changed."

# record-prior record and the progress map
FUSION = (
    "We fused the record and the sensor two ways and measured both; once a sensor week exists the record added "
    "nothing detectable. What adds something is the meal log and fingersticks."
)

# the opening of the Gate 2 claim
KEEP_MEALS = (
    "On 19 held-out patients, 5 days after the sensor comes off, Chhaya's estimate is 1.4 mg/dL (6 %) closer to "
    "the hidden sensor than the patient's own average day (p = 4e-05) and about 0.35 mg/dL closer than a control "
    "that uses no meals (p = 0.04). The gain comes from the meal log and is small."
)

# written for the product on 8 Oct, not yet read by healthcare-reviewer (Plan 5, Task D1)
PSEUDONYMS = (
    "Names are pseudonyms given by Chhaya for display. The datasets contain no names; the code beside each "
    "name is the dataset's own identifier."
)
SYNTHETIC = (
    "Mrs. R. is synthetic, so the sensor revealed here is simulated. On the held-out patients the revealed "
    "trace is the real sensor that was hidden from the estimate."
)
WHAT_IF = (
    "A simulation on the virtual patient of a meal the doctor enters. It is not a prediction for this patient "
    "and not advice. There are no dose, drug or activity options."
)


def fill(template: str, **gaps: object) -> str:
    """The sentence with its named gaps filled. A gap left out or left empty is an error, never a blank on screen."""
    empty = [name for name, value in gaps.items() if not str(value).strip()]
    if empty:
        raise ValueError(f"empty value for {', '.join(empty)}")
    return template.format(**gaps)
