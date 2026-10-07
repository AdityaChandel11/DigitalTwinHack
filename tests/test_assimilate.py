import numpy as np

from chhaya.twin.assimilate import FilterConfig, deviation, pooled_map, sensor_map

CFG = FilterConfig()


def test_no_fingersticks_means_no_deviation():
    assert deviation(np.array([]), np.array([]), np.arange(0.0, 600.0, 15.0)).tolist() == [0.0] * 40


def test_a_surprise_is_believed_in_part_and_then_fades():
    t = np.array([0.0, CFG.tau_min, 10 * CFG.tau_min])
    d = deviation(np.array([0.0]), np.array([30.0]), t)
    assert 15.0 < d[0] < 30.0  # shrunk toward zero by the observation noise
    assert abs(d[1] / d[0] - np.exp(-1.0)) < 1e-6  # one time constant later
    assert abs(d[2]) < 0.01


def test_the_live_estimate_never_changes_because_of_a_later_fingerstick():
    t_eval = np.arange(0.0, 300.0, 15.0)
    one = deviation(np.array([60.0]), np.array([20.0]), t_eval)
    two = deviation(np.array([60.0, 240.0]), np.array([20.0, -40.0]), t_eval)
    assert np.allclose(one[t_eval < 240.0], two[t_eval < 240.0])
    assert (one[t_eval < 60.0] == 0.0).all()


def test_in_hindsight_a_fingerstick_also_informs_the_time_before_it():
    t_eval = np.array([0.0, 30.0, 60.0])
    d = deviation(np.array([60.0]), np.array([30.0]), t_eval, smooth=True)
    assert 0.0 < d[0] < d[1] < d[2]


def test_two_fingersticks_at_the_same_minute_do_not_break_it():
    d = deviation(np.array([60.0, 60.0]), np.array([20.0, 30.0]), np.array([60.0, 90.0]))
    assert np.isfinite(d).all() and d[0] > 0


def test_fingersticks_given_out_of_order_give_the_same_answer():
    t_obs, z, t_eval = (
        np.array([300.0, 60.0, 180.0]),
        np.array([-10.0, 20.0, 5.0]),
        np.arange(0.0, 600.0, 30.0),
    )
    for smooth in (False, True):
        a = deviation(t_obs, z, t_eval, smooth=smooth)
        b = deviation(np.sort(t_obs), z[np.argsort(t_obs)], t_eval, smooth=smooth)
        assert np.allclose(a, b)


def test_slow_level_keeps_a_lasting_shift():
    t_obs = np.arange(0.0, 3 * 1440.0, 360.0)
    z = np.full(t_obs.size, 30.0)
    late = np.array([3 * 1440.0 + 600.0])  # ten hours after the last fingerstick
    fast_only = deviation(t_obs, z, late, FilterConfig(slow=False))
    with_slow = deviation(t_obs, z, late, FilterConfig(slow=True))
    assert fast_only[0] < 1.0 and with_slow[0] > 10.0


def test_sensor_map_falls_back_to_the_pooled_slope_with_few_pairs():
    rng = np.random.default_rng(0)
    cbg = rng.uniform(80, 300, 200)
    pooled = pooled_map(cbg, 5.0 + 0.9 * cbg + rng.normal(0, 3, 200))
    assert abs(pooled[1] - 0.9) < 0.02 and abs(pooled[0] - 5.0) < 4.0
    own = sensor_map(cbg[:30], -20.0 + 1.0 * cbg[:30], pooled)
    assert abs(own[1] - 1.0) < 0.01 and abs(own[0] + 20.0) < 1.0
    few = sensor_map(cbg[:4], cbg[:4] - 12.0, pooled)
    assert few[1] == pooled[1] and abs(np.mean(few[0] + few[1] * cbg[:4] - (cbg[:4] - 12.0))) < 1e-9
    assert sensor_map(cbg[:1], cbg[:1], pooled) == pooled
