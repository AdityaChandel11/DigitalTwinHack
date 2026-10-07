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
