import pandas as pd

from chhaya.eval.fusion import compare


def _runs(gap_at_k1: float):
    rows_r, rows_p = [], []
    for p in range(12):
        for k, extra in ((1, gap_at_k1), (3, 0.5), (5, 0.0)):
            base = 30.0 - 2.0 * k + 0.3 * p
            jitter = (-1) ** p * 0.01 * (p + 1)  # symmetric about zero: a tie, not a small consistent gain
            rows_r.append({"patient_id": f"p{p}", "k_days": k, "twin_rmse": base, "ode_rmse": base + 5})
            rows_p.append(
                {
                    "patient_id": f"p{p}",
                    "k_days": k,
                    "twin_rmse": base + extra + jitter,
                    "ode_rmse": base + 5 + 2 * extra,
                }
            )
    return pd.DataFrame(rows_r), pd.DataFrame(rows_p)


def test_record_prior_helps_when_sensor_data_is_short():
    out = compare(*_runs(gap_at_k1=3.0))
    k1 = next(r for r in out["by_k"] if r["k_days"] == 1)
    assert k1["n_patients"] == 12 and k1["twin_median_diff"] < -2.5 and k1["twin_p"] < 0.05
    assert out["p1_record_helps_at_k1"] is True
    assert (
        out["sensor_days_to_match"] == 3
    )  # the population prior needs 3 days to match the record prior at 1


def test_no_claim_when_the_priors_tie():
    out = compare(*_runs(gap_at_k1=0.0))
    assert out["p1_record_helps_at_k1"] is False


def test_only_patients_scored_in_both_runs_are_compared():
    rec, pop = _runs(3.0)
    out = compare(rec, pop[pop["patient_id"] != "p0"])
    assert all(r["n_patients"] == 11 for r in out["by_k"])
