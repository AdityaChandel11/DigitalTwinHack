"""The recording of the synthetic demo patient, "Mrs. R." (rule 7: synthetic in code, in files and on screen).

She is simulated by the twin itself with known parameters, as the test fixtures are, and then handed to the
real pipeline like any other recording: nothing downstream knows she is not a patient. Her story is built in
on purpose and stated on screen: a five-day sensor wear, then six days without it; meals logged, though what
she ate differs a little from the log and one evening snack is never logged; six fingersticks a day on a meter
that reads above the sensor; basal insulin started on the second day after the sensor, after which her glucose
runs lower; and one night on which the sensor reads low and no fingerstick agrees.
"""

from __future__ import annotations

import dataclasses

import jax.numpy as jnp
import numpy as np
import pandas as pd

from chhaya.config import SEED
from chhaya.data.schema import DOSE_COLS, MEAL_COLS, Recording
from chhaya.twin.inputs import build_inputs
from chhaya.twin.model import default_z, simulate_jit
from chhaya.units import mmol_to_mgdl

WEAR_DAYS = 5.0
HIDDEN_DAYS = 6
START = pd.Timestamp("2026-09-27 00:00")
Z_TRUE = default_z() + np.array([0.25, -0.6, -0.5, 0.08, 0.5, 0.3, -0.45])  # close to the fixtures' patient
DRIFT_MMOL = 1.5  # how far her basal glucose falls once basal insulin is on board
CHANGE_DAY = 2  # the day since the sensor on which basal insulin starts, at 22:00
MEAL_PLAN = (("breakfast", 460, 45.0), ("lunch", 790, 70.0), ("snack", 1005, 20.0), ("dinner", 1210, 60.0))
STICK_TIMES = (420, 585, 770, 915, 1190, 1330)  # six a day, as in the cohort the prompt was tested on
SENSOR_FROM_METER = (-6.0, 0.92)  # sensor = a + b x meter: her sensor reads lower, as Shanghai's did
SENSOR_SD, METER_SD = 6.0, 5.0  # mg/dL
ARTEFACT = (200, 30.0, 58.0)  # the last night: minute of the night, width in minutes, the reading it falls to


def _meals(rng: np.random.Generator, days: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """What she logged, and what she ate: amounts and times a little off, and an evening snack she never logs."""
    logged, eaten = [], []
    for d in range(days):
        for label, minute, carbs in MEAL_PLAN:
            t = float(d * 1440 + minute + 5 * rng.integers(-3, 4))
            c = float(np.round(carbs * rng.uniform(0.85, 1.15) / 5.0) * 5.0)
            macros = {"protein_g": float(rng.uniform(8, 28)), "fat_g": float(rng.uniform(6, 24))}
            row = {"t_min": t, "carb_g": c, **macros, "fibre_g": float(rng.uniform(1, 8)), "label": label}
            logged.append(row)
            eaten.append(
                {**row, "t_min": t + float(rng.integers(-10, 11)), "carb_g": c * rng.uniform(0.8, 1.25)}
            )
        if d % 2 == 1:
            eaten.append(
                {"t_min": float(d * 1440 + 1310), "carb_g": 18.0, "protein_g": 3.0, "fat_g": 6.0, "fibre_g": 1.0, "label": "snack"}
            )  # fmt: skip
    as_frame = lambda rows: pd.DataFrame(rows, columns=MEAL_COLS).sort_values("t_min", ignore_index=True)  # noqa: E731
    return as_frame(logged), as_frame(eaten)


def mrs_r(seed: int = SEED) -> Recording:
    rng = np.random.default_rng(seed)
    days = int(WEAR_DAYS) + HIDDEN_DAYS
    n_min, split = days * 1440, int(WEAR_DAYS * 1440)
    logged, eaten = _meals(rng, days)
    met = np.ones(n_min)
    for d in range(days):
        met[d * 1440 + 1080 : d * 1440 + 1120] = 3.5  # an evening walk
    activity = pd.DataFrame({"t_min": np.arange(n_min, dtype=float), "met": met, "hr": 72.0})
    fasting = float(mmol_to_mgdl(np.exp(Z_TRUE[3])))
    static = {
        "age": 58.0,
        "sex": "F",
        "weight_kg": 68.0,
        "bmi": 27.1,
        "diabetes_duration_y": 9.0,
        "hba1c_pct": 8.1,
        "fasting_glucose_mgdl": fasting,
        "fasting_insulin_uu_ml": 12.0,
        "agents": "metformin; insulin glargine, started after the sensor wear",
        "group": "t2d",
        "synthetic": True,
        "genetic_marker": "synthetic field",
    }
    t15 = np.arange(0, n_min, 15)
    shell = Recording(
        rec_id="mrs-r",
        patient_id="mrs-r",
        dataset="synthetic",
        start=START,
        n_min=n_min,
        cgm=pd.DataFrame({"t_min": t15, "glucose_mgdl": np.full(t15.size, fasting)}),
        static=static,
        meals=eaten,
        activity=activity,
    )
    inp, _, _ = build_inputs(shell)
    z_after = Z_TRUE.copy()
    z_after[3] = np.log(np.exp(Z_TRUE[3]) - DRIFT_MMOL)
    before = np.asarray(simulate_jit(jnp.asarray(Z_TRUE), inp).gi)
    after = np.asarray(simulate_jit(jnp.asarray(z_after), inp).gi)
    started = split + (CHANGE_DAY - 1) * 1440 + 22 * 60
    weight = np.clip((np.arange(n_min) - started) / 1440.0, 0.0, 1.0)  # the new level arrives over a day
    truth = np.asarray(mmol_to_mgdl((1.0 - weight) * before + weight * after))

    minute, width, floor = ARTEFACT
    centre = (days - 1) * 1440 + minute
    dip = (truth[centre] - floor) * np.exp(-(((t15 - centre) / width) ** 2))  # the sensor's own artefact
    sensor = np.clip(truth[t15] + rng.normal(0.0, SENSOR_SD, t15.size) - dip, 40.0, 400.0)
    cgm = pd.DataFrame({"t_min": t15, "glucose_mgdl": sensor})

    a, b = SENSOR_FROM_METER
    stick_t = np.array([d * 1440 + m + 5 * rng.integers(-2, 3) for d in range(days) for m in STICK_TIMES])
    meter = np.round((truth[stick_t] - a) / b + rng.normal(0.0, METER_SD, stick_t.size))
    sticks = pd.DataFrame({"t_min": stick_t, "glucose_mgdl": meter})

    doses = [(d * 1440 + m, "metformin", np.nan, "oral") for d in range(days) for m in (480, 1200)]
    doses += [(float(t), "insulin glargine", np.nan, "sc") for t in range(started, n_min, 1440)]
    dose_table = pd.DataFrame(doses, columns=DOSE_COLS).astype({"t_min": float})
    dose_table = dose_table.sort_values("t_min", ignore_index=True)
    return dataclasses.replace(shell, cgm=cgm, fingersticks=sticks, meals=logged, doses=dose_table)
