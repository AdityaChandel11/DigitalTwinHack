import dataclasses

import pandas as pd
import pytest

from chhaya.data.schema import CGM_COLS, MEAL_COLS, empty


def test_empty_frames_have_the_contract_columns():
    assert list(empty(MEAL_COLS).columns) == MEAL_COLS
    assert len(empty(CGM_COLS)) == 0


def test_valid_recording_passes(rec):
    rec.validate()


def test_reading_past_the_end_is_rejected(rec):
    bad = pd.concat(
        [rec.cgm, pd.DataFrame({"t_min": [rec.n_min + 5], "glucose_mgdl": [120.0]})], ignore_index=True
    )
    with pytest.raises(ValueError, match="outside"):
        dataclasses.replace(rec, cgm=bad).validate()


def test_unsorted_cgm_is_rejected(rec):
    with pytest.raises(ValueError, match="not sorted"):
        dataclasses.replace(rec, cgm=rec.cgm.iloc[::-1]).validate()


def test_empty_cgm_is_rejected(rec):
    with pytest.raises(ValueError, match="no CGM"):
        dataclasses.replace(rec, cgm=rec.cgm.iloc[:0]).validate()


def test_implausible_glucose_is_rejected(rec):
    bad = rec.cgm.copy()
    bad.loc[3, "glucose_mgdl"] = 5.4  # a mmol/L value left unconverted
    with pytest.raises(ValueError, match="20-600"):
        dataclasses.replace(rec, cgm=bad).validate()


def test_frame_missing_a_column_is_rejected(rec):
    with pytest.raises(ValueError, match="lacks columns"):
        dataclasses.replace(rec, meals=rec.meals.drop(columns=["fibre_g"])).validate()
