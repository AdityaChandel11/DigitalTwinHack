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


def test_the_threshold_lets_at_most_one_in_ten_quiet_recordings_alarm():
    scores = np.arange(1.0, 21.0)  # twenty recordings that did not drift
    drifted = np.zeros(20, dtype=bool)
    h = st.threshold(scores, drifted)
    assert h == 19.0 and np.mean(scores > h) == 0.05
    assert st.threshold(np.r_[scores, 500.0], np.r_[drifted, True]) == 19.0  # a drifted one does not set it
    assert np.mean(np.arange(11.0) > st.threshold(np.arange(11.0), np.zeros(11, dtype=bool))) <= 0.10
    with pytest.raises(ValueError, match="without drift"):
        st.threshold([1.0], [True])


def _rows():
    rows = []
    for i in range(12):
        hot = i < 5
        stat = np.full(8, 9.0 if hot else 1.0) * np.linspace(0.25, 1.0, 8)
        rows.append({"rec_id": f"r{i}", "patient_id": f"p{i}", "drift": 30.0 if hot else 2.0, "drifted": hot,
                     "score": float(stat.max()), "n_sticks": 8, "plain": 5.0 + (0.1 * i if hot else 0.0),
                     "days": np.arange(1.0, 9.0), "stat": stat})  # fmt: skip
    return rows


def test_alarms_report_sensitivity_false_alarms_and_days_to_alarm():
    out = st.alarms(_rows(), "score", 4.0)
    assert out["sensitivity"] == 1.0 and out["false_alarm_rate"] == 0.0 and out["n_alarms"] == 5
    assert out["median_days_to_alarm"] == 3.0  # 9 x 0.25, 0.357, 0.464: above 4 at the third fingerstick
    none = st.alarms(_rows(), "score", 99.0)
    assert none["sensitivity"] == 0.0 and np.isnan(none["median_days_to_alarm"])
    assert "median_days_to_alarm" not in st.alarms(_rows(), "plain", 5.05)


def test_auroc_intervals_resample_patients_and_skip_one_class_resamples():
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("days", "stat")} for r in _rows()])
    out = st.boot_auroc(df, n_boot=300)
    assert out["score"]["auroc"] == 1.0 and out["score"]["lo"] == 1.0
    assert out["diff"]["difference"] == pytest.approx(1.0 - out["plain"]["auroc"])
    assert 0 < out["n_resamples_used"] <= 300
    one_class = st.boot_auroc(df.assign(drifted=False), n_boot=50)
    assert np.isnan(one_class["score"]["auroc"]) and one_class["n_resamples_used"] == 0


def test_thresholds_come_from_development_recordings_and_test_recordings_only_report():
    dev = [_recording(0.0, seed=s) for s in range(20, 28)] + [_recording(40.0, seed=s) for s in (30, 31)]
    test = [_recording(0.0, seed=s) for s in range(40, 44)] + [
        _recording(45.0, seed=s) for s in range(50, 53)
    ]
    result = st.run(test, dev, [3.0], confirmatory=True, n_boot=200)
    block = result["by_k"][0]
    assert block["n_recordings"] == 7 and block["n_drifted"] == 3 and block["n_drifted_down"] == 0
    assert block["development"] == {"n_recordings": 10, "n_without_drift": 8}
    assert block["auroc"]["score"]["auroc"] == 1.0 and block["score"]["sensitivity"] == 1.0
    assert block["auroc_of_fingerstick_count"] == 0.5  # every recording here tests equally often
    assert block["score"]["false_alarm_rate"] <= 0.25 and block["score"]["median_days_to_alarm"] < 2.0
    again = st.run(
        test, dev[:8], [3.0], confirmatory=True, n_boot=50
    )  # no development recording drifted: fine
    assert again["by_k"][0]["score"]["threshold"] == block["score"]["threshold"]
    text = st._report(result)
    assert "set on development recordings" in text and "synth" not in text  # aggregates only
    empty = st.run(
        [make_recording(days=8)], dev, [3.0], confirmatory=True, n_boot=50
    )  # no fingersticks: no cohort
    assert empty["by_k"][0]["n_recordings"] == 0 and "No recording in the cohort" in st._report(empty)
    with pytest.raises(ValueError, match="pooled sensor map"):
        st.run(test, [], [3.0], confirmatory=True)
