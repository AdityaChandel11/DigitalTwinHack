"""Pseudonyms, the FHIR-shaped record and "treatment changed since the sensor"."""

import dataclasses
import json

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.product.names import SURNAMES, pseudonyms
from chhaya.product.record import fhir_record
from chhaya.product.treatment import treatment_since

SPLIT = 3 * 1440


# ---------- names ----------
def test_the_same_patients_always_get_the_same_names_and_no_two_share_one():
    ids = [f"shanghai-{n}" for n in range(2000, 2100)]
    sex = dict.fromkeys(ids, "M")
    first, again = pseudonyms(ids, "shanghai", sex), pseudonyms(list(reversed(ids)), "shanghai", sex)
    assert first == again and len(set(first.values())) == 100


def test_the_honorific_follows_the_recorded_sex_and_is_left_out_when_none_is_recorded():
    ids = ["cgmacros-001", "cgmacros-002", "cgmacros-003", "cgmacros-004"]
    names = pseudonyms(ids, "cgmacros", {ids[0]: "M", ids[1]: "F", ids[2]: None, ids[3]: "female"})
    assert (
        names[ids[0]].startswith("Mr. ")
        and names[ids[1]].startswith("Ms. ")
        and names[ids[3]].startswith("Ms. ")
    )
    assert names[ids[2]] in SURNAMES["cgmacros"]


def test_the_two_cohorts_draw_from_different_lists_and_nobody_is_called_mrs_r():
    assert not set(SURNAMES["shanghai"]) & set(SURNAMES["cgmacros"])
    assert len(SURNAMES["shanghai"]) >= 100 and len(SURNAMES["cgmacros"]) >= 45
    everyone = [n for names in SURNAMES.values() for n in names]
    assert "R." not in everyone and not any(n.startswith("Mrs") for n in everyone)


def test_an_unknown_cohort_or_more_patients_than_names_is_an_error():
    with pytest.raises(ValueError, match="cohort"):
        pseudonyms(["x"], "elsewhere", {})
    with pytest.raises(ValueError, match="names"):
        pseudonyms([f"p{n}" for n in range(500)], "cgmacros", {})


# ---------- record ----------
def _with_static(**static):
    rec = make_recording(days=4)
    return dataclasses.replace(rec, static={**rec.static, **static})


def _resources(bundle: dict, kind: str) -> list[dict]:
    return [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == kind]


def test_the_record_carries_what_the_dataset_recorded_in_fhir_shapes():
    rec = _with_static(age=61.0, sex="F", bmi=27.44, hba1c_pct=8.13, agents="metformin, insulin glargine")
    bundle = fhir_record(dataclasses.replace(rec, dataset="shanghai"))
    assert bundle["resourceType"] == "Bundle" and _resources(bundle, "Patient")[0]["gender"] == "female"
    seen = {o["code"]["text"]: o["valueQuantity"] for o in _resources(bundle, "Observation")}
    assert seen["HbA1c"] == {"value": 8.1, "unit": "%"} and seen["Age"] == {"value": 61, "unit": "a"}
    assert seen["Body mass index"]["value"] == 27.4 and seen["Fasting glucose"]["unit"] == "mg/dL"
    assert _resources(bundle, "Condition")[0]["code"]["text"] == "Type 2 diabetes mellitus"
    assert (
        _resources(bundle, "MedicationStatement")[0]["medicationCodeableConcept"]["text"]
        == "metformin, insulin glargine"
    )
    assert "meta" not in bundle


def test_a_value_the_dataset_does_not_hold_is_left_out_never_written_as_nan():
    rec = _with_static(age=float("nan"), sex=None, bmi=np.nan, hba1c_pct=float("nan"), agents=None)
    bundle = fhir_record(rec)
    text = json.dumps(bundle, allow_nan=False)  # raises on NaN
    assert "NaN" not in text and "gender" not in _resources(bundle, "Patient")[0]
    assert {o["code"]["text"] for o in _resources(bundle, "Observation")} == {"Fasting glucose"}
    assert not _resources(bundle, "MedicationStatement")


def test_a_synthetic_record_says_so_and_its_genetic_marker_is_labelled_synthetic():
    rec = _with_static(genetic_marker="synthetic field")
    bundle = fhir_record(rec, synthetic=True)
    assert bundle["meta"]["tag"][0]["code"] == "synthetic"
    marker = next(o for o in _resources(bundle, "Observation") if o["code"]["text"] == "Genetic marker")
    assert "synthetic" in marker["valueString"]
    assert not [
        o
        for o in _resources(fhir_record(_with_static()), "Observation")
        if o["code"]["text"] == "Genetic marker"
    ]


def test_a_free_living_participant_gets_no_diagnosis_from_a_group_the_loader_derived():
    rec = dataclasses.replace(_with_static(group="t2d"), dataset="cgmacros")
    assert not _resources(fhir_record(rec), "Condition")


# ---------- treatment ----------
def _with_doses(rows):
    rec = make_recording(days=8)
    doses = pd.DataFrame(rows, columns=["t_min", "drug", "dose", "route"]).astype({"t_min": float})
    return dataclasses.replace(rec, doses=doses)


def _daily(drug, route, days, at=480):
    return [(d * 1440 + at, drug, np.nan, route) for d in days]


def test_a_recording_without_a_dose_table_is_not_recorded_never_unchanged():
    assert treatment_since(make_recording(days=8), 3) == {"state": "not_recorded", "day": None}


def test_doses_on_one_side_of_the_split_only_cannot_be_compared():
    assert treatment_since(_with_doses(_daily("metformin", "oral", range(3))), 3)["state"] == "not_recorded"
    assert (
        treatment_since(_with_doses(_daily("metformin", "oral", range(3, 8))), 3)["state"] == "not_recorded"
    )


def test_the_same_agents_at_any_dose_are_no_recorded_change():
    rows = _daily("metformin 0.5 g", "oral", range(3)) + _daily("metformin 1 g", "oral", range(3, 8))
    assert treatment_since(_with_doses(rows), 3) == {"state": "none", "day": None}


def test_insulin_started_after_the_sensor_is_a_change_dated_by_its_first_dose():
    rows = _daily("metformin", "oral", range(8)) + _daily("Novolin R 8 IU", "sc", range(5, 8))
    assert treatment_since(_with_doses(rows), 3) == {
        "state": "changed",
        "day": 3,
    }  # day 1 is the first 24 hours


def test_a_pump_started_or_an_agent_class_added_or_stopped_is_a_change():
    oral = _daily("metformin", "oral", range(8))
    assert (
        treatment_since(_with_doses(oral + _daily("bolus 4 IU", "csii", range(4, 8))), 3)["state"]
        == "changed"
    )
    stopped = _daily("metformin", "oral", range(8)) + _daily("Novolin R 8 IU", "sc", range(3))
    assert treatment_since(_with_doses(stopped), 3) == {"state": "changed", "day": None}  # a stop has no date
