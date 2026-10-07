# Record Prior and Fingerstick Experiments Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the two remaining pre-registered experiments of Amendment 3: the record as the twin's prior (section P, CGMacros) and fingersticks after the sensor comes off (section F, ShanghaiT2DM).

**Architecture:** Section P needs one switch on the existing Gate 2 command and a small comparison module that reads two results folders. Section F needs a filter that turns fingersticks into a decaying deviation from the patient's daily shape, and an experiment module that scores it against the control on held-out patients and against the fingerstick itself.

**Tech Stack:** Python 3.13, NumPy, pandas, SciPy (Wilcoxon), the existing JAX twin (section P only), pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-10-04-chhaya-m3-design.md`; bars in `docs/PREREGISTRATION.md`, Amendment 3, sections P and F.

## Global Constraints

- Split by patient only: `chhaya.config.is_dev_patient`. Filter constants and the pooled sensor map come from development patients.
- Test patients are scored once per experiment, only with `--confirm`, and only with the code defaults (no filter overrides).
- In the hidden window an estimator may use fingersticks, never sensor readings. The live estimate may use only fingersticks already taken.
- The confirmatory Gate 2 folder `results/gate2/cgmacros-test/` must never be overwritten: every new Gate 2 run in this plan passes `--tag`.
- Results folders hold aggregates only. Glucose in mg/dL. `encoding="utf-8"` on every text write.
- `uv run ruff check src tests` and `uv run ruff format src tests` clean; line length 110.

## Review Focus

- A recording whose fingersticks all fall before the split: skipped and counted, not scored on zero observations.
- Two fingersticks at the same minute: the filter must not divide by a zero time step.
- A patient with fewer than three calibration pairs: the pooled map is used, and the run says how many patients that was.
- A Gate 2 run started without `--tag` in this plan: it would overwrite the confirmatory folder; the steps below always pass one.
- A fingerstick of 0 or a reference below 1 mg/dL in the accuracy metrics: relative error must not divide by zero (the loader already drops values under 20).

## File Structure

| File | Responsibility |
|---|---|
| `src/chhaya/eval/gate2.py` (modify) | `--prior` and `--tag` switches |
| `src/chhaya/eval/fusion.py` (new) | Compare two Gate 2 folders: record prior against population prior |
| `src/chhaya/eval/metrics.py` (modify) | `within_15_15`, `clarke_zones` |
| `src/chhaya/twin/assimilate.py` (new) | Sensor map and the decaying-deviation filter |
| `src/chhaya/eval/fingersticks.py` (new) | Experiment F: cohort, estimators, scores, verdict, CLI |
| `tests/test_fusion.py`, `tests/test_assimilate.py`, `tests/test_fingersticks.py` (new); `tests/test_gate2.py`, `tests/test_metrics.py` (append) | Tests |

---

### Task 1: `--prior` and `--tag` on the Gate 2 command

**Files:**
- Modify: `src/chhaya/eval/gate2.py`
- Test: `tests/test_gate2.py` (append)

**Interfaces:**
- Produces: `results_dir(dataset, split, limit, tag=None) -> Path`; `run_cohort(recs, k_list, n_members=200, jobs=1, prior="record")`; CLI flags `--prior {record,population}` and `--tag NAME`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_gate2.py`)

```python
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
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_gate2.py -q`
Expected: FAIL, `TypeError: results_dir() got an unexpected keyword argument 'tag'`

- [ ] **Step 3: Implement**

In `gate2.py`: add `from chhaya.twin.priors import population_prior` to the imports, then change these four places.

```python
def _rows_for(rec: Recording, k_list: list[int], n_members: int, prior: str = "record") -> list[dict]:
    ...
        try:
            # None lets the reveal build the record-informed prior, as every Gate 2 run did
            out = run_reveal(rec, k, prior=population_prior() if prior == "population" else None, n_members=n_members)
```

```python
def run_cohort(
    recs: list[Recording], k_list: list[int], n_members: int = 200, jobs: int = 1, prior: str = "record"
) -> pd.DataFrame:
    ...
    work = partial(_rows_for, k_list=k_list, n_members=n_members, prior=prior)
```

```python
def results_dir(dataset: str, split: str, limit: int | None, tag: str | None = None) -> Path:
    """Where a run writes. Partial, per-split and tagged runs get their own folder so they cannot overwrite a full run."""
    name = dataset + ("" if split == "all" else f"-{split}") + (f"-limit{limit}" if limit else "")
    return RESULTS_DIR / "gate2" / (name + (f"-{tag}" if tag else ""))
```

In `main`: add the two arguments, pass them through, and keep a tagged run from being labelled confirmatory.

```python
    ap.add_argument("--prior", choices=["record", "population"], default="record")
    ap.add_argument("--tag", default=None, help="suffix for the results folder; required for any run that is not Gate 2 itself")
    ...
    df = run_cohort(recs, args.k, args.members, args.jobs, args.prior)
    out_dir = results_dir(args.dataset, args.split, args.limit, args.tag)
    confirmatory = args.split == "test" and args.limit is None and args.tag is None and args.prior == "record"
    result = write_report(df, args.k, out_dir, confirmatory=confirmatory)
```

In `provenance`, add `"prior": args.prior, "tag": args.tag` to the returned dict.

- [ ] **Step 4: Run, lint, commit**

Run: `uv run pytest tests/test_gate2.py -q` (expected: pass), then

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/gate2.py tests/test_gate2.py
git commit -m "feat: prior and tag switches on the Gate 2 command"
```

---

### Task 2: Record prior against population prior (section P)

**Files:**
- Create: `src/chhaya/eval/fusion.py`, `tests/test_fusion.py`
- Create after the runs: `docs/decisions/<date>-record-prior.md`

**Interfaces:**
- Consumes: two folders written by Gate 2, each with `metrics.csv` (columns `patient_id, k_days, twin_rmse, ode_rmse`).
- Produces: `compare(record: pd.DataFrame, population: pd.DataFrame) -> dict` with keys `by_k`, `p1_record_helps_at_k1`, `sensor_days_to_match`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_fusion.py
import pandas as pd

from chhaya.eval.fusion import compare


def _runs(gap_at_k1: float):
    rows_r, rows_p = [], []
    for p in range(12):
        for k, extra in ((1, gap_at_k1), (3, 0.5), (5, 0.0)):
            base = 30.0 - 2.0 * k + 0.3 * p
            rows_r.append({"patient_id": f"p{p}", "k_days": k, "twin_rmse": base, "ode_rmse": base + 5})
            rows_p.append({"patient_id": f"p{p}", "k_days": k, "twin_rmse": base + extra + 0.01 * p, "ode_rmse": base + 5 + 2 * extra})
    return pd.DataFrame(rows_r), pd.DataFrame(rows_p)


def test_record_prior_helps_when_sensor_data_is_short():
    out = compare(*_runs(gap_at_k1=3.0))
    k1 = next(r for r in out["by_k"] if r["k_days"] == 1)
    assert k1["n_patients"] == 12 and k1["twin_median_diff"] < -2.5 and k1["twin_p"] < 0.05
    assert out["p1_record_helps_at_k1"] is True
    assert out["sensor_days_to_match"] == 3  # the population prior needs 3 days to match the record prior at 1


def test_no_claim_when_the_priors_tie():
    out = compare(*_runs(gap_at_k1=-0.02))
    assert out["p1_record_helps_at_k1"] is False


def test_only_patients_scored_in_both_runs_are_compared():
    rec, pop = _runs(3.0)
    out = compare(rec, pop[pop["patient_id"] != "p0"])
    assert all(r["n_patients"] == 11 for r in out["by_k"])
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_fusion.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'chhaya.eval.fusion'`

- [ ] **Step 3: Implement**

```python
# src/chhaya/eval/fusion.py
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
    (out_dir / "summary.json").write_text(json.dumps(_clean(out), indent=2, allow_nan=False), encoding="utf-8")
    table = pd.DataFrame(out["by_k"]).round(3).to_markdown(index=False)
    verdict = "PASS" if out["p1_record_helps_at_k1"] else "NOT PASSED"
    text = f"# The record as the prior\n\nP1 (record prior helps at k = 1): **{verdict}**\n\n{table}\n\nSensor days the population prior needs to match the record prior at k = 1: {out['sensor_days_to_match']}\n"
    (out_dir / "report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, lint, commit**

Run: `uv run pytest tests/test_fusion.py -q` (expected: 3 passed), lint, then

```bash
git add src/chhaya/eval/fusion.py tests/test_fusion.py
git commit -m "feat: compare record prior against population prior"
```

- [ ] **Step 5: The two runs (each about 25 minutes; start both in the background and say so)**

```bash
uv run python -m chhaya.eval.gate2 --dataset cgmacros --split test --k 1 3 5 7 --jobs 6 --prior record --tag ksweep-prior-record
uv run python -m chhaya.eval.gate2 --dataset cgmacros --split test --k 1 3 5 7 --jobs 5 --prior population --tag ksweep-prior-population
```

Each is run once. Check afterwards that `results/gate2/cgmacros-test/` is unchanged (`git status` shows no modification there) and that the k = 5 row of the record-prior run matches the corrected Gate 2 run (Chhaya 21.9 mg/dL).

- [ ] **Step 6: Compare, record, commit**

```bash
uv run python -m chhaya.eval.fusion --record results/gate2/cgmacros-test-ksweep-prior-record --population results/gate2/cgmacros-test-ksweep-prior-population
```

Write `docs/decisions/<date>-record-prior.md` (verdict on P1, the table, the sensor-days figure, one "claim to quote" sentence, and the plain statement if the record made no difference). Update the roadmap Status table and `docs/PROGRESS.md`.

```bash
git add results/gate2 results/fusion docs
git commit -m "results: the record as the prior, k = 1 to 7 on held-out patients"
```

---

### Task 3: Accuracy against a reference reading

**Files:**
- Modify: `src/chhaya/eval/metrics.py`
- Test: `tests/test_metrics.py` (append)

**Interfaces:**
- Produces: `within_15_15(pred, ref) -> float` (percent); `clarke_zones(pred, ref) -> dict[str, float]` (percent per zone A to E).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_metrics.py`)

```python
def test_within_15_15_uses_absolute_error_below_100_and_relative_above():
    from chhaya.eval.metrics import within_15_15

    ref = np.array([80.0, 80.0, 200.0, 200.0])
    pred = np.array([94.0, 96.0, 229.0, 231.0])  # 14 and 16 mg/dL off; 14.5 % and 15.5 % off
    assert within_15_15(pred, ref) == 50.0


def test_clarke_zones_on_clear_cases():
    from chhaya.eval.metrics import clarke_zones

    ref = np.array([100.0, 60.0, 100.0, 100.0, 300.0, 200.0, 60.0])
    pred = np.array([110.0, 65.0, 140.0, 250.0, 150.0, 60.0, 200.0])
    z = clarke_zones(pred, ref)  # A, A, B, C, D, E, E
    assert round(z["A"], 1) == 28.6 and round(z["B"], 1) == 14.3 and round(z["C"], 1) == 14.3
    assert round(z["D"], 1) == 14.3 and round(z["E"], 1) == 28.6
    assert abs(sum(z.values()) - 100.0) < 1e-9
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_metrics.py -q`
Expected: FAIL, `ImportError: cannot import name 'within_15_15'`

- [ ] **Step 3: Implement** (append to `src/chhaya/eval/metrics.py`)

```python
def within_15_15(pred, ref) -> float:
    """Percent of readings within 15 mg/dL of a reference below 100 mg/dL, or within 15 % of one at or above it.

    The agreement rule of ISO 15197:2013 for glucose meters, used here to put an estimate next to a real sensor.
    """
    pred, ref = np.asarray(pred, dtype=float), np.asarray(ref, dtype=float)
    err = np.abs(pred - ref)
    return float(100.0 * np.mean(np.where(ref < 100.0, err <= 15.0, err <= 0.15 * ref)))


def clarke_zones(pred, ref) -> dict[str, float]:
    """Percent of readings in each zone of the Clarke error grid (A: clinically accurate ... E: opposite treatment)."""
    pred, ref = np.asarray(pred, dtype=float), np.asarray(ref, dtype=float)
    a = ((ref <= 70) & (pred <= 70)) | ((pred >= 0.8 * ref) & (pred <= 1.2 * ref))
    e = ((ref >= 180) & (pred <= 70)) | ((ref <= 70) & (pred >= 180))
    c = ((ref >= 70) & (ref <= 290) & (pred >= ref + 110)) | ((ref >= 130) & (ref <= 180) & (pred <= 1.4 * ref - 182))
    d = (
        ((ref >= 240) & (pred >= 70) & (pred <= 180))
        | ((ref <= 175 / 3) & (pred >= 70) & (pred <= 180))
        | ((ref >= 175 / 3) & (ref <= 70) & (pred >= 1.2 * ref))
    )
    zone = np.select([a, e, c, d], ["A", "E", "C", "D"], default="B")
    return {z: float(100.0 * np.mean(zone == z)) for z in "ABCDE"}
```

Before quoting any zone figure, check three plotted points of this function against the published Clarke grid figure; say in the README that the Clarke grid is used, not the consensus grid.

- [ ] **Step 4: Run, lint, commit**

```bash
uv run pytest tests/test_metrics.py -q
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/metrics.py tests/test_metrics.py
git commit -m "feat: 15/15 agreement and Clarke zones against a reference reading"
```

---

### Task 4: The sensor map and the decaying-deviation filter

**Files:**
- Create: `src/chhaya/twin/assimilate.py`, `tests/test_assimilate.py`

**Interfaces:**
- Produces: `FilterConfig(tau_min=120.0, fast_sd=25.0, obs_sd=15.0, slow=False, slow_sd_per_sqrt_day=8.0, slow_sd0=20.0)`; `pooled_map(cbg, cgm) -> tuple[float, float]` (intercept, slope); `sensor_map(cbg, cgm, pooled) -> tuple[float, float]`; `deviation(t_obs, z, t_eval, cfg=FilterConfig(), smooth=False) -> np.ndarray`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_assimilate.py
import numpy as np

from chhaya.twin.assimilate import FilterConfig, deviation, pooled_map, sensor_map

CFG = FilterConfig()


def test_no_fingersticks_means_no_deviation():
    assert deviation(np.array([]), np.array([]), np.arange(0.0, 600.0, 15.0)).tolist() == [0.0] * 40


def test_a_surprise_is_believed_in_part_and_then_fades():
    t = np.array([0.0, CFG.tau_min, 10 * CFG.tau_min])
    d = deviation(np.array([0.0]), np.array([30.0]), t)
    assert 15.0 < d[0] < 30.0  # shrunk toward zero by the observation noise
    assert abs(d[1] / d[0] - np.exp(-1.0)) < 1e-6  # one time constant later
    assert abs(d[2]) < 0.01


def test_the_live_estimate_never_changes_because_of_a_later_fingerstick():
    t_eval = np.arange(0.0, 300.0, 15.0)
    one = deviation(np.array([60.0]), np.array([20.0]), t_eval)
    two = deviation(np.array([60.0, 240.0]), np.array([20.0, -40.0]), t_eval)
    assert np.allclose(one[t_eval < 240.0], two[t_eval < 240.0])
    assert (one[t_eval < 60.0] == 0.0).all()


def test_in_hindsight_a_fingerstick_also_informs_the_time_before_it():
    t_eval = np.array([0.0, 30.0, 60.0])
    d = deviation(np.array([60.0]), np.array([30.0]), t_eval, smooth=True)
    assert 0.0 < d[0] < d[1] < d[2]


def test_two_fingersticks_at_the_same_minute_do_not_break_it():
    d = deviation(np.array([60.0, 60.0]), np.array([20.0, 30.0]), np.array([60.0, 90.0]))
    assert np.isfinite(d).all() and d[0] > 0


def test_slow_level_keeps_a_lasting_shift():
    t_obs = np.arange(0.0, 3 * 1440.0, 360.0)
    z = np.full(t_obs.size, 30.0)
    late = np.array([3 * 1440.0 + 600.0])  # ten hours after the last fingerstick
    fast_only = deviation(t_obs, z, late, FilterConfig(slow=False))
    with_slow = deviation(t_obs, z, late, FilterConfig(slow=True))
    assert fast_only[0] < 1.0 and with_slow[0] > 10.0


def test_sensor_map_falls_back_to_the_pooled_slope_with_few_pairs():
    rng = np.random.default_rng(0)
    cbg = rng.uniform(80, 300, 200)
    pooled = pooled_map(cbg, 5.0 + 0.9 * cbg + rng.normal(0, 3, 200))
    assert abs(pooled[1] - 0.9) < 0.02 and abs(pooled[0] - 5.0) < 4.0
    own = sensor_map(cbg[:30], -20.0 + 1.0 * cbg[:30], pooled)
    assert abs(own[1] - 1.0) < 0.01 and abs(own[0] + 20.0) < 1.0
    few = sensor_map(cbg[:4], cbg[:4] - 12.0, pooled)
    assert few[1] == pooled[1] and abs(np.mean(few[0] + few[1] * cbg[:4] - (cbg[:4] - 12.0))) < 1e-9
    assert sensor_map(cbg[:1], cbg[:1], pooled) == pooled
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_assimilate.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'chhaya.twin.assimilate'`

- [ ] **Step 3: Implement**

```python
# src/chhaya/twin/assimilate.py
"""Fingersticks after the sensor comes off: a deviation from the patient's daily shape that fades.

A fingerstick says how far glucose is from the expected shape *now*. Exploration on development patients
(docs/decisions/2026-10-04-plan-revision.md) showed that carrying that difference forward as a lasting level
makes the estimate worse; letting it fade over about two hours makes it slightly better.
"""

from __future__ import annotations

from typing import NamedTuple

import numpy as np


class FilterConfig(NamedTuple):
    tau_min: float = 120.0  # how long a deviation seen at a fingerstick persists
    fast_sd: float = 25.0  # stationary spread of the fading deviation, mg/dL
    obs_sd: float = 15.0  # fingerstick against sensor disagreement after the map, mg/dL
    slow: bool = False  # also track a slow level (drift over days)
    slow_sd_per_sqrt_day: float = 8.0
    slow_sd0: float = 20.0


MIN_OWN_PAIRS = 8  # a patient's own slope needs this many calibration pairs ...
MIN_OWN_SPAN = 40.0  # ... spanning at least this many mg/dL
MIN_OFFSET_PAIRS = 3
SLOPE_RANGE = (0.6, 1.2)


def pooled_map(cbg, cgm) -> tuple[float, float]:
    """Sensor = intercept + slope x fingerstick, over development patients' calibration pairs."""
    slope, intercept = np.polyfit(np.asarray(cbg, dtype=float), np.asarray(cgm, dtype=float), 1)
    return float(intercept), float(slope)


def sensor_map(cbg, cgm, pooled: tuple[float, float]) -> tuple[float, float]:
    """This patient's map from calibration-window pairs; the pooled slope, then the pooled map, when pairs are few."""
    cbg, cgm = np.asarray(cbg, dtype=float), np.asarray(cgm, dtype=float)
    if cbg.size >= MIN_OWN_PAIRS and np.ptp(cbg) > MIN_OWN_SPAN:
        slope = float(np.clip(np.polyfit(cbg, cgm, 1)[0], *SLOPE_RANGE))
        return float(np.mean(cgm - slope * cbg)), slope
    if cbg.size >= MIN_OFFSET_PAIRS:
        return float(np.mean(cgm - pooled[1] * cbg)), pooled[1]
    return pooled


def deviation(t_obs, z, t_eval, cfg: FilterConfig = FilterConfig(), smooth: bool = False) -> np.ndarray:
    """Deviation from the daily shape at `t_eval`, from surprises `z` seen at fingerstick times `t_obs`.

    State: a slow level (random walk, optional) and a fast deviation that fades with time constant `tau_min`.
    Live (`smooth=False`): each value uses only fingersticks at or before it. In hindsight (`smooth=True`):
    all fingersticks, for the retrospective report.
    """
    t_obs, z, t_eval = (np.asarray(a, dtype=float) for a in (t_obs, z, t_eval))
    n = t_obs.size
    if n == 0:
        return np.zeros(t_eval.size)
    h = np.array([1.0, 1.0])
    x = np.zeros(2)
    p = np.diag([cfg.slow_sd0**2 if cfg.slow else 0.0, cfg.fast_sd**2])
    q_slow = cfg.slow_sd_per_sqrt_day**2 / 1440.0 if cfg.slow else 0.0
    xs, ps, xps, pps, fs = [], [], [], [], []
    last = t_obs[0]
    for t, y in zip(t_obs, z, strict=True):
        dt = max(t - last, 0.0)
        a = np.exp(-dt / cfg.tau_min)
        f = np.diag([1.0, a])
        xp = f @ x
        pp = f @ p @ f.T + np.diag([q_slow * dt, cfg.fast_sd**2 * (1.0 - a * a)])
        gain = pp @ h / (h @ pp @ h + cfg.obs_sd**2)
        x = xp + gain * (y - h @ xp)
        p = pp - np.outer(gain, h @ pp)
        xs.append(x.copy()), ps.append(p.copy()), xps.append(xp.copy()), pps.append(pp.copy()), fs.append(f)
        last = t
    xs = np.array(xs)
    if smooth:
        for i in range(n - 2, -1, -1):
            c = ps[i] @ fs[i + 1].T @ np.linalg.pinv(pps[i + 1])
            xs[i] = xs[i] + c @ (xs[i + 1] - xps[i + 1])
    idx = np.searchsorted(t_obs, t_eval, side="right") - 1
    j = np.clip(idx, 0, n - 1)
    back = np.where(idx >= 0, xs[j, 0] + xs[j, 1] * np.exp(-(t_eval - t_obs[j]) / cfg.tau_min), 0.0)
    if not smooth:
        return back
    nxt = np.clip(idx + 1, 0, n - 1)
    fwd = xs[nxt, 0] + xs[nxt, 1] * np.exp(-(t_obs[nxt] - t_eval) / cfg.tau_min)
    gap = np.maximum(t_obs[nxt] - t_obs[j], 1.0)
    w = np.clip((t_eval - t_obs[j]) / gap, 0.0, 1.0)
    between = (1.0 - w) * back + w * fwd
    return np.where(idx < 0, fwd, np.where(idx + 1 < n, between, back))
```

- [ ] **Step 4: Run the tests and see them pass**

Run: `uv run pytest tests/test_assimilate.py -q`
Expected: 7 passed. `test_in_hindsight...` relies on the forward-fading branch for times before the first fingerstick; if it fails, check the `idx < 0` branch before touching the test.

- [ ] **Step 5: Lint, commit**

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/twin/assimilate.py tests/test_assimilate.py
git commit -m "feat: sensor map and decaying-deviation filter for fingersticks"
```

---

### Task 5: The fingerstick experiment

**Files:**
- Create: `src/chhaya/eval/fingersticks.py`, `tests/test_fingersticks.py`

**Interfaces:**
- Consumes: `paired` (Plan 2, Task 1); `FilterConfig`, `pooled_map`, `sensor_map`, `deviation` (Task 4); `within_15_15`, `clarke_zones`, `rmse`, `mard` (metrics); `average_day_baseline`; `why_skipped`; `_paired_p`, `_clean`, `_git` from `gate2`.
- Produces: `thin(t, day, rule) -> np.ndarray[bool]`; `why_not(rec, k_days) -> str | None`; `run_recording(rec, k_days, cfg, pooled, rule="all") -> dict | None`; `summarise(df) -> dict`; `verdict(s) -> dict`; CLI.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_fingersticks.py
import dataclasses

import numpy as np
import pandas as pd
from conftest import make_recording

from chhaya.eval import fingersticks as fx
from chhaya.twin.assimilate import FilterConfig

SPLIT = 3 * 1440
POOLED = (0.0, 1.0)


def _recording(shift: float, every_min: int = 240):
    """Seven days; after day 3 the patient's glucose runs `shift` mg/dL higher. Fingersticks read the sensor exactly."""
    rec = make_recording(days=7, seed=11)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = np.clip(cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] + shift, 40, 400)
    sticks = cgm[cgm["t_min"] % every_min == 0].reset_index(drop=True)
    return dataclasses.replace(rec, cgm=cgm, fingersticks=sticks)


def test_fingersticks_help_when_the_patient_has_changed():
    row = fx.run_recording(_recording(40.0), 3, FilterConfig(slow=True), POOLED)
    assert row["live_rmse"] < row["control_rmse"] - 8.0
    assert row["hindsight_rmse"] <= row["live_rmse"] + 1.0
    assert row["n_sticks"] > 20 and row["sensor_within15"] == 100.0
    assert row["live_within15"] > row["control_within15"]


def test_fingersticks_do_no_harm_when_nothing_changed():
    row = fx.run_recording(_recording(0.0), 3, FilterConfig(), POOLED)
    assert row["live_rmse"] < row["control_rmse"] + 2.0


def test_hidden_sensor_readings_never_reach_the_estimate():
    rec = _recording(40.0)
    cgm = rec.cgm.copy()
    cgm.loc[cgm["t_min"] >= SPLIT, "glucose_mgdl"] = 111.0
    a, b = fx.estimates(rec, 3, FilterConfig(), POOLED), fx.estimates(dataclasses.replace(rec, cgm=cgm), 3, FilterConfig(), POOLED)
    assert np.allclose(a["live"], b["live"]) and np.allclose(a["hindsight"], b["hindsight"])


def test_recordings_that_cannot_be_scored_say_why(rec):
    assert "fingerstick" in fx.why_not(rec, 3)  # no fingersticks at all
    early = dataclasses.replace(_recording(0.0), fingersticks=_recording(0.0).fingersticks.query("t_min < @SPLIT"))
    assert "after the split" in fx.why_not(early, 3)
    assert fx.run_recording(rec, 3, FilterConfig(), POOLED) is None


def test_thinning_keeps_the_first_fingerstick_of_the_day():
    t = np.array([400.0, 800.0, 1200.0, 1900.0, 2300.0, 3300.0])
    day = t // 1440
    assert fx.thin(t, day, "all").sum() == 6
    assert fx.thin(t, day, "2/day").tolist() == [True, False, True, True, True, True]
    assert fx.thin(t, day, "1/day").tolist() == [True, False, False, True, False, True]
    assert fx.thin(t, day, "every 2nd day").tolist() == [True, False, False, False, False, True]


def test_verdict_needs_a_reliable_gain():
    good = pd.DataFrame({"patient_id": [f"p{i}" for i in range(10)], "control_rmse": 30.0,
                         "live_rmse": np.linspace(27, 29.5, 10), "hindsight_rmse": np.linspace(25, 29, 10)})
    assert fx.verdict(fx.summarise(good)) == {"f1_live_beats_control": True, "f2_hindsight_beats_control": True}
    bad = good.assign(live_rmse=np.linspace(29, 33, 10))
    assert fx.verdict(fx.summarise(bad))["f1_live_beats_control"] is False
```

- [ ] **Step 2: Run and see them fail**

Run: `uv run pytest tests/test_fingersticks.py -q`
Expected: FAIL, `ImportError: cannot import name 'fingersticks'`

- [ ] **Step 3: Implement**

```python
# src/chhaya/eval/fingersticks.py
"""Experiment F: after the sensor comes off, what do fingersticks add to the patient's daily shape?

Bars are in docs/PREREGISTRATION.md, Amendment 3, section F. The filter design is chosen on development
patients; test patients are scored once, with the code defaults, and only with --confirm.
Usage: python -m chhaya.eval.fingersticks [--tau 120] [--slow]     (development patients)
       python -m chhaya.eval.fingersticks --confirm                (the one confirmatory run)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.pairs import paired
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline
from chhaya.eval.gate2 import _clean, _git, _paired_p
from chhaya.eval.metrics import clarke_zones, mard, rmse, within_15_15
from chhaya.eval.reveal import why_skipped
from chhaya.twin.assimilate import FilterConfig, deviation, pooled_map, sensor_map

BIN = 30
MIN_HIDDEN_DAYS = 2.0
MIN_STICKS_PER_DAY = 1.0
MIN_HIDDEN_PAIRS = 3
RULES = ("all", "2/day", "1/day", "every 2nd day")


def thin(t, day, rule: str) -> np.ndarray:
    """Which fingersticks are kept under a thinning rule. The first of the day is always the one kept."""
    keep = np.zeros(len(t), dtype=bool)
    if rule == "all":
        keep[:] = True
        return keep
    for d in np.unique(day):
        idx = np.flatnonzero(day == d)
        if rule == "2/day":
            keep[idx[0]] = keep[idx[-1]] = True
        elif rule == "1/day" or (rule == "every 2nd day" and d % 2 == 0):
            keep[idx[0]] = True
    return keep


def why_not(rec: Recording, k_days: float) -> str | None:
    """Why this recording is outside the cohort of section F, or None when it is in."""
    why = why_skipped(rec, k_days, min_test_days=MIN_HIDDEN_DAYS)
    if why is not None:
        return why
    if len(rec.fingersticks) / (rec.n_min / 1440.0) < MIN_STICKS_PER_DAY:
        return "fewer than one fingerstick a day"
    if len(paired(rec, lo=k_days * 1440.0)) < MIN_HIDDEN_PAIRS:
        return "fewer than three paired fingersticks after the split"
    return None


def estimates(rec: Recording, k_days: float, cfg: FilterConfig, pooled: tuple[float, float], rule: str = "all") -> dict:
    """Control, live and in-hindsight estimates on the hidden sensor timestamps, on the sensor's scale.

    Everything learned (shape, mean, map) comes from before the split. After it only fingersticks are read.
    """
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    tod0 = rec.start.hour * 60 + rec.start.minute
    cal = t < split
    centres = np.arange(0, 1440, BIN) + BIN // 2
    shape = 0.5 * average_day_baseline((tod0 + t[cal]) % 1440, g[cal], centres, BIN) + 0.5 * float(g[cal].mean())
    at = lambda tt: shape[((tod0 + np.asarray(tt)) % 1440).astype(int) // BIN]  # noqa: E731
    cal_pairs = paired(rec, hi=split)
    a, b = sensor_map(cal_pairs["cbg"], cal_pairs["cgm"], pooled)
    hid = paired(rec, lo=split)
    keep = thin(hid["t_min"].to_numpy(), ((tod0 + hid["t_min"].to_numpy()) // 1440).astype(int), rule)
    hid = hid[keep].reset_index(drop=True)
    ft = hid["t_min"].to_numpy(dtype=float)
    z = a + b * hid["cbg"].to_numpy(dtype=float) - at(ft)
    tt = t[~cal]
    control = at(tt)
    return {
        "t": tt, "control": control, "map": (a, b), "sticks": hid, "z": z, "shape_at": at,
        "live": control + deviation(ft, z, tt, cfg, smooth=False),
        "hindsight": control + deviation(ft, z, tt, cfg, smooth=True),
    }  # fmt: skip


def run_recording(
    rec: Recording, k_days: float, cfg: FilterConfig, pooled: tuple[float, float], rule: str = "all"
) -> dict | None:
    """One row of scores for a recording in the cohort; None when it is outside it."""
    if why_not(rec, k_days) is not None:
        return None
    e = estimates(rec, k_days, cfg, pooled, rule)
    if len(e["sticks"]) < 2:
        return None
    truth = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)[rec.cgm["t_min"].to_numpy() >= k_days * 1440.0]
    a, b = e["map"]
    ft = e["sticks"]["t_min"].to_numpy(dtype=float)
    ref = e["sticks"]["cbg"].to_numpy(dtype=float)
    # each fingerstick predicted from the shape and the fingersticks before it, on the fingerstick's own scale
    before = np.array([deviation(ft[:i], e["z"][:i], ft[i : i + 1], cfg)[0] for i in range(len(ft))])
    pred = {
        "sensor": e["sticks"]["cgm"].to_numpy(dtype=float),
        "control": (e["shape_at"](ft) - a) / b,
        "live": (e["shape_at"](ft) + before - a) / b,
    }
    row = {
        "rec_id": rec.rec_id, "patient_id": rec.patient_id, "dev": is_dev_patient(rec.patient_id), "k_days": k_days,
        "rule": rule, "n_sticks": len(ft), "hidden_days": float((e["t"].max() - k_days * 1440.0) / 1440.0),
        "control_rmse": rmse(e["control"], truth), "live_rmse": rmse(e["live"], truth),
        "hindsight_rmse": rmse(e["hindsight"], truth),
    }  # fmt: skip
    for name, p in pred.items():
        row[f"{name}_mard"] = mard(p, ref)
        row[f"{name}_within15"] = within_15_15(p, ref)
        row[f"{name}_zone_a"] = clarke_zones(p, ref)["A"]
    return row


def summarise(df: pd.DataFrame) -> dict:
    """Patient-level medians and paired tests (recordings of one patient are averaged first)."""
    per = df.groupby("patient_id").mean(numeric_only=True)
    live, hind = per["live_rmse"] - per["control_rmse"], per["hindsight_rmse"] - per["control_rmse"]
    out = {
        "n_patients": int(len(per)),
        "control_rmse": float(per["control_rmse"].median()),
        "live_rmse": float(per["live_rmse"].median()),
        "hindsight_rmse": float(per["hindsight_rmse"].median()),
        "live_median_diff": float(live.median()), "live_frac_better": float((live < 0).mean()), "live_p": _paired_p(live),
        "hindsight_median_diff": float(hind.median()), "hindsight_frac_better": float((hind < 0).mean()),
        "hindsight_p": _paired_p(hind),
    }  # fmt: skip
    for col in per.columns:
        if col.endswith(("_mard", "_within15", "_zone_a")):
            out[col] = float(per[col].median())
    return out


def verdict(s: dict) -> dict:
    return {
        "f1_live_beats_control": bool(s["live_median_diff"] < 0 and s["live_p"] < 0.05),
        "f2_hindsight_beats_control": bool(s["hindsight_median_diff"] < 0 and s["hindsight_p"] < 0.05),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test patients; this is done once")
    ap.add_argument("--k", type=float, nargs="+", default=[3.0, 5.0])
    ap.add_argument("--tau", type=float, default=None, help="development runs only")
    ap.add_argument("--slow", action="store_true", help="development runs only")
    args = ap.parse_args()
    if args.confirm and (args.tau is not None or args.slow):
        raise SystemExit("the confirmatory run uses the code defaults; remove --tau and --slow")
    from chhaya.data.shanghai import load_all

    recs = load_all()
    dev_recs = [r for r in recs if is_dev_patient(r.patient_id)]
    scored = [r for r in recs if not is_dev_patient(r.patient_id)] if args.confirm else dev_recs
    cfg = FilterConfig() if args.confirm or (args.tau is None and not args.slow) else FilterConfig(
        tau_min=args.tau or FilterConfig().tau_min, slow=args.slow
    )
    result = {"confirmatory": args.confirm, "filter": cfg._asdict(), "by_k": []}
    for k in args.k:
        cal = pd.concat([paired(r, hi=k * 1440.0) for r in dev_recs], ignore_index=True)
        pooled = pooled_map(cal["cbg"], cal["cgm"])
        skipped = Counter(w for w in (why_not(r, k) for r in scored) if w)
        block = {"k_days": k, "pooled_map": pooled, "skipped": dict(skipped), "rules": {}}
        for rule in RULES:
            rows = [row for row in (run_recording(r, k, cfg, pooled, rule) for r in scored) if row]
            if rows:
                s = summarise(pd.DataFrame(rows))
                block["rules"][rule] = {**s, **(verdict(s) if rule == "all" else {})}
        result["by_k"].append(block)
    out_dir = RESULTS_DIR / "fingersticks" / ("shanghai" if args.confirm else "shanghai-dev")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(_clean(result), indent=2, allow_nan=False), encoding="utf-8")
    lines = ["# Fingersticks after the sensor comes off", "", f"Filter: `{cfg._asdict()}`", ""]
    lines.append("Confirmatory run on test patients." if args.confirm else "Development patients. Not confirmatory.")
    for block in result["by_k"]:
        lines += ["", f"## k = {block['k_days']:g} days", "", pd.DataFrame(block["rules"]).T.round(3).to_markdown()]
        lines += ["", "Recordings outside the cohort: " + "; ".join(f"{v} ({k})" for k, v in block["skipped"].items())]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    prov = {"commit": _git("rev-parse", "--short", "HEAD"), "uncommitted_changes_in_src": bool(_git("status", "--porcelain", "--", "src")),
            "confirm": args.confirm, "k": args.k}  # fmt: skip
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and see them pass**

Run: `uv run pytest tests/test_fingersticks.py -q`
Expected: 6 passed. `why_skipped(rec, k, min_test_days=2.0)` already exists in `chhaya.eval.reveal` with that signature.

- [ ] **Step 5: Whole fast suite, lint, commit**

```bash
uv run pytest -q -m "not slow"
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/fingersticks.py tests/test_fingersticks.py
git commit -m "feat: fingerstick experiment with a guarded confirmatory run"
```

---

### Task 6: Choose the filter on development patients, freeze it, run once

**Files:**
- Modify: `src/chhaya/twin/assimilate.py` (the two defaults `tau_min` and `slow`, only if the choice differs)
- Create: `docs/decisions/<date>-fingersticks.md`

- [ ] **Step 1: The six declared designs on development patients**

```bash
uv run python -m chhaya.eval.fingersticks --tau 60
uv run python -m chhaya.eval.fingersticks --tau 120
uv run python -m chhaya.eval.fingersticks --tau 240
uv run python -m chhaya.eval.fingersticks --tau 60 --slow
uv run python -m chhaya.eval.fingersticks --tau 120 --slow
uv run python -m chhaya.eval.fingersticks --tau 240 --slow
```

From each, note the median `live_rmse` at k = 3 with all fingersticks. The design with the lowest value is the choice; a tie within 0.1 mg/dL goes to the simpler design (no slow level, then the shorter time constant). These six and nothing else: no other constant is tuned.

- [ ] **Step 2: Freeze the choice**

Set the defaults of `tau_min` and `slow` in `FilterConfig` to the chosen design. Start `docs/decisions/<date>-fingersticks.md` with the six development values and the choice. Run `uv run pytest tests/test_assimilate.py tests/test_fingersticks.py -q`; a test that pinned the old default (`CFG.tau_min`) reads the constant, so it follows. Commit:

```bash
git add src/chhaya/twin/assimilate.py docs/decisions
git commit -m "decide: fingerstick filter design, chosen on development patients"
```

- [ ] **Step 3: Independent review**

Run `mle-reviewer` on `src/chhaya/twin/assimilate.py` and `src/chhaya/eval/fingersticks.py` with this question: "Find any path by which a sensor reading after the split, a fingerstick taken later than the time being estimated (in the live estimate), or any test patient's data reaches an estimate, the sensor map or a filter constant." Run `python-reviewer` on both. Fix what they find, tests first.

- [ ] **Step 4: The one confirmatory run**

`git status` clean under `src/`, then: `uv run python -m chhaya.eval.fingersticks --confirm`
Run once. Whatever it prints is the result.

- [ ] **Step 5: Record and commit**

Complete the decision record: verdict on F1 and F2 at k = 3; k = 5; the thinning table; accuracy against the fingerstick for the real sensor, the control and the live estimate (MARD, within 15/15, Clarke zone A); recordings outside the cohort with reasons; one "claim to quote" sentence. If F1 fails, the sentence is "fingersticks did not improve the live estimate" with the number. Update the roadmap Status table and `docs/PROGRESS.md`.

```bash
git add results/fingersticks docs
git commit -m "results: fingersticks after the sensor comes off, held-out Shanghai patients"
```

Report-level errors (mean, time above 180, time in range against the stale report) and error by day since the sensor are part of Plan 4, which reuses `estimates` from this module.
