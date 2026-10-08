import dataclasses

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.eval import staleness as st
from chhaya.twin.staleness import cusum, first_alarm, surprise_scale

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(shift: float, from_day: int = 3, seed: int = 11, pid: str | None = None):
    """Eight days; from `from_day` on glucose runs `shift` higher. Fingersticks every 4 hours read the sensor."""
    rec = make_recording(days=8, seed=seed)
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= from_day * 1440
    cgm.loc[late, "glucose_mgdl"] = np.clip(cgm.loc[late, "glucose_mgdl"] + shift, 40, 400)
    sticks = cgm[cgm["t_min"] % 240 == 0].reset_index(drop=True)
    pid = pid or f"synth-{seed}-{shift:g}"
    return dataclasses.replace(rec, cgm=cgm, fingersticks=sticks, rec_id=pid, patient_id=pid)


def test_the_sum_ignores_noise_and_grows_on_a_run_of_surprises_on_one_side():
    rng = np.random.default_rng(0)
    noise = rng.normal(0.0, 1.0, 60)
    assert cusum(noise).max() < 6.0
    assert cusum(noise + 1.5)[-1] > 40.0 and cusum(noise - 1.5)[-1] > 40.0  # up or down
    assert cusum([3.0, -3.0, 3.0, -3.0]).max() == 2.5  # alternating surprises cancel
    assert cusum([]).size == 0


def test_the_alarm_time_is_the_first_fingerstick_above_the_threshold():
    stat = cusum(np.r_[np.zeros(5), np.full(10, 2.0)])
    assert first_alarm(np.arange(15.0), stat, 4.0) == 7.0  # 1.5 a reading: above 4 at the third
    assert first_alarm(np.arange(15.0), stat, 99.0) is None
    assert surprise_scale(20.0, 15.0) == 25.0


def test_a_patient_who_changed_scores_far_above_one_who_did_not():
    changed, same = (
        st.score_recording(_recording(40.0), 3, POOLED),
        st.score_recording(_recording(0.0), 3, POOLED),
    )
    assert changed["drifted"] and not same["drifted"] and changed["drift"] > 30.0
    assert changed["score"] > 3.0 * same["score"] and changed["plain"] > same["plain"] + 20.0
    assert changed["days"].min() >= 0.0 and changed["stat"].size == changed["days"].size
    down = st.score_recording(_recording(-40.0), 3, POOLED)
    assert down["drifted"] and down["drift"] < -20.0 and down["score"] > 3.0 * same["score"]


def test_the_alarm_never_reads_a_hidden_sensor_value_and_the_label_does():
    rec = _recording(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    a, b = (
        st.score_recording(rec, 3, POOLED),
        st.score_recording(dataclasses.replace(rec, cgm=cgm), 3, POOLED),
    )
    assert a["score"] == b["score"] and a["plain"] == b["plain"] and np.array_equal(a["stat"], b["stat"])
    assert a["drift"] != b["drift"]


def test_a_recording_without_fingersticks_is_outside_the_cohort(rec):
    assert st.score_recording(rec, 3, POOLED) is None


def test_the_threshold_is_the_smallest_score_that_at_most_one_in_ten_quiet_recordings_exceed():
    quiet = np.zeros(20, dtype=bool)
    scores = np.arange(1.0, 21.0)  # twenty recordings that did not drift
    h = st.threshold(scores, quiet)
    assert h == 18.0 and np.mean(scores > h) == 0.10  # two of twenty above is exactly ten percent
    assert st.threshold(np.arange(1.0, 11.0), np.zeros(10, dtype=bool)) == 9.0  # one of ten above
    assert st.threshold(np.arange(1.0, 18.0), np.zeros(17, dtype=bool)) == 16.0  # one of seventeen: 5.9 %
    assert st.threshold(np.r_[scores, 500.0], np.r_[quiet, True]) == 18.0  # a drifted one does not set it
    for n in range(1, 60):  # whatever the count, never more than one in ten, and no smaller score would do
        x = np.random.default_rng(n).normal(size=n)
        h = st.threshold(x, np.zeros(n, dtype=bool))
        assert np.mean(x > h) <= 0.10 and all(np.mean(x > v) > 0.10 for v in x[x < h])
    assert st.threshold([2.0, 2.0, 2.0], [False] * 3) == 2.0  # ties: nothing lies above
    with pytest.raises(ValueError, match="without drift"):
        st.threshold([1.0], [True])


def test_the_early_score_reads_only_the_first_two_days_so_every_recording_has_the_same_length():
    # glucose 60 higher from the fourth day after the sensor: two of five hidden days, a drift of about 28
    late = st.score_recording(_recording(60.0, from_day=6), 3, POOLED)
    soon = st.score_recording(_recording(40.0, from_day=3), 3, POOLED)
    same = st.score_recording(_recording(0.0), 3, POOLED)
    assert late["drifted"] and late["score"] > 3.0 * same["score"]  # the whole window sees it
    assert late["early"] == same["early"]  # the first two days cannot: nothing had changed yet
    assert soon["early"] > 3.0 * same["early"] and soon["early"] <= soon["score"]
    assert (soon["days"] < st.EARLY_DAYS).sum() == 12  # six fingersticks a day for two days


def _rows():
    rows = []
    for i in range(12):
        hot = i < 5
        stat = np.full(8, 9.0 if hot else 1.0) * np.linspace(0.25, 1.0, 8)
        rows.append({"rec_id": f"r{i}", "patient_id": f"p{i}", "drift": 30.0 if hot else 2.0, "drifted": hot,
                     "score": float(stat.max()), "early": float(stat[:2].max()), "n_sticks": 8 + (i % 3),
                     "plain": 5.0 + (0.1 * i if hot else 0.0),
                     "days": np.arange(1.0, 9.0), "stat": stat})  # fmt: skip
    return rows


def test_alarms_report_counts_sensitivity_false_alarms_and_days_to_alarm():
    out = st.alarms(_rows(), "score", 4.0)
    assert out["sensitivity"] == 1.0 and out["false_alarm_rate"] == 0.0 and out["n_alarms"] == 5
    assert (out["drifted_alarmed"], out["n_drifted"], out["quiet_alarmed"], out["n_quiet"]) == (5, 5, 0, 7)
    assert out["median_days_to_alarm"] == 3.0  # 9 x 0.25, 0.357, 0.464: above 4 at the third fingerstick
    none = st.alarms(_rows(), "score", 99.0)
    assert none["sensitivity"] == 0.0 and np.isnan(none["median_days_to_alarm"])
    assert "median_days_to_alarm" not in st.alarms(_rows(), "plain", 5.05)
    assert "median_days_to_alarm" not in st.alarms(_rows(), "early", 1.0)


def test_auroc_intervals_resample_patients_and_skip_one_class_resamples():
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("days", "stat")} for r in _rows()])
    out = st.boot_auroc(df, n_boot=300)
    assert out["score"]["auroc"] == 1.0 and out["score"]["lo"] == 1.0
    assert out["diff"]["difference"] == pytest.approx(1.0 - out["plain"]["auroc"])
    assert set(out) == {"score", "early", "plain", "n_sticks", "diff", "n_resamples_used"}
    assert (
        out["n_sticks"]["lo"] <= out["n_sticks"]["auroc"] <= out["n_sticks"]["hi"]
    )  # the count has its interval
    assert 0 < out["n_resamples_used"] <= 300
    one_class = st.boot_auroc(df.assign(drifted=False), n_boot=50)
    assert np.isnan(one_class["score"]["auroc"]) and one_class["n_resamples_used"] == 0


def _dev_and_test():
    dev = [_recording(0.0, seed=s) for s in range(20, 28)] + [_recording(40.0, seed=s) for s in (30, 31)]
    test = [_recording(0.0, seed=s) for s in range(40, 44)] + [
        _recording(45.0, seed=s) for s in range(50, 53)
    ]
    return dev, test


def test_thresholds_come_from_development_recordings_and_test_recordings_only_report():
    dev, test = _dev_and_test()
    result = st.run(test, dev, [3.0], confirmatory=True, n_boot=200)
    block = result["by_k"][0]
    assert block["primary"] is True and block["n_recordings"] == 7 and block["n_drifted"] == 3
    assert block["n_drifted_down"] == 0 and block["development"] == {"n_recordings": 10, "n_without_drift": 8}
    assert block["auroc"]["score"]["auroc"] == 1.0 and block["score"]["sensitivity"] == 1.0
    assert block["auroc"]["n_sticks"]["auroc"] == 0.5  # every recording here tests equally often
    assert block["score"]["false_alarm_rate"] <= 0.25 and block["score"]["median_days_to_alarm"] < 2.0

    def rows(recs):
        return [st.score_recording(r, 3.0, st.pooled_line(dev, 3.0)) for r in recs]

    for name in st.SCORES:
        from_dev = st.threshold([r[name] for r in rows(dev)], [r["drifted"] for r in rows(dev)])
        from_test = st.threshold([r[name] for r in rows(test)], [r["drifted"] for r in rows(test)])
        assert block[name]["threshold"] == from_dev != from_test, (
            name
        )  # set on the test recordings, it would differ
    text = st._report(result)
    assert "set on development recordings" in text and "(primary)" in text and "synth" not in text
    empty = st.run([make_recording(days=8)], dev, [3.0], confirmatory=True, n_boot=50)  # no fingersticks
    assert empty["by_k"][0]["n_recordings"] == 0 and "No recording in the cohort" in st._report(empty)
    with pytest.raises(ValueError, match="pooled sensor map"):
        st.run(test, [], [3.0], confirmatory=True)


def test_a_pass_over_test_recordings_refuses_a_patient_who_also_set_the_thresholds():
    dev, test = _dev_and_test()
    with pytest.raises(ValueError, match="both"):
        st.run(test, [*dev, test[0]], [3.0], confirmatory=True, n_boot=20)
    st.run(dev, dev, [3.0], confirmatory=False, n_boot=20)  # a development run scores the same recordings


def test_a_calibration_length_with_no_quiet_development_recording_is_a_row_with_its_error():
    dev, test = _dev_and_test()
    all_drifted = dev[8:]  # the two development recordings that drifted
    result = st.run(test, [*all_drifted, *dev[:8]], [3.0, 5.0], confirmatory=True, n_boot=20)
    assert [b["primary"] for b in result["by_k"]] == [True, False] and "error" not in result["by_k"][0]
    only = st.run(test, all_drifted, [3.0, 5.0], confirmatory=True, n_boot=20)
    assert all("without drift" in b["error"] and b["n_recordings"] == 0 for b in only["by_k"])
    assert "without drift" in st._report(only)  # said in the report, not lost


def test_the_pass_runs_only_with_the_registered_filter_constants():
    st.check_frozen(st.FilterConfig())
    with pytest.raises(SystemExit, match="fingerstick spread"):
        st.check_frozen(st.FilterConfig(obs_sd=10.0))
    with pytest.raises(SystemExit, match="frozen design"):
        st.check_frozen(st.FilterConfig(tau_min=60.0))
