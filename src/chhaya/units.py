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
