import json
import sys

import numpy as np
import pandas as pd
import pytest
from conftest import make_recording

from chhaya.eval import traces as tc
from chhaya.eval.metrics import coverage, rmse
from chhaya.eval.reveal import run_reveal


def _dev_and_test_ids():
    ids = [f"synth-{i}" for i in range(40)]
    return next(i for i in ids if tc.split_of(i) == "dev"), next(i for i in ids if tc.split_of(i) == "test")


def fake_trace(
    patient_id: str, k_days: float = 3.0, days: int = 3, off: float = 5.0, group: str = "t2d"
) -> dict:
    """A trace with no fit behind it: the estimate sits `off` above the truth inside a band of +-10."""
    t = k_days * 1440 + np.arange(0, days * 1440, 15.0)
    truth = 140.0 + 20.0 * np.sin(2 * np.pi * t / 1440)
    cal_t = np.arange(0, k_days * 1440, 15.0)
    twin = truth + off
    return {
        "rec_id": patient_id,
        "patient_id": patient_id,
        "dataset": "cgmacros",
        "group": group,
        "k_days": k_days,
        "t": t,
        "truth": truth,
        "twin": twin,
        "lo": twin - 10.0,
        "hi": twin + 10.0,
        "shrunk": truth + 2 * off,
        "day": truth + 4 * off,
        "cal_t": cal_t,
        "cal_truth": 140.0 + 20.0 * np.sin(2 * np.pi * cal_t / 1440),
    }


def test_a_trace_comes_back_as_it_was_saved_and_only_from_its_own_split(tmp_path):
    dev, test = _dev_and_test_ids()
    for pid in (dev, test):
        tc.save_trace(fake_trace(pid), tmp_path)
        tc.save_trace(fake_trace(pid, k_days=5.0), tmp_path)
    got = tc.load_traces("cgmacros", "dev", 3.0, tmp_path)
    assert [tr["patient_id"] for tr in got] == [dev] and got[0]["k_days"] == 3.0 and got[0]["group"] == "t2d"
    assert np.array_equal(got[0]["twin"], fake_trace(dev)["twin"]) and isinstance(got[0]["rec_id"], str)
    assert [tr["patient_id"] for tr in tc.load_traces("cgmacros", "test", 5.0, tmp_path)] == [test]
    assert tc.load_traces("cgmacros", "dev", 7.0, tmp_path) == []
    with pytest.raises(ValueError, match="split"):
        tc.load_traces("cgmacros", "all", 3.0, tmp_path)


def test_a_test_patients_file_in_the_development_folder_is_refused(tmp_path):
    dev, test = _dev_and_test_ids()
    wrong = tmp_path / "cgmacros" / "dev" / f"{test}-k3.npz"
    wrong.parent.mkdir(parents=True)
    np.savez_compressed(wrong, **fake_trace(test))
    with pytest.raises(ValueError, match="other split"):
        tc.load_traces("cgmacros", "dev", 3.0, tmp_path)


def _gate2_rows(traces):
    return pd.DataFrame(
        [
            {
                "rec_id": tr["rec_id"],
                "k_days": int(tr["k_days"]),
                "twin_rmse": rmse(tr["twin"], tr["truth"]),
                "twin_cov80": coverage(tr["truth"], tr["lo"], tr["hi"]),
            }
            for tr in traces
        ]
    )


def test_traces_must_give_back_what_gate2_committed():
    traces = [fake_trace("a"), fake_trace("b", off=7.0)]
    metrics = _gate2_rows(traces)
    assert tc.gate2_differences(traces, metrics) == []
    moved = metrics.assign(twin_rmse=metrics["twin_rmse"] + 0.01)
    assert (
        len(tc.gate2_differences(traces, moved)) == 2
        and "twin_rmse" in tc.gate2_differences(traces, moved)[0]
    )
    missing = tc.gate2_differences(traces[:1], metrics)
    assert missing == ["b k=3: scored by the Gate 2 run, no trace"]
    extra = tc.gate2_differences(traces, metrics.iloc[:1])
    assert extra == ["b k=3: not scored by the Gate 2 run"]
    failed = pd.concat([metrics, pd.DataFrame([{"rec_id": "c", "k_days": 3, "twin_rmse": np.nan}])])
    assert tc.gate2_differences(traces, failed) == []  # a recording Gate 2 could not score needs no trace
    other_k = pd.concat([metrics, _gate2_rows([fake_trace("a", k_days=7.0)])])
    assert tc.gate2_differences(traces, other_k) == []  # a k that was not traced is not asked for


@pytest.mark.slow
def test_building_traces_saves_what_the_reveal_estimated_and_indexes_what_it_could_not(tmp_path):
    rec = make_recording(days=6, seed=3)
    index = tc.build([rec], [4.0, 6.0], n_members=20, root=tmp_path)
    assert index["k_days"].tolist() == [4.0, 6.0] and index["skipped"].notna().tolist() == [False, True]
    (tr,) = tc.load_traces("synthetic", tc.split_of(rec.patient_id), 4.0, tmp_path)
    out = run_reveal(rec, 4.0, n_members=20)
    assert np.array_equal(tr["twin"], out.twin) and np.array_equal(tr["lo"], out.lo)
    assert tr["t"].min() >= 4 * 1440 and tr["cal_t"].max() < 4 * 1440
    assert abs(rmse(tr["twin"], tr["truth"]) - index["twin_rmse"].iloc[0]) < 1e-9
    assert tc.load_traces("synthetic", tc.split_of(rec.patient_id), 6.0, tmp_path) == []


def test_a_fit_that_fails_keeps_its_row(tmp_path, monkeypatch, rec):
    def boom(rec, k, n_members=200):
        raise RuntimeError("no convergence")

    monkeypatch.setattr(tc, "run_reveal", boom)
    index = tc.build([rec], [3.0], root=tmp_path)
    assert index["error"].tolist() == ["no convergence"] and not list(tmp_path.rglob("*.npz"))


def test_a_recording_that_can_no_longer_be_traced_leaves_no_old_trace_behind(tmp_path, monkeypatch, rec):
    skipped = tc.trace_file(tmp_path, rec.dataset, rec.patient_id, rec.rec_id, 6.0)
    failed = tc.trace_file(tmp_path, rec.dataset, rec.patient_id, rec.rec_id, 3.0)
    skipped.parent.mkdir(parents=True)
    for old in (skipped, failed):
        old.write_bytes(b"from an earlier build")
    assert tc.build([rec], [6.0], root=tmp_path)["skipped"].notna().all()  # six days leave nothing to hide
    assert not skipped.exists() and failed.exists()

    def boom(rec, k, n_members=200):
        raise RuntimeError("no convergence")

    monkeypatch.setattr(tc, "run_reveal", boom)
    tc.build([rec], [3.0], root=tmp_path)
    assert not failed.exists()  # a later pass must not read a trace this build could not make


def test_a_check_against_gate2_cannot_pass_on_nothing(tmp_path):
    traces = [fake_trace("a"), fake_trace("b", off=7.0)]
    metrics = _gate2_rows(traces)
    assert tc.gate2_differences([], metrics, ks=[3.0]) == [
        "a k=3: scored by the Gate 2 run, no trace",
        "b k=3: scored by the Gate 2 run, no trace",
    ]
    both = pd.concat([metrics, _gate2_rows([fake_trace("a", k_days=5.0)])])
    assert tc.gate2_differences(traces, both, ks=[3.0, 5.0]) == ["a k=5: scored by the Gate 2 run, no trace"]
    path = tmp_path / "metrics.csv"
    both.to_csv(path, index=False)
    tc.require_gate2(traces, 3.0, path)
    for too_few in ([], traces[:1]):
        with pytest.raises(SystemExit, match="no trace"):
            tc.require_gate2(too_few, 3.0, path)
    with pytest.raises(SystemExit, match="did not score k = 7"):
        tc.require_gate2(traces, 7.0, path)
    with pytest.raises(SystemExit, match="missing"):
        tc.require_gate2(traces, 3.0, tmp_path / "nowhere.csv")


def _stub_main(monkeypatch, tmp_path, argv, calls, status=""):
    """Run `traces.main` without data: record whether it got as far as loading and building."""
    monkeypatch.setattr(tc, "TRACE_DIR", tmp_path)
    monkeypatch.setattr(tc, "GATE2_TEST", tmp_path / "gate2.csv")
    monkeypatch.setattr(tc, "_git", lambda *args: status)
    monkeypatch.setattr(tc, "load", lambda dataset: calls.append("load") or [])
    monkeypatch.setattr(tc, "build", lambda *a, **k: calls.append("build") or pd.DataFrame([]))
    monkeypatch.setattr(sys, "argv", ["traces", *argv])


def test_test_patients_are_traced_only_with_confirm_on_committed_code_at_the_registered_settings(
    monkeypatch, tmp_path
):
    calls = []
    refusals = (
        (["--split", "test"], "", "--confirm"),
        (["--split", "test", "--confirm"], " M src/chhaya/eval/reveal.py", "uncommitted"),
        (["--split", "test", "--confirm", "--k", "7"], "", "registered"),
        (["--split", "test", "--confirm", "--members", "50"], "", "registered"),
    )
    for argv, status, why in refusals:
        _stub_main(monkeypatch, tmp_path, argv, calls, status)
        with pytest.raises(SystemExit, match=why):
            tc.main()
    assert calls == [] and not list(tmp_path.iterdir())  # no patient was loaded, nothing was written


def test_a_test_build_that_does_not_give_back_gate2_stops_with_an_error(monkeypatch, tmp_path):
    calls = []
    _stub_main(monkeypatch, tmp_path, ["--split", "test", "--confirm"], calls)
    _gate2_rows([fake_trace("a")]).to_csv(tmp_path / "gate2.csv", index=False)
    with pytest.raises(SystemExit, match="no trace"):
        tc.main()  # nothing was traced, yet Gate 2 scored a recording at k = 3
    assert calls == ["load", "build"]


def test_a_development_build_needs_no_confirm_and_records_what_built_it(monkeypatch, tmp_path):
    calls = []
    _stub_main(monkeypatch, tmp_path, ["--split", "dev", "--k", "4"], calls)
    tc.main()
    prov = tc.trace_provenance("cgmacros", "dev", tmp_path)
    assert calls == ["load", "build"] and (prov["split"], prov["k"], prov["members"]) == ("dev", [4.0], 200)
    assert (
        prov["n_traces"] == 0
        and "commit" in prov
        and tc.trace_provenance("cgmacros", "test", tmp_path) is None
    )
    saved = json.loads((tmp_path / "cgmacros" / "build-dev.json").read_text(encoding="utf-8"))
    assert saved == prov and "Users" not in json.dumps(saved)  # no local path in it
