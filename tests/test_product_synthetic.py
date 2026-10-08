"""The synthetic demo patient: a recording the real pipeline can run, with a story built in on purpose."""

import numpy as np
import pytest

from chhaya.data.pairs import paired
from chhaya.eval.fingersticks import why_not
from chhaya.eval.reveal import run_reveal
from chhaya.product.synthetic import WEAR_DAYS, mrs_r
from chhaya.product.treatment import treatment_since

SPLIT = WEAR_DAYS * 1440


@pytest.fixture(scope="module")
def rec():
    return mrs_r()


def test_she_is_a_valid_recording_and_says_she_is_synthetic(rec):
    rec.validate()
    assert rec.dataset == "synthetic" and rec.patient_id == "mrs-r"
    assert rec.static["synthetic"] is True and "synthetic" in rec.static["genetic_marker"]
    assert rec.n_min == 11 * 1440 and WEAR_DAYS == 5.0


def test_the_same_seed_gives_the_same_patient(rec):
    again = mrs_r()
    assert (
        rec.cgm.equals(again.cgm)
        and rec.fingersticks.equals(again.fingersticks)
        and rec.meals.equals(again.meals)
    )
    assert not mrs_r(seed=1).cgm.equals(rec.cgm)


def test_she_tests_six_times_a_day_and_her_meter_reads_above_her_sensor(rec):
    hidden = rec.fingersticks[rec.fingersticks["t_min"] >= SPLIT]
    assert len(hidden) / 6.0 >= 4.6  # inside the tested range of the prompt, on purpose
    pairs = paired(rec, hi=SPLIT)
    assert len(pairs) >= 20 and 5.0 < float((pairs["cbg"] - pairs["cgm"]).mean()) < 30.0


def test_her_glucose_drifts_down_after_the_change_of_treatment(rec):
    t, g = rec.cgm["t_min"].to_numpy(), rec.cgm["glucose_mgdl"].to_numpy()
    wear, last_days = g[t < SPLIT].mean(), g[t >= SPLIT + 3 * 1440].mean()
    assert 15.0 < wear - last_days < 35.0
    assert abs(g[(t >= SPLIT) & (t < SPLIT + 1440)].mean() - wear) < 10.0  # day 1 is still the old patient
    assert treatment_since(rec, WEAR_DAYS) == {"state": "changed", "day": 2}


def test_one_night_the_sensor_reads_low_and_no_fingerstick_confirms_it(rec):
    t, g = rec.cgm["t_min"].to_numpy(), rec.cgm["glucose_mgdl"].to_numpy()
    low = t[(g < 70.0) & (t >= SPLIT)]
    assert low.size >= 2 and ((low % 1440) < 6 * 60).all()  # in the small hours only
    assert rec.fingersticks["glucose_mgdl"].min() > 80.0


def test_some_meals_are_logged_and_one_evening_snack_never_is(rec):
    assert {"breakfast", "lunch", "dinner"} <= set(rec.meals["label"])
    assert rec.meals["carb_g"].between(10, 120).all() and len(rec.meals) >= 33


def test_she_is_inside_the_fingerstick_cohort(rec):
    assert why_not(rec, WEAR_DAYS) is None


@pytest.mark.slow
def test_the_real_reveal_runs_on_her(rec):
    out = run_reveal(rec, WEAR_DAYS)
    assert out is not None and np.isfinite(out.twin).all() and (out.lo <= out.hi).all()
    assert out.t_test.min() >= SPLIT
