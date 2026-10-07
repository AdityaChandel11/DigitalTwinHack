import numpy as np
import pytest

from chhaya.eval.metrics import coverage, mard, pearson, rmse, score, time_in_ranges


def test_basic_errors():
    assert rmse([100, 120], [110, 110]) == pytest.approx(10.0)
    assert mard([90, 220], [100, 200]) == pytest.approx(10.0)
    assert np.isnan(pearson([100, 100, 100], [90, 100, 110]))


def test_ranges_use_70_and_180_inclusive():
    r = time_in_ranges([69, 70, 180, 181])
    assert (r["tbr"], r["tir"], r["tar"]) == (25.0, 50.0, 25.0)


def test_coverage_counts_edges_as_inside():
    assert coverage([100, 150, 200], [100, 100, 100], [150, 150, 150]) == pytest.approx(2 / 3)


def test_score_reports_clinical_summary_errors():
    truth = np.array([60.0, 100.0, 150.0, 200.0])
    s = score(truth + 10.0, truth, truth - 20.0, truth + 20.0)
    assert s["bias"] == pytest.approx(10.0)
    assert s["tbr_err"] == pytest.approx(25.0)  # the 60 became 70 and left the low range
    assert s["gmi_err"] == pytest.approx(0.2392)
    assert s["cov80"] == 1.0
    assert "cov80" not in score(truth, truth)


def test_score_rejects_mismatched_or_empty_input():
    with pytest.raises(ValueError):
        score([100.0], [100.0, 110.0])
    with pytest.raises(ValueError):
        score([], [])


def test_correlation_with_a_constant_estimate_is_undefined_not_rounding_noise():
    truth = np.linspace(90.0, 180.0, 884)
    assert np.isnan(pearson(np.full(884, 0.1 + 0.2), truth))  # np.std of this constant is 1e-17, not 0


def test_within_15_15_uses_absolute_error_below_100_and_relative_above():
    from chhaya.eval.metrics import within_15_15

    ref = np.array([80.0, 80.0, 200.0, 200.0])
    pred = np.array([94.0, 96.0, 229.0, 231.0])  # 14 and 16 mg/dL off; 14.5 % and 15.5 % off
    assert within_15_15(pred, ref) == 50.0


def test_clarke_zones_on_clear_cases():
    from chhaya.eval.metrics import clarke_zones

    ref = np.array([100.0, 60.0, 100.0, 100.0, 300.0, 200.0, 60.0])
    pred = np.array([110.0, 65.0, 140.0, 250.0, 150.0, 60.0, 200.0])
    z = clarke_zones(pred, ref)  # A, A, B, C, D, E, E
    assert round(z["A"], 1) == 28.6 and round(z["B"], 1) == 14.3 and round(z["C"], 1) == 14.3
    assert round(z["D"], 1) == 14.3 and round(z["E"], 1) == 28.6
    assert abs(sum(z.values()) - 100.0) < 1e-9
