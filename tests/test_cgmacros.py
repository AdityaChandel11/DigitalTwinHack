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
