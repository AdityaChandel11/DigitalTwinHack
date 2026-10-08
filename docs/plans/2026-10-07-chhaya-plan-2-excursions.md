# Label Check and Excursion Experiment (Gate 3) Implementation Plan

**Goal:** Regenerate the sensor-against-fingerstick label check from a repo command, and run the pre-registered post-meal excursion experiment (Amendment 3, sections L and M) on ShanghaiT2DM.

**Architecture:** A pairing module turns fingersticks and sensor readings into pairs. A feature module turns each `Recording` into one row per eligible meal with a label and four feature groups (record, sensor history, fingersticks, sensor on). A gate module fits one logistic model per arm on development patients and scores test patients once, with patient-level bootstrap intervals and a verdict.

**Tech Stack:** Python 3.13, pandas, NumPy, scikit-learn (logistic regression, imputer, scaler, metrics), LightGBM for one sensitivity run, pytest, ruff.

**Spec:** `docs/specs/2026-10-04-chhaya-m3-design.md`; bars in `docs/PREREGISTRATION.md`, Amendment 3, sections L and M.

## Global Constraints

- Split by patient only: `chhaya.config.is_dev_patient`. Anything fitted uses development patients.
- Test patients are scored once, and only when the command is given `--confirm`. Without it no test patient's row reaches a model or a metric.
- A feature may use nothing stamped at or after the meal time, except the sensor-on group, which may use sensor readings up to the meal time.
- Sensor lows are never a label. The sheet's "Hypoglycemia (yes/no)" column is never a feature.
- Results folders hold aggregates only: no per-meal rows, no per-patient lab values.
- Glucose in mg/dL everywhere in these modules. Always pass `encoding="utf-8"` when writing text.
- `uv run ruff check src tests` and `uv run ruff format src tests` clean; line length 110.
- Bootstrap: 2,000 resamples of patients, seed `chhaya.config.SEED`, 95 % percentile interval.
- From a git worktree, run with the main checkout's interpreter; otherwise `uv run`.

## Review Focus

- A recording with no fingersticks at all: the fingerstick features must be "none" (missing or zero), not an error, and the meal must still be scored.
- A meal logged twice within an hour: it must count as one meal, or the same excursion is scored twice.
- A patient with a single class in the bootstrap resample or in the test set: metrics must skip or return NaN, not crash.
- A record with every lab missing: imputation must use development medians and the run must finish.
- A recording shorter than four days: skipped and counted, never silently dropped.

## File Structure

| File | Responsibility |
|---|---|
| `src/chhaya/data/pairs.py` (new) | Pair fingersticks with sensor readings; the label-validity table |
| `src/chhaya/data/audit.py` (modify) | Write `label_validity.json` during the audit |
| `src/chhaya/data/shanghai.py` (modify) | Two more record fields: 2-hour glucose and C-peptide |
| `src/chhaya/eval/events.py` (new) | Meals, the excursion label, the per-meal feature table |
| `src/chhaya/eval/gate3.py` (new) | Arms, fitting, metrics, bootstrap, verdict, report, CLI |
| `tests/test_pairs.py`, `tests/test_events.py`, `tests/test_gate3.py` (new) | Tests for each |

---

### Task 1: Label check (sensor against fingerstick)

**Files:**
- Create: `src/chhaya/data/pairs.py`, `tests/test_pairs.py`
- Modify: `src/chhaya/data/audit.py` (the `main` function)

**Interfaces:**
- Consumes: `Recording` (`cgm`, `fingersticks`, `start`, `n_min`, `patient_id`).
- Produces: `paired(rec, lo=0.0, hi=None, max_gap=10) -> pd.DataFrame` with columns `t_min, cbg, cgm, slope, hour`; `validity_table(pairs) -> dict`; `label_validity(recs) -> dict`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pairs.py
import dataclasses

import pandas as pd

from chhaya.data.pairs import label_validity, paired, validity_table


def test_pair_uses_the_nearest_reading_and_drops_far_ones(rec):
    cgm = rec.cgm[(rec.cgm["t_min"] < 1000) | (rec.cgm["t_min"] > 1100)]
    sticks = pd.DataFrame({"t_min": [37.0, 1050.0], "glucose_mgdl": [120.0, 130.0]})
    p = paired(dataclasses.replace(rec, cgm=cgm, fingersticks=sticks))
    assert len(p) == 1 and p["t_min"].iloc[0] == 37.0 and p["cbg"].iloc[0] == 120.0
    assert p["cgm"].iloc[0] == float(rec.cgm.loc[rec.cgm["t_min"] == 30, "glucose_mgdl"].iloc[0])
    assert p["hour"].iloc[0] == 0  # the synthetic recording starts at midnight


def test_no_fingersticks_gives_an_empty_frame(rec):
    assert paired(rec).empty


def test_validity_counts_agreement_at_each_threshold():
    p = pd.DataFrame({"cgm": [60.0, 65.0, 60.0, 200.0, 190.0, 100.0], "cbg": [65.0, 95.0, 100.0, 210.0, 170.0, 60.0]})
    v = validity_table(p)
    assert v["below_70"] == {"sensor_flags": 3, "fingerstick_flags": 2, "both": 1, "ppv": 1 / 3, "sensitivity": 0.5}
    assert v["above_180"]["sensor_flags"] == 2 and v["above_180"]["both"] == 1
    assert v["above_180"]["ppv"] == 0.5 and v["above_180"]["sensitivity"] == 1.0


def test_label_validity_reports_pairs_and_patients(rec):
    sticks = pd.DataFrame({"t_min": [30.0, 600.0], "glucose_mgdl": [100.0, 150.0]})
    out = label_validity([dataclasses.replace(rec, fingersticks=sticks)])
    assert out["n_pairs"] == 2 and out["n_patients"] == 1
    assert set(out["thresholds"]) == {"below_54", "below_70", "above_180", "above_250"}
    assert out["mard_percent"] > 0.0
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_pairs.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'chhaya.data.pairs'`

- [ ] **Step 3: Implement**

```python
# src/chhaya/data/pairs.py
"""Sensor readings paired with fingersticks: is a sensor threshold crossing also a capillary one?"""

from __future__ import annotations

import numpy as np
import pandas as pd

from chhaya.data.schema import Recording

MAX_GAP_MIN = 10
PAIR_COLS = ["t_min", "cbg", "cgm", "slope", "hour"]
THRESHOLDS = {"below_54": (54.0, True), "below_70": (70.0, True), "above_180": (180.0, False), "above_250": (250.0, False)}
RANGES = [(0.0, 70.0), (70.0, 100.0), (100.0, 180.0), (180.0, 250.0), (250.0, 600.0)]
FLAT_SLOPE = 5.0  # mg/dL per 15 minutes: below this the sensor trace is flat, so a mismatch is not lag


def paired(rec: Recording, lo: float = 0.0, hi: float | None = None, max_gap: float = MAX_GAP_MIN) -> pd.DataFrame:
    """Each fingerstick in [lo, hi) with the nearest sensor reading no further than `max_gap` minutes away.

    `slope` is the sensor's change per reading around the pair (NaN at the ends of the trace); `hour` is the
    clock hour of the fingerstick.
    """
    hi = float(rec.n_min) if hi is None else hi
    fs = rec.fingersticks[(rec.fingersticks["t_min"] >= lo) & (rec.fingersticks["t_min"] < hi)]
    ft = fs["t_min"].to_numpy(dtype=float)
    fg = fs["glucose_mgdl"].to_numpy(dtype=float)
    ct = rec.cgm["t_min"].to_numpy(dtype=float)
    cg = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    if ft.size == 0 or ct.size < 2:
        return pd.DataFrame({c: pd.Series(dtype=float) for c in PAIR_COLS})
    j = np.clip(np.searchsorted(ct, ft), 1, ct.size - 1)
    near = np.where(np.abs(ct[j] - ft) < np.abs(ct[j - 1] - ft), j, j - 1)
    ok = np.abs(ct[near] - ft) <= max_gap
    inner = (near > 0) & (near < ct.size - 1)
    slope = np.where(inner, (cg[np.clip(near + 1, 0, ct.size - 1)] - cg[np.clip(near - 1, 0, ct.size - 1)]) / 2.0, np.nan)
    tod0 = rec.start.hour * 60 + rec.start.minute
    return pd.DataFrame(
        {"t_min": ft[ok], "cbg": fg[ok], "cgm": cg[near][ok], "slope": slope[ok], "hour": ((tod0 + ft[ok]) % 1440) // 60}
    )


def validity_table(pairs: pd.DataFrame) -> dict:
    """For each threshold: how often the sensor flags, the fingerstick flags, and both."""
    out = {}
    for name, (thr, low) in THRESHOLDS.items():
        s = pairs["cgm"] < thr if low else pairs["cgm"] > thr
        f = pairs["cbg"] < thr if low else pairs["cbg"] > thr
        both = int((s & f).sum())
        out[name] = {
            "sensor_flags": int(s.sum()),
            "fingerstick_flags": int(f.sum()),
            "both": both,
            "ppv": both / int(s.sum()) if s.any() else None,
            "sensitivity": both / int(f.sum()) if f.any() else None,
        }
    return out


def label_validity(recs: list[Recording]) -> dict:
    """The label check of Amendment 3, section L, over every recording given."""
    frames = [paired(r).assign(patient_id=r.patient_id) for r in recs]
    p = pd.concat([f for f in frames if len(f)], ignore_index=True)
    diff = p["cgm"] - p["cbg"]
    by_range = []
    for lo, hi in RANGES:
        m = (p["cbg"] >= lo) & (p["cbg"] < hi)
        if m.any():
            by_range.append(
                {"fingerstick_from": lo, "fingerstick_to": hi, "n": int(m.sum()), "bias": float(diff[m].mean()),
                 "mard_percent": float(100 * (diff[m].abs() / p.loc[m, "cbg"]).mean())}
            )
    low = p[p["cgm"] < 70.0]
    flat = low[low["slope"].abs() <= FLAT_SLOPE]
    night = low[low["hour"] < 6]
    share = lambda d: float((d["cbg"] < 70.0).mean()) if len(d) else None  # noqa: E731
    return {
        "n_pairs": int(len(p)),
        "n_patients": int(p["patient_id"].nunique()),
        "mard_percent": float(100 * (diff.abs() / p["cbg"]).mean()),
        "bias": float(diff.mean()),
        "thresholds": validity_table(p),
        "by_fingerstick_range": by_range,
        "sensor_below_70": {
            "n": int(len(low)),
            "patients": int(low["patient_id"].nunique()),
            "fingerstick_median": float(low["cbg"].median()) if len(low) else None,
            "confirmed_share": share(low),
            "flat_trace_n": int(len(flat)),
            "flat_trace_confirmed_share": share(flat),
            "night_n": int(len(night)),
            "night_confirmed_share": share(night),
        },
    }
```

In `src/chhaya/data/audit.py`, inside `main`, in the `if name == "shanghai":` block after the food strings are written, add:

```python
            from chhaya.data.pairs import label_validity

            (out_dir / "label_validity.json").write_text(
                json.dumps(label_validity(recs), indent=2), encoding="utf-8"
            )
```

- [ ] **Step 4: Run the tests and see them pass**

Run: `uv run pytest tests/test_pairs.py tests/test_audit.py -q`
Expected: all pass.

- [ ] **Step 5: Regenerate the audit on the real files and check it against the research record**

Run: `uv run python -m chhaya.data.audit`
Expected in `results/audit/label_validity.json`: `n_pairs` 3268; `below_70` sensor flags 64, both 8; `above_180` sensor flags 809, both 732; `night_n` 9 with confirmed share 0. If any differs from `docs/decisions/2026-10-04-plan-revision.md`, stop and find out why before going on.

- [ ] **Step 6: Lint, commit**

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/data/pairs.py src/chhaya/data/audit.py tests/test_pairs.py results/audit
git commit -m "feat: label check, sensor against fingerstick (Amendment 3, L)"
```

---

### Task 2: Two more record fields

**Files:**
- Modify: `src/chhaya/data/shanghai.py` (`SUMMARY` and `_static`)
- Test: `tests/test_shanghai.py`

**Interfaces:**
- Produces: `Recording.static["pp2h_glucose_mgdl"]` and `Recording.static["pp2h_cpeptide_nmol"]` (float, NaN when absent).

- [ ] **Step 1: Write the failing test** (append to `tests/test_shanghai.py`)

```python
def test_record_carries_two_hour_glucose_and_cpeptide():
    from chhaya.data.shanghai import _static

    row = pd.Series(
        {
            "Age (years)": 60,
            "Fasting Plasma Glucose (mg/dl)": 150.0,
            "2-hour Postprandial Plasma Glucose (mg/dl)": 250.2,
            "Fasting C-peptide (nmol/L)": 0.4,
            "2-hour Postprandial C-peptide (nmol/L)": 1.1,
        }
    )
    s = _static(row)
    assert s["fasting_glucose_mgdl"] == 150.0 and s["pp2h_glucose_mgdl"] == 250.2
    assert s["fasting_cpeptide_nmol"] == 0.4 and s["pp2h_cpeptide_nmol"] == 1.1
    assert np.isnan(_static(pd.Series({"Age (years)": 60}))["pp2h_glucose_mgdl"])
```

- [ ] **Step 2: Run it and see it fail**

Run: `uv run pytest tests/test_shanghai.py -q`
Expected: FAIL with `KeyError: 'pp2h_glucose_mgdl'`

- [ ] **Step 3: Implement**

In `SUMMARY`, after the `fasting_cpeptide_nmol` line, add:

```python
    "pp2h_glucose_mgdl": r"^2-hour postprandial plasma glucose",
    "pp2h_cpeptide_nmol": r"^2-hour postprandial c-?peptide",
```

In the dict returned by `_static`, after the `fasting_cpeptide_nmol` line, add:

```python
        "pp2h_glucose_mgdl": num.get("pp2h_glucose_mgdl", np.nan),
        "pp2h_cpeptide_nmol": num.get("pp2h_cpeptide_nmol", np.nan),
```

- [ ] **Step 4: Run, lint, commit**

Run: `uv run pytest tests/test_shanghai.py -q` (expected: pass), then

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/data/shanghai.py tests/test_shanghai.py
git commit -m "feat: 2-hour glucose and C-peptide in the Shanghai record"
```

---

### Task 3: Meals, the excursion label and the per-meal feature table

**Files:**
- Create: `src/chhaya/eval/events.py`, `tests/test_events.py`

**Interfaces:**
- Consumes: `Recording`; `chhaya.eval.reveal.why_skipped(rec, k_days)`; `chhaya.eval.baselines.average_day_baseline(cal_tod, cal_g, test_tod, bin_min=30)`; `chhaya.config.is_dev_patient`.
- Produces: `merge_meals(t_min) -> np.ndarray`; `excursion(t, g, meal_t, threshold=180.0) -> bool | None`; `drug_flags(agents) -> dict`; `meal_table(rec, k_days=3.0) -> pd.DataFrame`; column lists `CONTEXT`, `RECORD`, `HISTORY`, `STICKS`, `SENSOR`. Table columns besides those: `rec_id, patient_id, dev, t_min, hidden_days, pump, y, y250, start_high`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_events.py
import dataclasses

import numpy as np
import pandas as pd

from chhaya.eval.events import CONTEXT, HISTORY, RECORD, SENSOR, STICKS, drug_flags, excursion, meal_table, merge_meals

SPLIT = 3 * 1440


def test_entries_within_an_hour_are_one_meal():
    assert merge_meals([300.0, 100.0, 130.0, 170.0]).tolist() == [100.0, 170.0, 300.0]


def test_excursion_needs_two_consecutive_readings_above_the_threshold():
    t = np.arange(0.0, 240.0, 15.0)
    g = np.full(t.size, 140.0)
    g[4] = 200.0  # one reading alone is not an event
    assert excursion(t, g, 30.0) is False
    g[5] = 190.0
    assert excursion(t, g, 30.0) is True
    assert excursion(t, g, 30.0, threshold=250.0) is False
    assert excursion(t[:5], g[:5], 30.0) is None  # fewer than six readings after the meal


def test_drug_flags_read_the_agents_list():
    f = drug_flags("metformin, Humulin 70/30, gliclazide")
    assert f == {"r_insulin": 1.0, "r_secretagogue": 1.0, "r_agi": 0.0, "r_metformin": 1.0}
    assert drug_flags(None)["r_insulin"] == 0.0 and drug_flags("acarbose")["r_agi"] == 1.0


def test_table_has_one_row_per_meal_after_the_split(rec):
    tab = meal_table(rec, 3.0)
    assert len(tab) == 9 and (tab["t_min"] >= SPLIT).all()  # three meals a day on days 4 to 6
    for col in CONTEXT + RECORD + HISTORY + STICKS + SENSOR + ["y", "y250", "start_high", "dev", "hidden_days", "pump"]:
        assert col in tab.columns
    assert (tab["f_has"] == 0).all() and tab["f_last"].isna().all()  # no fingersticks in this recording


def test_hidden_sensor_readings_reach_only_the_label_and_the_sensor_arm(rec):
    cgm = rec.cgm.copy()
    hidden = cgm["t_min"] >= SPLIT
    cgm.loc[hidden, "glucose_mgdl"] = np.clip(cgm.loc[hidden, "glucose_mgdl"] + 60.0, 40.0, 400.0)
    a, b = meal_table(rec, 3.0), meal_table(dataclasses.replace(rec, cgm=cgm), 3.0)
    pd.testing.assert_frame_equal(a[CONTEXT + RECORD + HISTORY + STICKS], b[CONTEXT + RECORD + HISTORY + STICKS])
    assert not np.allclose(a["s_last"], b["s_last"])


def test_only_fingersticks_taken_before_the_meal_are_used(rec):
    first = float(meal_table(rec, 3.0)["t_min"].iloc[0])
    sticks = pd.DataFrame({"t_min": [SPLIT - 50.0, first - 60.0, rec.n_min - 10.0], "glucose_mgdl": [300.0, 150.0, 90.0]})
    tab = meal_table(dataclasses.replace(rec, fingersticks=sticks), 3.0)
    row = tab.iloc[0]
    assert row["f_has"] == 1 and row["f_last"] == 150.0 and row["f_age"] == 60.0 and row["f_n"] == 1
    assert tab["f_n"].iloc[-1] == 1  # the fingerstick at the end of the recording is after every meal
    assert tab["f_mean"].iloc[-1] == 150.0  # and the one before the split is not counted


def test_short_recording_gives_no_rows(rec):
    short = dataclasses.replace(rec, cgm=rec.cgm[rec.cgm["t_min"] < SPLIT + 600])
    assert meal_table(short, 3.0).empty
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_events.py -q`
Expected: FAIL, `ModuleNotFoundError: No module named 'chhaya.eval.events'`

- [ ] **Step 3: Implement**

```python
# src/chhaya/eval/events.py
"""Post-meal excursions: the adverse event of Amendment 3, and what each data stream knows before the meal."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from chhaya.config import is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline
from chhaya.eval.reveal import why_skipped

EVENT_MGDL = 180.0
SEVERE_MGDL = 250.0
HORIZON_MIN = 120.0
MERGE_MIN = 60.0  # a diet entry this soon after a meal's start belongs to that meal
MIN_READINGS = 6  # of the 8 a 15-minute sensor takes in two hours
MAX_STEP_MIN = 20.0  # two readings further apart than this are not consecutive
PRE_GAP_MIN = 20.0  # the sensor-on arm needs a reading this soon before the meal
RECENT_MIN = 180.0  # a fingerstick older than this is not "the last fingerstick"
BIN = 30

CONTEXT = ["c_sin", "c_cos"]
RECORD = ["r_age", "r_male", "r_bmi", "r_duration", "r_hba1c", "r_fpg", "r_pp2h", "r_cpep", "r_egfr",
          "r_insulin", "r_secretagogue", "r_agi", "r_metformin"]  # fmt: skip
HISTORY = ["h_mean", "h_sd", "h_tar", "h_at", "h_peak", "h_rate"]
STICKS = ["f_has", "f_last", "f_age", "f_n", "f_mean"]
SENSOR = ["s_last", "s_slope", "s_mean"]

_DRUGS = {
    "r_insulin": r"insulin|novolin|humulin|gansulin|scilin|aspart|glargine|glarigine|degludec|detemir|glulisine",
    "r_secretagogue": r"gliclazide|glimepiride|gliquidone|glipizide|glibenclamide|repaglinide|nateglinide",
    "r_agi": r"acarbose|voglibose|miglitol",
    "r_metformin": r"metformin",
}


def merge_meals(t_min) -> np.ndarray:
    """Meal start times: an entry within MERGE_MIN of the current meal's start belongs to that meal."""
    out: list[float] = []
    for t in np.sort(np.asarray(t_min, dtype=float)):
        if not out or t - out[-1] > MERGE_MIN:
            out.append(float(t))
    return np.array(out)


def excursion(t, g, meal_t: float, threshold: float = EVENT_MGDL) -> bool | None:
    """Two consecutive readings above `threshold` in the two hours after the meal; None when too few readings."""
    m = (t > meal_t) & (t <= meal_t + HORIZON_MIN)
    if int(m.sum()) < MIN_READINGS:
        return None
    above = g[m] > threshold
    return bool(np.any(above[1:] & above[:-1] & (np.diff(t[m]) <= MAX_STEP_MIN)))


def drug_flags(agents) -> dict[str, float]:
    text = "" if agents is None else str(agents).lower()
    return {k: float(bool(re.search(p, text))) for k, p in _DRUGS.items()}


def _record(static: dict) -> dict[str, float]:
    num = lambda key: float(static[key]) if static.get(key) is not None else np.nan  # noqa: E731
    sex = static.get("sex")
    return {
        "r_age": num("age"),
        "r_male": np.nan if sex is None else float(sex == "M"),
        "r_bmi": num("bmi"),
        "r_duration": num("diabetes_duration_y"),
        "r_hba1c": num("hba1c_pct"),
        "r_fpg": num("fasting_glucose_mgdl"),
        "r_pp2h": num("pp2h_glucose_mgdl"),
        "r_cpep": num("fasting_cpeptide_nmol"),
        "r_egfr": num("egfr"),
        **drug_flags(static.get("agents")),
    }


def meal_table(rec: Recording, k_days: float = 3.0) -> pd.DataFrame:
    """One row per eligible meal after the split: the label and every arm's features.

    Record features come from the static record; history features from sensor readings before the split;
    fingerstick features from fingersticks after the split and before the meal; sensor features from sensor
    readings up to the meal. Nothing else may look past the meal time.
    """
    if why_skipped(rec, k_days) is not None:
        return pd.DataFrame()
    split = k_days * 1440.0
    t = rec.cgm["t_min"].to_numpy(dtype=float)
    g = rec.cgm["glucose_mgdl"].to_numpy(dtype=float)
    tod0 = rec.start.hour * 60 + rec.start.minute
    cal = t < split
    centres = np.arange(0, 1440, BIN) + BIN // 2
    shape = 0.5 * average_day_baseline((tod0 + t[cal]) % 1440, g[cal], centres, BIN) + 0.5 * float(g[cal].mean())
    meals = merge_meals(rec.meals["t_min"])
    seen = [e for e in (excursion(t[cal], g[cal], m) for m in meals[meals < split - HORIZON_MIN]) if e is not None]
    history = {
        "h_mean": float(g[cal].mean()),
        "h_sd": float(g[cal].std()),
        "h_tar": float(np.mean(g[cal] > EVENT_MGDL)),
        "h_rate": (sum(seen) + 1.0) / (len(seen) + 2.0),  # shrunk toward one half when few meals were seen
    }
    record = _record(rec.static)
    ft = rec.fingersticks["t_min"].to_numpy(dtype=float)
    fg = rec.fingersticks["glucose_mgdl"].to_numpy(dtype=float)
    pump = float("csii" in set(rec.doses["route"])) if len(rec.doses) else 0.0
    rows = []
    for m in meals[meals >= split]:
        y = excursion(t, g, m)
        before = (t <= m) & (t >= m - HORIZON_MIN)
        if y is None or not before.any() or m - t[before][-1] > PRE_GAP_MIN:
            continue
        clock = (tod0 + m) % 1440
        b0 = int(clock) // BIN
        earlier = (ft >= split) & (ft < m)
        recent = earlier & (ft >= m - RECENT_MIN)
        rows.append(
            {
                "rec_id": rec.rec_id,
                "patient_id": rec.patient_id,
                "dev": is_dev_patient(rec.patient_id),
                "t_min": float(m),
                "hidden_days": float((t.max() - split) / 1440.0),
                "pump": pump,
                "y": int(y),
                "y250": int(bool(excursion(t, g, m, SEVERE_MGDL))),
                "start_high": int(g[before][-1] > EVENT_MGDL),
                "c_sin": float(np.sin(2 * np.pi * clock / 1440)),
                "c_cos": float(np.cos(2 * np.pi * clock / 1440)),
                **record,
                **history,
                "h_at": float(shape[b0]),
                "h_peak": float(max(shape[(b0 + i) % shape.size] for i in range(5))),
                "f_has": int(recent.any()),
                "f_last": float(fg[recent][-1]) if recent.any() else np.nan,
                "f_age": float(m - ft[recent][-1]) if recent.any() else np.nan,
                "f_n": int(earlier.sum()),
                "f_mean": float(fg[earlier].mean()) if earlier.any() else np.nan,
                "s_last": float(g[before][-1]),
                "s_slope": float(g[before][-1] - np.interp(m - 30.0, t, g)),
                "s_mean": float(g[before].mean()),
            }
        )
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run the tests and see them pass**

Run: `uv run pytest tests/test_events.py -q`
Expected: 7 passed. If `test_table_has_one_row_per_meal_after_the_split` counts fewer than 9, print the table's `t_min` and check eligibility of the last meal of day 6 before changing anything.

- [ ] **Step 5: Lint, commit**

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/events.py tests/test_events.py
git commit -m "feat: post-meal excursion label and per-meal features, with leakage tests"
```

---

### Task 4: Arms, metrics, bootstrap and verdict

**Files:**
- Create: `src/chhaya/eval/gate3.py`, `tests/test_gate3.py`

**Interfaces:**
- Consumes: the table and column lists of Task 3; `chhaya.config.SEED`.
- Produces: `ARMS: dict[str, list[str]]`; `fit_predict(train, test, cols, y="y") -> np.ndarray`; `metrics(y, p) -> dict`; `boot_diff(patient, y, pa, pb, n_boot=2000, seed=SEED) -> dict` with keys `diff, lo, hi`; `evaluate(dev, test, y="y", n_boot=2000) -> dict` with keys `arms, diffs, verdict, n_meals, n_patients, prevalence, alerts, net_benefit`; `out_of_fold(dev, y="y") -> pd.DataFrame`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_gate3.py
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
                patient_id=f"p{p}", rec_id=f"p{p}", dev=p % 2 == 0, t_min=float(m), hidden_days=7.0, pump=0.0,
                y=int(rng.random() < 1 / (1 + np.exp(-logit))), y250=0, start_high=0,
                r_hba1c=rec_part, h_rate=hist_part, f_last=stick_part, f_has=1.0,
            )
            rows.append(row)
    return pd.DataFrame(rows)


def test_fusion_passes_when_each_stream_holds_part_of_the_signal():
    t = _table(signal=True)
    out = gate3.evaluate(t[t["dev"]], t[~t["dev"]], n_boot=300)
    assert out["arms"]["fused"]["auprc"] > max(out["arms"][a]["auprc"] for a in ("record", "history", "fingersticks"))
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
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_gate3.py -q`
Expected: FAIL, `ImportError: cannot import name 'gate3'`

- [ ] **Step 3: Implement the scoring half of `gate3.py`**

```python
# src/chhaya/eval/gate3.py
"""Gate 3: is a post-meal excursion predictable at meal time, and does fusing the streams help?

Bars are in docs/PREREGISTRATION.md, Amendment 3, section M. Models are fitted on development patients.
Test patients are scored once, and only with --confirm.
Usage: python -m chhaya.eval.gate3            (development patients, cross-validated)
       python -m chhaya.eval.gate3 --confirm  (the one confirmatory run)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from chhaya.config import SEED
from chhaya.eval.events import CONTEXT, HISTORY, RECORD, SENSOR, STICKS

ARMS = {
    "record": CONTEXT + RECORD,
    "history": CONTEXT + HISTORY,
    "fingersticks": CONTEXT + STICKS,
    "fused": CONTEXT + RECORD + HISTORY + STICKS,
    "sensor_on": CONTEXT + RECORD + HISTORY + STICKS + SENSOR,
}
SINGLE = ("record", "history", "fingersticks")
BASELINE = "personal_rate"
TARGET_SENSITIVITY = 0.80
NB_THRESHOLDS = (0.3, 0.5, 0.7)
MIN_EACH = 5  # events and non-events a patient needs for a within-patient AUROC


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, cols: list[str], y: str = "y") -> np.ndarray:
    """L2 logistic regression with median imputation, fitted on `train` only."""
    model = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
        StandardScaler(),
        LogisticRegression(C=1.0, max_iter=2000),
    )
    model.fit(train[cols].to_numpy(dtype=float), train[y].to_numpy(dtype=int))
    return model.predict_proba(test[cols].to_numpy(dtype=float))[:, 1]


def _two_classes(y) -> bool:
    return 0 < int(np.sum(y)) < len(y)


def metrics(y, p) -> dict:
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    if not _two_classes(y):
        return {"auprc": float("nan"), "auroc": float("nan"), "brier": float("nan"),
                "calibration_slope": float("nan"), "calibration_intercept": float("nan")}  # fmt: skip
    out = {
        "auprc": float(average_precision_score(y, p)),
        "auroc": float(roc_auc_score(y, p)),
        "brier": float(brier_score_loss(y, np.clip(p, 0, 1))),
        "calibration_slope": float("nan"),
        "calibration_intercept": float("nan"),
    }
    if np.ptp(p) > 0:
        q = np.clip(p, 1e-6, 1 - 1e-6)
        cal = LogisticRegression(C=1e6, max_iter=2000).fit(np.log(q / (1 - q)).reshape(-1, 1), y)
        out["calibration_slope"] = float(cal.coef_[0, 0])
        out["calibration_intercept"] = float(cal.intercept_[0])
    return out


def within_patient_auroc(patient, y, p) -> dict:
    """Mean AUROC inside patients that have enough of both outcomes: does it know *when*, not just *who*?"""
    df = pd.DataFrame({"patient": np.asarray(patient), "y": np.asarray(y, dtype=int), "p": np.asarray(p, dtype=float)})
    vals = [
        roc_auc_score(g["y"], g["p"])
        for _, g in df.groupby("patient")
        if g["y"].sum() >= MIN_EACH and (1 - g["y"]).sum() >= MIN_EACH
    ]
    return {"within_patient_auroc": float(np.mean(vals)) if vals else float("nan"), "within_patient_n": len(vals)}


def boot_diff(patient, y, pa, pb, n_boot: int = 2000, seed: int = SEED) -> dict:
    """AUPRC(a) - AUPRC(b) with a percentile interval from resampling patients."""
    patient, y = np.asarray(patient), np.asarray(y, dtype=int)
    pa, pb = np.asarray(pa, dtype=float), np.asarray(pb, dtype=float)
    groups = [np.flatnonzero(patient == u) for u in pd.unique(patient)]
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        if _two_classes(y[idx]):
            diffs.append(average_precision_score(y[idx], pa[idx]) - average_precision_score(y[idx], pb[idx]))
    point = average_precision_score(y, pa) - average_precision_score(y, pb) if _two_classes(y) else float("nan")
    lo, hi = np.percentile(diffs, [2.5, 97.5]) if diffs else (float("nan"), float("nan"))
    return {"diff": float(point), "lo": float(lo), "hi": float(hi)}


def out_of_fold(dev: pd.DataFrame, y: str = "y", folds: int = 5) -> pd.DataFrame:
    """Each development meal predicted by models that never saw its patient."""
    out = pd.DataFrame(index=dev.index, columns=list(ARMS), dtype=float)
    k = min(folds, dev["patient_id"].nunique())
    for tr, te in GroupKFold(k).split(dev, groups=dev["patient_id"]):
        for arm, cols in ARMS.items():
            out.iloc[te, out.columns.get_loc(arm)] = fit_predict(dev.iloc[tr], dev.iloc[te], cols, y)
    return out


def _alerts(dev: pd.DataFrame, dev_p, test: pd.DataFrame, test_p, y: str) -> dict:
    """Threshold giving the target sensitivity on development meals, applied to the scored meals."""
    pos = np.sort(np.asarray(dev_p)[dev[y].to_numpy(dtype=bool)])
    if pos.size == 0:
        return {}
    thr = float(pos[int(np.floor((1 - TARGET_SENSITIVITY) * pos.size))])
    alert = np.asarray(test_p) >= thr
    truth = test[y].to_numpy(dtype=bool)
    weeks = float(test.drop_duplicates("rec_id")["hidden_days"].sum() / 7.0)
    return {
        "threshold": thr,
        "sensitivity": float(alert[truth].mean()) if truth.any() else float("nan"),
        "false_alerts_per_patient_week": float((alert & ~truth).sum() / weeks) if weeks > 0 else float("nan"),
    }


def _net_benefit(y, p) -> dict:
    y, p = np.asarray(y, dtype=bool), np.asarray(p, dtype=float)
    out = {}
    for pt in NB_THRESHOLDS:
        w = pt / (1 - pt)
        alert = p >= pt
        out[str(pt)] = {
            "model": float(((alert & y).sum() - w * (alert & ~y).sum()) / y.size),
            "alert_always": float((y.sum() - w * (~y).sum()) / y.size),
        }
    return out


def evaluate(dev: pd.DataFrame, test: pd.DataFrame, y: str = "y", n_boot: int = 2000) -> dict:
    """Fit every arm on `dev`, score `test`, and apply the bars of Amendment 3, section M."""
    truth = test[y].to_numpy(dtype=int)
    pid = test["patient_id"].to_numpy()
    preds = {arm: fit_predict(dev, test, cols, y) for arm, cols in ARMS.items()}
    preds[BASELINE] = test["h_rate"].to_numpy(dtype=float)
    arms = {a: {**metrics(truth, p), **within_patient_auroc(pid, truth, p)} for a, p in preds.items()}
    diffs = {b: boot_diff(pid, truth, preds["fused"], preds[b], n_boot) for b in (*SINGLE, BASELINE)}
    m1 = all(diffs[b]["lo"] > 0 for b in SINGLE)
    m2 = diffs[BASELINE]["lo"] > 0
    slope = arms["fused"]["calibration_slope"]
    prevalence = float(truth.mean()) if truth.size else float("nan")
    gain_on, gain_off = arms["sensor_on"]["auprc"] - prevalence, arms["fused"]["auprc"] - prevalence
    oof = out_of_fold(dev, y)["fused"].to_numpy(dtype=float)
    return {
        "n_meals": int(truth.size),
        "n_patients": int(pd.unique(pid).size),
        "prevalence": prevalence,
        "arms": arms,
        "diffs": diffs,
        "kept_without_sensor": float(gain_off / gain_on) if gain_on > 0 else float("nan"),
        "alerts": _alerts(dev, oof, test, preds["fused"], y),
        "net_benefit": _net_benefit(truth, preds["fused"]),
        "verdict": {
            "m1_fused_beats_every_single_stream": bool(m1),
            "m2_fused_beats_personal_rate": bool(m2),
            "m3_calibration_slope_in_range": bool(0.8 <= slope <= 1.2),
            "pass": bool(m1 and m2),
        },
    }
```

- [ ] **Step 4: Run the tests and see them pass**

Run: `uv run pytest tests/test_gate3.py -q`
Expected: 5 passed in under a minute. If `test_nothing_passes_on_noise` fails because an interval's lower end is just above 0, that is a real false positive at this sample size: do not loosen the test, raise `n_patients` in `_table` to 100 and re-run.

- [ ] **Step 5: Lint, commit**

```bash
uv run ruff check src tests && uv run ruff format src tests
git add src/chhaya/eval/gate3.py tests/test_gate3.py
git commit -m "feat: Gate 3 scoring - arms, patient bootstrap, verdict"
```

---

### Task 5: The command, the development run, the one confirmatory run

**Files:**
- Modify: `src/chhaya/eval/gate3.py` (append), `tests/test_gate3.py` (append)
- Create after the run: `docs/decisions/<date>-gate3.md`

**Interfaces:**
- Consumes: `evaluate`, `out_of_fold`, `metrics`, `boot_diff` (Task 4); `meal_table` (Task 3); `chhaya.eval.gate2._clean`, `_git`; `chhaya.data.shanghai.load_all`.
- Produces: `build_table(recs, k_days=3.0) -> tuple[pd.DataFrame, dict]`; `development_run(dev, n_boot) -> dict`; `write_report(result, out_dir, confirmatory) -> None`; CLI flags `--confirm`, `--k`, `--boot`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_gate3.py`)

```python
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
```

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_gate3.py -q`
Expected: 3 new failures with `AttributeError: module 'chhaya.eval.gate3' has no attribute ...`

- [ ] **Step 3: Implement** (append to `src/chhaya/eval/gate3.py`; add `import argparse`, `import json`, `from collections import Counter`, `from pathlib import Path` to the imports, and `from chhaya.config import RESULTS_DIR`, `from chhaya.data.schema import Recording`, `from chhaya.eval.events import meal_table`, `from chhaya.eval.gate2 import _clean, _git`, `from chhaya.eval.reveal import why_skipped`)

```python
def build_table(recs: list[Recording], k_days: float = 3.0) -> tuple[pd.DataFrame, dict]:
    """Every eligible meal of every recording, and a count of recordings skipped with the reason."""
    frames, skipped = [], Counter()
    for rec in recs:
        why = why_skipped(rec, k_days)
        tab = meal_table(rec, k_days) if why is None else pd.DataFrame()
        if tab.empty:
            skipped[why or "no eligible meal after the split"] += 1
        else:
            frames.append(tab)
    table = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return table, dict(skipped)


def development_run(dev: pd.DataFrame, y: str = "y", n_boot: int = 2000) -> dict:
    """Cross-validated on development patients. For checking the pipeline; it gives no verdict."""
    oof = out_of_fold(dev, y)
    truth = dev[y].to_numpy(dtype=int)
    pid = dev["patient_id"].to_numpy()
    preds = {arm: oof[arm].to_numpy(dtype=float) for arm in ARMS}
    preds[BASELINE] = dev["h_rate"].to_numpy(dtype=float)
    return {
        "confirmatory": False,
        "n_meals": int(truth.size),
        "n_patients": int(pd.unique(pid).size),
        "prevalence": float(truth.mean()),
        "arms": {a: {**metrics(truth, p), **within_patient_auroc(pid, truth, p)} for a, p in preds.items()},
        "diffs": {b: boot_diff(pid, truth, preds["fused"], preds[b], n_boot) for b in (*SINGLE, BASELINE)},
    }


def _secondary(dev: pd.DataFrame, test: pd.DataFrame, n_boot: int) -> dict:
    """The pre-declared secondary analyses: 250 mg/dL, meals that start in range, and subgroups."""
    out = {"above_250": evaluate(dev, test, "y250", n_boot)}
    low_dev, low_test = dev[dev["start_high"] == 0], test[test["start_high"] == 0]
    if len(low_test) and low_dev["y"].nunique() == 2:
        out["starts_at_or_below_180"] = evaluate(low_dev, low_test, "y", n_boot)
    p = fit_predict(dev, test, ARMS["fused"])
    groups = {
        "on_insulin": test["r_insulin"] == 1, "not_on_insulin": test["r_insulin"] == 0,
        "pump": test["pump"] == 1, "no_pump": test["pump"] == 0,
        "male": test["r_male"] == 1, "female": test["r_male"] == 0,
        "age_65_or_more": test["r_age"] >= 65, "under_65": test["r_age"] < 65,
    }  # fmt: skip
    out["subgroups_fused"] = {
        name: {"n_meals": int(m.sum()), "n_patients": int(test.loc[m, "patient_id"].nunique()),
               **metrics(test.loc[m, "y"], p[m.to_numpy()])}
        for name, m in groups.items() if m.any()
    }  # fmt: skip
    return out


def write_report(result: dict, out_dir: Path, confirmatory: bool) -> None:
    """summary.json and report.md. Aggregates only: no per-meal rows, no patient identifiers."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(_clean(result), indent=2, allow_nan=False), encoding="utf-8")
    r = result["primary"]
    lines = ["# Gate 3 — post-meal excursion above 180 mg/dL, predicted at meal time", ""]
    if confirmatory:
        lines.append(f"Verdict: **{'PASS' if r['verdict']['pass'] else 'NOT PASSED'}** (bars M1 and M2, Amendment 3)")
        lines += ["", "```json", json.dumps(r["verdict"], indent=2), "```"]
    else:
        lines.append("Development patients, cross-validated. Not confirmatory: no verdict.")
    lines += ["", f"Meals {r['n_meals']}, patients {r['n_patients']}, share with the event {r['prevalence']:.3f}.", ""]
    arms = pd.DataFrame(r["arms"]).T.round(3)
    lines += [arms.to_markdown(), "", "AUPRC of the fused sensor-off model minus each comparator (95 % interval over patients):", ""]
    lines.append(pd.DataFrame(r["diffs"]).T.round(3).to_markdown())
    if result.get("skipped"):
        lines += ["", "Recordings skipped: " + "; ".join(f"{v} ({k})" for k, v in result["skipped"].items())]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="score the test patients; this is done once")
    ap.add_argument("--k", type=float, default=3.0)
    ap.add_argument("--boot", type=int, default=2000)
    args = ap.parse_args()
    from chhaya.data.shanghai import load_all

    table, skipped = build_table(load_all(), args.k)
    dev = table[table["dev"]].reset_index(drop=True)
    if not args.confirm:
        del table  # no test patient's row is used below this line
        result = {"primary": development_run(dev, n_boot=args.boot), "skipped": skipped}
        out_dir = RESULTS_DIR / "gate3" / "shanghai-dev"
    else:
        test = table[~table["dev"]].reset_index(drop=True)
        result = {"primary": evaluate(dev, test, "y", args.boot), "skipped": skipped,
                  "secondary": _secondary(dev, test, args.boot)}  # fmt: skip
        out_dir = RESULTS_DIR / "gate3" / "shanghai"
    write_report(result, out_dir, confirmatory=args.confirm)
    status = _git("status", "--porcelain", "--", "src")
    prov = {"commit": _git("rev-parse", "--short", "HEAD"), "uncommitted_changes_in_src": bool(status),
            "k_days": args.k, "boot": args.boot, "seed": SEED, "confirm": args.confirm}  # fmt: skip
    (out_dir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    print((out_dir / "report.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
```

The test in Step 1 expects exactly `summary.json` and `report.md` from `write_report`; `provenance.json` is written by `main`.

- [ ] **Step 4: Run the tests, the whole fast suite, and lint**

Run: `uv run pytest -q -m "not slow"` then `uv run ruff check src tests && uv run ruff format src tests`
Expected: everything passes; commit.

```bash
git add src/chhaya/eval/gate3.py tests/test_gate3.py
git commit -m "feat: Gate 3 command with a development run and a guarded confirmatory run"
```

- [ ] **Step 5: Development run on the real files**

Run: `uv run python -m chhaya.eval.gate3`
Read `results/gate3/shanghai-dev/report.md` and check, before anything else:
- The share of meals with the event. If it is above 0.85 or below 0.10, failure 2 of the roadmap is triggered: note it in the decision record now; the primary analysis still runs as registered.
- The number of recordings skipped and the reasons. More than 15 skipped means the eligibility code is wrong, not the data.
- The sensor-on arm must beat the fused arm. If it does not, the sensor features are broken.
Do **not** change features, the learner or the label because of what this run shows. Only defects (a crash, a miscount, a leak) may be fixed, each with a failing test first.

- [ ] **Step 6: Independent review before the confirmatory run**

Run an independent code review on `src/chhaya/eval/events.py` and `src/chhaya/eval/gate3.py` with this question: "Find any path by which a sensor reading at or after the meal time, or any test patient's data, reaches a feature, an imputation value, a scaler, a threshold or a fitted coefficient outside the sensor-on arm." Run a code review on the same files. Fix what they find, tests first.

- [ ] **Step 7: The one confirmatory run**

Check `git status` is clean under `src/`, then run: `uv run python -m chhaya.eval.gate3 --confirm`
This is run once. Whatever it prints is the result.

- [ ] **Step 8: Record and commit**

Write `docs/decisions/<date>-gate3.md` with: the verdict; the arms table; the four differences with intervals; the share of the sensor-on gain kept without the sensor; alerts and net benefit; the secondary analyses; what was seen in the development run; any defect fixed between the runs. Add one sentence headed "The claim to quote". Update the Status table of the roadmap and `docs/PROGRESS.md` in the same commit.

```bash
git add results/gate3 docs
git commit -m "results: Gate 3 on held-out Shanghai patients"
```
