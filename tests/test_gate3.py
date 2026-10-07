import dataclasses
import json

import numpy as np
import pandas as pd
import pytest

from chhaya.eval import gate3
from chhaya.eval.events import CONTEXT, HISTORY, RECORD, SENSOR, STICKS


def _table(signal: bool, seed: int = 0, n_patients: int = 60, meals: int = 20) -> pd.DataFrame:
    """Each stream sees a different part of what drives the event, so only the fused arm sees all of it."""
    rng = np.random.default_rng(seed)
    rows = []
    for p in range(n_patients):
        rec_part, hist_part = rng.normal(), rng.normal()
        for m in range(meals):
            stick_part = rng.normal()
            logit = 1.2 * (rec_part + hist_part + stick_part) if signal else 0.0
            row = dict.fromkeys(CONTEXT + RECORD + HISTORY + STICKS + SENSOR, 0.0)
            row.update(
                patient_id=f"p{p}",
                rec_id=f"p{p}",
                dev=p % 2 == 0,
                t_min=float(m),
                hidden_days=7.0,
                pump=0.0,
                y=int(rng.random() < 1 / (1 + np.exp(-logit))),
                y250=0,
                start_high=0,
                mins_to_high=np.nan,
                r_hba1c=rec_part,
                h_rate=hist_part,
                h_share=hist_part,
                f_last=stick_part,
                f_has=1.0,
            )
            rows.append(row)
    return pd.DataFrame(rows)


def _split(t: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return t[t["dev"]], t[~t["dev"]]


def test_fusion_passes_when_each_stream_holds_part_of_the_signal():
    out = gate3.evaluate(*_split(_table(signal=True)), n_boot=300)
    assert out["arms"]["fused"]["auprc"] > max(
        out["arms"][a]["auprc"] for a in ("record", "history", "fingersticks")
    )
    assert out["verdict"]["m1_fused_beats_every_single_stream"] is True
    assert out["verdict"]["m2_fused_beats_personal_rate"] is True
    assert 0.6 < out["arms"]["fused"]["calibration_slope"] < 1.6


def test_nothing_passes_on_noise():
    out = gate3.evaluate(*_split(_table(signal=False, seed=1)), n_boot=300)
    assert out["verdict"]["m1_fused_beats_every_single_stream"] is False
    assert out["verdict"]["pass"] is False


def test_missing_values_and_an_all_missing_column_do_not_stop_the_run():
    t = _table(signal=True, seed=2)
    t.loc[t.index[::3], "r_hba1c"] = np.nan
    t["r_egfr"] = np.nan
    out = gate3.evaluate(*_split(t), n_boot=100)
    assert np.isfinite(out["arms"]["record"]["auprc"])


def test_m2_is_judged_against_the_raw_share_and_the_smoothed_one_is_reported_beside_it():
    t = _table(signal=True, seed=8)
    truth_rate = t.groupby("patient_id")["y"].transform("mean")
    t["h_share"] = truth_rate  # a baseline that knows each patient's true rate
    t.loc[t["patient_id"] == "p1", "h_share"] = np.nan  # no calibration meal could be scored
    t["h_rate"] = 0.5  # the smoothed variant knows nothing
    out = gate3.evaluate(*_split(t), n_boot=100)
    assert out["arms"]["personal_rate"]["auprc"] > out["arms"]["personal_rate_smoothed"]["auprc"] + 0.1
    assert set(out["diffs"]) == {
        "record",
        "history",
        "fingersticks",
        "personal_rate",
        "personal_rate_smoothed",
    }
    assert out["verdict"]["m2_fused_beats_personal_rate"] == (out["diffs"]["personal_rate"]["lo"] > 0)
    assert out["n_meals_without_a_personal_rate"] == 20


def test_bootstrap_resamples_patients_not_meals(monkeypatch):
    y = np.array([1, 0] * 10)
    pa = y.astype(float)  # perfect
    pb = np.full(20, 0.5)
    d = gate3.boot_diff(np.repeat(["a", "b", "c", "d"], 5), y, pa, pb, n_boot=200)
    assert d["diff"] > 0 and d["lo"] > 0 and d["lo"] <= d["diff"] <= d["hi"]
    assert 0 < d["n_resamples_used"] <= 200
    sizes = []
    real = gate3.average_precision_score
    monkeypatch.setattr(
        gate3, "average_precision_score", lambda yy, pp: sizes.append(len(yy)) or real(yy, pp)
    )
    gate3.boot_diff(np.array(["a"] * 2 + ["b"] * 18), y, pa, pb, n_boot=100)
    # whole patients are drawn: two draws of a 2-meal and an 18-meal patient give 4, 20 or 36 meals
    assert set(sizes) <= {4, 20, 36} and len(set(sizes)) > 1


def test_out_of_fold_predictions_never_come_from_the_same_patient(monkeypatch):
    dev, _ = _split(_table(signal=True, seed=3))
    real = gate3.fit_predict
    folds = []

    def checked(train, test, cols, y="y"):
        assert set(train["patient_id"]).isdisjoint(test["patient_id"])
        folds.append(len(test))
        return real(train, test, cols, y)

    monkeypatch.setattr(gate3, "fit_predict", checked)
    oof = gate3.out_of_fold(dev)
    assert list(oof.index) == list(dev.index) and set(gate3.ARMS) <= set(oof.columns)
    assert oof["fused"].between(0, 1).all() and sum(folds) == len(dev) * len(gate3.ARMS)


def test_a_fold_that_cannot_be_fitted_is_left_empty_not_a_crash():
    dev, _ = _split(_table(signal=True, seed=3, n_patients=10))
    dev = dev.assign(y=(dev["patient_id"] == "p0").astype(int))  # every event sits in one patient
    oof = gate3.out_of_fold(dev)
    assert oof.loc[dev["patient_id"] == "p0", "fused"].isna().all()  # its training fold has one outcome only
    assert oof.loc[dev["patient_id"] != "p0", "fused"].notna().all()
    assert gate3._alerts(dev, oof["fused"].to_numpy(), dev, np.full(len(dev), 0.5), "y") == {}


def test_alert_threshold_gives_the_target_sensitivity_on_development_meals():
    dev = pd.DataFrame({"y": [1] * 10 + [0] * 10})
    dev_p = np.r_[np.linspace(0.1, 1.0, 10), np.full(10, 0.05)]
    test = pd.DataFrame({"y": [1, 1, 0, 0, 0], "rec_id": ["a", "a", "a", "b", "b"], "hidden_days": [7.0] * 5})
    out = gate3._alerts(dev, dev_p, test, np.array([0.9, 0.2, 0.5, 0.31, 0.1]), "y")
    assert out["threshold"] == pytest.approx(0.3)  # 8 of the 10 development events score at least this
    assert (
        out["sensitivity"] == 0.5 and out["false_alerts_per_patient_week"] == 1.0
    )  # 2 false alerts, 2 weeks
    assert out["eligible_meals_per_patient_week"] == 2.5


def test_net_benefit_against_alerting_at_every_meal():
    y = np.array([1, 1, 0, 0])
    nb = gate3._net_benefit(y, np.array([0.9, 0.6, 0.6, 0.1]))["0.5"]
    assert nb["model"] == pytest.approx((2 - 1) / 4) and nb["alert_always"] == pytest.approx((2 - 2) / 4)


def test_within_patient_auroc_ignores_who_and_asks_when():
    y = np.array([1] * 5 + [0] * 5 + [1] * 5 + [0] * 5 + [1, 0])
    p = np.r_[np.full(5, 0.9), np.full(5, 0.8), np.full(5, 0.2), np.full(5, 0.1), 0.5, 0.5]
    out = gate3.within_patient_auroc(["a"] * 10 + ["b"] * 10 + ["c"] * 2, y, p)
    assert out == {"within_patient_auroc": 1.0, "within_patient_n": 2}  # c has too few meals to count


def test_development_run_gives_no_verdict():
    dev, _ = _split(_table(signal=True, seed=4))
    out = gate3.development_run(dev, n_boot=100)
    assert out["n_patients"] == 30 and out["confirmatory"] is False
    assert "fused" in out["arms"] and "verdict" not in out


def test_report_is_written_without_any_per_meal_rows(tmp_path):
    result = gate3.evaluate(*_split(_table(signal=True, seed=5)), n_boot=100)
    gate3.write_report({"primary": result, "skipped": {"too short": 2}}, tmp_path, confirmatory=True)
    assert {p.name for p in tmp_path.iterdir()} == {"summary.json", "report.md"}
    text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "**PASS**" in text and "fused" in text
    for name in ("report.md", "summary.json"):  # no patient identifiers in either file
        body = (tmp_path / name).read_text(encoding="utf-8")
        assert "p0" not in body and "p1" not in body and "patient_id" not in body


def test_build_table_counts_what_it_skips(rec):
    short = dataclasses.replace(rec, rec_id="short", cgm=rec.cgm[rec.cgm["t_min"] < 2 * 1440])
    table, skipped = gate3.build_table([rec, short], 3.0)
    assert len(table) == 9 and sum(skipped.values()) == 1


def _secondary_table(seed: int) -> pd.DataFrame:
    t = _table(signal=True, seed=seed)
    n = t["patient_id"].str[1:].astype(int)
    t["y250"] = t["y"] * (t["t_min"] % 2 == 0).astype(int)
    t["mins_to_high"] = np.where(t["y"] == 1, 45.0, np.nan)
    t["r_age"] = np.where(n % 4 < 2, 70.0, 50.0)  # every subgroup exists in each split
    t["r_insulin"] = (n % 8 < 4).astype(float)
    t["r_male"] = (n % 6 < 2).astype(float)
    t["pump"] = (n % 10 < 2).astype(float)
    t.loc[t["patient_id"] == "p3", "r_insulin"] = np.nan  # no agents entry: in neither insulin subgroup
    return t


def test_secondary_analyses_cover_everything_the_registration_lists():
    dev, test = _split(_secondary_table(6))
    out = gate3._secondary(dev, test, n_boot=50)
    assert out["above_250"]["n_meals"] == len(test) and out["starts_at_or_below_180"]["n_meals"] == len(test)
    assert "verdict" not in out["above_250"] and "verdict" not in out["starts_at_or_below_180"]  # no bar
    assert out["minutes_to_first_reading_above_180"] == {"median": 45.0, "n_meals": int(test["y"].sum())}
    assert 0.5 < out["lightgbm_fused"]["auprc"] <= 1.0
    sub = out["subgroups_fused"]
    assert set(sub) == {
        "on_insulin", "not_on_insulin", "pump", "no_pump", "male", "female", "age_65_or_more", "under_65"
    }  # fmt: skip
    for a, b in (("pump", "no_pump"), ("male", "female"), ("age_65_or_more", "under_65")):
        assert sub[a]["n_meals"] + sub[b]["n_meals"] == len(test) and sub[a]["n_patients"] > 0
    assert sub["on_insulin"]["n_meals"] + sub["not_on_insulin"]["n_meals"] == len(test) - 20


def test_secondary_analysis_with_one_outcome_only_is_skipped_not_a_crash():
    t = _table(signal=True, seed=7)  # y250 is 0 for every meal
    out = gate3._secondary(*_split(t), n_boot=50)
    assert "above_250" not in out and out["minutes_to_first_reading_above_180"]["median"] is None


def test_a_secondary_analysis_that_fails_is_a_row_with_an_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("no boosting today")

    monkeypatch.setattr(gate3, "_lightgbm", boom)
    out = gate3._secondary(*_split(_secondary_table(6)), n_boot=20)
    assert "no boosting today" in out["lightgbm_fused"]["error"]
    assert "arms" in out["above_250"] and "male" in out["subgroups_fused"]  # the others still ran


def test_the_primary_result_is_on_disk_before_any_secondary_analysis_runs(tmp_path, monkeypatch):
    def boom(*a, **k):
        assert json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))["primary"]["verdict"]
        raise MemoryError("out of memory in a secondary analysis")

    monkeypatch.setattr(gate3, "_secondary", boom)
    dev, test = _split(_table(signal=True, seed=5))
    gate3.confirmatory_run(dev, test, {"too short": 1}, tmp_path, n_boot=50)
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert saved["primary"]["verdict"]["pass"] in (True, False)
    assert "out of memory" in saved["secondary"]["error"]
    with pytest.raises(SystemExit, match="already"):  # and the test split cannot be scored again
        gate3.refuse_second_run(tmp_path)


def test_confirmatory_run_refuses_to_mix_development_and_test_patients(tmp_path):
    dev, test = _split(_table(signal=True, seed=5))
    with pytest.raises(AssertionError, match="both"):
        gate3.confirmatory_run(dev, pd.concat([test, dev.head(3)]), {}, tmp_path, n_boot=10)
    assert not (tmp_path / "summary.json").exists()


def test_the_test_patients_cannot_be_scored_a_second_time(tmp_path):
    gate3.refuse_second_run(tmp_path)  # nothing there yet: allowed
    (tmp_path / "summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="already"):
        gate3.refuse_second_run(tmp_path)


def test_the_confirmatory_run_only_starts_at_the_registered_settings_on_committed_code():
    gate3.check_registered(3.0, 2000, "")  # as registered, clean tree: allowed
    for k, boot, status, why in (
        (5.0, 2000, "", "k = 3"),
        (3.0, 200, "", "2000"),
        (3.0, 2000, " M src/chhaya/eval/gate3.py", "uncommitted"),
        (3.0, 2000, None, "git"),
    ):
        with pytest.raises(SystemExit, match=why):
            gate3.check_registered(k, boot, status)
