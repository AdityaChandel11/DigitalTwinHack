import numpy as np
import pandas as pd

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
                r_hba1c=rec_part,
                h_rate=hist_part,
                f_last=stick_part,
                f_has=1.0,
            )
            rows.append(row)
    return pd.DataFrame(rows)


def test_fusion_passes_when_each_stream_holds_part_of_the_signal():
    t = _table(signal=True)
    out = gate3.evaluate(t[t["dev"]], t[~t["dev"]], n_boot=300)
    assert out["arms"]["fused"]["auprc"] > max(
        out["arms"][a]["auprc"] for a in ("record", "history", "fingersticks")
    )
    assert out["verdict"]["m1_fused_beats_every_single_stream"] is True
    assert out["verdict"]["m2_fused_beats_personal_rate"] is True
    assert 0.6 < out["arms"]["fused"]["calibration_slope"] < 1.6


def test_nothing_passes_on_noise():
    t = _table(signal=False, seed=1)
    out = gate3.evaluate(t[t["dev"]], t[~t["dev"]], n_boot=300)
    assert out["verdict"]["m1_fused_beats_every_single_stream"] is False
    assert out["verdict"]["pass"] is False


def test_missing_values_and_an_all_missing_column_do_not_stop_the_run():
    t = _table(signal=True, seed=2)
    t.loc[t.index[::3], "r_hba1c"] = np.nan
    t["r_egfr"] = np.nan
    out = gate3.evaluate(t[t["dev"]], t[~t["dev"]], n_boot=100)
    assert np.isfinite(out["arms"]["record"]["auprc"])


def test_bootstrap_resamples_patients_not_meals():
    y = np.array([1, 0] * 10)
    pa = y.astype(float)  # perfect
    pb = np.full(20, 0.5)
    d = gate3.boot_diff(np.repeat(["a", "b", "c", "d"], 5), y, pa, pb, n_boot=200)
    assert d["diff"] > 0 and d["lo"] > 0 and d["lo"] <= d["diff"] <= d["hi"]


def test_out_of_fold_predictions_never_come_from_the_same_patient():
    t = _table(signal=True, seed=3)
    dev = t[t["dev"]]
    oof = gate3.out_of_fold(dev)
    assert list(oof.index) == list(dev.index) and set(gate3.ARMS) <= set(oof.columns)
    assert oof["fused"].between(0, 1).all()


def test_development_run_scores_only_development_patients():
    t = _table(signal=True, seed=4)
    out = gate3.development_run(t[t["dev"]], n_boot=100)
    assert out["n_patients"] == 30 and out["confirmatory"] is False
    assert "fused" in out["arms"] and "verdict" not in out  # a development run gives no verdict


def test_report_is_written_without_any_per_meal_rows(tmp_path):
    t = _table(signal=True, seed=5)
    result = gate3.evaluate(t[t["dev"]], t[~t["dev"]], n_boot=100)
    gate3.write_report({"primary": result, "skipped": {"too short": 2}}, tmp_path, confirmatory=True)
    assert {p.name for p in tmp_path.iterdir()} == {"summary.json", "report.md"}
    text = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "PASS" in text and "fused" in text and "p0" not in text  # no patient identifiers


def test_build_table_counts_what_it_skips(rec):
    import dataclasses

    short = dataclasses.replace(rec, rec_id="short", cgm=rec.cgm[rec.cgm["t_min"] < 2 * 1440])
    table, skipped = gate3.build_table([rec, short], 3.0)
    assert len(table) == 9 and sum(skipped.values()) == 1


def test_secondary_analyses_cover_everything_the_registration_lists():
    t = _table(signal=True, seed=6)
    t["y250"] = t["y"] * (t["t_min"] % 2 == 0).astype(int)
    t["mins_to_high"] = np.where(t["y"] == 1, 45.0, np.nan)
    t["r_age"] = np.where(t["patient_id"].str[1:].astype(int) % 4 < 2, 70.0, 50.0)  # both ages in each split
    out = gate3._secondary(t[t["dev"]], t[~t["dev"]], n_boot=50)
    assert out["above_250"]["n_meals"] == int((~t["dev"]).sum())
    assert out["starts_at_or_below_180"]["n_meals"] == int((~t["dev"]).sum())
    assert out["minutes_to_first_reading_above_180"] == {
        "median": 45.0,
        "n_meals": int(t.loc[~t["dev"], "y"].sum()),
    }
    assert 0.5 < out["lightgbm_fused"]["auprc"] <= 1.0 and "verdict" not in out["lightgbm_fused"]
    assert {"age_65_or_more", "under_65", "not_on_insulin"} <= set(out["subgroups_fused"])


def test_secondary_analysis_with_one_outcome_only_is_skipped_not_a_crash():
    t = _table(signal=True, seed=7)  # y250 is 0 for every meal
    t["mins_to_high"] = np.nan
    out = gate3._secondary(t[t["dev"]], t[~t["dev"]], n_boot=50)
    assert "above_250" not in out and out["minutes_to_first_reading_above_180"]["median"] is None


def test_the_test_patients_cannot_be_scored_a_second_time(tmp_path):
    import pytest

    gate3.refuse_second_run(tmp_path)  # nothing there yet: allowed
    (tmp_path / "summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="already"):
        gate3.refuse_second_run(tmp_path)
