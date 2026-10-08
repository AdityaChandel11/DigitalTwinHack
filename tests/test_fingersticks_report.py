import dataclasses
import json

import numpy as np
import pytest
from conftest import make_recording

from chhaya.eval import fingersticks_report as fr
from chhaya.eval.descriptive import REPORT_KEYS, pooled_line

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(shift: float, every_min: int = 240, days: int = 7, seed: int = 11):
    """After day 3 the patient's glucose runs `shift` mg/dL higher. Fingersticks read the sensor exactly."""
    rec = make_recording(days=days, seed=seed)
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= SPLIT
    cgm.loc[late, "glucose_mgdl"] = np.clip(cgm.loc[late, "glucose_mgdl"] + shift, 40, 400)
    sticks = cgm[cgm["t_min"] % every_min == 0].reset_index(drop=True)
    return dataclasses.replace(rec, cgm=cgm, fingersticks=sticks)


def _cohort(n: int = 7, shift: float = 40.0):
    rec = _recording(shift, days=8)
    return [dataclasses.replace(rec, rec_id=f"r{i}", patient_id=f"p{i}") for i in range(n)]


def test_when_the_patient_has_changed_the_shadow_states_the_report_better_than_the_old_one():
    row, days = fr.recording_rows(_recording(40.0), 3, POOLED)
    assert row["stale_mean_err"] > 30.0 and row["stale_mean_err"] == row["abs_dmean"] and row["moved"] == 1.0
    assert row["hindsight_mean_err"] < row["stale_mean_err"] - 20.0
    assert row["hindsight_tar_err"] < row["stale_tar_err"]
    assert [d["day"] for d in days] == [1, 2, 3, 4]
    assert all(d["hindsight_rmse"] < d["control_rmse"] - 5.0 for d in days)
    assert all(d["hindsight_mean_err"] < d["abs_dmean"] for d in days)


def test_when_nothing_changed_the_old_report_is_still_right():
    row, _ = fr.recording_rows(_recording(0.0), 3, POOLED)
    assert row["stale_mean_err"] < 8.0 and row["moved"] == 0.0 and row["stale_tir_err"] < 8.0


def test_no_stated_report_reads_a_hidden_sensor_value():
    rec = _recording(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    a, _ = fr.stated(rec, 3, POOLED)
    b, _ = fr.stated(dataclasses.replace(rec, cgm=cgm), 3, POOLED)
    assert set(a) == set(fr.SOURCES)
    for source in fr.SOURCES:
        assert a[source] == pytest.approx(b[source]), source


def test_testing_frequency_is_recorded_per_recording():
    row, _ = fr.recording_rows(_recording(0.0, every_min=240), 3, POOLED)
    assert row["sticks_per_day"] == 6.0 and row["sticks_per_day_hidden"] == 6.0 and row["n_sticks"] == 24


def test_a_recording_outside_the_cohort_is_not_scored(rec):
    assert fr.recording_rows(rec, 3, POOLED) is None  # no fingersticks at all
    assert fr.block_for([rec], 3.0, POOLED) == {"k_days": 3.0, "n_patients": 0}


def test_the_summary_compares_every_source_and_two_recordings_of_a_patient_count_once():
    recs = _cohort()
    recs.append(dataclasses.replace(recs[0], rec_id="again"))
    block = fr.block_for(recs, 3.0, POOLED)
    assert block["n_patients"] == 7 and block["recordings"] == 8
    for key in REPORT_KEYS:
        assert set(block[key]["errors"]) == set(fr.SOURCES)
        assert block[key]["hindsight_vs_stale"]["n_patients"] == 7
    assert block["mean"]["hindsight_vs_stale"]["median_diff"] < -20.0
    assert block["aged"]["share_moved"] == 1.0 and block["density"]["sticks_per_day"]["median"] == 6.0
    assert [d["day"] for d in block["by_day"]] == [1, 2, 3, 4, 5]
    assert block["by_day"][0]["hindsight_rmse_vs_control_rmse"]["median_diff"] < 0
    assert {s["column"] for s in block["slopes"]} == {"control_rmse", "hindsight_rmse", "abs_dmean"}


def _committed(recs, k_list=(3.0, 5.0)):
    """What the run being repeated would have written: by_k[i].rules.all, as chhaya.eval.fingersticks does."""
    by_k = []
    for k in k_list:
        block = fr.block_for(recs, k, pooled_line(recs, k))
        by_k.append({"k_days": k, "rules": {"all": {key: block[key] for key in fr.CHECKED}}})
    return {"by_k": by_k}


def test_the_pass_is_written_only_when_it_reproduces_the_run_it_repeats(tmp_path):
    recs = _cohort()
    committed = _committed(recs)
    result = fr.run(recs, recs, [3.0, 5.0], tmp_path / "ok", True, committed)
    assert result["by_k"][0]["density_dev"]["sticks_per_day"]["median"] == 6.0
    saved = json.loads((tmp_path / "ok" / "summary.json").read_text(encoding="utf-8"))
    assert saved["confirmatory"] is True and len(saved["by_k"]) == 2
    text = (tmp_path / "ok" / "report.md").read_text(encoding="utf-8")
    assert "second time" in text and "p0" not in text and "r0" not in text  # aggregates only

    committed["by_k"][1]["rules"]["all"]["control_rmse"] += 0.01  # the second k, after the first passed
    with pytest.raises(SystemExit, match="does not reproduce"):
        fr.run(recs, recs, [3.0, 5.0], tmp_path / "bad", True, committed)
    assert not (tmp_path / "bad").exists()  # nothing is written, not even the k that matched


def test_a_committed_run_at_another_k_is_not_accepted_as_the_same_run(tmp_path):
    recs = _cohort()
    with pytest.raises(SystemExit, match="k = 5"):
        fr.run(recs, recs, [3.0], tmp_path, False, _committed(recs, (5.0,)))


def test_a_development_run_carries_no_second_density_block(tmp_path):
    recs = _cohort()
    result = fr.run(recs, recs, [3.0], tmp_path, False)
    assert result["confirmatory"] is False and "density_dev" not in result["by_k"][0]
    assert "Not confirmatory" in (tmp_path / "report.md").read_text(encoding="utf-8")
