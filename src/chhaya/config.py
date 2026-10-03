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
