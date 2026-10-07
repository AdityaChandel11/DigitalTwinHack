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
            "shrunk_rmse": [d - 4 for d in day],
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
        "few_failed_fits": True,
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


def test_many_failed_fits_block_a_go():
    failed = pd.DataFrame(
        {"rec_id": ["x1", "x2"], "patient_id": ["x1", "x2"], "k_days": 5, "error": "diverged"}
    )
    s = gate2.summarise(pd.concat([_frame(GOOD, DAY), failed], ignore_index=True))
    v = gate2.verdict(s)
    assert s["n_failed"] == 2 and s["frac_failed"] == 0.2
    assert v["p1_beats_average_day"] is True and v["few_failed_fits"] is False and v["go"] is False


def test_an_occasional_failed_fit_does_not_block_a_go():
    failed = pd.DataFrame({"rec_id": ["x1"], "patient_id": ["x1"], "k_days": 5, "error": "diverged"})
    s = gate2.summarise(pd.concat([_frame(GOOD + GOOD, DAY + DAY), failed], ignore_index=True))
    assert s["n_failed"] == 1 and gate2.verdict(s)["go"] is True  # 1 of 17 is under the 10 % limit


def test_run_without_the_primary_k_cannot_print_go(tmp_path):
    df = _frame(GOOD, DAY)
    df["k_days"] = 3
    result = gate2.write_report(df, [3], tmp_path)
    assert result["verdict"]["go"] is False and result["verdict"]["primary_k_run"] is False
    assert "was not run" in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_summary_compares_against_the_physiology_free_control():
    s = gate2.summarise(_frame(GOOD, DAY))
    assert s["shrunk_rmse"] == 24.0 and s["frac_better_vs_shrunk"] == 1.0 and s["p_vs_shrunk"] < 0.05
    assert s["median_diff_vs_shrunk"] < 0 and (s["cov80_min"], s["cov80_max"]) == (0.8, 0.8)


def test_skipped_recordings_are_counted_in_the_outputs(rec, monkeypatch):
    monkeypatch.setattr(gate2, "run_reveal", lambda *a, **k: None)
    monkeypatch.setattr(
        gate2, "why_skipped", lambda *a, **k: "calibration window only 14 % covered by the sensor"
    )
    df = gate2.run_cohort([rec], [5])
    assert df.loc[0, "skipped"].startswith("calibration window") and df.loc[0, "error"] is None
    s = gate2.summarise(df)
    assert s["n_skipped"] == 1 and s["n_failed"] == 0 and s["n_patients"] == 0


def test_only_a_full_test_split_run_is_labelled_confirmatory(tmp_path):
    ref = gate2.write_report(_frame(GOOD, DAY), [5], tmp_path / "dev")
    assert ref["verdict"]["confirmatory"] is False
    assert "not confirmatory" in (tmp_path / "dev" / "report.md").read_text(encoding="utf-8")
    claim = gate2.write_report(_frame(GOOD, DAY), [5], tmp_path / "test", confirmatory=True)
    assert claim["verdict"]["confirmatory"] is True
    assert "not confirmatory" not in (tmp_path / "test" / "report.md").read_text(encoding="utf-8")


def test_small_p_values_are_not_printed_as_zero(tmp_path):
    twin = [20.0 + 0.1 * i for i in range(16)]
    day = [28.0 + 0.37 * i for i in range(16)]  # sixteen patients, all better, no tied differences
    gate2.write_report(_frame(twin, day), [5], tmp_path)
    assert "1.5e-05" in (tmp_path / "report.md").read_text(
        encoding="utf-8"
    )  # 1 / 2**16, which rounds to 0.000


def test_summary_file_is_strict_json_even_when_a_statistic_is_undefined(tmp_path):
    gate2.write_report(_frame([20, 21], [28, 27]), [5], tmp_path)  # two patients: no signed-rank test
    text = (tmp_path / "summary.json").read_text()
    assert "NaN" not in text and json.loads(text)["primary"]["wilcoxon_p"] is None


def test_partial_runs_cannot_overwrite_full_results():
    assert gate2.results_dir("cgmacros", "test", None).name == "cgmacros-test"
    assert gate2.results_dir("cgmacros", "all", None).name == "cgmacros"
    assert gate2.results_dir("cgmacros", "dev", 5).name == "cgmacros-dev-limit5"


def test_a_tagged_run_cannot_overwrite_the_confirmatory_folder():
    plain = gate2.results_dir("cgmacros", "test", None)
    tagged = gate2.results_dir("cgmacros", "test", None, tag="ksweep-prior-population")
    assert plain.name == "cgmacros-test" and tagged.name == "cgmacros-test-ksweep-prior-population"


def test_population_prior_is_passed_to_the_reveal(monkeypatch, rec):
    seen = []
    monkeypatch.setattr(gate2, "run_reveal", lambda rec, k, prior=None, n_members=200: seen.append(prior))
    gate2.run_cohort([rec], [3], prior="record")
    gate2.run_cohort([rec], [3], prior="population")
    assert seen[0] is None and seen[1] is not None and seen[1].mu.shape == (7,)
