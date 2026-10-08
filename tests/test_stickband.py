"""The spread the frozen fingerstick filter assigns to its own estimate (note to Amendment 3, 8 Oct, the band)."""

import numpy as np
import pytest

from chhaya.twin.assimilate import FilterConfig, deviation
from chhaya.twin.stickband import Z80, _posterior, band, deviation_sd

CFG = FilterConfig()
AT_A_STICK = np.sqrt(CFG.fast_sd**2 * CFG.obs_sd**2 / (CFG.fast_sd**2 + CFG.obs_sd**2))  # 12.86 mg/dL


def test_with_no_fingerstick_the_spread_is_the_filters_stationary_spread():
    sd = deviation_sd([], [0.0, 300.0, 5000.0])
    assert np.allclose(sd, 25.0)


def test_at_a_fingerstick_the_spread_is_the_posterior_of_one_reading():
    sd = deviation_sd([600.0], [600.0])
    assert sd[0] == pytest.approx(AT_A_STICK)
    assert sd[0] == pytest.approx(12.86, abs=0.01)


def test_a_reading_stamped_at_the_fingersticks_own_minute_is_not_narrowed_when_read_strictly_before():
    # F1 was scored this way: a fingerstick and a sensor reading that share a minute have no known order
    sd = deviation_sd([600.0], [600.0, 601.0], strictly_before=True)
    assert sd[0] == pytest.approx(25.0)
    assert sd[1] == pytest.approx(13.15, abs=0.02)  # a minute later the fingerstick counts, barely faded


def test_the_spread_returns_to_the_stationary_one_five_time_constants_after_a_fingerstick():
    sd = deviation_sd([0.0], [5 * CFG.tau_min])
    assert 24.75 < sd[0] <= 25.0


def test_before_the_first_fingerstick_the_live_spread_is_the_stationary_one():
    assert deviation_sd([600.0], [0.0, 599.0])[1] == pytest.approx(25.0)


def test_the_spread_does_not_depend_on_what_the_fingersticks_read():
    rng = np.random.default_rng(3)
    t_obs = np.sort(rng.uniform(0, 3000, 12))
    t_eval = np.arange(0.0, 3000.0, 15.0)
    for smooth in (False, True):
        _, a = _posterior(t_obs, rng.normal(0, 30, 12), t_eval, CFG, smooth, False)
        _, b = _posterior(t_obs, rng.normal(40, 60, 12), t_eval, CFG, smooth, False)
        assert np.array_equal(a, b)
        assert np.array_equal(a, deviation_sd(t_obs, t_eval, smooth=smooth))


@pytest.mark.parametrize(
    ("smooth", "strictly_before"),
    [(False, False), (False, True), (True, False)],
    ids=["live", "strict", "hindsight"],
)
def test_the_mean_of_the_same_recursion_is_the_frozen_estimators_own(smooth, strictly_before):
    # the band is only the filter's own spread if this module runs the filter that section F scored
    rng = np.random.default_rng(11)
    t_obs = np.round(rng.uniform(100, 4000, 25))
    t_obs[5] = t_obs[4]  # two fingersticks in one minute
    z = rng.normal(0, 30, t_obs.size)
    t_eval = np.concatenate([np.arange(0.0, 4300.0, 15.0), t_obs[:6]])
    mean, _ = _posterior(t_obs, z, t_eval, CFG, smooth, strictly_before)
    want = deviation(t_obs, z, t_eval, CFG, smooth=smooth, strictly_before=strictly_before)
    assert np.allclose(mean, want, atol=1e-8)


def test_in_hindsight_the_spread_is_never_wider_than_live():
    rng = np.random.default_rng(5)
    t_obs = np.sort(rng.uniform(0, 4000, 20))
    t_eval = np.arange(0.0, 4200.0, 10.0)
    live = deviation_sd(t_obs, t_eval)
    hind = deviation_sd(t_obs, t_eval, smooth=True)
    assert (hind <= live + 1e-9).all()
    assert hind.min() > 0.0


def test_fingersticks_given_in_any_order_give_the_same_spread():
    t_obs = np.array([900.0, 100.0, 500.0, 2000.0])
    t_eval = np.arange(0.0, 2500.0, 25.0)
    for smooth in (False, True):
        assert np.allclose(
            deviation_sd(t_obs, t_eval, smooth=smooth), deviation_sd(np.sort(t_obs), t_eval, smooth=smooth)
        )


@pytest.mark.parametrize("smooth", [False, True], ids=["live", "hindsight"])
def test_on_data_drawn_from_the_filters_own_model_the_80_percent_band_holds_80_percent(smooth):
    # the check that the variance, the bridge between fingersticks and the smoother are right, not just plausible
    rng = np.random.default_rng(7)
    tau, sd, obs = CFG.tau_min, CFG.fast_sd, CFG.obs_sd
    grid = np.arange(0.0, 2880.0, 30.0)
    t_obs = grid[[7, 15, 16, 30, 44, 52, 70, 88]] + 10.0
    times = np.sort(np.concatenate([grid, t_obs]))
    inside, total = 0, 0
    for _ in range(600):
        d = np.empty(times.size)
        d[0] = rng.normal(0, sd)
        for i in range(1, times.size):
            a = np.exp(-(times[i] - times[i - 1]) / tau)
            d[i] = a * d[i - 1] + rng.normal(0, sd * np.sqrt(1 - a * a))
        truth = d[np.isin(times, grid)]
        z = d[np.searchsorted(times, t_obs)] + rng.normal(0, obs, t_obs.size)
        mean, spread = _posterior(t_obs, z, grid, CFG, smooth, False)
        inside += int((np.abs(truth - mean) <= Z80 * spread).sum())
        total += grid.size
    assert inside / total == pytest.approx(0.80, abs=0.012)


def test_a_filter_with_a_slow_level_is_refused():
    with pytest.raises(ValueError, match="slow"):
        deviation_sd([0.0], [10.0], FilterConfig(slow=True))


def test_band_is_symmetric_and_scales_with_the_patients_spread():
    est, sd = np.array([100.0, 150.0]), np.array([25.0, 12.5])
    lo, hi = band(est, sd)
    assert np.allclose(hi - est, est - lo)
    assert np.allclose(hi - est, 1.2816 * sd, atol=1e-3)
    lo2, hi2 = band(est, sd, scale=2.0)
    assert np.allclose(hi2 - est, 2.0 * (hi - est))


def test_band_refuses_a_scale_that_is_not_positive():
    with pytest.raises(ValueError, match="scale"):
        band(np.array([100.0]), np.array([25.0]), scale=0.0)
