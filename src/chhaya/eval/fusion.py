"""Fusion as a prior: what the health record is worth to the twin, in sensor days (Amendment 3, section P).

Usage: python -m chhaya.eval.fusion --record results/gate2/<a> --population results/gate2/<b>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from chhaya.config import RESULTS_DIR
from chhaya.eval.gate2 import _clean, _paired_p


def _per_patient(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[df["twin_rmse"].notna()]
    return ok.groupby(["k_days", "patient_id"])[["twin_rmse", "ode_rmse"]].mean()


def compare(record: pd.DataFrame, population: pd.DataFrame) -> dict:
    """Paired by patient at each k: record prior minus population prior, for the estimate and the physiology."""
    r, p = _per_patient(record), _per_patient(population)
    both = r.join(p, lsuffix="_record", rsuffix="_population", how="inner")
    by_k = []
    for k, g in both.groupby(level="k_days"):
        row = {"k_days": int(k), "n_patients": int(len(g))}
        for name in ("twin", "ode"):
            d = g[f"{name}_rmse_record"] - g[f"{name}_rmse_population"]
            row.update(
                {
                    f"{name}_record": float(g[f"{name}_rmse_record"].median()),
                    f"{name}_population": float(g[f"{name}_rmse_population"].median()),
                    f"{name}_median_diff": float(d.median()),
                    f"{name}_frac_record_better": float((d < 0).mean()),
                    f"{name}_p": _paired_p(d),
                }
            )
        by_k.append(row)
    k1 = next((row for row in by_k if row["k_days"] == 1), None)
    p1 = bool(k1 is not None and k1["twin_median_diff"] < 0 and k1["twin_p"] < 0.05)
    match = None
    if k1 is not None:
        match = next((row["k_days"] for row in by_k if row["twin_population"] <= k1["twin_record"]), None)
    return {"by_k": by_k, "p1_record_helps_at_k1": p1, "sensor_days_to_match": match}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", type=Path, required=True)
    ap.add_argument("--population", type=Path, required=True)
    args = ap.parse_args()
    out = compare(pd.read_csv(args.record / "metrics.csv"), pd.read_csv(args.population / "metrics.csv"))
    out_dir = RESULTS_DIR / "fusion"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(
        json.dumps(_clean(out), indent=2, allow_nan=False), encoding="utf-8"
    )
    table = pd.DataFrame(out["by_k"]).round(3).to_markdown(index=False)
    verdict = "PASS" if out["p1_record_helps_at_k1"] else "NOT PASSED"
    text = (
        f"# The record as the prior\n\nP1 (record prior helps at k = 1): **{verdict}**\n\n{table}\n\n"
        f"Sensor days the population prior needs to match the record prior at k = 1: "
        f"{out['sensor_days_to_match']}\n"
    )
    (out_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
