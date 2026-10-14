"""Tests for the Record Summary (EHR Fusion Visibility) feature.

Ensures:
1. _record_summary extracts the required clinical fields as a flat dict.
2. Synthetic patient Mrs. R produces expected fields and types.
3. Zero leakage: CGM sensor data changes have zero effect on record_summary.
4. Edge cases: empty static dict, NaN values, missing keys all map to None.
5. Strict JSON serialization without NaN.
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
from conftest import make_recording

from chhaya.product import patient as pt
from chhaya.product.patient import _record_summary
from chhaya.product.synthetic import mrs_r

K = 3.0
SPLIT = K * 1440.0
POOLED = (0.0, 1.0)
THRESHOLDS = {3.0: 5.41, 5.0: 5.61}


def test_mrs_r_record_summary():
    rec = mrs_r()
    summary = _record_summary(rec)

    assert summary["diagnosis"] == "Type 2 diabetes mellitus"
    assert summary["duration_years"] == 9
    assert summary["hba1c"] == 8.1
    assert summary["fasting_glucose"] == 137
    assert summary["bmi"] == 27.1
    assert "metformin" in summary["medications"]
    assert summary["age"] == 58
    assert summary["sex"] == "Female"


def test_record_summary_handles_missing_and_nan():
    rec = make_recording(days=6, seed=42)
    # make_recording sets group='t2d', dataset='synthetic', fasting_glucose_mgdl, weight_kg, fasting_insulin
    summary = _record_summary(rec)

    assert summary["diagnosis"] == "Type 2 diabetes mellitus"
    assert isinstance(summary["fasting_glucose"], int)
    # The rest should safely be None, not NaN
    assert summary["duration_years"] is None
    assert summary["hba1c"] is None
    assert summary["bmi"] is None
    assert summary["medications"] is None
    assert summary["age"] is None
    assert summary["sex"] is None


def test_zero_leakage_on_record_summary():
    rec = mrs_r()
    base_summary = _record_summary(rec)

    # Corrupt post-split sensor glucose
    cgm_corrupt = rec.cgm.copy()
    late = cgm_corrupt["t_min"] >= SPLIT
    cgm_corrupt.loc[late, "glucose_mgdl"] = 599.0
    rec_corrupt = dataclasses.replace(rec, cgm=cgm_corrupt)

    corrupt_summary = _record_summary(rec_corrupt)
    assert base_summary == corrupt_summary


def test_patient_bundle_includes_record_summary():
    rec = mrs_r()
    bundle = pt.patient_bundle(
        rec,
        K,
        name="Mrs. R.",
        cohort="synthetic",
        estimate=pt.stick_estimate(rec, K, POOLED),
        pooled=POOLED,
        thresholds=THRESHOLDS,
        synthetic=True,
    )

    assert "record_summary" in bundle
    assert bundle["record_summary"]["diagnosis"] == "Type 2 diabetes mellitus"

    # Strict JSON serialization with allow_nan=False
    text = json.dumps(bundle, allow_nan=False)
    assert "record_summary" in text
    for banned in ('"tir"', '"tbr"', "gmi", "hba1c_est", "alarm", "time_in_range"):
        assert banned not in text.lower(), banned
