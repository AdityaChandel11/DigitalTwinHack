"""Tests added after the review of 8 Oct of the band pass: a harder leakage test, the choice pinned, the report."""

import dataclasses

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.eval import stickband as sb
from chhaya.eval.descriptive import profile_sigma
from chhaya.twin.assimilate import FilterConfig

POOLED = (0.0, 1.0)
VALUES = {
    "very low": lambda n: np.full(n, 25.0),
    "very high": lambda n: np.full(n, 400.0),
    "any": lambda n: np.random.default_rng(0).uniform(20.0, 600.0, n),
}


def _recording(seed: int = 11, pid: str | None = None, start: str = "2026-01-01 07:30", ragged: bool = False):
    """Nine days starting at 07:30. `ragged`: a five-hour gap on a hidden day and readings off the 15-minute grid."""
    rec = make_recording(days=9, seed=seed)
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)
    cgm = rec.cgm
    if ragged:
        cgm = cgm[~cgm["t_min"].between(6 * 1440 + 300, 6 * 1440 + 600)].reset_index(drop=True)
        cgm = cgm.assign(t_min=cgm["t_min"] + np.arange(len(cgm)) % 3)
    pid = pid or f"synth-{seed}"
    return dataclasses.replace(
        rec, cgm=cgm, fingersticks=sticks, rec_id=pid, patient_id=pid, start=pd.Timestamp(start)
    )


def _with_hidden(rec, k: float, values):
    cgm = rec.cgm.copy()
    late = cgm["t_min"] >= k * 1440
    cgm.loc[late, "glucose_mgdl"] = values(int(late.sum()))
    return dataclasses.replace(rec, cgm=cgm)


@pytest.mark.parametrize("ragged", [False, True], ids=["regular", "gap and off-grid"])
@pytest.mark.parametrize("values", VALUES)
@pytest.mark.parametrize("k", [3, 5])
def test_no_hidden_sensor_value_of_any_size_moves_the_estimate_or_its_band(k, values, ragged):
    for seed in (11, 12):
        rec = _recording(seed=seed, ragged=ragged)
        changed = _with_hidden(rec, k, VALUES[values])
        for which in sb.ESTIMATES:
            for construction in sb.CONSTRUCTIONS:
                a = sb.band_of(rec, k, POOLED, construction, which)
                b = sb.band_of(changed, k, POOLED, construction, which)
                for key in ("t", "est", "lo", "hi"):
                    assert np.array_equal(a[key], b[key]), (seed, which, construction, key)


def test_dropping_hidden_sensor_rows_leaves_the_band_at_the_remaining_times_unchanged():
    rec = _recording()
    full = sb.band_of(rec, 3, POOLED, "patient", "hindsight")
    keep = (rec.cgm["t_min"] < 3 * 1440) | (np.arange(len(rec.cgm)) % 2 == 0)
    thinned = dataclasses.replace(rec, cgm=rec.cgm[keep].reset_index(drop=True))
    half = sb.band_of(thinned, 3, POOLED, "patient", "hindsight")
    at = np.isin(full["t"], half["t"])
    assert half["t"].size < full["t"].size
    for key in ("est", "lo", "hi"):
        assert np.array_equal(full[key][at], half[key]), key


def test_the_patients_width_is_read_on_the_clock_of_the_day_not_from_the_start_of_the_recording():
    rec = _recording(start="2026-01-01 07:30")
    plain, own = (sb.band_of(rec, 3, POOLED, c, "live") for c in sb.CONSTRUCTIONS)
    cal = rec.cgm[rec.cgm["t_min"] < 3 * 1440]
    t, g = cal["t_min"].to_numpy(), cal["glucose_mgdl"].to_numpy()
    want, from_start = profile_sigma(450 + t, g), profile_sigma(t, g)
    assert not np.isclose(want, from_start)  # otherwise this test could not tell the two apart
    ratio = (own["hi"] - own["est"]) / (plain["hi"] - plain["est"])
    assert np.allclose(ratio, want / FilterConfig().fast_sd)


def test_the_choice_is_made_once_on_the_live_estimate_of_development_patients_at_the_first_k(monkeypatch):
    dev = [_recording(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]
    seen = []
    monkeypatch.setattr(sb, "choose", lambda by: seen.append(by) or "filter")
    blocks = sb.run(dev, dev, [3.0, 5.0], confirmatory=False, frozen=None)["by_k"]
    assert len(seen) == 1 and seen[0] == blocks[0]["choice"]["development"]["live"]
    assert [b["choice"]["chosen"] for b in blocks] == ["filter", "filter"]
    assert [b["choice"]["at_k"] for b in blocks] == [3.0, 3.0]


def _flat(pid: str = "flat"):
    rec = _recording(seed=4, pid=pid)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] < 3 * 1440, "glucose_mgdl"] = 120.0
    return dataclasses.replace(rec, cgm=cgm, fingersticks=cgm[cgm["t_min"] % 240 == 0].reset_index(drop=True))


def test_a_band_that_cannot_be_formed_is_its_own_kind_of_error():
    assert issubclass(sb.BandUnavailable, ValueError)
    with pytest.raises(sb.BandUnavailable, match="spread"):
        sb.band_of(_flat(), 3, POOLED, "patient", "live")


def test_any_other_error_stops_the_run_instead_of_becoming_a_row(monkeypatch):
    dev = [_recording(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]

    def broken(*args, **kwargs):
        raise ValueError("operands could not be broadcast together")

    monkeypatch.setattr(sb, "_bands", broken)
    with pytest.raises(ValueError, match="broadcast"):
        sb.run(dev, dev, [3.0], confirmatory=False, frozen=None)


def test_the_run_says_who_was_outside_the_cohort_and_which_development_recordings_failed():
    dev = [_recording(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]
    no_sticks = dataclasses.replace(make_recording(days=9, seed=8), rec_id="none", patient_id="none")
    block = sb.run([*dev, no_sticks, _flat()], [*dev, no_sticks, _flat()], [3.0], False, None)["by_k"][0]
    assert block["outside"] == {"fewer than one fingerstick a day": 1}
    assert [e["rec_id"] for e in block["errors"]] == ["flat"]
    assert [e["rec_id"] for e in block["choice"]["development_errors"]] == ["flat"]


def test_the_report_names_the_estimates_the_scale_and_which_band_was_chosen_also_by_day():
    dev = [_recording(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]
    no_sticks = dataclasses.replace(make_recording(days=9, seed=8), rec_id="none", patient_id="none")
    text = sb._report(sb.run([*dev, no_sticks], [*dev, no_sticks], [3.0], False, None))
    assert "strictly before" in text and "sensor's scale" in text
    assert "fewer than one fingerstick a day: 1" in text
    by_day = text.split("By day since the sensor")[1]
    assert "(chosen)" in by_day and "(not chosen)" in by_day


def test_a_day_that_few_patients_reach_is_marked():
    rows = [{"patient_id": p, "days": [{"day": 1, "live_filter_cov": 80.0}]} for p in "abcdef"]
    rows.append({"patient_id": "a", "days": [{"day": 2, "live_filter_cov": 50.0}]})
    days = sb.by_day(rows)
    assert [d["few_patients"] for d in days] == [False, True]  # six patients on day 1, one on day 2
    assert days[1]["share_of_cohort"] == pytest.approx(1 / 6)


# ---------- second review, 8 Oct: tests that would have passed on wrong code ----------
def _grid(seed: int = 11, pid: str | None = None, days: int = 8):
    """Starts at midnight, fingersticks every four hours on the grid: positions in the gap are easy to name."""
    rec = make_recording(days=days, seed=seed)
    sticks = rec.cgm[rec.cgm["t_min"] % 240 == 0].reset_index(drop=True)
    pid = pid or f"grid-{seed}"
    return dataclasses.replace(rec, fingersticks=sticks, rec_id=pid, patient_id=pid)


def test_the_live_band_is_not_narrowed_at_a_fingersticks_own_minute():
    # F1 read fingersticks stamped strictly before the minute, so the band must too
    b = sb.band_of(_grid(), 3, POOLED, "filter", "live")
    assert (b["hi"] - b["est"])[b["t"] % 240 == 0].min() > 31.5


def test_in_the_middle_of_a_gap_hindsight_is_narrower_than_live_by_more_than_half_a_mgdl():
    live, hind = (sb.band_of(_grid(), 3, POOLED, "filter", w) for w in sb.ESTIMATES)
    mid = (live["t"] % 240 == 120) & (
        live["t"] < live["t"].max() - 240
    )  # not the gap after the last fingerstick
    assert ((live["hi"] - live["est"]) - (hind["hi"] - hind["est"]))[mid].min() > 0.5


def test_the_choice_takes_the_filter_when_it_is_clearly_closer_to_80():
    assert (
        sb.choose({"filter": {"mean": 81.0, "n_within": 3}, "patient": {"mean": 88.0, "n_within": 9}})
        == "filter"
    )


def test_by_day_averages_a_patients_recordings_first_and_counts_who_reaches_each_day():
    recs = [_grid(seed=1, pid="a"), _grid(seed=2, pid="a"), _grid(seed=3, pid="b"), _grid(seed=5, pid="c")]
    recs.append(_grid(seed=6, pid="d", days=6))  # three hidden days only
    block = sb.run(recs, recs, [3.0], confirmatory=False, frozen=None)["by_k"][0]
    assert block["n_recordings"] == 5 and block["n_patients"] == 4
    by = {d["day"]: d for d in block["by_day"]}
    assert [by[d]["n_patients"] for d in (1, 3, 4, 5)] == [4, 4, 3, 3]
    assert by[3]["share_of_cohort"] == 1.0 and by[4]["share_of_cohort"] == 0.75
    rows = [
        sb.score_recording(r, 3.0, block_pooled) for r in recs for block_pooled in [sb.pooled_line(recs, 3.0)]
    ]
    day1 = {r["rec_id"] + str(i): r["days"][0]["live_filter_cov"] for i, r in enumerate(rows)}
    a = (rows[0]["days"][0]["live_filter_cov"] + rows[1]["days"][0]["live_filter_cov"]) / 2.0
    others = [rows[i]["days"][0]["live_filter_cov"] for i in (2, 3, 4)]
    assert by[1]["live_filter_cov"] == pytest.approx((a + sum(others)) / 4.0) and len(day1) == 5


# a single flat recording makes the pooled line degenerate, which is the case under test
@pytest.mark.filterwarnings("ignore:Polyfit may be poorly conditioned")
def test_an_error_row_names_the_patient_and_all_failing_says_so():
    block = sb.run([_grid(seed=1, pid="ok"), _flat()], [_grid(seed=1, pid="ok"), _flat()], [3.0], False, None)
    assert block["by_k"][0]["errors"][0]["patient_id"] == "flat"
    with pytest.raises(ValueError, match="could not be given a band"):
        sb.run([_flat()], [_flat()], [3.0], confirmatory=False, frozen=None)


def test_a_failure_at_a_later_k_does_not_lose_the_primary_result(monkeypatch):
    dev = [_grid(seed=s, pid=f"dev-{s}") for s in (1, 2, 3)]
    test = [_grid(seed=9, pid="test-9")]
    chosen = sb.run(dev, dev, [3.0], confirmatory=False, frozen=None)["by_k"][0]["choice"]["chosen"]
    real = sb._score_all

    def fails_on_test_patients_at_k5(recs, k_days, pooled):
        if k_days == 5.0 and recs is test:
            raise RuntimeError("disk full")
        return real(recs, k_days, pooled)

    monkeypatch.setattr(sb, "_score_all", fails_on_test_patients_at_k5)
    blocks = sb.run(test, dev, [3.0, 5.0], confirmatory=True, frozen=chosen)["by_k"]
    assert blocks[0]["n_patients"] == 1 and "bands" in blocks[0]
    assert blocks[1] == {"k_days": 5.0, "primary": False, "error": "RuntimeError('disk full')"}
    assert "could not be computed" in sb._report({"confirmatory": True, "frozen": chosen, "by_k": blocks})


def test_the_registered_filter_has_no_slow_level():
    with pytest.raises(SystemExit):
        sb.check_frozen(FilterConfig(slow=True))
