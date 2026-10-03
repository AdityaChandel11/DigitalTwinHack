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
