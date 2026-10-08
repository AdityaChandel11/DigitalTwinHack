import numpy as np
import pytest

from chhaya.eval import calibrate as cb
from chhaya.eval.metrics import coverage


def _trace(
    patient_id: str, spread: float, k_days: float = 5.0, days: int = 5, seed: int = 0, grow: float = 0.0
):
    """A band drawn for an error of 10 mg/dL around an estimate whose real error is `spread`.

    With `grow`, the real error rises by that share per day since the sensor while the band stays as drawn.
    """
    rng = np.random.default_rng(seed)
    t = k_days * 1440 + np.arange(0, days * 1440, 15.0)
    twin = 140.0 + 20.0 * np.sin(2 * np.pi * t / 1440)
    day = (t - k_days * 1440) // 1440
    truth = twin + rng.normal(0.0, spread, t.size) * (1.0 + grow * day)
    half = 1.2816 * 10.0  # the 10th and 90th percentiles of a normal error of 10
    return {"patient_id": patient_id, "k_days": k_days, "t": t, "truth": truth, "twin": twin,
            "lo": twin - half, "hi": twin + half}  # fmt: skip


def _items(spread: float = 10.0, n: int = 12, **kw):
    return [cb.prepare(_trace(f"p{i}", spread, seed=i, **kw)) for i in range(n)]


def test_the_factor_a_reading_needs_is_the_factor_at_which_the_rescaled_band_reaches_it():
    tr = _trace("p", 14.0)
    item = cb.prepare(tr)
    for f in (0.7, 1.0, 1.6):
        lo, hi = cb.rescale(tr, f)
        assert np.mean(item["need"] <= f) == coverage(tr["truth"], lo, hi)
    assert cb.rescale(tr, 1.0)[0] == pytest.approx(tr["lo"]) and cb.rescale(tr, 1.0)[1] == pytest.approx(
        tr["hi"]
    )
    assert item["day"].min() == 1 and item["day"].max() == 5


def test_a_band_that_is_too_narrow_is_widened_to_cover_80_percent():
    items = _items(spread=14.0)  # the real error is 1.4 times what the band was drawn for
    before = cb.patient_coverage(items).mean()
    f = cb.fit_factor(items)
    after = cb.patient_coverage(items, {"design": "single", "factor": f}).mean()
    assert before < 0.68 and 1.3 < f < 1.5 and abs(after - 0.80) < 0.01
    assert 0.6 < cb.fit_factor(_items(spread=7.0)) < 0.8  # and one that is too wide is narrowed
    assert abs(cb.fit_factor(_items(spread=10.0)) - 1.0) < 0.05
    with pytest.raises(ValueError, match="no trace"):
        cb.fit_factor([])


def test_two_recordings_of_one_patient_count_once():
    items = _items(spread=10.0, n=3)
    twice = [*items, {**items[0], "need": items[0]["need"] * 3.0}]
    cov = cb.patient_coverage(twice)
    assert len(cov) == 3 and cov["p0"] < cb.patient_coverage(items)["p0"]


def test_a_band_with_no_width_cannot_divide_by_zero():
    tr = _trace("p", 10.0)
    flat = {**tr, "lo": tr["twin"].copy(), "hi": tr["twin"].copy()}
    item = cb.prepare(flat)
    assert np.isfinite(item["need"]).all() and np.mean(item["need"] <= 2.0) < 0.01


def test_a_factor_per_day_is_fitted_only_for_days_enough_patients_reach():
    items = _items(spread=10.0, grow=0.25)  # the error grows a quarter per day; the drawn band does not
    by_day = cb.fit_by_day(items)
    assert list(by_day) == ["1", "2", "3", "4", "5"] and by_day["1"] < by_day["3"] < by_day["5"]
    assert cb.fit_by_day(items[:9]) == {}  # nine patients are too few for any day
    short = [*items[:9], *(cb.prepare(_trace(f"s{i}", 10.0, days=2, seed=50 + i)) for i in range(3))]
    assert list(cb.fit_by_day(short)) == ["1", "2"]  # only nine patients reach day 3
    many = [*(cb.prepare(_trace(f"m{i}", 10.0, seed=70 + i)) for i in range(14)),
            *(cb.prepare(_trace(f"e{i}", 10.0, days=2, seed=90 + i)) for i in range(6))]  # fmt: skip
    assert list(cb.fit_by_day(many)) == [
        "1",
        "2",
    ]  # 14 of 20 reach day 3: enough heads, too few of the cohort
    design = {"design": "by_day", "by_day": {"1": 1.0, "2": 1.5}}
    f = cb.factors(items[0], design)
    assert f[0] == 1.0 and f[-1] == 1.5  # days past the last fitted day use the last factor


def test_the_per_day_design_is_chosen_only_when_it_helps_patients_left_out():
    growing = cb.choose(_items(spread=10.0, grow=0.25))
    gap = growing["left_out_day_gap"]
    assert growing["design"] == "by_day" and growing["n_patients"] == 12
    assert (
        gap["single"] > 0.06 and gap["by_day"] < gap["single"] - cb.MIN_GAIN
    )  # day 1 too wide, day 5 too narrow
    assert growing["left_out_patients_within"] == {"single": 12, "by_day": 12}  # per patient both look fine
    steady = cb.choose(_items(spread=14.0))
    assert (
        steady["design"] == "single" and 1.3 < steady["factor"] < 1.5
    )  # no real gain: the single factor stays
    assert abs(steady["left_out_day_gap"]["single"] - steady["left_out_day_gap"]["by_day"]) < cb.MIN_GAIN
    few = cb.choose(_items(spread=14.0, n=8))
    assert few["design"] == "single" and few["by_day"] == {} and np.isnan(few["left_out_day_gap"]["by_day"])


def test_a_factor_per_day_must_not_lose_on_the_number_the_registration_reports():
    closer = {"single": 0.030, "by_day": 0.002}
    assert cb.prefer_by_day(closer, {"single": 12, "by_day": 12}, fitted=True) is True
    assert (
        cb.prefer_by_day(closer, {"single": 17, "by_day": 14}, fitted=True) is False
    )  # fewer patients within
    assert cb.prefer_by_day({"single": 0.030, "by_day": 0.015}, {"single": 12, "by_day": 13}, True) is False
    assert cb.prefer_by_day(closer, {"single": 12, "by_day": 12}, fitted=False) is False
    assert (
        cb.prefer_by_day({"single": 0.03, "by_day": float("nan")}, {"single": 8, "by_day": 0}, False) is False
    )


def test_the_recalibrated_band_is_used_only_if_it_transfers_to_held_out_patients():
    def block(before, after, n_before, n_after):
        return {"before": {"mean_coverage": before, "patients_within": n_before},
                "after": {"mean_coverage": after, "patients_within": n_after}}  # fmt: skip

    assert cb.transfers(block(0.87, 0.80, 10, 13)) is True
    assert cb.transfers(block(0.83, 0.74, 10, 12)) is False  # further from 80 % than it was
    assert cb.transfers(block(0.87, 0.80, 10, 9)) is False  # closer on average, fewer patients within


def test_the_evaluation_reports_patients_within_70_to_90_before_and_after():
    items = _items(spread=14.0)
    out = cb.evaluate(items, {"design": "single", "factor": cb.fit_factor(items), "by_day": {}})
    assert (
        out["n_patients"] == 12 and out["before"]["patients_within"] < out["after"]["patients_within"] == 12
    )
    assert out["before"]["mean_coverage"] < 0.68 and abs(out["after"]["mean_coverage"] - 0.80) < 0.01
    assert [d["day"] for d in out["by_day"]] == [1, 2, 3, 4, 5] and out["by_day"][0]["n_patients"] == 12


def test_test_patients_only_report_a_design_fixed_beforehand():
    dev = {5.0: _items(spread=14.0), 3.0: _items(spread=14.0, k_days=3.0, days=7)}
    chosen = cb.run(dev, confirmatory=False)
    assert chosen["confirmatory"] is False and [b["k_days"] for b in chosen["by_k"]] == [5.0, 3.0]
    # held-out patients whose band was right as drawn: widening it for them is a step away from target
    test = {5.0: _items(spread=10.0), 3.0: _items(spread=10.0, k_days=3.0, days=7)}
    reported = cb.run(test, confirmatory=True, design=chosen["design"])
    assert reported["design"] == chosen["design"]  # nothing is refitted on the patients being reported
    assert chosen["use_recalibrated_band"] is None and reported["use_recalibrated_band"] is False
    # so a cohort that differs from the development one ends up off target, and the report says so
    assert reported["by_k"][0]["after"]["mean_coverage"] > 0.88
    text = cb._report(reported)
    assert "fixed on development patients" in text and "did not transfer" in text and "p0" not in text
    assert "in-sample" in cb._report(chosen)
