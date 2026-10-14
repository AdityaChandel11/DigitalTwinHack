"""Tests for the Meal Excursion History feature (chhaya.product.meal_risk).

Ensures:
1. meal_risk_profile returns the declared structure.
2. Zero leakage: changing post-split sensor data or post-split meals has ZERO effect.
3. Edge cases: no meals, fewer than 3 meals, all meals same type, custom labels.
4. Patient bundle integration: strict JSON serialization with no NaN.
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pandas as pd
from conftest import make_recording

from chhaya.data.schema import MEAL_COLS, empty
from chhaya.product import patient as pt
from chhaya.product.meal_risk import meal_risk_profile

K = 3.0
SPLIT = K * 1440.0
POOLED = (0.0, 1.0)
THRESHOLDS = {3.0: 5.41, 5.0: 5.61}


def test_meal_risk_structure_and_computation():
    rec = make_recording(days=6, seed=42)
    profile = meal_risk_profile(rec, k_days=K)

    assert profile["state"] == "shown"
    assert "meals_scored" in profile
    assert profile["meals_scored"] >= 3
    assert "excursions" in profile
    assert 0 <= profile["excursions"] <= profile["meals_scored"]
    assert profile["rate"] == round(profile["excursions"] / profile["meals_scored"], 2)

    assert isinstance(profile["by_type"], list)
    assert len(profile["by_type"]) >= 1

    total_from_types = sum(b["total"] for b in profile["by_type"])
    excursions_from_types = sum(b["excursions"] for b in profile["by_type"])
    assert total_from_types == profile["meals_scored"]
    assert excursions_from_types == profile["excursions"]

    for item in profile["by_type"]:
        assert "label" in item and isinstance(item["label"], str)
        assert "total" in item and item["total"] > 0
        assert "excursions" in item and 0 <= item["excursions"] <= item["total"]
        assert "rate" in item and item["rate"] == round(item["excursions"] / item["total"], 2)


def test_zero_leakage_after_calibration_split():
    """CRITICAL RULE: NEVER read sensor data after the split.

    Corrupting post-split CGM glucose to extreme values must not change meal_risk_profile output at all.
    """
    rec = make_recording(days=6, seed=42)
    base_profile = meal_risk_profile(rec, k_days=K)

    # 1. Modify hidden CGM glucose after split
    cgm_corrupt = rec.cgm.copy()
    late = cgm_corrupt["t_min"] >= SPLIT
    cgm_corrupt.loc[late, "glucose_mgdl"] = 580.0
    rec_cgm_corrupt = dataclasses.replace(rec, cgm=cgm_corrupt)
    profile_after_cgm_change = meal_risk_profile(rec_cgm_corrupt, k_days=K)
    assert base_profile == profile_after_cgm_change

    # 2. Add meals after the split
    late_meal = pd.DataFrame(
        [
            {
                "t_min": SPLIT + 200.0,
                "carb_g": 90.0,
                "protein_g": 20.0,
                "fat_g": 20.0,
                "fibre_g": 5.0,
                "label": "dinner",
            }
        ]
    )
    meals_with_late = pd.concat([rec.meals, late_meal], ignore_index=True)
    rec_late_meals = dataclasses.replace(rec, meals=meals_with_late)
    profile_after_late_meals = meal_risk_profile(rec_late_meals, k_days=K)
    assert base_profile == profile_after_late_meals


def test_edge_case_no_meals():
    rec = make_recording(days=6, seed=1)
    rec_no_meals = dataclasses.replace(rec, meals=empty(MEAL_COLS))
    profile = meal_risk_profile(rec_no_meals, k_days=K)
    assert profile == {"state": "insufficient", "meals_scored": 0}


def test_edge_case_fewer_than_3_meals():
    rec = make_recording(days=6, seed=2)
    # Filter down to only 1 meal in the calibration window
    early_meals = rec.meals[rec.meals["t_min"] < SPLIT - 120.0].iloc[:2].reset_index(drop=True)
    rec_few = dataclasses.replace(rec, meals=early_meals)
    profile = meal_risk_profile(rec_few, k_days=K)
    assert profile["state"] == "insufficient"
    assert profile["meals_scored"] == len(early_meals)


def test_edge_case_all_meals_same_type():
    rec = make_recording(days=6, seed=3)
    meals_same = rec.meals.copy()
    meals_same["label"] = "breakfast"
    rec_same = dataclasses.replace(rec, meals=meals_same)
    profile = meal_risk_profile(rec_same, k_days=K)

    assert profile["state"] == "shown"
    assert len(profile["by_type"]) == 1
    assert profile["by_type"][0]["label"] == "breakfast"
    assert profile["by_type"][0]["total"] == profile["meals_scored"]
    assert profile["by_type"][0]["excursions"] == profile["excursions"]


def test_multiple_meal_types_and_canonical_ordering():
    rec = make_recording(days=6, seed=4)
    # Assign breakfast, lunch, dinner in order
    meals = rec.meals.copy()
    labels = ["breakfast", "lunch", "dinner", "snack"]
    meals["label"] = [labels[i % len(labels)] for i in range(len(meals))]
    rec_labeled = dataclasses.replace(rec, meals=meals)
    profile = meal_risk_profile(rec_labeled, k_days=K)

    assert profile["state"] == "shown"
    type_labels = [b["label"] for b in profile["by_type"]]
    # Should follow canonical order
    expected_order = [l for l in labels if l in type_labels]
    assert type_labels == expected_order


def test_patient_bundle_includes_meal_risk_and_serializes_strictly():
    rec = make_recording(days=6, seed=5)
    bundle = pt.patient_bundle(
        rec,
        K,
        name="Test Patient",
        cohort="supervised",
        estimate=pt.stick_estimate(rec, K, POOLED),
        pooled=POOLED,
        thresholds=THRESHOLDS,
    )
    assert "meal_risk" in bundle
    # Must serialize with allow_nan=False (strict JSON requirement)
    serialized = json.dumps(bundle, allow_nan=False)
    deserialized = json.loads(serialized)
    assert deserialized["meal_risk"]["meals_scored"] == bundle["meal_risk"]["meals_scored"]
