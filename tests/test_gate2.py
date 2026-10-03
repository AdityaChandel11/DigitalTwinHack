import json

import pandas as pd

from chhaya.eval import gate2


def _frame(twin, day, tir=4.0, cov=0.8):
    n = len(twin)
    return pd.DataFrame(
        {
            "rec_id": [f"r{i}" for i in range(n)],
            "patient_id": [f"p{i}" for i in range(n)],
            "k_days": 5,
            "error": None,
            "twin_rmse": twin,
            "day_rmse": day,
            "mean_rmse": [d + 5 for d in day],
            "twin_mard": 12.0,
            "twin_tir_err": tir,
            "day_tir_err": 9.0,
            "twin_cov80": cov,
        }
    )


GOOD = [20, 21, 19, 22, 18, 20, 21, 19]
DAY = [28, 27, 30, 29, 26, 31, 27, 28]


def test_go_when_twin_is_reliably_better():
    s = gate2.summarise(_frame(GOOD, DAY))
    assert s["n_patients"] == 8 and s["frac_twin_better"] == 1.0 and s["wilcoxon_p"] < 0.05
    assert gate2.verdict(s) == {
        "p1_beats_average_day": True,
        "p2_tir_within_bar": True,
        "p3_band_calibrated": True,
        "go": True,
    }


def test_no_go_when_twin_is_worse_or_tir_misses():
    worse = gate2.summarise(_frame([g + 10 for g in GOOD], DAY))
    assert gate2.verdict(worse)["go"] is False
    off = gate2.verdict(gate2.summarise(_frame(GOOD, DAY, tir=14.0)))
    assert off["p1_beats_average_day"] is True and off["go"] is False


def test_overconfident_band_is_flagged_without_blocking():
    v = gate2.verdict(gate2.summarise(_frame(GOOD, DAY, cov=0.55)))
    assert v["p3_band_calibrated"] is False and v["go"] is True


def test_too_few_patients_cannot_pass():
    assert gate2.verdict(gate2.summarise(_frame([20, 21], [28, 27])))["go"] is False


def test_repeat_recordings_of_one_patient_count_once():
    df = _frame([20, 22, 30], [28, 28, 28])
    df["patient_id"] = ["a", "a", "b"]
    assert gate2.summarise(df)["n_patients"] == 2


def test_failed_fits_are_recorded_not_dropped(rec, monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise RuntimeError("twin calibration diverged from every start")

    monkeypatch.setattr(gate2, "run_reveal", boom)
    df = gate2.run_cohort([rec], [5])
    assert df.loc[0, "error"].startswith("twin calibration diverged")
    result = gate2.write_report(df, [5], tmp_path)
    assert result["verdict"]["go"] is False
    assert json.loads((tmp_path / "summary.json").read_text())["primary"]["n_failed"] == 1
    assert "NO-GO" in (tmp_path / "report.md").read_text(encoding="utf-8")
