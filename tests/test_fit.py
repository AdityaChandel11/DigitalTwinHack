import numpy as np
import pytest
from conftest import Z_SHIFT

from chhaya.twin.fit import draw_ensemble, fit_twin
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import default_z
from chhaya.twin.priors import GB, population_prior, record_prior


@pytest.fixture(scope="module")
def fitted(rec):
    inp, obs_idx, obs_mmol = build_inputs(rec)
    cal = obs_idx < 4 * 1440
    return fit_twin(inp, obs_idx[cal], obs_mmol[cal], population_prior(), n_starts=3)


@pytest.mark.slow
def test_recovers_the_identifiable_parameters(fitted):
    z_true = default_z() + Z_SHIFT
    assert abs(fitted.z_map[GB] - z_true[GB]) < 0.05  # basal glucose within 5 %
    assert abs(fitted.z_map[0] - z_true[0]) < 0.25  # absorption rate
    assert abs(fitted.z_map[2] - z_true[2]) < 0.5  # beta-cell responsiveness
    assert 0.2 < fitted.sigma_res < 0.7  # close to the 0.4 mmol/L noise that was added


@pytest.mark.slow
def test_posterior_is_usable(fitted):
    assert np.allclose(fitted.cov, fitted.cov.T)
    assert np.linalg.eigvalsh(fitted.cov).min() > 0.0
    zs = draw_ensemble(fitted, n=50, seed=1)
    assert zs.shape == (50, 7)
    assert np.array_equal(zs[0], fitted.z_map)
    assert np.array_equal(zs, draw_ensemble(fitted, n=50, seed=1))  # reproducible


def test_too_few_readings_is_an_error(rec):
    inp, obs_idx, obs_mmol = build_inputs(rec)
    with pytest.raises(ValueError, match="at least 24"):
        fit_twin(inp, obs_idx[:10], obs_mmol[:10], population_prior())


def test_record_prior_uses_fasting_glucose_when_plausible():
    assert record_prior({"fasting_glucose_mgdl": 180.16}).mu[GB] == pytest.approx(np.log(10.0))
    assert record_prior({"fasting_glucose_mgdl": 180.16}).sd[GB] < population_prior().sd[GB]
    for junk in (None, float("nan"), 9.0, 4000.0):
        assert record_prior({"fasting_glucose_mgdl": junk}).mu[GB] == population_prior().mu[GB]
    assert record_prior({}).mu[GB] == population_prior().mu[GB]


@pytest.mark.slow
def test_fit_reports_how_the_optimiser_ended(fitted):
    assert fitted.nfev > 0
    assert fitted.status in (0, 1, 2, 3, 4)  # SciPy: 0 means it stopped on the evaluation limit
    assert 0 <= fitted.n_at_bound <= 7
