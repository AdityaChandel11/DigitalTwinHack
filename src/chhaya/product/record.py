"""The health record as FHIR-shaped JSON: what the dataset recorded about a patient, and nothing it did not.

"FHIR-shaped": the resource types and field names of FHIR R4 (Bundle, Patient, Condition, Observation,
MedicationStatement) with LOINC codes on the observations, not a validated FHIR document. A value the dataset
does not hold is left out. A synthetic record is tagged synthetic, and so is its genetic-marker field, which
no model reads.
"""

from __future__ import annotations

import math

from chhaya.data.schema import Recording

LOINC = "http://loinc.org"
GENDER = {"M": "male", "F": "female"}
# static key, display text, LOINC code, unit, decimals
OBSERVATIONS = (
    ("age", "Age", "30525-0", "a", 0),
    ("hba1c_pct", "HbA1c", "4548-4", "%", 1),
    ("fasting_glucose_mgdl", "Fasting glucose", "1558-6", "mg/dL", 0),
    ("bmi", "Body mass index", "39156-5", "kg/m2", 1),
)
DIAGNOSED_COHORTS = ("shanghai", "synthetic")  # recruited as people with type 2 diabetes


def _number(value, decimals: int) -> float | int | None:
    """A finite number rounded for display, or None: JSON has no NaN and the screen must not show one."""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return int(round(x)) if decimals == 0 else round(x, decimals)


def fhir_record(rec: Recording, synthetic: bool = False) -> dict:
    static = rec.static
    patient: dict = {"resourceType": "Patient", "id": rec.patient_id}
    gender = GENDER.get(str(static.get("sex") or "").strip().upper()[:1])
    if gender:
        patient["gender"] = gender
    resources = [patient]
    # CGMacros groups are derived by the loader from HbA1c: that is not a diagnosis, so none is written
    if static.get("group") == "t2d" and rec.dataset in DIAGNOSED_COHORTS:
        condition: dict = {"resourceType": "Condition", "code": {"text": "Type 2 diabetes mellitus"}}
        years = _number(static.get("diabetes_duration_y"), 0)
        if years is not None:
            condition["note"] = [{"text": f"duration {years} years"}]
        resources.append(condition)
    for key, text, code, unit, decimals in OBSERVATIONS:
        value = _number(static.get(key), decimals)
        if value is not None:
            resources.append(
                {
                    "resourceType": "Observation",
                    "code": {"text": text, "coding": [{"system": LOINC, "code": code}]},
                    "valueQuantity": {"value": value, "unit": unit},
                }
            )
    agents = str(static.get("agents") or "").strip()
    if agents and agents.lower() not in ("nan", "none"):
        resources.append(
            {"resourceType": "MedicationStatement", "medicationCodeableConcept": {"text": agents}}
        )
    if synthetic and static.get("genetic_marker"):
        resources.append(
            {
                "resourceType": "Observation",
                "code": {"text": "Genetic marker"},
                "valueString": f"{static['genetic_marker']} (synthetic; read by no model)",
            }
        )
    bundle: dict = {"resourceType": "Bundle", "type": "collection"}
    if synthetic:
        bundle["meta"] = {"tag": [{"code": "synthetic", "display": "Synthetic patient: not a real person"}]}
    bundle["entry"] = [{"resource": r} for r in resources]
    return bundle
