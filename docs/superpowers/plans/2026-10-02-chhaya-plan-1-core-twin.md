# Chhaya Plan 1 — Core Twin, Data Truth and the Reveal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A tested Python package that loads both open datasets, calibrates a physiological glucose–insulin twin on the first *k* days of a patient's sensor data, estimates the hidden days without the sensor, and prints a pre-registered go/no-go verdict on real patients.

**Architecture:** Loaders turn each dataset into one `Recording` type. `build_inputs` turns a `Recording` into arrays; a JAX ODE (E-DES core plus circadian and exercise terms) is calibrated by bounded least squares with the health record as prior, and a Laplace ensemble gives the uncertainty band. The reveal experiment scores the twin against the patient's own average day on readings it never saw.

**Tech Stack:** Python 3.13, uv, JAX (float64, CPU), SciPy, pandas, pytest, ruff.

**Spec:** [docs/WAR_ROOM.md](../../WAR_ROOM.md) (Phase 4 Finalist A, Phase 6), the brief at [docs/brief/Digital_Twin_Challenge_2026_Content.txt](../../brief/Digital_Twin_Challenge_2026_Content.txt), and the roadmap [2026-10-02-chhaya-roadmap.md](2026-10-02-chhaya-roadmap.md) (milestones M1 and M2). Project rules: [CLAUDE.md](../../../CLAUDE.md).

**Provenance of the code below.** Every source and test file in this plan was written and run before the plan was: 67 tests pass in about 30 s, `ruff check` and `ruff format` are clean, on this machine (Python 3.13.7, JAX 0.11.0). The loaders were tested against files built from the documented column names, **not** against the real downloads — Tasks 9 and 10 are the first contact with real data, and are where surprises will be.

## Global Constraints

- Python `>=3.12,<3.14`; dependencies only as listed in `pyproject.toml` in Task 1.
- Glucose is **mg/dL** everywhere outside `chhaya/twin/model.py`; inside the ODE it is **mmol/L**. Convert only with `chhaya.units`.
- Time is integer minutes `t_min` from `Recording.start`; the ODE step is 1 minute.
- In a scored window the twin may read meals and activity, never CGM.
- The only patient split is `chhaya.config.is_dev_patient`.
- Datasets live under `CHHAYA_DATA_DIR` (default `./data`, git-ignored) and are never committed.
- Every text file read or write passes `encoding="utf-8"`.
- Pass bars are those in `docs/PREREGISTRATION.md` (Task 6): primary k = 5 days; P1 twin beats average day with one-sided Wilcoxon p < 0.05; P2 median time-in-range error ≤ 10 points; P3 80 % band covers 70–90 %.
- Gate 1: at least 60 Shanghai recordings with ≥ 3 days and ≥ 2 logged meals per day.
- Nothing is named Gluco* or Glyco*.
- `ruff check src tests` and `ruff format --check src tests` are clean before every commit.

## Review Focus

The inputs most likely to bite a person using this on real files, and the test that pins each:

1. **File headers differ from the documentation** (trailing spaces, different spelling, a renamed column) → the loader finds columns by pattern, and when it cannot, the error lists the headers it saw. Tests: `test_headers_are_matched_by_pattern_not_exact_spelling`, `test_workbook_without_a_cgm_column_names_the_headers_it_found` (Task 8), `test_bio_headers_are_stripped_and_indexed_by_participant` (Task 7).
2. **Glucose in the wrong unit** (a mmol/L column treated as mg/dL) → converted when detectable, rejected otherwise. Tests: `test_sheet_in_mmol_is_converted` (Task 8), `test_implausible_glucose_is_rejected` (Task 2).
3. **A patient with missing streams** — no meals with carbohydrate values, gaps in the band, no weight or fasting insulin → the twin still runs, on stated defaults. Tests: `test_meals_without_carbohydrate_values_are_ignored`, `test_gaps_in_the_band_count_as_rest`, `test_missing_weight_and_insulin_fall_back_to_reference_adult` (Task 2).
4. **A recording too short to hold out a day, or with one sensor missing** → skipped and counted, or the other sensor is used. Tests: `test_too_short_to_hold_out_a_day_returns_none` (Task 5), `test_dexcom_is_used_when_libre_is_missing` (Task 7).
5. **Calibration that diverges or wanders to absurd parameters** → the simulation stays finite across the whole box the optimiser may search, and a failed fit becomes a row with an error, never a missing patient. Tests: `test_stays_finite_everywhere_the_optimiser_may_go` (Task 2), `test_failed_fits_are_recorded_not_dropped` (Task 6).

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml`, `.gitignore`, `LICENSE` | Environment, ignore rules, MIT licence with dataset-licence note |
| `src/chhaya/config.py` | Paths, seed, the dev/test patient split |
| `src/chhaya/units.py` | Unit conversions and GMI |
| `src/chhaya/data/schema.py` | `Recording`, the only type crossing module boundaries, and its validation |
| `src/chhaya/twin/model.py` | The ODE and its integration |
| `src/chhaya/twin/inputs.py` | `Recording` → model input arrays |
| `src/chhaya/twin/priors.py` | Population prior, record-informed prior, search box |
| `src/chhaya/twin/fit.py` | Calibration and posterior ensemble |
| `src/chhaya/eval/metrics.py` | Accuracy and clinical-summary metrics |
| `src/chhaya/eval/baselines.py` | Mean and average-day baselines |
| `src/chhaya/eval/reveal.py` | The hide-and-reveal experiment for one recording |
| `src/chhaya/eval/gate2.py` | Cohort run, verdict, report |
| `src/chhaya/data/download.py` | Fetch, checksum, unpack |
| `src/chhaya/data/cgmacros.py` | CGMacros → `Recording` |
| `src/chhaya/data/shanghai.py` | ShanghaiT2DM → `Recording`, diet-string worklist |
| `src/chhaya/data/audit.py` | Dataset counts and Gate 1 |
| `docs/PREREGISTRATION.md` | The bars, committed before real data is touched |
| `tests/conftest.py` | Synthetic recordings with known true parameters |

Tasks 1–6 need no downloaded data. Tasks 7–8 depend only on Task 2's `Recording` and can be done by a second person in parallel. Start the downloads (Task 7, Step 5) as early as possible — CGMacros is 627 MB.

---

### Task 1: Project scaffold, units and the patient split

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `LICENSE`
- Create: `src/chhaya/__init__.py`, `src/chhaya/data/__init__.py`, `src/chhaya/twin/__init__.py`, `src/chhaya/eval/__init__.py` (all empty)
- Create: `src/chhaya/config.py`, `src/chhaya/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Produces: `chhaya.config.REPO_ROOT, DATA_DIR, RAW_DIR, RESULTS_DIR: Path`, `SEED: int`, `is_dev_patient(patient_id: str) -> bool`
- Produces: `chhaya.units.MGDL_PER_MMOL, LB_TO_KG, INCH_TO_M: float`, `mgdl_to_mmol(x)`, `mmol_to_mgdl(x)`, `gmi_percent(mean_glucose_mgdl)`, `hba1c_ifcc_to_percent(mmol_per_mol)`, `insulin_pmol_to_uu_ml(pmol_per_l)`

- [x] **Step 1: keep the environment and data out of OneDrive.** Skipped: OneDrive is signed out on this machine, so nothing syncs. Optional, if that changes:

In PowerShell, then restart the terminal or the Claude app so the variables are picked up:

```powershell
[Environment]::SetEnvironmentVariable("UV_PROJECT_ENVIRONMENT", "C:\dev\chhaya-venv", "User")
[Environment]::SetEnvironmentVariable("CHHAYA_DATA_DIR", "C:\dev\chhaya-data", "User")
```

Skipping this still works; OneDrive will then try to sync a virtualenv and 627 MB of data.

- [ ] **Step 2: Write `pyproject.toml`**

````toml
[project]
name = "chhaya"
version = "0.1.0"
description = "Chhaya: a Type 2 diabetes digital twin that keeps working after the glucose sensor comes off"
requires-python = ">=3.12,<3.14"
license = "MIT"
dependencies = [
    "jax>=0.4.35",
    "numpy>=2.0",
    "scipy>=1.14",
    "pandas>=2.2",
    "pyarrow>=17",
    "openpyxl>=3.1",
    "xlrd>=2.0",
    "lightgbm>=4.5",
    "scikit-learn>=1.5",
    "plotly>=5.24",
    "streamlit>=1.40",
    "requests>=2.32",
    "tabulate>=0.9",
]

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/chhaya"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["slow: fits a twin (seconds each)", "data: needs downloaded datasets"]
addopts = "-m 'not data'"
pythonpath = ["tests"]

[tool.ruff]
line-length = 110
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
# E501: the formatter owns line length. B008: Fixed() and SlowCoef() defaults are immutable NamedTuples.
ignore = ["E501", "B008"]
````

- [ ] **Step 3: Write `.gitignore`**

````text
# datasets are never committed: CGMacros is CC BY-NC-SA and must be fetched by the user
data/
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.env
results/**/*.npz
````

- [ ] **Step 4: Write `LICENSE`**

````text
MIT License

Copyright (c) 2026 The Chhaya authors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This licence covers the code in this repository only. The datasets it downloads
keep their own licences: ShanghaiT2DM is CC BY 4.0; CGMacros is CC BY-NC-SA 4.0
and may not be used commercially. Neither dataset is redistributed here.
````

- [ ] **Step 5: Create the four empty `__init__.py` files and install**

```bash
mkdir -p src/chhaya/data src/chhaya/twin src/chhaya/eval tests
touch src/chhaya/__init__.py src/chhaya/data/__init__.py src/chhaya/twin/__init__.py src/chhaya/eval/__init__.py
uv sync
```

Expected: `uv sync` ends with a list of installed packages including `jax`, `lightgbm` and `chhaya`.

- [ ] **Step 6: Write the failing test `tests/test_units.py`**

````python
import pytest

from chhaya import units
from chhaya.config import is_dev_patient


def test_glucose_round_trip():
    assert units.mmol_to_mgdl(units.mgdl_to_mmol(180.0)) == pytest.approx(180.0)
    assert units.mgdl_to_mmol(180.16) == pytest.approx(10.0)


def test_gmi_matches_published_anchor():
    # Bergenstal 2018: mean glucose 154 mg/dL corresponds to GMI 7.0 %
    assert units.gmi_percent(154.0) == pytest.approx(7.0, abs=0.01)


def test_hba1c_ifcc_anchor():
    # 53 mmol/mol is 7.0 %
    assert units.hba1c_ifcc_to_percent(53.0) == pytest.approx(7.0, abs=0.01)


def test_split_is_stable_and_roughly_balanced():
    ids = [f"p{i}" for i in range(200)]
    flags = [is_dev_patient(i) for i in ids]
    assert flags == [is_dev_patient(i) for i in ids]
    assert 70 <= sum(flags) <= 130
````

- [ ] **Step 7: Run it and see it fail**

Run: `uv run pytest tests/test_units.py -q`
Expected: collection error, `ImportError: cannot import name 'units' from 'chhaya'`.

- [ ] **Step 8: Write `src/chhaya/units.py`**

````python
"""Unit conversions. Storage and reporting use mg/dL; the ODE runs in mmol/L."""

from __future__ import annotations

MGDL_PER_MMOL = 18.016
LB_TO_KG = 0.45359237
INCH_TO_M = 0.0254


def mgdl_to_mmol(x):
    return x / MGDL_PER_MMOL


def mmol_to_mgdl(x):
    return x * MGDL_PER_MMOL


def gmi_percent(mean_glucose_mgdl):
    """Glucose Management Indicator (Bergenstal 2018)."""
    return 3.31 + 0.02392 * mean_glucose_mgdl


def hba1c_ifcc_to_percent(mmol_per_mol):
    """IFCC mmol/mol -> NGSP percent."""
    return 0.09148 * mmol_per_mol + 2.152


def insulin_pmol_to_uu_ml(pmol_per_l):
    return pmol_per_l / 6.0
````

- [ ] **Step 9: Write `src/chhaya/config.py`**

````python
"""Paths and experiment constants. Every module reads locations from here."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("CHHAYA_DATA_DIR", REPO_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
RESULTS_DIR = REPO_ROOT / "results"
SEED = 20261002


def is_dev_patient(patient_id: str) -> bool:
    """Stable 50/50 split by patient. Dev patients tune population settings; test patients only score."""
    return int(hashlib.sha256(patient_id.encode()).hexdigest(), 16) % 2 == 0
````

- [ ] **Step 10: Run the test and the linter**

Run: `uv run pytest tests/test_units.py -q && uv run ruff check src tests && uv run ruff format --check src tests`
Expected: `4 passed`, `All checks passed!`, and no file listed as needing reformatting.

- [ ] **Step 11: Commit, then branch**

`.claude/`, `.agents/` and `skills-lock.json` are deliberately left out. `docs/` (including the War Room) is public by decision.

```bash
git add pyproject.toml uv.lock .gitignore LICENSE README.md CLAUDE.md src tests docs
git commit -m "chore: scaffold chhaya package with units and patient split"
git switch -c core-twin
```

---

### Task 2: The Recording contract and the twin core

**Files:**
- Create: `src/chhaya/data/schema.py`, `src/chhaya/twin/model.py`, `src/chhaya/twin/inputs.py`, `src/chhaya/twin/priors.py`
- Test: `tests/conftest.py`, `tests/test_schema.py`, `tests/test_model.py`, `tests/test_inputs.py`

**Interfaces:**
- Consumes: `chhaya.units.mgdl_to_mmol`, `mmol_to_mgdl`
- Produces: `chhaya.data.schema.Recording` (frozen dataclass: `rec_id, patient_id, dataset: str`, `start: pd.Timestamp`, `n_min: int`, `cgm: DataFrame`, `static: dict`, and optional frames `cgm_ref, fingersticks, meals, activity, doses`), `Recording.validate() -> None` (raises `ValueError`), column lists `CGM_COLS, MEAL_COLS, ACTIVITY_COLS, DOSE_COLS`, `empty(cols) -> DataFrame`
- Produces: `chhaya.twin.model.Fixed`, `Inputs`, `Params`, `Trajectory` (NamedTuples), `THETA_NAMES`, `N_THETA = 7`, `default_z() -> np.ndarray`, `unpack(z, ib, fx) -> Params`, `meal_window(meal_t, n_steps, width=6, horizon_min=720.0) -> np.ndarray`, `simulate(z, inp, fx) -> Trajectory`, `simulate_jit`, `simulate_ensemble(zs, inp, fx) -> Trajectory` with leading ensemble axis
- Produces: `chhaya.twin.inputs.SlowCoef`, `build_inputs(rec, slow=SlowCoef()) -> tuple[Inputs, np.ndarray, np.ndarray]` returning `(inputs, obs_idx, obs_mmol)`
- Produces: `chhaya.twin.priors.Prior(mu, sd)`, `POP_SD`, `GB = 3`, `BOX_SD = 3.0`, `population_prior() -> Prior`, `record_prior(static: dict) -> Prior`
- Static keys read downstream: `weight_kg`, `fasting_insulin_uu_ml`, `fasting_glucose_mgdl`, `group`

The model in one paragraph, for whoever implements this without the War Room context: four E-DES compartments — glucose mass in the gut, plasma glucose, plasma insulin, interstitial glucose (what a CGM reads). Meals enter the gut through a Weibull-shaped appearance curve; the pancreas secretes insulin in response to how far glucose is above its basal level and how fast it is rising (this is what a Type 1 model lacks); the liver puts out glucose with a 24-hour rhythm; muscle takes glucose up in proportion to insulin, more so after activity. Seven numbers are personal; the rest are population constants. With no meals and no activity the model must sit exactly at the patient's fasting glucose and insulin — that is the first test.

- [ ] **Step 1: Write the shared fixture `tests/conftest.py`**

It generates recordings by running the twin with known parameters, so later tests can check recovery.

````python
"""Synthetic recordings generated by the twin itself, so tests know the true parameters."""

from __future__ import annotations

import dataclasses

import jax.numpy as jnp
import numpy as np
import pandas as pd
import pytest

from chhaya.data.schema import Recording
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import default_z, simulate_jit
from chhaya.units import mmol_to_mgdl

Z_SHIFT = np.array([0.25, -0.6, -0.5, 0.12, 0.5, 0.3, -0.15])


def make_recording(
    days: int = 6, seed: int = 0, z=None, noise_mmol: float = 0.4, with_ref: bool = False
) -> Recording:
    rng = np.random.default_rng(seed)
    n_min = days * 1440
    rows = []
    for d in range(days):
        for hour, carbs in ((8, 45), (13, 70), (20, 60)):
            rows.append(
                {
                    "t_min": float(d * 1440 + hour * 60 + rng.integers(-30, 30)),
                    "carb_g": carbs * rng.uniform(0.6, 1.4),
                    "protein_g": rng.uniform(5, 30),
                    "fat_g": rng.uniform(5, 30),
                    "fibre_g": rng.uniform(0, 10),
                    "label": "meal",
                }
            )
    met = np.ones(n_min)
    for d in range(days):
        met[d * 1440 + 18 * 60 : d * 1440 + 18 * 60 + 40] = 4.0
    activity = pd.DataFrame({"t_min": np.arange(n_min, dtype=float), "met": met, "hr": 70.0})
    z = default_z() + Z_SHIFT if z is None else np.asarray(z)
    fasting = float(mmol_to_mgdl(np.exp(z[3])))
    static = {
        "weight_kg": 70.0,
        "fasting_insulin_uu_ml": 12.0,
        "fasting_glucose_mgdl": fasting,
        "group": "t2d",
    }
    t = np.arange(0, n_min, 15)
    shell = Recording(
        rec_id=f"synth-{seed}",
        patient_id=f"synth-{seed}",
        dataset="synthetic",
        start=pd.Timestamp("2026-01-01 00:00"),
        n_min=n_min,
        cgm=pd.DataFrame({"t_min": t, "glucose_mgdl": np.full(t.size, fasting)}),
        static=static,
        meals=pd.DataFrame(rows),
        activity=activity,
    )
    inp, _, _ = build_inputs(shell)
    truth = np.asarray(simulate_jit(jnp.asarray(z), inp).gi)

    def sensor(step: int) -> pd.DataFrame:
        ts = np.arange(0, n_min, step)
        g = mmol_to_mgdl(truth[ts] + rng.normal(0.0, noise_mmol, ts.size))
        return pd.DataFrame({"t_min": ts, "glucose_mgdl": np.clip(g, 40.0, 400.0)})

    cgm = sensor(15)
    return dataclasses.replace(shell, cgm=cgm, cgm_ref=sensor(5) if with_ref else shell.cgm_ref)


@pytest.fixture(scope="session")
def rec() -> Recording:
    return make_recording()
````

- [ ] **Step 2: Write the failing tests**

`tests/test_schema.py`:

````python
import dataclasses

import pandas as pd
import pytest

from chhaya.data.schema import CGM_COLS, MEAL_COLS, empty


def test_empty_frames_have_the_contract_columns():
    assert list(empty(MEAL_COLS).columns) == MEAL_COLS
    assert len(empty(CGM_COLS)) == 0


def test_valid_recording_passes(rec):
    rec.validate()


def test_reading_past_the_end_is_rejected(rec):
    bad = pd.concat(
        [rec.cgm, pd.DataFrame({"t_min": [rec.n_min + 5], "glucose_mgdl": [120.0]})], ignore_index=True
    )
    with pytest.raises(ValueError, match="outside"):
        dataclasses.replace(rec, cgm=bad).validate()


def test_unsorted_cgm_is_rejected(rec):
    with pytest.raises(ValueError, match="not sorted"):
        dataclasses.replace(rec, cgm=rec.cgm.iloc[::-1]).validate()


def test_empty_cgm_is_rejected(rec):
    with pytest.raises(ValueError, match="no CGM"):
        dataclasses.replace(rec, cgm=rec.cgm.iloc[:0]).validate()


def test_implausible_glucose_is_rejected(rec):
    bad = rec.cgm.copy()
    bad.loc[3, "glucose_mgdl"] = 5.4  # a mmol/L value left unconverted
    with pytest.raises(ValueError, match="20-600"):
        dataclasses.replace(rec, cgm=bad).validate()


def test_frame_missing_a_column_is_rejected(rec):
    with pytest.raises(ValueError, match="lacks columns"):
        dataclasses.replace(rec, meals=rec.meals.drop(columns=["fibre_g"])).validate()
````

`tests/test_model.py`:

````python
import dataclasses

import jax.numpy as jnp
import numpy as np

from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import Fixed, default_z, meal_window, simulate_ensemble, simulate_jit, unpack
from chhaya.twin.priors import BOX_SD, population_prior


def _sim(rec, z=None):
    inp, _, _ = build_inputs(rec)
    return inp, simulate_jit(jnp.asarray(default_z() if z is None else z), inp)


def test_fasting_rest_is_a_steady_state(rec):
    inp, _, _ = build_inputs(
        dataclasses.replace(rec, meals=rec.meals.iloc[:0], activity=rec.activity.iloc[:0])
    )
    z = default_z()
    z[4] = -30.0  # no dawn effect
    inp = inp._replace(g0=float(np.exp(z[3])))
    tr = simulate_jit(jnp.asarray(z), inp)
    assert np.allclose(np.asarray(tr.g), np.exp(z[3]), atol=1e-6)
    assert np.allclose(np.asarray(tr.ins), inp.ib, atol=1e-6)


def test_a_meal_raises_glucose_and_it_comes_back(rec):
    _, tr = _sim(rec)
    day2 = np.asarray(tr.gi)[1440:2880]
    assert day2.max() - day2.min() > 2.0  # mmol/L excursion from three meals
    assert day2[7 * 60] < day2.max() - 1.5  # by 07:00 the overnight fast has brought it down


def test_more_carbohydrate_gives_a_higher_peak(rec):
    _, base = _sim(rec)
    bigger = dataclasses.replace(rec, meals=rec.meals.assign(carb_g=rec.meals["carb_g"] * 1.5))
    _, more = _sim(bigger)
    assert float(more.gi.max()) > float(base.gi.max()) + 0.5


def test_exercise_lowers_glucose(rec):
    _, active = _sim(rec)
    _, resting = _sim(dataclasses.replace(rec, activity=rec.activity.assign(met=1.0)))
    assert float(active.gi.mean()) < float(resting.gi.mean())


def test_insulin_independent_uptake_never_negative():
    fx = Fixed()
    for ib in (2.0, 12.0, 60.0):
        for z1 in (-6.0, 0.0, 6.0):
            z = default_z()
            z[1] = z1
            p = unpack(jnp.asarray(z), ib, fx)
            c11 = fx.gbliv * (fx.km + p.gb) / p.gb - p.k5 * fx.beta * ib
            assert float(c11) >= 0.0


def test_stays_finite_everywhere_the_optimiser_may_go(rec):
    inp, _, _ = build_inputs(rec)
    prior = population_prior()
    rng = np.random.default_rng(0)
    zs = prior.mu + prior.sd * rng.uniform(-BOX_SD, BOX_SD, (128, prior.mu.size))
    gi = np.asarray(simulate_ensemble(jnp.asarray(zs), inp, Fixed()).gi)
    assert np.isfinite(gi).all()
    assert gi.min() >= 0.5 and gi.max() < 100.0  # mmol/L: absurd corners stay bounded, never NaN


def test_meal_window_lists_recent_meals_only():
    win = meal_window([100.0, 400.0], n_steps=1500, width=3, horizon_min=720.0)
    assert set(win[50]) == {2}  # nothing eaten yet: only the dummy index
    assert set(win[100]) == {0, 2}  # the meal at minute 100 starts inside step 100
    assert set(win[500]) == {0, 1, 2}
    assert set(win[900]) == {1, 2}  # the first meal is more than 12 h old
    assert set(win[1400]) == {2}


def test_meal_window_with_no_meals():
    win = meal_window([], n_steps=10)
    assert win.shape == (10, 6) and (win == 0).all()
````

`tests/test_inputs.py`:

````python
import dataclasses

import jax.numpy as jnp
import numpy as np

from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import default_z, simulate_jit
from chhaya.units import mgdl_to_mmol


def test_shapes_and_observations(rec):
    inp, obs_idx, obs_mmol = build_inputs(rec)
    assert inp.met.shape == (rec.n_min,)
    assert inp.meal_win.shape[0] == rec.n_min
    assert inp.meal_t.shape[0] == len(rec.meals) + 1  # the zero-carb dummy
    assert float(inp.meal_carb_mg[-1]) == 0.0
    assert (np.asarray(inp.meal_slow) >= 1.0).all()
    assert obs_idx.shape == obs_mmol.shape == (len(rec.cgm),)
    assert obs_mmol[0] == mgdl_to_mmol(rec.cgm["glucose_mgdl"].iloc[0]) == inp.g0


def test_missing_weight_and_insulin_fall_back_to_reference_adult(rec):
    bare = dataclasses.replace(rec, static={"weight_kg": float("nan"), "fasting_insulin_uu_ml": None})
    inp, _, _ = build_inputs(bare)
    assert inp.body_mass == 70.0 and inp.ib == 10.0


def test_implausible_fasting_insulin_is_clipped(rec):
    inp, _, _ = build_inputs(dataclasses.replace(rec, static={**rec.static, "fasting_insulin_uu_ml": 400.0}))
    assert inp.ib == 60.0


def test_meals_without_carbohydrate_values_are_ignored(rec):
    text_only = rec.meals.assign(carb_g=np.nan)
    inp, _, _ = build_inputs(dataclasses.replace(rec, meals=text_only))
    assert inp.meal_t.shape[0] == 1
    assert np.isfinite(np.asarray(simulate_jit(jnp.asarray(default_z()), inp).gi)).all()


def test_gaps_in_the_band_count_as_rest(rec):
    half = rec.activity[rec.activity["t_min"] < rec.n_min // 2]
    inp, _, _ = build_inputs(dataclasses.replace(rec, activity=half))
    assert (np.asarray(inp.met)[rec.n_min // 2 :] == 1.0).all()
````

- [ ] **Step 3: Run them and see them fail**

Run: `uv run pytest tests/test_schema.py tests/test_model.py tests/test_inputs.py -q`
Expected: errors at collection, `ModuleNotFoundError: No module named 'chhaya.data.schema'`.

- [ ] **Step 4: Write `src/chhaya/data/schema.py`**

````python
"""The single interchange type between loaders, the twin and evaluation."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

CGM_COLS = ["t_min", "glucose_mgdl"]
MEAL_COLS = ["t_min", "carb_g", "protein_g", "fat_g", "fibre_g", "label"]
ACTIVITY_COLS = ["t_min", "met", "hr"]
DOSE_COLS = ["t_min", "drug", "dose", "route"]
_TEXT_COLS = ("label", "drug", "route")


def empty(cols: list[str]) -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="object" if c in _TEXT_COLS else "float64") for c in cols})


@dataclass(frozen=True)
class Recording:
    """One continuous monitoring period of one patient. `t_min` counts minutes from `start`."""

    rec_id: str
    patient_id: str
    dataset: str
    start: pd.Timestamp
    n_min: int
    cgm: pd.DataFrame
    static: dict
    cgm_ref: pd.DataFrame = field(default_factory=lambda: empty(CGM_COLS))
    fingersticks: pd.DataFrame = field(default_factory=lambda: empty(CGM_COLS))
    meals: pd.DataFrame = field(default_factory=lambda: empty(MEAL_COLS))
    activity: pd.DataFrame = field(default_factory=lambda: empty(ACTIVITY_COLS))
    doses: pd.DataFrame = field(default_factory=lambda: empty(DOSE_COLS))

    def validate(self) -> None:
        """Raise ValueError when the recording would silently corrupt a fit."""
        for name, cols in (
            ("cgm", CGM_COLS),
            ("cgm_ref", CGM_COLS),
            ("fingersticks", CGM_COLS),
            ("meals", MEAL_COLS),
            ("activity", ACTIVITY_COLS),
            ("doses", DOSE_COLS),
        ):
            df = getattr(self, name)
            missing = [c for c in cols if c not in df.columns]
            if missing:
                raise ValueError(f"{self.rec_id}: {name} lacks columns {missing}")
            if len(df) and ((df["t_min"] < 0).any() or (df["t_min"] >= self.n_min).any()):
                raise ValueError(f"{self.rec_id}: {name} has t_min outside [0, {self.n_min})")
        if self.cgm.empty:
            raise ValueError(f"{self.rec_id}: no CGM readings")
        if not self.cgm["t_min"].is_monotonic_increasing:
            raise ValueError(f"{self.rec_id}: cgm is not sorted by time")
        g = self.cgm["glucose_mgdl"]
        if g.isna().any() or (g < 20).any() or (g > 600).any():
            raise ValueError(f"{self.rec_id}: cgm glucose missing or outside 20-600 mg/dL")
````

- [ ] **Step 5: Write `src/chhaya/twin/model.py`**

````python
"""T2D glucose-insulin twin core.

Structure follows E-DES (Maas et al. 2015; CGM form of Erdos et al. 2023): gut, plasma glucose,
plasma insulin with glucose-driven endogenous secretion, interstitial glucose. Added here: a
circadian term on hepatic output and an exercise term on insulin-dependent uptake.

Units: time min, glucose mmol/L, insulin mU/L, gut glucose mg.
"""

from __future__ import annotations

from typing import NamedTuple

import jax
import jax.numpy as jnp
import numpy as np

jax.config.update("jax_enable_x64", True)

N_THETA = 7
THETA_NAMES = ("log_k1", "logit_fit", "log_k6", "log_gb", "logit_dawn", "log_kex", "log_bmeal")


class Fixed(NamedTuple):
    """Population constants. Values follow the published E-DES reference implementation."""

    k2: float = 0.633  # 1/min, gut -> plasma
    k3: float = 5.0e-5  # 1/min, hepatic response to glucose deviation
    k4: float = 1.0e-3  # hepatic response to insulin deviation
    k7: float = 1.15  # basal secretion gain
    k8: float = 4.71  # derivative secretion gain
    k9: float = 1.08e-2  # 1/min, insulin loss to interstitium
    sigma: float = 1.35  # Weibull shape of meal appearance
    km: float = 0.63  # mmol/L, Michaelis constant of glucose uptake
    f: float = 0.005551  # mmol per mg glucose
    vg: float = 17.0 / 70.0  # L/kg glucose distribution volume
    gbliv: float = 0.043  # mmol/L/min basal hepatic output
    beta: float = 1.0
    tau_i: float = 31.0  # min
    tau_d: float = 3.0  # min
    g_th: float = 10.0  # mmol/L renal threshold
    c1: float = 0.1  # renal clearance constant
    tau_g: float = 10.0  # min, plasma -> interstitial (CGM) lag
    tau_ex: float = 45.0  # min, exercise effect time constant
    met_rest: float = 1.5  # METs below this count as rest
    dawn_peak_min: float = 300.0  # minute of day of peak hepatic output (05:00)
    dawn_max: float = 0.5  # upper bound of dawn amplitude


class Inputs(NamedTuple):
    meal_t: jnp.ndarray  # (M+1,) minutes from t=0; last entry is a zero-carb dummy
    meal_carb_mg: jnp.ndarray  # (M+1,) carbohydrate as mg glucose
    meal_slow: jnp.ndarray  # (M+1,) >=1, divisor on k1 from fat/protein/fibre
    meal_win: jnp.ndarray  # (T, W) int, indices of meals that can still be absorbing at minute t
    met: jnp.ndarray  # (T,) METs per minute (1.0 = rest)
    t0_min_of_day: float  # clock minute at t=0
    body_mass: float  # kg
    ib: float  # mU/L fasting insulin
    g0: float  # mmol/L glucose at t=0


class Params(NamedTuple):
    k1: jnp.ndarray
    k5: jnp.ndarray
    k6: jnp.ndarray
    gb: jnp.ndarray
    dawn: jnp.ndarray
    kex: jnp.ndarray
    bmeal: jnp.ndarray
    fit: jnp.ndarray  # insulin-mediated fraction of basal glucose disposal


class Trajectory(NamedTuple):
    g: jnp.ndarray  # (T,) plasma glucose mmol/L
    gi: jnp.ndarray  # (T,) interstitial (CGM) glucose mmol/L
    ins: jnp.ndarray  # (T,) plasma insulin mU/L


def unpack(z: jnp.ndarray, ib: float, fx: Fixed = Fixed()) -> Params:
    """Map the unconstrained vector z to physical parameters.

    k5 is expressed as a fraction of its largest admissible value so that the
    insulin-independent uptake constant c11 can never go negative.
    """
    gb = jnp.exp(z[3])
    fit = jax.nn.sigmoid(z[1])
    k5_max = fx.gbliv * (fx.km + gb) / (gb * fx.beta * ib)
    return Params(
        k1=jnp.exp(z[0]),
        k5=fit * k5_max,
        k6=jnp.exp(z[2]),
        gb=gb,
        dawn=fx.dawn_max * jax.nn.sigmoid(z[4]),
        kex=jnp.exp(z[5]),
        bmeal=jnp.exp(z[6]),
        fit=fit,
    )


def default_z() -> np.ndarray:
    """Reference adult with T2D-leaning values: the population prior mean until one is learned."""
    return np.array([np.log(0.012), 0.0, np.log(0.25), np.log(7.0), -1.4, np.log(0.15), 0.0])


def meal_window(meal_t, n_steps: int, width: int = 6, horizon_min: float = 720.0) -> np.ndarray:
    """For each minute, indices of up to `width` most recent meals started within `horizon_min`.

    Unused slots hold len(meal_t), the index of the zero-carb dummy the caller appends.
    """
    meal_t = np.asarray(meal_t, dtype=float)
    dummy = meal_t.size
    win = np.full((n_steps, width), dummy, dtype=np.int32)
    if dummy == 0:
        return win
    order = np.argsort(meal_t, kind="stable")
    t_end = np.arange(n_steps) + 1.0
    hi = np.searchsorted(meal_t[order], t_end, side="left")  # meals with meal_t < t + 1
    for j in range(width):
        k = hi - 1 - j
        idx = order[np.clip(k, 0, dummy - 1)]
        recent = (k >= 0) & (t_end - meal_t[idx] <= horizon_min)
        win[:, j] = np.where(recent, idx, dummy)
    return win


def _weibull(tau, k1, sigma):
    pos = tau > 0.0
    ts = jnp.where(pos, tau, 1.0)
    w = sigma * k1**sigma * ts ** (sigma - 1.0) * jnp.exp(-((k1 * ts) ** sigma))
    return jnp.where(pos, w, 0.0)


def _derivs(x, t, met, win, p: Params, inp: Inputs, fx: Fixed):
    mg, g, ins, gi, ex = x
    k1_m = p.k1 / inp.meal_slow[win]
    mgmeal = p.bmeal * jnp.sum(_weibull(t - inp.meal_t[win], k1_m, fx.sigma) * inp.meal_carb_mg[win])
    d_mg = mgmeal - fx.k2 * mg

    tod = inp.t0_min_of_day + t
    circ = 1.0 + p.dawn * jnp.cos(2.0 * jnp.pi * (tod - fx.dawn_peak_min) / 1440.0)
    gliv = jnp.maximum(fx.gbliv * circ - fx.k3 * (g - p.gb) - fx.k4 * fx.beta * (ins - inp.ib), 0.0)
    ggut = fx.k2 * fx.f / (fx.vg * inp.body_mass) * mg
    sat = g / (fx.km + g)
    c11 = fx.gbliv * (fx.km + p.gb) / p.gb - p.k5 * fx.beta * inp.ib
    gnonit = c11 * sat
    git = p.k5 * fx.beta * ins * sat * (1.0 + p.kex * ex)
    gren = fx.c1 / (fx.vg * inp.body_mass) * jnp.maximum(g - fx.g_th, 0.0)
    d_g = gliv + ggut - gnonit - git - gren

    ipnc = jnp.maximum(
        (p.k6 * (g - p.gb) + (fx.k7 / fx.tau_i) * p.gb + fx.k8 * fx.tau_d * d_g) / fx.beta, 0.0
    )
    iliv = fx.k7 * p.gb / (fx.beta * fx.tau_i * inp.ib) * ins
    iif = fx.k9 * (ins - inp.ib)
    d_ins = ipnc - iliv - iif

    d_gi = (g - gi) / fx.tau_g
    d_ex = (jnp.maximum(met - fx.met_rest, 0.0) - ex) / fx.tau_ex
    return jnp.stack([d_mg, d_g, d_ins, d_gi, d_ex])


_FLOOR = jnp.array([0.0, 0.5, 0.0, 0.5, 0.0])


def simulate(z: jnp.ndarray, inp: Inputs, fx: Fixed = Fixed()) -> Trajectory:
    """Integrate the twin on a 1-minute grid with RK4. Output index i is the state at minute i."""
    p = unpack(z, inp.ib, fx)
    x0 = jnp.array([0.0, inp.g0, inp.ib, inp.g0, 0.0])

    def step(x, tm):
        t, met, win = tm
        a = _derivs(x, t, met, win, p, inp, fx)
        b = _derivs(x + 0.5 * a, t + 0.5, met, win, p, inp, fx)
        c = _derivs(x + 0.5 * b, t + 0.5, met, win, p, inp, fx)
        d = _derivs(x + c, t + 1.0, met, win, p, inp, fx)
        x_new = jnp.maximum(x + (a + 2.0 * b + 2.0 * c + d) / 6.0, _FLOOR)
        return x_new, x

    ts = jnp.arange(inp.met.shape[0], dtype=jnp.float64)
    _, xs = jax.lax.scan(step, x0, (ts, inp.met, inp.meal_win))
    return Trajectory(g=xs[:, 1], gi=xs[:, 3], ins=xs[:, 2])


simulate_jit = jax.jit(simulate)
simulate_ensemble = jax.jit(jax.vmap(simulate, in_axes=(0, None, None)))
````

- [ ] **Step 6: Write `src/chhaya/twin/inputs.py`**

````python
"""Turn a Recording into the arrays the twin integrates."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp
import numpy as np

from chhaya.data.schema import Recording
from chhaya.twin.model import Inputs, meal_window
from chhaya.units import mgdl_to_mmol


class SlowCoef(NamedTuple):
    """How much each gram of fat, protein and fibre slows carbohydrate appearance (population-level)."""

    fat: float = 0.010
    protein: float = 0.005
    fibre: float = 0.020


def _ok(v) -> bool:
    return v is not None and np.isfinite(v)


def build_inputs(rec: Recording, slow: SlowCoef = SlowCoef()) -> tuple[Inputs, np.ndarray, np.ndarray]:
    """Return (inputs, obs_idx, obs_mmol): model inputs plus the CGM minutes and values to fit against."""
    rec.validate()
    meals = rec.meals[rec.meals["carb_g"].notna() & (rec.meals["carb_g"] > 0)].sort_values("t_min")
    meal_t = meals["t_min"].to_numpy(dtype=float)
    macros = meals[["fat_g", "protein_g", "fibre_g"]].astype(float).fillna(0.0).to_numpy()
    meal_slow = 1.0 + macros @ np.array([slow.fat, slow.protein, slow.fibre])

    met = np.ones(rec.n_min)
    act = rec.activity[rec.activity["met"].notna()]
    if len(act):
        met[act["t_min"].to_numpy(dtype=int)] = np.clip(act["met"].to_numpy(dtype=float), 0.9, 18.0)

    weight = rec.static.get("weight_kg")
    ib = rec.static.get("fasting_insulin_uu_ml")
    obs_idx = rec.cgm["t_min"].to_numpy(dtype=int)
    obs_mmol = mgdl_to_mmol(rec.cgm["glucose_mgdl"].to_numpy(dtype=float))
    inp = Inputs(
        meal_t=jnp.asarray(np.append(meal_t, 0.0)),
        meal_carb_mg=jnp.asarray(np.append(meals["carb_g"].to_numpy(dtype=float) * 1000.0, 0.0)),
        meal_slow=jnp.asarray(np.append(meal_slow, 1.0)),
        meal_win=jnp.asarray(meal_window(meal_t, rec.n_min)),
        met=jnp.asarray(met),
        t0_min_of_day=float(rec.start.hour * 60 + rec.start.minute),
        body_mass=float(weight) if _ok(weight) else 70.0,
        ib=float(np.clip(ib, 2.0, 60.0)) if _ok(ib) else 10.0,
        g0=float(obs_mmol[0]),
    )
    return inp, obs_idx, obs_mmol
````

- [ ] **Step 7: Write `src/chhaya/twin/priors.py`**

````python
"""Priors on the twin's seven personal parameters."""

from __future__ import annotations

from typing import NamedTuple

import numpy as np

from chhaya.twin.model import default_z
from chhaya.units import mgdl_to_mmol

POP_SD = np.array([0.5, 1.5, 1.0, 0.25, 1.5, 1.0, 0.3])
GB = 3  # index of log basal glucose in z
BOX_SD = 3.0  # calibration may not leave prior mean +/- this many prior SDs


class Prior(NamedTuple):
    mu: np.ndarray  # (7,)
    sd: np.ndarray  # (7,)


def population_prior() -> Prior:
    return Prior(mu=default_z(), sd=POP_SD.copy())


def record_prior(static: dict) -> Prior:
    """Population prior shifted by what the health record says about this patient.

    Only the fasting-glucose shift is applied here; the learned record-to-parameter map replaces it later.
    """
    prior = population_prior()
    fg = static.get("fasting_glucose_mgdl")
    if fg is not None and np.isfinite(fg) and 60.0 <= fg <= 400.0:
        prior.mu[GB] = np.log(mgdl_to_mmol(fg))
        prior.sd[GB] = 0.15
    return prior
````

- [ ] **Step 8: Run the tests**

Run: `uv run pytest tests/test_schema.py tests/test_model.py tests/test_inputs.py -q`
Expected: `20 passed`. The first run takes a few extra seconds while JAX compiles.

- [ ] **Step 9: Lint and commit**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/data/schema.py src/chhaya/twin tests/conftest.py tests/test_schema.py tests/test_model.py tests/test_inputs.py
git commit -m "feat: Recording contract and E-DES twin core with circadian and exercise terms"
```

---

### Task 3: Calibration and the posterior ensemble

**Files:**
- Create: `src/chhaya/twin/fit.py`
- Test: `tests/test_fit.py`

**Interfaces:**
- Consumes: `simulate`, `Fixed`, `Inputs` from `chhaya.twin.model`; `Prior`, `BOX_SD` from `chhaya.twin.priors`; `build_inputs`; `conftest.Z_SHIFT`
- Produces: `chhaya.twin.fit.SIGMA_OBS: float`, `TwinFit(z_map, cov, sigma_res, cost, n_obs)`, `fit_twin(inp, obs_idx, obs_mmol, prior, fx=Fixed(), n_starts=6, seed=0) -> TwinFit` (raises `ValueError` under 24 readings, `RuntimeError` if every start diverges), `draw_ensemble(fit, n=200, seed=0) -> np.ndarray` of shape `(n, 7)` with row 0 equal to `z_map`

How it works: the residual vector is the CGM misfit stacked with `(z − prior mean) / prior sd`, so least squares on it is a MAP estimate — the record enters through the prior mean. The posterior is approximated by a Gaussian around the optimum (Laplace), widened for misfit and for the fact that neighbouring CGM residuals are correlated.

- [ ] **Step 1: Write the failing test `tests/test_fit.py`**

````python
import numpy as np
import pytest
from conftest import Z_SHIFT

from chhaya.twin.fit import draw_ensemble, fit_twin
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import default_z
from chhaya.twin.priors import GB, population_prior, record_prior


@pytest.fixture(scope="module")
def fitted(rec):
    inp, obs_idx, obs_mmol = build_inputs(rec)
    cal = obs_idx < 4 * 1440
    return fit_twin(inp, obs_idx[cal], obs_mmol[cal], population_prior(), n_starts=3)


@pytest.mark.slow
def test_recovers_the_identifiable_parameters(fitted):
    z_true = default_z() + Z_SHIFT
    assert abs(fitted.z_map[GB] - z_true[GB]) < 0.05  # basal glucose within 5 %
    assert abs(fitted.z_map[0] - z_true[0]) < 0.25  # absorption rate
    assert abs(fitted.z_map[2] - z_true[2]) < 0.5  # beta-cell responsiveness
    assert 0.2 < fitted.sigma_res < 0.7  # close to the 0.4 mmol/L noise that was added


@pytest.mark.slow
def test_posterior_is_usable(fitted):
    assert np.allclose(fitted.cov, fitted.cov.T)
    assert np.linalg.eigvalsh(fitted.cov).min() > 0.0
    zs = draw_ensemble(fitted, n=50, seed=1)
    assert zs.shape == (50, 7)
    assert np.array_equal(zs[0], fitted.z_map)
    assert np.array_equal(zs, draw_ensemble(fitted, n=50, seed=1))  # reproducible


def test_too_few_readings_is_an_error(rec):
    inp, obs_idx, obs_mmol = build_inputs(rec)
    with pytest.raises(ValueError, match="at least 24"):
        fit_twin(inp, obs_idx[:10], obs_mmol[:10], population_prior())


def test_record_prior_uses_fasting_glucose_when_plausible():
    assert record_prior({"fasting_glucose_mgdl": 180.16}).mu[GB] == pytest.approx(np.log(10.0))
    assert record_prior({"fasting_glucose_mgdl": 180.16}).sd[GB] < population_prior().sd[GB]
    for junk in (None, float("nan"), 9.0, 4000.0):
        assert record_prior({"fasting_glucose_mgdl": junk}).mu[GB] == population_prior().mu[GB]
    assert record_prior({}).mu[GB] == population_prior().mu[GB]
````

- [ ] **Step 2: Run it and see it fail**

Run: `uv run pytest tests/test_fit.py -q`
Expected: `ModuleNotFoundError: No module named 'chhaya.twin.fit'`.

- [ ] **Step 3: Write `src/chhaya/twin/fit.py`**

````python
"""MAP calibration of the twin with a Laplace posterior ensemble."""

from __future__ import annotations

from typing import NamedTuple

import jax
import jax.numpy as jnp
import numpy as np
from scipy.optimize import least_squares

from chhaya.twin.model import Fixed, Inputs, simulate
from chhaya.twin.priors import BOX_SD, Prior

SIGMA_OBS = 1.0  # mmol/L nominal CGM residual scale


class TwinFit(NamedTuple):
    z_map: np.ndarray  # (7,)
    cov: np.ndarray  # (7, 7)
    sigma_res: float  # mmol/L, SD of calibration residuals
    cost: float
    n_obs: int


def _n_eff(r: np.ndarray) -> float:
    """Effective sample size of autocorrelated residuals (AR(1) approximation)."""
    if r.size < 3 or np.std(r) == 0.0:
        return float(r.size)
    rho = float(np.clip(np.corrcoef(r[:-1], r[1:])[0, 1], 0.0, 0.99))
    return r.size * (1.0 - rho) / (1.0 + rho)


def fit_twin(
    inp: Inputs,
    obs_idx: np.ndarray,
    obs_mmol: np.ndarray,
    prior: Prior,
    fx: Fixed = Fixed(),
    n_starts: int = 6,
    seed: int = 0,
) -> TwinFit:
    """Fit z by bounded least squares from several prior draws; keep the lowest-cost solution."""
    if len(obs_idx) < 24:
        raise ValueError(f"need at least 24 CGM readings to calibrate, got {len(obs_idx)}")
    idx = jnp.asarray(obs_idx)
    obs = jnp.asarray(obs_mmol)
    mu = jnp.asarray(prior.mu)
    sd = jnp.asarray(prior.sd)

    def res(z):
        gi = simulate(z, inp, fx).gi
        return jnp.concatenate([(gi[idx] - obs) / SIGMA_OBS, (z - mu) / sd])

    res_j = jax.jit(res)
    jac_j = jax.jit(jax.jacfwd(res))
    rng = np.random.default_rng(seed)
    lo = prior.mu - BOX_SD * prior.sd
    hi = prior.mu + BOX_SD * prior.sd
    draws = [prior.mu + 0.5 * prior.sd * rng.standard_normal(prior.mu.size) for _ in range(n_starts - 1)]
    best = None
    for z0 in [prior.mu, *draws]:
        sol = least_squares(
            lambda z: np.asarray(res_j(z)),
            np.clip(z0, lo + 1e-6, hi - 1e-6),
            jac=lambda z: np.asarray(jac_j(z)),
            bounds=(lo, hi),
            method="trf",
            x_scale="jac",
            max_nfev=80,
        )
        if np.all(np.isfinite(sol.fun)) and (best is None or sol.cost < best.cost):
            best = sol
    if best is None:
        raise RuntimeError("twin calibration diverged from every start")
    n = len(obs_idx)
    r_data = best.fun[:n] * SIGMA_OBS
    sigma_res = float(np.sqrt(np.mean(r_data**2)))
    # Laplace covariance, widened for misfit and for autocorrelated residuals.
    h = best.jac.T @ best.jac
    widen = max(1.0, (sigma_res / SIGMA_OBS) ** 2) * n / max(_n_eff(r_data), 1.0)
    cov = np.linalg.inv(h + 1e-9 * np.eye(h.shape[0])) * widen
    return TwinFit(z_map=best.x, cov=cov, sigma_res=sigma_res, cost=float(best.cost), n_obs=n)


def draw_ensemble(fit: TwinFit, n: int = 200, seed: int = 0) -> np.ndarray:
    """Sample parameter vectors from the Laplace posterior. Member 0 is the MAP."""
    rng = np.random.default_rng(seed)
    zs = rng.multivariate_normal(fit.z_map, fit.cov, size=n, method="eigh")
    zs[0] = fit.z_map
    return zs
````

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_fit.py -q`
Expected: `4 passed` in roughly 10 s (one three-start calibration of four days).

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/twin/fit.py tests/test_fit.py
git commit -m "feat: MAP calibration with record prior and Laplace ensemble"
```

---

### Task 4: Metrics and the baselines to beat

**Files:**
- Create: `src/chhaya/eval/metrics.py`, `src/chhaya/eval/baselines.py`
- Test: `tests/test_metrics.py`, `tests/test_baselines.py`

**Interfaces:**
- Consumes: `chhaya.units.gmi_percent`
- Produces: `chhaya.eval.metrics.rmse, mae, mard, pearson` (each `(pred, truth) -> float`), `time_in_ranges(g) -> {"tbr","tir","tar"}`, `coverage(truth, lo, hi) -> float`, `score(pred, truth, lo=None, hi=None) -> dict` with keys `rmse, mae, mard, r, bias, tir_err, tar_err, tbr_err, gmi_err` and `cov80` when bands are given
- Produces: `chhaya.eval.baselines.mean_baseline(cal_g, n_test) -> np.ndarray`, `average_day_baseline(cal_tod, cal_g, test_tod, bin_min=30) -> np.ndarray`

- [ ] **Step 1: Write the failing tests**

`tests/test_metrics.py`:

````python
import numpy as np
import pytest

from chhaya.eval.metrics import coverage, mard, pearson, rmse, score, time_in_ranges


def test_basic_errors():
    assert rmse([100, 120], [110, 110]) == pytest.approx(10.0)
    assert mard([90, 220], [100, 200]) == pytest.approx(10.0)
    assert np.isnan(pearson([100, 100, 100], [90, 100, 110]))


def test_ranges_use_70_and_180_inclusive():
    r = time_in_ranges([69, 70, 180, 181])
    assert (r["tbr"], r["tir"], r["tar"]) == (25.0, 50.0, 25.0)


def test_coverage_counts_edges_as_inside():
    assert coverage([100, 150, 200], [100, 100, 100], [150, 150, 150]) == pytest.approx(2 / 3)


def test_score_reports_clinical_summary_errors():
    truth = np.array([60.0, 100.0, 150.0, 200.0])
    s = score(truth + 10.0, truth, truth - 20.0, truth + 20.0)
    assert s["bias"] == pytest.approx(10.0)
    assert s["tbr_err"] == pytest.approx(25.0)  # the 60 became 70 and left the low range
    assert s["gmi_err"] == pytest.approx(0.2392)
    assert s["cov80"] == 1.0
    assert "cov80" not in score(truth, truth)


def test_score_rejects_mismatched_or_empty_input():
    with pytest.raises(ValueError):
        score([100.0], [100.0, 110.0])
    with pytest.raises(ValueError):
        score([], [])
````

`tests/test_baselines.py`:

````python
import numpy as np
import pytest

from chhaya.eval.baselines import average_day_baseline, mean_baseline


def test_mean_baseline():
    assert mean_baseline([100.0, 140.0], 3).tolist() == [120.0, 120.0, 120.0]


def test_average_day_reproduces_a_repeating_daily_pattern():
    t = np.arange(0, 3 * 1440, 15)
    g = 120.0 + 40.0 * np.sin(2 * np.pi * (t % 1440) / 1440.0)
    cal = t < 2 * 1440
    pred = average_day_baseline(t[cal], g[cal], t[~cal], bin_min=15)
    assert np.allclose(pred, g[~cal])


def test_average_day_fills_hours_never_seen_in_calibration():
    cal_tod = np.array([0, 30, 720])  # nothing between 01:00 and 12:00
    pred = average_day_baseline(cal_tod, np.array([100.0, 100.0, 200.0]), np.array([360]))
    assert 100.0 < pred[0] < 200.0


def test_average_day_handles_clock_times_past_midnight():
    pred = average_day_baseline(np.array([1440 + 60]), np.array([150.0]), np.array([60, 2 * 1440 + 60]))
    assert pred.tolist() == [150.0, 150.0]


def test_average_day_needs_calibration_data():
    with pytest.raises(ValueError):
        average_day_baseline(np.array([], dtype=int), np.array([]), np.array([0]))
````

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_metrics.py tests/test_baselines.py -q`
Expected: `ModuleNotFoundError: No module named 'chhaya.eval.metrics'`.

- [ ] **Step 3: Write `src/chhaya/eval/metrics.py`**

````python
"""Accuracy metrics. All glucose arguments are mg/dL."""

from __future__ import annotations

import numpy as np

from chhaya.units import gmi_percent


def rmse(pred, truth) -> float:
    return float(np.sqrt(np.mean((np.asarray(pred) - np.asarray(truth)) ** 2)))


def mae(pred, truth) -> float:
    return float(np.mean(np.abs(np.asarray(pred) - np.asarray(truth))))


def mard(pred, truth) -> float:
    """Mean absolute relative difference, percent."""
    pred, truth = np.asarray(pred), np.asarray(truth)
    return float(100.0 * np.mean(np.abs(pred - truth) / truth))


def pearson(pred, truth) -> float:
    pred, truth = np.asarray(pred), np.asarray(truth)
    if pred.size < 3 or np.std(pred) == 0.0 or np.std(truth) == 0.0:
        return float("nan")
    return float(np.corrcoef(pred, truth)[0, 1])


def time_in_ranges(g) -> dict[str, float]:
    """Percent of readings below 70, within 70-180 and above 180 mg/dL."""
    g = np.asarray(g)
    return {
        "tbr": float(100.0 * np.mean(g < 70.0)),
        "tir": float(100.0 * np.mean((g >= 70.0) & (g <= 180.0))),
        "tar": float(100.0 * np.mean(g > 180.0)),
    }


def coverage(truth, lo, hi) -> float:
    truth = np.asarray(truth)
    return float(np.mean((truth >= np.asarray(lo)) & (truth <= np.asarray(hi))))


def score(pred, truth, lo=None, hi=None) -> dict[str, float]:
    """Every metric reported for an estimate of a hidden glucose trace."""
    pred, truth = np.asarray(pred, dtype=float), np.asarray(truth, dtype=float)
    if pred.shape != truth.shape or pred.size == 0:
        raise ValueError(f"pred {pred.shape} and truth {truth.shape} must match and be non-empty")
    rp, rt = time_in_ranges(pred), time_in_ranges(truth)
    out = {
        "rmse": rmse(pred, truth),
        "mae": mae(pred, truth),
        "mard": mard(pred, truth),
        "r": pearson(pred, truth),
        "bias": float(np.mean(pred - truth)),
        "tir_err": abs(rp["tir"] - rt["tir"]),
        "tar_err": abs(rp["tar"] - rt["tar"]),
        "tbr_err": abs(rp["tbr"] - rt["tbr"]),
        "gmi_err": float(abs(gmi_percent(pred.mean()) - gmi_percent(truth.mean()))),
    }
    if lo is not None and hi is not None:
        out["cov80"] = coverage(truth, lo, hi)
    return out
````

- [ ] **Step 4: Write `src/chhaya/eval/baselines.py`**

````python
"""Sensor-off baselines: what you can say about hidden glucose without a twin."""

from __future__ import annotations

import numpy as np


def mean_baseline(cal_g, n_test: int) -> np.ndarray:
    """The patient's calibration-window mean, repeated."""
    return np.full(n_test, float(np.mean(cal_g)))


def average_day_baseline(cal_tod, cal_g, test_tod, bin_min: int = 30) -> np.ndarray:
    """The patient's own average daily curve: mean glucose per time-of-day bin in the calibration window.

    `*_tod` are minutes of the day (0-1439). Empty bins are filled from their neighbours around the clock.
    """
    cal_tod = np.asarray(cal_tod, dtype=int) % 1440
    cal_g = np.asarray(cal_g, dtype=float)
    n_bins = 1440 // bin_min
    sums = np.bincount(cal_tod // bin_min, weights=cal_g, minlength=n_bins)
    counts = np.bincount(cal_tod // bin_min, minlength=n_bins)
    have = counts > 0
    if not have.any():
        raise ValueError("no calibration readings")
    profile = np.where(have, sums / np.maximum(counts, 1), np.nan)
    if not have.all():
        centres = np.arange(n_bins)
        known = centres[have]
        profile = np.interp(centres, known, profile[have], period=n_bins)
    return profile[(np.asarray(test_tod, dtype=int) % 1440) // bin_min]
````

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_metrics.py tests/test_baselines.py -q`
Expected: `10 passed`.

- [ ] **Step 6: Lint and commit**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/eval/metrics.py src/chhaya/eval/baselines.py tests/test_metrics.py tests/test_baselines.py
git commit -m "feat: accuracy metrics and sensor-off baselines"
```

---

### Task 5: The hide-and-reveal experiment

**Files:**
- Create: `src/chhaya/eval/reveal.py`
- Test: `tests/test_reveal.py`

**Interfaces:**
- Consumes: `build_inputs`, `fit_twin`, `draw_ensemble`, `TwinFit`, `simulate_ensemble`, `Fixed`, `Prior`, `record_prior`, `score`, `rmse`, `average_day_baseline`, `mean_baseline`, `config.SEED`, `conftest.make_recording`
- Produces: `chhaya.eval.reveal.Reveal(rec_id, k_days, t_test, truth, twin, lo, hi, day, mean, fit, metrics)` — arrays in mg/dL aligned to `t_test`; `metrics` keys are `n_test`, `sigma_res_mgdl`, `twin_*`, `day_*`, `mean_*` for every key of `score`, `twin_cov80`, and `floor_rmse`, `twin_rmse_vs_ref` when a second sensor exists
- Produces: `run_reveal(rec, k_days, prior=None, fx=Fixed(), n_members=200, seed=SEED, min_test_days=1.0) -> Reveal | None` (`None` when the recording cannot hold out a day)

This is the experiment the whole project rests on. One simulation runs from minute 0 across the whole recording; only readings before the split enter the fit; only readings after it are scored.

- [ ] **Step 1: Write the failing test `tests/test_reveal.py`**

````python
import dataclasses

import pytest
from conftest import make_recording

from chhaya.eval.reveal import run_reveal


@pytest.fixture(scope="module")
def reveal():
    return run_reveal(make_recording(days=6, seed=3, with_ref=True), k_days=4, n_members=60)


@pytest.mark.slow
def test_twin_beats_the_average_day_when_meals_vary(reveal):
    m = reveal.metrics
    assert m["twin_rmse"] < m["day_rmse"]
    assert m["twin_rmse"] < 15.0  # mg/dL; sensor noise alone is about 7
    assert reveal.twin.shape == reveal.truth.shape == reveal.lo.shape
    assert (reveal.t_test >= 4 * 1440).all()  # nothing from the calibration window is scored


@pytest.mark.slow
def test_band_is_neither_useless_nor_overconfident(reveal):
    assert (reveal.lo < reveal.hi).all()
    assert 0.55 <= reveal.metrics["twin_cov80"] <= 0.97


@pytest.mark.slow
def test_second_sensor_gives_a_noise_floor(reveal):
    assert 3.0 < reveal.metrics["floor_rmse"] < 20.0
    assert reveal.metrics["twin_rmse_vs_ref"] > 0.0


def test_too_short_to_hold_out_a_day_returns_none(rec):
    assert run_reveal(rec, k_days=6) is None  # six-day recording, nothing left to test on
    short = dataclasses.replace(rec, cgm=rec.cgm[rec.cgm["t_min"] < 4 * 1440 + 600])
    assert run_reveal(short, k_days=4) is None  # only ten hours after the split
````

- [ ] **Step 2: Run it and see it fail**

Run: `uv run pytest tests/test_reveal.py -q`
Expected: `ModuleNotFoundError: No module named 'chhaya.eval.reveal'`.

- [ ] **Step 3: Write `src/chhaya/eval/reveal.py`**

````python
"""The hide-and-reveal experiment: calibrate on the first k days, estimate the rest without the sensor."""

from __future__ import annotations

from typing import NamedTuple

import jax.numpy as jnp
import numpy as np

from chhaya.config import SEED
from chhaya.data.schema import Recording
from chhaya.eval.baselines import average_day_baseline, mean_baseline
from chhaya.eval.metrics import rmse, score
from chhaya.twin.fit import TwinFit, draw_ensemble, fit_twin
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import Fixed, simulate_ensemble
from chhaya.twin.priors import Prior, record_prior
from chhaya.units import mmol_to_mgdl


class Reveal(NamedTuple):
    rec_id: str
    k_days: int
    t_test: np.ndarray  # minutes from recording start
    truth: np.ndarray  # hidden sensor, mg/dL
    twin: np.ndarray  # twin estimate (MAP member), mg/dL
    lo: np.ndarray  # 10th percentile of the predictive band
    hi: np.ndarray  # 90th percentile
    day: np.ndarray  # average-day baseline
    mean: np.ndarray  # mean baseline
    fit: TwinFit
    metrics: dict[str, float]


def run_reveal(
    rec: Recording,
    k_days: int,
    prior: Prior | None = None,
    fx: Fixed = Fixed(),
    n_members: int = 200,
    seed: int = SEED,
    min_test_days: float = 1.0,
) -> Reveal | None:
    """Return None when the recording is too short to calibrate on k days and still test on a day."""
    inp, obs_idx, obs_mmol = build_inputs(rec)
    split = k_days * 1440
    cal = obs_idx < split
    test = ~cal
    if cal.sum() < 48 or test.sum() < 24 or obs_idx[test].max() - split < min_test_days * 1440:
        return None
    prior = prior if prior is not None else record_prior(rec.static)
    fit = fit_twin(inp, obs_idx[cal], obs_mmol[cal], prior, fx, seed=seed)

    zs = draw_ensemble(fit, n_members, seed)
    ens = np.asarray(simulate_ensemble(jnp.asarray(zs), inp, fx).gi)[:, obs_idx[test]]
    noise = np.random.default_rng(seed).normal(0.0, fit.sigma_res, ens.shape)
    lo, hi = mmol_to_mgdl(np.quantile(ens + noise, [0.1, 0.9], axis=0))
    twin = mmol_to_mgdl(ens[0])
    truth = mmol_to_mgdl(obs_mmol[test])

    tod0 = int(inp.t0_min_of_day)
    cal_g = mmol_to_mgdl(obs_mmol[cal])
    day = average_day_baseline(tod0 + obs_idx[cal], cal_g, tod0 + obs_idx[test])
    mean = mean_baseline(cal_g, int(test.sum()))

    metrics: dict[str, float] = {"n_test": float(test.sum()), "sigma_res_mgdl": mmol_to_mgdl(fit.sigma_res)}
    for name, est in (("twin", twin), ("day", day), ("mean", mean)):
        bands = (lo, hi) if name == "twin" else (None, None)
        metrics.update({f"{name}_{k}": v for k, v in score(est, truth, *bands).items()})
    if len(rec.cgm_ref):
        # A second physical sensor: how far apart two real sensors are bounds what any estimate can reach.
        ref = np.interp(obs_idx[test], rec.cgm_ref["t_min"], rec.cgm_ref["glucose_mgdl"])
        metrics["floor_rmse"] = rmse(ref, truth)
        metrics["twin_rmse_vs_ref"] = rmse(twin, ref)
    return Reveal(rec.rec_id, k_days, obs_idx[test], truth, twin, lo, hi, day, mean, fit, metrics)
````

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_reveal.py -q`
Expected: `4 passed` in roughly 15 s.

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/eval/reveal.py tests/test_reveal.py
git commit -m "feat: hide-and-reveal experiment with band and noise floor"
```

---

### Task 6: Pre-registration and the Gate 2 runner

**Files:**
- Create: `docs/PREREGISTRATION.md`, `src/chhaya/eval/gate2.py`
- Test: `tests/test_gate2.py`

**Interfaces:**
- Consumes: `run_reveal`, `Recording`, `config.RESULTS_DIR`, `config.is_dev_patient`; lazily `chhaya.data.cgmacros.load_all`, `chhaya.data.shanghai.load_all` (Tasks 7–8)
- Produces: `chhaya.eval.gate2.PRIMARY_K = 5`, `TIR_BAR = 10.0`, `COVERAGE_BAND = (0.70, 0.90)`, `run_cohort(recs, k_list, n_members=200) -> DataFrame` (one row per recording and k, with `error`), `summarise(df, k=PRIMARY_K) -> dict`, `verdict(summary) -> dict` with keys `p1_beats_average_day, p2_tir_within_bar, p3_band_calibrated, go`, `write_report(df, k_list, out_dir) -> dict`, `load(dataset) -> list[Recording]`, CLI `python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7 [--limit N] [--members N]`
- Writes: `results/gate2/<dataset>/metrics.csv`, `summary.json`, `report.md`

- [ ] **Step 1: Write `docs/PREREGISTRATION.md` and commit it on its own**

This commit must exist before any real data is loaded. Its hash is quoted in the README later.

````markdown
# Pre-registration — sensor-off evaluation

Committed before any model in this repository was run on real patient data. Amendments are appended
below with a date and a reason; nothing above an amendment is edited.

## Question

After calibrating on the first *k* days of a patient's CGM, can the twin estimate that patient's glucose
on the following days **without CGM input**, using logged meals and band activity, better than the
patient's own average daily curve?

## Experiment

- **Data.** Every CGMacros participant with at least one day of primary-sensor data. Primary sensor:
  FreeStyle Libre Pro, one reading per 15 minutes. The Dexcom G6 Pro trace is never used for calibration.
- **Split in time.** Calibrate on readings with `t < k × 1440` minutes. Score on all later readings.
  Recordings that leave less than one full day to score are skipped and counted.
- **Calibration lengths.** k = 3, 5, 7 days. **Primary: k = 5.**
- **What the twin may see in the scored window.** Logged meals (time and macronutrients) and Fitbit METs.
  Nothing else.
- **Comparators.** (a) The patient's own average daily curve: mean glucose per 30-minute time-of-day bin
  over the calibration window. (b) The patient's calibration-window mean.
- **Unit of analysis.** The patient. Several recordings of one patient are averaged first.
- **Failures.** A calibration that fails is recorded with its error and reported as a count. It is not
  replaced or retried with different settings.

## Pass bars (primary, k = 5)

| | Bar | Role |
|---|---|---|
| **P1** | Median over patients of (twin RMSE − average-day RMSE) is below 0, and a one-sided Wilcoxon signed-rank test gives p < 0.05 | Required for GO |
| **P2** | Median absolute error in time-in-range (70–180 mg/dL) is at most 10 percentage points | Required for GO |
| **P3** | The 80 % predictive band contains between 70 % and 90 % of hidden readings | Reported; if it fails, bands are recalibrated on dev patients and re-reported on test patients |

**GO** = P1 and P2. **NO-GO** switches the headline to the overnight-low module on the same engine, as
planned in `docs/WAR_ROOM.md`.

## Also reported, without a bar

RMSE, MAE, MARD, correlation, bias, GMI error, time-above and time-below-range error; all of these for
k = 3 and k = 7; results by group (healthy, pre-diabetes, T2D — the T2D group is about 14 people, too few
for its own test); RMSE between the two physical sensors as a noise floor; twin RMSE against the Dexcom
reference.

## What counts as tuning

The first run uses the defaults in this commit, so every patient counts toward the verdict. After that
run, any change to model structure, fixed constants, priors or band width is chosen using **dev patients
only** (`chhaya.config.is_dev_patient`) and its effect is claimed on **test patients only**.

## Amendments

None.
````

```bash
git add docs/PREREGISTRATION.md
git commit -m "docs: pre-register the sensor-off evaluation and its pass bars"
```

- [ ] **Step 2: Write the failing test `tests/test_gate2.py`**

````python
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
````

- [ ] **Step 3: Run it and see it fail**

Run: `uv run pytest tests/test_gate2.py -q`
Expected: `ImportError: cannot import name 'gate2' from 'chhaya.eval'`.

- [ ] **Step 4: Write `src/chhaya/eval/gate2.py`**

````python
"""Gate 2: does the sensor-off twin beat the patient's own average day?

The pass bars are fixed in docs/PREREGISTRATION.md before this is run on real data.
Usage: python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from chhaya.config import RESULTS_DIR, is_dev_patient
from chhaya.data.schema import Recording
from chhaya.eval.reveal import run_reveal

PRIMARY_K = 5
TIR_BAR = 10.0  # percentage points
COVERAGE_BAND = (0.70, 0.90)


def run_cohort(recs: list[Recording], k_list: list[int], n_members: int = 200) -> pd.DataFrame:
    """One row per (recording, k). Failed fits are kept as rows with an `error` so nothing vanishes silently."""
    rows = []
    for rec in recs:
        base = {
            "rec_id": rec.rec_id,
            "patient_id": rec.patient_id,
            "dataset": rec.dataset,
            "group": rec.static.get("group"),
            "dev": is_dev_patient(rec.patient_id),
        }
        for k in k_list:
            try:
                out = run_reveal(rec, k, n_members=n_members)
            except (RuntimeError, ValueError) as err:
                rows.append({**base, "k_days": k, "error": str(err)})
                continue
            if out is not None:
                rows.append({**base, "k_days": k, "error": None, **out.metrics})
            print(f"{rec.rec_id} k={k}: {'skipped' if out is None else round(out.metrics['twin_rmse'], 1)}")
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame, k: int = PRIMARY_K) -> dict:
    """Patient-level summary at calibration length k (recordings of one patient are averaged first)."""
    if "twin_rmse" not in df.columns:
        return {"k_days": k, "n_patients": 0, "n_failed": int(len(df))}
    ok = df[(df["k_days"] == k) & df["twin_rmse"].notna()]
    per = ok.groupby("patient_id").mean(numeric_only=True)
    diff = per["twin_rmse"] - per["day_rmse"]
    testable = len(per) >= 6 and bool((diff != 0).any())
    out = {
        "k_days": k,
        "n_patients": int(len(per)),
        "n_failed": int(((df["k_days"] == k) & df["error"].notna()).sum()),
        "twin_rmse": float(per["twin_rmse"].median()),
        "day_rmse": float(per["day_rmse"].median()),
        "mean_rmse": float(per["mean_rmse"].median()),
        "median_diff": float(diff.median()),
        "frac_twin_better": float((diff < 0).mean()),
        "wilcoxon_p": float(wilcoxon(diff, alternative="less").pvalue) if testable else float("nan"),
        "twin_mard": float(per["twin_mard"].median()),
        "twin_tir_err": float(per["twin_tir_err"].median()),
        "day_tir_err": float(per["day_tir_err"].median()),
        "cov80": float(per["twin_cov80"].mean()),
    }
    if "floor_rmse" in per.columns:
        out["floor_rmse"] = float(per["floor_rmse"].median())
    return out


def verdict(s: dict) -> dict:
    """Apply the pre-registered bars. GO needs P1 and P2; P3 is reported and fixed later if it fails."""
    if s["n_patients"] == 0:
        return {
            "p1_beats_average_day": False,
            "p2_tir_within_bar": False,
            "p3_band_calibrated": False,
            "go": False,
        }
    p1 = s["median_diff"] < 0 and s["wilcoxon_p"] < 0.05
    p2 = s["twin_tir_err"] <= TIR_BAR
    p3 = COVERAGE_BAND[0] <= s["cov80"] <= COVERAGE_BAND[1]
    return {
        "p1_beats_average_day": bool(p1),
        "p2_tir_within_bar": bool(p2),
        "p3_band_calibrated": bool(p3),
        "go": bool(p1 and p2),
    }


def write_report(df: pd.DataFrame, k_list: list[int], out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "metrics.csv", index=False)
    summaries = [summarise(df, k) for k in k_list]
    primary = next((s for s in summaries if s["k_days"] == PRIMARY_K), summaries[0])
    result = {"summaries": summaries, "primary": primary, "verdict": verdict(primary)}
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    lines = ["# Gate 2 — sensor-off twin vs the patient's own average day", ""]
    lines.append(f"Verdict at k={primary['k_days']} days: **{'GO' if result['verdict']['go'] else 'NO-GO'}**")
    lines += ["", "```json", json.dumps(result["verdict"], indent=2), "```", ""]
    lines.append(pd.DataFrame(summaries).round(3).to_markdown(index=False))
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def load(dataset: str) -> list[Recording]:
    if dataset == "cgmacros":
        from chhaya.data.cgmacros import load_all
    elif dataset == "shanghai":
        from chhaya.data.shanghai import load_all
    else:
        raise ValueError(f"unknown dataset {dataset!r}")
    return load_all()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="cgmacros")
    ap.add_argument("--k", type=int, nargs="+", default=[3, 5, 7])
    ap.add_argument("--limit", type=int, default=None, help="only the first N recordings (smoke run)")
    ap.add_argument("--members", type=int, default=200)
    args = ap.parse_args()
    recs = load(args.dataset)[: args.limit]
    df = run_cohort(recs, args.k, args.members)
    result = write_report(df, args.k, RESULTS_DIR / "gate2" / args.dataset)
    print(json.dumps(result["primary"], indent=2))
    print(json.dumps(result["verdict"], indent=2))
    if np.isnan(result["primary"].get("wilcoxon_p", np.nan)):
        print("Too few patients for the signed-rank test; the verdict is NO-GO by construction.")


if __name__ == "__main__":
    main()
````

- [ ] **Step 5: Run the tests, then the whole suite**

Run: `uv run pytest tests/test_gate2.py -q`
Expected: `6 passed`.

Run: `uv run pytest -q`
Expected: `48 passed`.

- [ ] **Step 6: Lint and commit**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/eval/gate2.py tests/test_gate2.py
git commit -m "feat: Gate 2 cohort runner with pre-registered verdict"
```

---

### Task 7: Download and the CGMacros loader

**Files:**
- Create: `src/chhaya/data/download.py`, `src/chhaya/data/cgmacros.py`
- Test: `tests/test_download.py`, `tests/test_cgmacros.py`

**Interfaces:**
- Consumes: `Recording`, `empty`, `CGM_COLS`, `MEAL_COLS`, `ACTIVITY_COLS`; `config.RAW_DIR`; `units.LB_TO_KG`, `INCH_TO_M`; `build_inputs` (in a test)
- Produces: `chhaya.data.download.SOURCES: dict`, `file_digest(path, algo) -> str`, `verify(path, algo, digest) -> None` (raises `ValueError`), `fetch(name, raw_dir=RAW_DIR) -> Path`, CLI `python -m chhaya.data.download [shanghai] [cgmacros]`
- Produces: `chhaya.data.cgmacros.load_bio(root) -> DataFrame`, `load_recording(csv_path, bio_row) -> Recording | None`, `load_all(root=RAW_DIR / "cgmacros") -> list[Recording]` (raises `FileNotFoundError` naming the download command)
- Static keys produced: `age, sex, bmi, weight_kg, height_m, hba1c_pct, fasting_glucose_mgdl, fasting_insulin_uu_ml, triglycerides_mgdl, hdl_mgdl, group, primary_sensor`

Facts from the dataset's data dictionary that the loader relies on: per-participant CSV on a 1-minute grid with columns `Timestamp, Libre GL, Dexcom GL, HR, Calories (Activity), Mets, Meal Type, Calories, Carbs, Protein, Fat, Fiber, Amount Consumed, Image Path`; `Mets` is the MET value multiplied by 10; `bio.csv` gives weight in pounds, height in inches, HbA1c in percent (the dictionary's "mmol/mol" label is wrong — the range is 4.6–8.5), fasting insulin in µU/mL, and some headers carry trailing spaces. The Libre column is thinned to one reading per 15 minutes so an interpolated 1-minute series is not over-weighted in the fit.

- [ ] **Step 1: Write the failing tests**

`tests/test_download.py`:

````python
import pytest

from chhaya.data.download import SOURCES, verify


def test_checksum_mismatch_is_an_error(tmp_path):
    f = tmp_path / "x.zip"
    f.write_bytes(b"abc")
    verify(f, "md5", "900150983cd24fb0d6963f7d28e17f72")
    with pytest.raises(ValueError, match="does not match"):
        verify(f, "md5", "0" * 32)


def test_every_source_states_its_licence_and_checksum():
    for src in SOURCES.values():
        assert src["license"] and len(src["digest"]) in (32, 64) and src["url"].startswith("https://")
````

`tests/test_cgmacros.py`:

````python
import numpy as np
import pandas as pd
import pytest

from chhaya.data.cgmacros import load_all, load_bio
from chhaya.twin.inputs import build_inputs


def _write_participant(root, number: int, days: int = 2, libre: bool = True):
    """A file with the headers listed in DataDictionary_CGMacros-00X.csv, on a 1-minute grid."""
    n = days * 1440
    ts = pd.date_range("2025-03-01 07:00", periods=n, freq="min")
    df = pd.DataFrame(
        {
            "Timestamp": ts.strftime("%m/%d/%Y %H:%M"),
            "Libre GL": 110.0 + 20.0 * np.sin(np.arange(n) / 200.0) if libre else np.nan,
            "Dexcom GL": 112.0 + 20.0 * np.sin(np.arange(n) / 200.0),
            "HR": 70.0,
            "Calories (Activity)": 1.1,
            "Mets": 10.0,
            "Meal Type": None,
            "Calories": np.nan,
            "Carbs": np.nan,
            "Protein": np.nan,
            "Fat": np.nan,
            "Fiber": np.nan,
            "Amount Consumed": np.nan,
            "Image Path": None,
        }
    )
    df.loc[60, ["Meal Type", "Calories", "Carbs", "Protein", "Fat", "Fiber", "Amount Consumed"]] = [
        "Breakfast",
        400,
        60,
        20,
        10,
        5,
        50,
    ]
    df.loc[360, ["Meal Type", "Calories", "Carbs", "Protein", "Fat", "Fiber"]] = ["Lunch", 700, 80, 30, 25, 9]
    df.loc[400:430, "Mets"] = 45.0
    folder = root / f"CGMacros-{number:03d}"
    folder.mkdir(parents=True)
    df.to_csv(folder / f"CGMacros-{number:03d}.csv", index=False)


@pytest.fixture
def root(tmp_path):
    _write_participant(tmp_path, 1)
    _write_participant(tmp_path, 2, libre=False)
    pd.DataFrame(
        {
            "subject": [1, 2],
            "Age": [50, 61],
            "Gender": ["F", "M"],
            "BMI": [31.0, 27.0],
            "Body weight ": [200.0, 180.0],
            "Height ": [65, 70],
            "A1c PDL (Lab)": [7.1, 5.4],
            "Fasting GLU - PDL (Lab)": [140, 92],
            "Insulin ": [18.0, 6.0],
        }
    ).to_csv(tmp_path / "bio.csv", index=False)
    return tmp_path


def test_bio_headers_are_stripped_and_indexed_by_participant(root):
    bio = load_bio(root)
    assert "Body weight" in bio.columns and list(bio.index) == [1, 2]


def test_participant_becomes_a_valid_recording(root):
    rec = load_all(root)[0]
    assert rec.rec_id == "cgmacros-001" and rec.n_min == 2 * 1440
    assert rec.start == pd.Timestamp("2025-03-01 07:00")
    assert len(rec.cgm) == 2 * 96  # Libre thinned to one reading per 15 minutes
    assert len(rec.cgm_ref) == 2 * 288  # Dexcom at 5 minutes
    assert rec.static["primary_sensor"] == "libre" and rec.static["group"] == "t2d"
    assert rec.static["weight_kg"] == pytest.approx(90.72, abs=0.01)
    assert rec.static["fasting_insulin_uu_ml"] == 18.0


def test_meals_are_scaled_by_the_fraction_eaten(root):
    meals = load_all(root)[0].meals
    assert meals["t_min"].tolist() == [60.0, 360.0]
    assert meals["carb_g"].tolist() == [30.0, 80.0]  # half of the breakfast was eaten; lunch has no figure
    assert meals["fibre_g"].tolist() == [2.5, 9.0]


def test_mets_are_divided_by_ten(root):
    act = load_all(root)[0].activity
    assert act["met"].min() == 1.0 and act["met"].max() == 4.5


def test_dexcom_is_used_when_libre_is_missing(root):
    rec = load_all(root)[1]
    assert rec.static["primary_sensor"] == "dexcom" and rec.static["group"] == "healthy"
    assert len(rec.cgm) == 2 * 96 and rec.cgm_ref.empty


def test_loaded_recording_feeds_the_twin(root):
    inp, obs_idx, _ = build_inputs(load_all(root)[0])
    assert inp.meal_t.shape[0] == 3 and float(inp.met.max()) == 4.5 and len(obs_idx) == 192


def test_missing_download_says_what_to_run(tmp_path):
    with pytest.raises(FileNotFoundError, match="chhaya.data.download"):
        load_all(tmp_path)
````

- [ ] **Step 2: Run them and see them fail**

Run: `uv run pytest tests/test_download.py tests/test_cgmacros.py -q`
Expected: `ModuleNotFoundError: No module named 'chhaya.data.download'`.

- [ ] **Step 3: Write `src/chhaya/data/download.py`**

Checksums are the ones published by Figshare (MD5) and PhysioNet (`SHA256SUMS.txt`).

````python
"""Fetch the open datasets. Nothing here is ever committed or redistributed.

Usage: python -m chhaya.data.download shanghai cgmacros
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

import requests

from chhaya.config import RAW_DIR

SOURCES = {
    "shanghai": {
        "url": "https://ndownloader.figshare.com/files/42966622",
        "file": "diabetes_datasets.zip",
        "algo": "md5",
        "digest": "4bfb61cfa506b48155fd9e841ee48e21",
        "license": "CC BY 4.0 (Zhao et al., Sci Data 2023, doi:10.6084/m9.figshare.c.6310860)",
    },
    "cgmacros": {
        "url": "https://physionet.org/files/cgmacros/1.0.0/CGMacros_dateshifted365.zip",
        "file": "CGMacros_dateshifted365.zip",
        "algo": "sha256",
        "digest": "05c8b0e6f1a2757050aced55ce4bf6ab2ac9b30f2fd8ca193056812d9c621d4d",
        "license": "CC BY-NC-SA 4.0 (Das et al., PhysioNet, doi:10.13026/3z8q-x658)",
    },
}


def file_digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, algo: str, digest: str) -> None:
    got = file_digest(path, algo)
    if got != digest:
        raise ValueError(f"{path.name}: {algo} {got} does not match the published {digest}; delete it and retry")


def fetch(name: str, raw_dir: Path = RAW_DIR) -> Path:
    """Download, check the published checksum, and unpack into raw_dir/name. Safe to re-run."""
    src = SOURCES[name]
    dest = raw_dir / name
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / src["file"]
    if not archive.exists():
        print(f"downloading {name} ({src['license']})")
        with requests.get(src["url"], stream=True, timeout=60) as resp:
            resp.raise_for_status()
            tmp = archive.with_suffix(".part")
            with tmp.open("wb") as fh:
                for chunk in resp.iter_content(1 << 20):
                    fh.write(chunk)
            tmp.replace(archive)
    verify(archive, src["algo"], src["digest"])
    if not (dest / ".unpacked").exists():
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
        for inner in dest.rglob("*.zip"):
            if inner != archive:
                with zipfile.ZipFile(inner) as zf:
                    zf.extractall(inner.parent)
        (dest / ".unpacked").touch()
    return dest


if __name__ == "__main__":
    for arg in sys.argv[1:] or list(SOURCES):
        print(fetch(arg))
````

- [ ] **Step 4: Write `src/chhaya/data/cgmacros.py`**

````python
"""CGMacros (PhysioNet, CC BY-NC-SA 4.0): two CGMs, Fitbit, meal macros, 45 people, 10 days.

Column names below are taken from the dataset's own data dictionaries.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RAW_DIR
from chhaya.data.schema import ACTIVITY_COLS, CGM_COLS, MEAL_COLS, Recording, empty
from chhaya.units import INCH_TO_M, LB_TO_KG

MIN_PRIMARY_READINGS = 96  # one day of 15-minute readings


def _strip(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
    return df


def load_bio(root: Path) -> pd.DataFrame:
    """Demographics and labs, indexed by participant number."""
    path = next(iter(sorted(root.rglob("bio.csv"))), None)
    if path is None:
        raise FileNotFoundError(f"bio.csv not found under {root}; run python -m chhaya.data.download cgmacros")
    bio = _strip(pd.read_csv(path))
    id_col = next((c for c in bio.columns if re.search(r"subject|participant|^id$", c, re.I)), bio.columns[0])
    return bio.set_index(bio[id_col].astype(int))


def _num(row: pd.Series | None, prefix: str) -> float:
    """First column starting with `prefix`, as a float; NaN when absent or unparseable."""
    if row is None:
        return float("nan")
    for col, val in row.items():
        if str(col).lower().startswith(prefix.lower()):
            return float(pd.to_numeric(val, errors="coerce"))
    return float("nan")


def _static(row: pd.Series | None) -> dict:
    hba1c = _num(row, "A1c")
    group = None if np.isnan(hba1c) else "healthy" if hba1c < 5.7 else "prediabetes" if hba1c <= 6.4 else "t2d"
    sex = None if row is None else next((str(v) for c, v in row.items() if str(c).lower() == "gender"), None)
    return {
        "age": _num(row, "Age"),
        "sex": sex,
        "bmi": _num(row, "BMI"),
        "weight_kg": _num(row, "Body weight") * LB_TO_KG,
        "height_m": _num(row, "Height") * INCH_TO_M,
        "hba1c_pct": hba1c,
        "fasting_glucose_mgdl": _num(row, "Fasting GLU"),
        "fasting_insulin_uu_ml": _num(row, "Insulin"),
        "triglycerides_mgdl": _num(row, "Triglycerides"),
        "hdl_mgdl": _num(row, "HDL"),
        "group": group,
    }


def _thin(df: pd.DataFrame, col: str, step: int) -> pd.DataFrame:
    """One reading per `step`-minute bin, so a sensor interpolated to 1 minute is not over-weighted."""
    if col not in df.columns:
        return empty(CGM_COLS)
    d = df.loc[df[col].notna(), ["t_min", col]]
    d = d[(d[col] >= 20) & (d[col] <= 600)]
    d = d.groupby(d["t_min"] // step, sort=True).first()
    return d.rename(columns={col: "glucose_mgdl"}).astype({"t_min": int, "glucose_mgdl": float}).reset_index(drop=True)


def load_recording(csv_path: Path, bio_row: pd.Series | None) -> Recording | None:
    """Parse one participant file. Returns None when neither sensor has a day of data."""
    df = _strip(pd.read_csv(csv_path))
    df["ts"] = pd.to_datetime(df["Timestamp"], format="mixed", errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")
    start = df["ts"].iloc[0].floor("min")
    df["t_min"] = ((df["ts"] - start).dt.total_seconds() // 60).astype(int)
    df = df.drop_duplicates("t_min")
    n_min = int(df["t_min"].iloc[-1]) + 1

    libre, dexcom = _thin(df, "Libre GL", 15), _thin(df, "Dexcom GL", 5)
    static = _static(bio_row)
    if len(libre) >= MIN_PRIMARY_READINGS:
        cgm, ref, static["primary_sensor"] = libre, dexcom, "libre"
    elif len(dexcom) >= MIN_PRIMARY_READINGS * 3:
        cgm, ref, static["primary_sensor"] = _thin(df, "Dexcom GL", 15), empty(CGM_COLS), "dexcom"
    else:
        return None

    m = df[df["Meal Type"].notna() & df["Carbs"].notna()] if "Meal Type" in df.columns else df.iloc[:0]
    frac = (pd.to_numeric(m.get("Amount Consumed"), errors="coerce").fillna(100.0).clip(0.0, 100.0) / 100.0).to_numpy()
    meals = pd.DataFrame(
        {
            "t_min": m["t_min"].to_numpy(dtype=float),
            "carb_g": m["Carbs"].to_numpy(dtype=float) * frac,
            "protein_g": m["Protein"].to_numpy(dtype=float) * frac,
            "fat_g": m["Fat"].to_numpy(dtype=float) * frac,
            "fibre_g": m["Fiber"].to_numpy(dtype=float) * frac,
            "label": m["Meal Type"].astype(str).to_numpy(),
        },
        columns=MEAL_COLS,
    )

    a = df[df["Mets"].notna()] if "Mets" in df.columns else df.iloc[:0]
    activity = pd.DataFrame(
        {
            "t_min": a["t_min"].to_numpy(dtype=float),
            "met": a["Mets"].to_numpy(dtype=float) / 10.0,  # the file stores METs multiplied by 10
            "hr": pd.to_numeric(a.get("HR"), errors="coerce").to_numpy(dtype=float),
        },
        columns=ACTIVITY_COLS,
    )

    number = int(re.search(r"(\d+)", csv_path.stem).group(1))
    rec = Recording(
        rec_id=f"cgmacros-{number:03d}",
        patient_id=f"cgmacros-{number:03d}",
        dataset="cgmacros",
        start=start,
        n_min=n_min,
        cgm=cgm,
        cgm_ref=ref,
        meals=meals,
        activity=activity,
        static=static,
    )
    rec.validate()
    return rec


def load_all(root: Path = RAW_DIR / "cgmacros") -> list[Recording]:
    bio = load_bio(root)
    recs = []
    for path in sorted(root.rglob("CGMacros-*.csv")):
        number = int(re.search(r"(\d+)", path.stem).group(1))
        rec = load_recording(path, bio.loc[number] if number in bio.index else None)
        if rec is not None:
            recs.append(rec)
    if not recs:
        raise FileNotFoundError(f"no CGMacros-*.csv under {root}; run python -m chhaya.data.download cgmacros")
    return recs
````

- [ ] **Step 5: Run the tests, then start both downloads**

Run: `uv run pytest tests/test_download.py tests/test_cgmacros.py -q`
Expected: `9 passed`.

Run (in the background; CGMacros is 627 MB): `uv run python -m chhaya.data.download shanghai cgmacros`
Expected: two directory paths printed. A checksum mismatch raises `ValueError` naming the file — delete it and re-run.

- [ ] **Step 6: Lint and commit**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/data/download.py src/chhaya/data/cgmacros.py tests/test_download.py tests/test_cgmacros.py
git commit -m "feat: dataset download with checksums and CGMacros loader"
```

---

### Task 8: The ShanghaiT2DM loader

**Files:**
- Create: `src/chhaya/data/shanghai.py`
- Test: `tests/test_shanghai.py`

**Interfaces:**
- Consumes: `Recording`, `CGM_COLS`, `MEAL_COLS`, `DOSE_COLS`; `config.RAW_DIR`; `units.MGDL_PER_MMOL`, `hba1c_ifcc_to_percent`, `insulin_pmol_to_uu_ml`
- Produces: `chhaya.data.shanghai.SERIES, SUMMARY: dict[str, str]` (field → header pattern), `match_columns(columns, patterns) -> dict[str, str]`, `load_summary(root) -> DataFrame`, `load_recording(path, summary_row) -> Recording | None` (raises `ValueError` listing the headers when no date or CGM column is found), `load_all(root=RAW_DIR / "shanghai") -> list[Recording]`, `food_strings(recs) -> pd.Series` (diet text → count)
- Static keys produced: `age, sex, weight_kg, bmi, diabetes_duration_y, fasting_glucose_mgdl, fasting_insulin_uu_ml, fasting_cpeptide_nmol, hba1c_pct, egfr, agents, hypoglycemia_history, group`

What is known from the dataset paper: one workbook per recording, named `<patient>_<period>_<start date>`, in a folder `Shanghai_T2DM`, with fields Date, CGM (every 15 min), CBG (fingerstick), blood ketone, dietary intake (free text of weighed foods), subcutaneous and intravenous insulin, non-insulin agents, pump bolus and basal; and a summary sheet `Shanghai_T2DM_Summary` with one row per workbook. What is **not** known is the exact header spelling and the summary's units for insulin — the patterns in `SERIES` and `SUMMARY` and the pmol/L assumption are best guesses to be confirmed in Task 9. Meals are loaded as text with empty macro columns; the food table that fills them is roadmap item 3.1.

- [ ] **Step 1: Write the failing test `tests/test_shanghai.py`**

Save the file as UTF-8 — it contains the Chinese header `饮食`.

````python
import numpy as np
import pandas as pd
import pytest

from chhaya.data.shanghai import food_strings, load_all, match_columns


@pytest.fixture
def root(tmp_path):
    folder = tmp_path / "Shanghai_T2DM"
    folder.mkdir()
    n = 3 * 96
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2021-07-01 08:00", periods=n, freq="15min"),
            "CGM (mg / dl)": 150.0 + 30.0 * np.sin(np.arange(n) / 10.0),
            "CBG (mg / dl)": np.nan,
            "Blood Ketone (mmol / L)": np.nan,
            "Dietary intake": None,
            "饮食": None,
            "Insulin dose - s.c.": None,
            "Non-insulin hypoglycemic agents": None,
            "CSII - bolus insulin (Novolin R, IU)": np.nan,
            "CSII - basal insulin (Novolin R, IU / H)": np.nan,
            "Insulin dose - i.v.": None,
        }
    )
    df.loc[[2, 50], "CBG (mg / dl)"] = [171.0, 142.2]
    df.loc[1, "Dietary intake"] = "rice 100 g, pork 50 g"
    df.loc[20, "Dietary intake"] = "noodles 150 g"
    df.loc[40, "Dietary intake"] = "rice 100 g, pork 50 g"
    df.loc[1, "Non-insulin hypoglycemic agents"] = "metformin 0.5 g"
    df.loc[30, "Insulin dose - s.c."] = "Novolin 30R, 12 IU"
    df.to_excel(folder / "2001_0_20210701.xlsx", index=False)
    pd.DataFrame(
        {
            "Patient Number": ["2001_0_20210701"],
            "Gender (Female=1, Male=2)": [2],
            "Age (years)": [63],
            "Weight (kg)": [68.0],
            "BMI (kg/m2)": [24.1],
            "Duration of Diabetes (years)": [11],
            "Hypoglycemic Agents": ["metformin, glimepiride"],
            "Fasting Plasma Glucose (mg/dl)": [158.4],
            "Fasting Insulin (pmol/L)": [72.0],
            "HbA1c (mmol/mol)": [69],
            "Estimated Glomerular Filtration Rate  (ml/min/1.73m2) ": [58.0],
            "Hypoglycemia (yes/no)": ["no"],
        }
    ).to_excel(tmp_path / "Shanghai_T2DM_Summary.xlsx", index=False)
    return tmp_path


def test_headers_are_matched_by_pattern_not_exact_spelling():
    cols = ["Date", "CGM (mg / dl)", "CBG (mg / dl)", "Insulin dose - s.c.", "Insulin dose - i.v.", "饮食"]
    found = match_columns(
        cols, {"cgm": r"^cgm", "ins_sc": r"insulin dose.*s\.?\s*c", "diet_zh": r"饮食", "x": r"^nope"}
    )
    assert found == {"cgm": "CGM (mg / dl)", "ins_sc": "Insulin dose - s.c.", "diet_zh": "饮食"}


def test_recording_carries_both_streams(root):
    (rec,) = load_all(root)
    assert rec.rec_id == "shanghai-2001_0_20210701" and rec.patient_id == "shanghai-2001"
    assert len(rec.cgm) == 288 and rec.n_min == 287 * 15 + 1
    assert rec.fingersticks["glucose_mgdl"].tolist() == [171.0, 142.2]
    assert rec.fingersticks["t_min"].tolist() == [30, 750]
    assert rec.meals["label"].tolist() == ["rice 100 g, pork 50 g", "noodles 150 g", "rice 100 g, pork 50 g"]
    assert rec.meals["carb_g"].isna().all()  # macros arrive with the food table
    assert sorted(rec.doses["route"]) == ["oral", "sc"]


def test_record_units_are_converted(root):
    static = load_all(root)[0].static
    assert static["sex"] == "M" and static["age"] == 63.0
    assert static["fasting_insulin_uu_ml"] == pytest.approx(12.0)
    assert static["hba1c_pct"] == pytest.approx(8.46, abs=0.01)
    assert static["egfr"] == 58.0 and static["agents"] == "metformin, glimepiride"


def test_food_strings_are_counted_for_the_macro_table(root):
    foods = food_strings(load_all(root))
    assert foods.to_dict() == {"rice 100 g, pork 50 g": 2, "noodles 150 g": 1}


def test_sheet_in_mmol_is_converted(root):
    path = root / "Shanghai_T2DM" / "2001_0_20210701.xlsx"
    df = pd.read_excel(path)
    df["CGM (mg / dl)"] = df["CGM (mg / dl)"] / 18.016
    df.to_excel(path, index=False)
    assert 100.0 < load_all(root)[0].cgm["glucose_mgdl"].median() < 200.0


def test_recording_without_summary_row_still_loads(root):
    (root / "Shanghai_T2DM" / "2001_0_20210701.xlsx").rename(root / "Shanghai_T2DM" / "2999_0_20210701.xlsx")
    (rec,) = load_all(root)
    assert rec.static == {"group": "t2d"}


def test_workbook_without_a_cgm_column_names_the_headers_it_found(root):
    path = root / "Shanghai_T2DM" / "2001_0_20210701.xlsx"
    pd.read_excel(path).rename(columns={"CGM (mg / dl)": "Glucose"}).to_excel(path, index=False)
    with pytest.raises(ValueError, match="no date/CGM column among .*Glucose"):
        load_all(root)
````

- [ ] **Step 2: Run it and see it fail**

Run: `uv run pytest tests/test_shanghai.py -q`
Expected: `ModuleNotFoundError: No module named 'chhaya.data.shanghai'`.

- [ ] **Step 3: Write `src/chhaya/data/shanghai.py`**

````python
"""ShanghaiT2DM (Figshare, CC BY 4.0): Libre CGM, fingersticks, diet text, drug doses, labs; 100 patients.

Workbook column names are matched by pattern because the published description gives field names
without their exact header spelling. `python -m chhaya.data.audit` prints the headers it actually found.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RAW_DIR
from chhaya.data.schema import CGM_COLS, DOSE_COLS, MEAL_COLS, Recording
from chhaya.units import MGDL_PER_MMOL, hba1c_ifcc_to_percent, insulin_pmol_to_uu_ml

SERIES = {
    "ts": r"^date",
    "cgm": r"^cgm",
    "cbg": r"^cbg",
    "diet_en": r"^dietary intake",
    "diet_zh": r"饮食",
    "ins_sc": r"insulin dose.*s\.?\s*c",
    "ins_iv": r"insulin dose.*i\.?\s*v",
    "agents": r"non-?insulin",
    "csii_bolus": r"csii.*bolus",
    "csii_basal": r"csii.*basal",
}
SUMMARY = {
    "age": r"^age",
    "sex_code": r"^gender",
    "weight_kg": r"^weight",
    "bmi": r"^bmi",
    "diabetes_duration_y": r"duration of diabetes",
    "fasting_glucose_mgdl": r"^fasting plasma glucose",
    "fasting_insulin_pmol": r"^fasting insulin",
    "fasting_cpeptide_nmol": r"^fasting c-?peptide",
    "hba1c_ifcc": r"^hba1c",
    "egfr": r"glomerular",
    "agents": r"^hypoglycemic agents",
    "hypoglycemia": r"^hypoglycemia",
}


def match_columns(columns, patterns: dict[str, str]) -> dict[str, str]:
    """Map each logical field to the first header matching its pattern (case-insensitive)."""
    found = {}
    for key, pat in patterns.items():
        hit = next((c for c in columns if re.search(pat, str(c).strip(), re.I)), None)
        if hit is not None:
            found[key] = hit
    return found


def load_summary(root: Path) -> pd.DataFrame:
    """Clinical summary sheet, indexed by recording file stem."""
    path = next(iter(sorted(root.rglob("Shanghai_T2DM_Summary.*"))), None)
    if path is None:
        raise FileNotFoundError(f"Shanghai_T2DM_Summary not found under {root}; run python -m chhaya.data.download shanghai")
    df = pd.read_excel(path)
    return df.set_index(df.columns[0]).rename(index=lambda s: str(s).strip())


def _static(row: pd.Series | None) -> dict:
    if row is None:
        return {"group": "t2d"}
    cols = match_columns(row.index, SUMMARY)
    num = {k: float(pd.to_numeric(row[c], errors="coerce")) for k, c in cols.items() if k not in ("agents", "hypoglycemia")}
    return {
        "age": num.get("age", np.nan),
        "sex": {1.0: "F", 2.0: "M"}.get(num.get("sex_code")),
        "weight_kg": num.get("weight_kg", np.nan),
        "bmi": num.get("bmi", np.nan),
        "diabetes_duration_y": num.get("diabetes_duration_y", np.nan),
        "fasting_glucose_mgdl": num.get("fasting_glucose_mgdl", np.nan),
        "fasting_insulin_uu_ml": insulin_pmol_to_uu_ml(num.get("fasting_insulin_pmol", np.nan)),
        "fasting_cpeptide_nmol": num.get("fasting_cpeptide_nmol", np.nan),
        "hba1c_pct": hba1c_ifcc_to_percent(num.get("hba1c_ifcc", np.nan)),
        "egfr": num.get("egfr", np.nan),
        "agents": str(row[cols["agents"]]) if "agents" in cols else None,
        "hypoglycemia_history": str(row[cols["hypoglycemia"]]) if "hypoglycemia" in cols else None,
        "group": "t2d",
    }


def _glucose(df: pd.DataFrame, col: str) -> pd.DataFrame:
    g = pd.to_numeric(df[col], errors="coerce")
    d = pd.DataFrame({"t_min": df["t_min"], "glucose_mgdl": g}).dropna()
    if len(d) and d["glucose_mgdl"].median() < 35.0:  # a sheet in mmol/L
        d["glucose_mgdl"] *= MGDL_PER_MMOL
    d = d[(d["glucose_mgdl"] >= 20) & (d["glucose_mgdl"] <= 600)]
    return d.astype({"t_min": int, "glucose_mgdl": float}).reset_index(drop=True)[CGM_COLS]


def _text_rows(df: pd.DataFrame, col: str | None) -> pd.DataFrame:
    if col is None:
        return df.iloc[:0].assign(text=pd.Series(dtype=str))
    text = df[col].astype("string").str.strip()
    keep = text.notna() & (text != "") & (text != "0")
    return df.loc[keep, ["t_min"]].assign(text=text[keep])


def load_recording(path: Path, summary_row: pd.Series | None) -> Recording | None:
    df = pd.read_excel(path)
    cols = match_columns(df.columns, SERIES)
    if "ts" not in cols or "cgm" not in cols:
        raise ValueError(f"{path.name}: no date/CGM column among {list(df.columns)}")
    df["ts"] = pd.to_datetime(df[cols["ts"]], errors="coerce")
    df = df.dropna(subset=["ts"]).sort_values("ts")
    if df.empty:
        return None
    start = df["ts"].iloc[0].floor("min")
    df["t_min"] = ((df["ts"] - start).dt.total_seconds() // 60).astype(int)
    df = df.drop_duplicates("t_min")

    cgm = _glucose(df, cols["cgm"])
    if len(cgm) < 96:
        return None
    diet = _text_rows(df, cols.get("diet_en") or cols.get("diet_zh"))
    meals = pd.DataFrame(
        {"t_min": diet["t_min"].to_numpy(dtype=float), "label": diet["text"].astype(str).to_numpy()}, columns=MEAL_COLS
    ).astype({c: float for c in MEAL_COLS[1:5]})
    doses = []
    for key, route in (("agents", "oral"), ("ins_sc", "sc"), ("ins_iv", "iv"), ("csii_bolus", "csii")):
        rows = _text_rows(df, cols.get(key))
        doses.append(pd.DataFrame({"t_min": rows["t_min"].astype(float), "drug": rows["text"].astype(str), "dose": np.nan, "route": route}))
    doses = pd.concat(doses, ignore_index=True)[DOSE_COLS].sort_values("t_min", ignore_index=True)

    stem = path.stem.strip()
    rec = Recording(
        rec_id=f"shanghai-{stem}",
        patient_id=f"shanghai-{stem.split('_')[0]}",
        dataset="shanghai",
        start=start,
        n_min=int(df["t_min"].iloc[-1]) + 1,
        cgm=cgm,
        fingersticks=_glucose(df, cols["cbg"]) if "cbg" in cols else cgm.iloc[:0],
        meals=meals,
        doses=doses,
        static=_static(summary_row),
    )
    rec.validate()
    return rec


def load_all(root: Path = RAW_DIR / "shanghai") -> list[Recording]:
    summary = load_summary(root)
    folder = next((p for p in sorted(root.rglob("Shanghai_T2DM")) if p.is_dir()), None)
    if folder is None:
        raise FileNotFoundError(f"Shanghai_T2DM folder not found under {root}")
    recs = []
    for path in sorted(folder.glob("*.xls*")):
        stem = path.stem.strip()
        rec = load_recording(path, summary.loc[stem] if stem in summary.index else None)
        if rec is not None:
            recs.append(rec)
    return recs


def food_strings(recs: list[Recording]) -> pd.Series:
    """Every distinct diet entry with its count: the worklist for the food-to-macros table."""
    labels = pd.concat([r.meals["label"] for r in recs], ignore_index=True)
    return labels.value_counts()
````

- [ ] **Step 4: Run the tests**

Run: `uv run pytest tests/test_shanghai.py -q`
Expected: `7 passed`.

- [ ] **Step 5: Lint and commit**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/data/shanghai.py tests/test_shanghai.py
git commit -m "feat: ShanghaiT2DM loader with pattern-matched headers and diet worklist"
```

---

### Task 9: Data audit and Gate 1

**Files:**
- Create: `src/chhaya/data/audit.py`
- Test: `tests/test_audit.py`
- Writes: `results/audit/cgmacros.csv`, `results/audit/shanghai.csv`, `results/audit/shanghai_food_strings.csv`, `results/audit/summary.json`, `docs/decisions/2026-10-04-gate1.md`

**Interfaces:**
- Consumes: `Recording`, `time_in_ranges`, both `load_all`, `shanghai.food_strings`, `config.RESULTS_DIR`
- Produces: `chhaya.data.audit.GATE1_MIN_RECORDINGS = 60`, `GATE1_MIN_DAYS = 3.0`, `GATE1_MIN_MEALS_PER_DAY = 2.0`, `low_events(t_min, g, threshold=70.0, min_readings=2) -> list[int]`, `audit_recording(rec) -> dict`, `audit(recs) -> DataFrame`, `gate1(shanghai_df) -> {"usable_recordings", "required", "go"}`, CLI `python -m chhaya.data.audit`

- [ ] **Step 1: Write the failing test `tests/test_audit.py`**

````python
import dataclasses

import numpy as np
import pandas as pd

from chhaya.data.audit import audit, gate1, low_events


def test_low_event_needs_two_consecutive_readings():
    t = np.arange(0, 120, 15)
    g = np.array([100, 65, 100, 60, 62, 64, 100, 66])
    assert low_events(t, g) == [45]


def test_audit_counts_what_gate1_needs(rec):
    lows = rec.cgm.copy()
    lows.loc[8:11, "glucose_mgdl"] = 60.0  # 02:00-02:45 on the first night
    sticks = pd.DataFrame({"t_min": [100, 800], "glucose_mgdl": [110.0, 190.0]})
    row = audit([dataclasses.replace(rec, cgm=lows, fingersticks=sticks)]).iloc[0]
    assert row["days"] == 6.0 and row["n_meals"] == 18 and row["meals_per_day"] == 3.0
    assert row["n_meals_with_carbs"] == 18 and row["n_fingersticks"] == 2
    assert row["n_low_events"] >= 1 and row["n_nights_with_low"] >= 1
    assert not row["on_insulin"] and row["has_fasting_insulin"]


def test_gate1_threshold():
    df = pd.DataFrame({"days": [5.0] * 60 + [2.0] * 40, "meals_per_day": [3.0] * 59 + [0.5] + [3.0] * 40})
    assert gate1(df) == {"usable_recordings": 59, "required": 60, "go": False}
    df.loc[59, "meals_per_day"] = 2.0
    assert gate1(df)["go"] is True
````

- [ ] **Step 2: Run it and see it fail**

Run: `uv run pytest tests/test_audit.py -q`
Expected: `ModuleNotFoundError: No module named 'chhaya.data.audit'`.

- [ ] **Step 3: Write `src/chhaya/data/audit.py`**

````python
"""Data truth: what is actually in the downloaded datasets. Decides Gate 1.

Usage: python -m chhaya.data.audit
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from chhaya.config import RESULTS_DIR
from chhaya.data.schema import Recording
from chhaya.eval.metrics import time_in_ranges

GATE1_MIN_RECORDINGS = 60
GATE1_MIN_DAYS = 3.0
GATE1_MIN_MEALS_PER_DAY = 2.0


def low_events(t_min: np.ndarray, g: np.ndarray, threshold: float = 70.0, min_readings: int = 2) -> list[int]:
    """Start minutes of runs of at least `min_readings` consecutive readings below `threshold`."""
    starts, run = [], 0
    for i, below in enumerate(g < threshold):
        run = run + 1 if below else 0
        if run == min_readings:
            starts.append(int(t_min[i - min_readings + 1]))
    return starts


def audit_recording(rec: Recording) -> dict:
    days = rec.n_min / 1440.0
    t = rec.cgm["t_min"].to_numpy()
    g = rec.cgm["glucose_mgdl"].to_numpy()
    lows = low_events(t, g)
    tod0 = rec.start.hour * 60 + rec.start.minute
    night_lows = {(tod0 + s) // 1440 for s in lows if (tod0 + s) % 1440 < 360}
    routes = set(rec.doses["route"]) if len(rec.doses) else set()
    return {
        "rec_id": rec.rec_id,
        "patient_id": rec.patient_id,
        "group": rec.static.get("group"),
        "days": round(days, 2),
        "n_cgm": len(rec.cgm),
        "n_ref": len(rec.cgm_ref),
        "n_fingersticks": len(rec.fingersticks),
        "fingersticks_per_day": round(len(rec.fingersticks) / days, 2),
        "n_meals": len(rec.meals),
        "meals_per_day": round(len(rec.meals) / days, 2),
        "n_meals_with_carbs": int(rec.meals["carb_g"].notna().sum()),
        "activity_minutes": len(rec.activity),
        "n_low_events": len(lows),
        "n_nights_with_low": len(night_lows),
        "on_insulin": bool(routes & {"sc", "iv", "csii"}),
        "has_fasting_insulin": bool(np.isfinite(rec.static.get("fasting_insulin_uu_ml", np.nan))),
        **{k: round(v, 1) for k, v in time_in_ranges(g).items()},
    }


def audit(recs: list[Recording]) -> pd.DataFrame:
    return pd.DataFrame([audit_recording(r) for r in recs])


def gate1(shanghai: pd.DataFrame) -> dict:
    """GO when enough Shanghai recordings are long enough and have meals logged."""
    usable = shanghai[(shanghai["days"] >= GATE1_MIN_DAYS) & (shanghai["meals_per_day"] >= GATE1_MIN_MEALS_PER_DAY)]
    return {"usable_recordings": int(len(usable)), "required": GATE1_MIN_RECORDINGS, "go": bool(len(usable) >= GATE1_MIN_RECORDINGS)}


def main(out_dir: Path = RESULTS_DIR / "audit") -> None:
    from chhaya.data import cgmacros, shanghai

    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {}
    for name, module in (("cgmacros", cgmacros), ("shanghai", shanghai)):
        recs = module.load_all()
        df = audit(recs)
        df.to_csv(out_dir / f"{name}.csv", index=False)
        summary[name] = {
            "recordings": len(df),
            "patients": int(df["patient_id"].nunique()),
            "patient_days": round(float(df["days"].sum()), 1),
            "fingersticks": int(df["n_fingersticks"].sum()),
            "meals": int(df["n_meals"].sum()),
            "meals_with_carbs": int(df["n_meals_with_carbs"].sum()),
            "low_events": int(df["n_low_events"].sum()),
            "nights_with_low": int(df["n_nights_with_low"].sum()),
            "recordings_on_insulin": int(df["on_insulin"].sum()),
            "by_group": df["group"].value_counts(dropna=False).to_dict(),
        }
        if name == "shanghai":
            summary["gate1"] = gate1(df)
            foods = shanghai.food_strings(recs)
            foods.rename_axis("text").reset_index(name="count").to_csv(out_dir / "shanghai_food_strings.csv", index=False)
            summary[name]["distinct_diet_entries"] = int(len(foods))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
````

- [ ] **Step 4: Run the tests and the whole suite**

Run: `uv run pytest -q`
Expected: `67 passed`.

- [ ] **Step 5: Commit the code**

```bash
uv run ruff check src tests && uv run ruff format --check src tests
git add src/chhaya/data/audit.py tests/test_audit.py
git commit -m "feat: dataset audit and Gate 1 check"
```

- [ ] **Step 6: First contact with the real files — look before trusting the loaders**

Wait for the Task 7 downloads to finish. Then print what is actually there:

```bash
uv run python -c "
from chhaya.config import RAW_DIR
import pandas as pd
x = sorted((RAW_DIR / 'shanghai').rglob('Shanghai_T2DM/*.xls*'))
print(len(x), 'workbooks; first:', x[0].name)
print(list(pd.read_excel(x[0]).columns))
s = sorted((RAW_DIR / 'shanghai').rglob('Shanghai_T2DM_Summary.*'))[0]
print(list(pd.read_excel(s).columns))
c = sorted((RAW_DIR / 'cgmacros').rglob('CGMacros-*.csv'))
print(len(c), 'participant files; first:', c[0])
d = pd.read_csv(c[0]); print(list(d.columns)); print(d[d['Meal Type'].notna()].head(6).to_string())
print(list(pd.read_csv(sorted((RAW_DIR / 'cgmacros').rglob('bio.csv'))[0]).columns))
"
```

Expected: 109 workbooks, 45 participant files, and five header lists. Compare each list with the patterns in `shanghai.SERIES`, `shanghai.SUMMARY` and the column names in `cgmacros.py`. Check three things by eye: the unit in the Shanghai fasting-insulin header (the loader assumes pmol/L), whether `Amount Consumed` is filled on the meal row in CGMacros, and that the first column of `bio.csv` is the participant number.

If a header does not match: add a test to `tests/test_shanghai.py` or `tests/test_cgmacros.py` that builds the fixture with the real header and fails, change the pattern or column name until it passes, and commit with a message that quotes the real header. Do not edit a pattern without a failing test first.

- [ ] **Step 7: Run the audit**

Run: `uv run python -m chhaya.data.audit`
Expected: a JSON summary with `cgmacros.recordings` near 45, `shanghai.recordings` near 109, and a `gate1` block. Files appear under `results/audit/`.

Sanity checks against the dataset paper — a mismatch means a loader bug, not a finding: Shanghai mean time-in-range across recordings should be near 77.7 %; total Shanghai CGM readings near 112,475; recording lengths between 3 and 14 days.

```bash
uv run python -c "
import pandas as pd
d = pd.read_csv('results/audit/shanghai.csv')
print('mean TIR', round(d.tir.mean(), 1), '| total CGM', d.n_cgm.sum(), '| days', d.days.min(), '-', d.days.max())
"
```

- [ ] **Step 8: Record the Gate 1 decision**

Write `docs/decisions/2026-10-04-gate1.md` with: the `gate1` block copied from `results/audit/summary.json`; the counts of fingersticks, overnight lows, recordings on insulin and distinct diet strings; any header that differed from this plan; and one line stating GO (Shanghai is the fingerstick and record cohort for Milestone 3) or NO-GO (CGMacros only, with simulated fingersticks), per the roadmap.

```bash
git add results/audit docs/decisions/2026-10-04-gate1.md
git commit -m "data: audit both datasets and record the Gate 1 decision"
```

`results/audit/shanghai_food_strings.csv` contains text from ShanghaiT2DM (CC BY 4.0, Zhao et al. 2023); the README must carry that attribution.

---

### Task 10: Gate 2 — the first real reveal

**Files:**
- Writes: `results/gate2/cgmacros/metrics.csv`, `summary.json`, `report.md`, `results/gate2/cgmacros/reveal_<rec_id>.html`, `docs/decisions/2026-10-08-gate2.md`

**Interfaces:**
- Consumes: `python -m chhaya.eval.gate2`, `run_reveal`, `cgmacros.load_all`

No new code is required if the run is clean. Code changes that the results call for follow the rule in `docs/PREREGISTRATION.md`: chosen on dev patients, claimed on test patients.

- [ ] **Step 1: Smoke run on five participants**

Run: `uv run python -m chhaya.eval.gate2 --dataset cgmacros --limit 5 --k 5 --members 50`
Expected: five lines like `cgmacros-001 k=5: 23.4`, then a summary and a verdict (NO-GO by construction with fewer than six patients). If every line says `skipped`, the recordings are shorter than six days — check `days` in `results/audit/cgmacros.csv`.

- [ ] **Step 2: Look at one patient before running the cohort**

```bash
uv run python -c "
import plotly.graph_objects as go
from chhaya.data.cgmacros import load_all
from chhaya.eval.reveal import run_reveal
rec = load_all()[0]
r = run_reveal(rec, 5)
h = r.t_test / 60
f = go.Figure()
f.add_scatter(x=h, y=r.hi, line_width=0, showlegend=False)
f.add_scatter(x=h, y=r.lo, fill='tonexty', line_width=0, name='80% band')
f.add_scatter(x=h, y=r.twin, name='twin, estimated (no sensor)')
f.add_scatter(x=h, y=r.day, name='own average day', line_dash='dot')
f.add_scatter(x=h, y=r.truth, name='hidden sensor', mode='markers', marker_size=3)
f.update_layout(title=rec.rec_id, xaxis_title='hours since start', yaxis_title='glucose, mg/dL')
f.write_html('results/gate2/cgmacros/reveal_' + rec.rec_id + '.html', include_plotlyjs='cdn')
print({k: round(v, 2) for k, v in r.metrics.items()})
"
```

Open the HTML file. Check by eye: do the twin's peaks line up in time with the hidden sensor's after meals; is the overnight level right; does the band contain most points. A twin that is flat while the sensor swings usually means meals did not load (`n_meals_with_carbs` in the audit) or METs were not divided by ten.

- [ ] **Step 3: Full run**

Run (about 40 minutes): `uv run python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7`
Expected: `results/gate2/cgmacros/report.md` with the verdict line and a three-row table (k = 3, 5, 7). `n_failed` should be 0 or close to it; read the `error` column of `metrics.csv` for any that failed.

- [ ] **Step 4: Break the result down**

```bash
uv run python -c "
import pandas as pd
d = pd.read_csv('results/gate2/cgmacros/metrics.csv').query('k_days == 5 and twin_rmse == twin_rmse')
print(d.groupby('group')[['twin_rmse', 'day_rmse', 'mean_rmse', 'twin_tir_err', 'twin_cov80', 'floor_rmse']].median().round(1))
print('worst five:'); print(d.nlargest(5, 'twin_rmse')[['rec_id', 'group', 'twin_rmse', 'day_rmse', 'twin_bias']].round(1))
"
```

Invoke the `scientific-critical-thinking` skill and the `mle-reviewer` agent on `results/gate2/cgmacros/` and `src/chhaya/eval/`. Ask specifically: is there any path by which a hidden reading reaches the estimate; is the average-day baseline given a fair chance; does the conclusion hold in the T2D group or only in healthy participants.

- [ ] **Step 5: Record the Gate 2 decision**

Write `docs/decisions/2026-10-08-gate2.md` with: the primary summary and verdict copied from `summary.json`; the by-group table; the noise floor; the failure count; what the worst five patients have in common; and the decision — GO (proceed to Milestone 3 with the reveal as headline), ITERATE (list the specific changes to try on dev patients before Thursday 8 Oct, each with the reason the data gives for it), or NO-GO (Night Watch headline).

```bash
git add results/gate2 docs/decisions/2026-10-08-gate2.md
git commit -m "results: first sensor-off reveal on CGMacros and the Gate 2 decision"
```

- [ ] **Step 6: Merge**

Use the `superpowers:finishing-a-development-branch` skill to bring `core-twin` into `main`.

---

## After this plan

Gate 2's decision record names the headline. The next plan — Milestone 3 in the roadmap — is written from that record: the food table, the learned record-to-prior map and the sensor-days-saved experiment, fingerstick assimilation, band recalibration, the hybrid corrector, and adverse-event prediction.
