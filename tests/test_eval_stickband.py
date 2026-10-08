"""The band of the fingerstick estimate as an experiment (note to Amendment 3, 8 Oct 2026; descriptive)."""

import dataclasses
import json

import numpy as np
import pytest
from conftest import make_recording

from chhaya.eval import stickband as sb
from chhaya.eval.descriptive import profile_sigma
from chhaya.twin.assimilate import FilterConfig

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(seed: int = 11, pid: str | None = None, days: int = 8):
    """Fingersticks every 4 hours read the sensor, so the sensor map is the identity."""
    rec = make_recording(days=days, seed=seed)
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)
    pid = pid or f"synth-{seed}"
    return dataclasses.replace(rec, fingersticks=sticks, rec_id=pid, patient_id=pid)


def _with_hidden(rec, values):
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = values
    return dataclasses.replace(rec, cgm=cgm)


@pytest.mark.parametrize("which", sb.ESTIMATES)
@pytest.mark.parametrize("construction", sb.CONSTRUCTIONS)
def test_the_band_never_reads_a_hidden_sensor_value(which, construction):
    rec = _recording()
    a = sb.band_of(rec, 3, POOLED, construction, which)
    b = sb.band_of(_with_hidden(rec, 111.0), 3, POOLED, construction, which)
    for key in ("t", "est", "lo", "hi"):
        assert np.array_equal(a[key], b[key]), key
    assert (a["t"] >= SPLIT).all() and (a["lo"] < a["est"]).all() and (a["est"] < a["hi"]).all()


def test_the_patient_construction_takes_its_width_from_the_patients_own_calibration_days():
    rec = _recording()
    plain, own = (sb.band_of(rec, 3, POOLED, c, "live") for c in sb.CONSTRUCTIONS)
    cal = rec.cgm[rec.cgm["t_min"] < SPLIT]
    want = profile_sigma(cal["t_min"].to_numpy(), cal["glucose_mgdl"].to_numpy()) / FilterConfig().fast_sd
    ratio = (own["hi"] - own["est"]) / (plain["hi"] - plain["est"])
    assert np.allclose(ratio, want) and np.array_equal(plain["est"], own["est"])


def test_far_from_any_fingerstick_the_filter_band_is_32_mgdl_each_side_and_narrower_just_after_one():
    rec = _recording()
    b = sb.band_of(rec, 3, POOLED, "filter", "live")
    half = b["hi"] - b["est"]
    assert half.max() <= 1.2816 * 25.0 + 1e-6
    # 15 minutes after a fingerstick the spread is sqrt(a^2 * 165.4 + 625 * (1 - a^2)) with a = exp(-15 / 120)
    assert half[b["t"] % 240 == 15].max() == pytest.approx(20.94, abs=0.05)
    assert half[b["t"] % 240 == 225].min() > 31.5  # and almost back to 32.0 just before the next one


def test_in_hindsight_the_band_is_never_wider_than_live():
    rec = _recording()
    live, hind = (sb.band_of(rec, 3, POOLED, "filter", w) for w in sb.ESTIMATES)
    assert ((hind["hi"] - hind["est"]) <= (live["hi"] - live["est"]) + 1e-9).all()


def test_coverage_is_the_share_of_hidden_readings_inside_the_band():
    rec = _recording()
    est = sb.band_of(rec, 3, POOLED, "filter", "live")["est"]
    on_it = sb.score_recording(_with_hidden(rec, est), 3, POOLED)
    far = sb.score_recording(_with_hidden(rec, np.clip(est + 200.0, 20, 600)), 3, POOLED)
    assert on_it["live_filter_cov"] == 100.0 and far["live_filter_cov"] == 0.0
    assert on_it["live_filter_half"] == pytest.approx(far["live_filter_half"])  # the width ignores the sensor
    assert 13.0 < on_it["live_filter_half"] < 32.1


def test_a_recording_without_fingersticks_is_outside_the_cohort(rec):
    assert sb.score_recording(rec, 3, POOLED) is None


def test_an_unknown_construction_or_estimate_is_refused():
    rec = _recording()
    with pytest.raises(ValueError, match="construction"):
        sb.band_of(rec, 3, POOLED, "widest", "live")
    with pytest.raises(ValueError, match="estimate"):
        sb.band_of(rec, 3, POOLED, "filter", "control")


def test_the_patient_is_the_unit_of_every_summary():
    rows = [
        {"patient_id": "a", "live_filter_cov": 60.0, "live_filter_half": 30.0},
        {"patient_id": "a", "live_filter_cov": 100.0, "live_filter_half": 30.0},
        {"patient_id": "b", "live_filter_cov": 90.0, "live_filter_half": 20.0},
    ]
    s = sb.summarise(rows, "live", "filter")
    assert s["n_patients"] == 2 and s["mean"] == 85.0  # (80 + 90) / 2, not the mean of three recordings
    assert (s["min"], s["max"], s["n_within"]) == (80.0, 90.0, 2)
    assert s["median_half_width"] == 25.0


def test_the_choice_is_the_construction_closer_to_80_then_the_one_with_more_patients_within_70_to_90():
    def s(mean, n):
        return {"mean": mean, "n_within": n}

    assert sb.choose({"filter": s(88.0, 9), "patient": s(82.0, 3)}) == "patient"  # 2 points off beats 8
    assert (
        sb.choose({"filter": s(77.5, 4), "patient": s(83.0, 9)}) == "patient"
    )  # 2.5 and 3: a tie, so by count
    assert sb.choose({"filter": s(83.0, 9), "patient": s(77.5, 9)}) == "filter"  # still tied: the first
    assert sb.choose({"filter": s(81.0, 1), "patient": s(79.9, 9)}) == "patient"  # 1.0 and 0.1: tie, by count


def test_run_reports_both_estimates_and_both_constructions_and_who_reaches_each_day(tmp_path):
    dev = [_recording(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]
    result = sb.run(dev, dev, [3.0], confirmatory=False, frozen=None)
    block = result["by_k"][0]
    assert block["primary"] and block["n_patients"] == 3 and block["n_recordings"] == 3
    for which in sb.ESTIMATES:
        for c in sb.CONSTRUCTIONS:
            assert 0.0 <= block["bands"][which][c]["mean"] <= 100.0
    assert block["choice"]["chosen"] in sb.CONSTRUCTIONS and block["choice"]["on"] == "live"
    days = block["by_day"]
    assert [d["day"] for d in days] == [1, 2, 3, 4, 5] and all(d["share_of_cohort"] == 1.0 for d in days)
    assert "live_filter_cov" in days[0] and "hindsight_patient_cov" in days[0]
    sb.write_outputs(tmp_path, result, sb._report(result))
    assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["by_k"][0]["k_days"] == 3.0


def test_a_pass_over_test_recordings_refuses_a_patient_who_is_also_a_development_patient():
    dev = [_recording(seed=1, pid="shared"), _recording(seed=2, pid="dev-2")]
    with pytest.raises(ValueError, match="both"):
        sb.run([_recording(seed=3, pid="shared")], dev, [3.0], confirmatory=True, frozen="filter")


def test_a_pass_over_test_recordings_needs_the_construction_frozen_on_development_patients():
    dev = [_recording(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]
    test = [_recording(seed=9, pid="test-9")]
    with pytest.raises(ValueError, match="frozen"):
        sb.run(test, dev, [3.0], confirmatory=True, frozen=None)
    chosen = sb.run(dev, dev, [3.0], confirmatory=False, frozen=None)["by_k"][0]["choice"]["chosen"]
    other = next(c for c in sb.CONSTRUCTIONS if c != chosen)
    with pytest.raises(ValueError, match="development patients choose"):
        sb.run(test, dev, [3.0], confirmatory=True, frozen=other)
    result = sb.run(test, dev, [3.0], confirmatory=True, frozen=chosen)
    assert result["frozen"] == chosen and result["by_k"][0]["n_patients"] == 1


def test_the_pass_runs_only_with_the_registered_filter_constants():
    sb.check_frozen(FilterConfig())
    for cfg in (FilterConfig(tau_min=60.0), FilterConfig(fast_sd=30.0), FilterConfig(obs_sd=10.0)):
        with pytest.raises(SystemExit):
            sb.check_frozen(cfg)


def test_a_recording_whose_band_cannot_be_formed_keeps_a_row_with_its_error():
    flat = _recording(seed=4, pid="flat")
    cgm = flat.cgm.copy()
    cgm.loc[cgm["t_min"] < SPLIT, "glucose_mgdl"] = (
        120.0  # no spread in the wear: no width for the patient band
    )
    sticks = cgm[cgm["t_min"] % 240 == 0].reset_index(drop=True)
    flat = dataclasses.replace(flat, cgm=cgm, fingersticks=sticks)
    dev = [_recording(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]
    block = sb.run([*dev, flat], [*dev, flat], [3.0], confirmatory=False, frozen=None)["by_k"][0]
    assert block["n_recordings"] == 3 and len(block["errors"]) == 1
    assert block["errors"][0]["rec_id"] == "flat" and "spread" in block["errors"][0]["error"]
