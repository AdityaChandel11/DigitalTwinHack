"""The meal what-if: the same twin as the reveal, one logged meal resized, labelled simulation."""

import json

import numpy as np
import pytest

from chhaya.eval.reveal import run_reveal
from chhaya.product import whatif as wi
from chhaya.product.synthetic import WEAR_DAYS, mrs_r

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def case():
    rec = mrs_r()
    return rec, run_reveal(rec, WEAR_DAYS)


@pytest.fixture(scope="module")
def result(case):
    rec, out = case
    return wi.meal_whatif(rec, out, WEAR_DAYS)


def test_the_logged_amount_gives_back_the_estimate_the_reveal_drew(case, result):
    rec, out = case
    base = wi.simulate_meal(rec, out, WEAR_DAYS, result["meal"]["t_abs"], result["meal"]["carbs"])
    assert np.allclose(base["est"], out.twin, atol=1e-6)
    assert np.allclose(base["lo"], out.lo, atol=1e-6) and np.allclose(base["hi"], out.hi, atol=1e-6)


def test_a_bigger_meal_raises_the_estimated_peak_and_a_smaller_one_lowers_it(result):
    peaks = [max(v for v in result["series"][str(a)]["est"] if v is not None) for a in result["amounts"]]
    assert peaks == sorted(peaks) and peaks[-1] - peaks[0] > 10.0


def test_the_what_if_is_the_largest_logged_meal_of_the_last_day_and_covers_its_afterglow(result):
    meal = result["meal"]
    assert meal["carbs"] == max(m["carbs"] for m in result["day_meals"]) and meal["label"] == "lunch"
    t = result["t"]
    assert min(t) >= meal["t"] - 60 and max(t) - meal["t"] >= 300
    assert result["amounts"] == [20, 30, 40, 50, 60, 70, 80, 90, 100]


def test_every_simulated_amount_has_its_band_and_the_page_has_its_label_and_no_advice(result):
    for series in result["series"].values():
        assert all(lo < e < hi for lo, e, hi in zip(series["lo"], series["est"], series["hi"], strict=True))
    text = json.dumps(result, allow_nan=False).lower()
    assert (
        result["label"] == "simulation"
        and "dose" not in text
        and "insulin" not in text
        and "alarm" not in text
    )
