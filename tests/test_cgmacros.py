import numpy as np
import pandas as pd
import pytest

from chhaya.data.cgmacros import load_all, load_bio
from chhaya.twin.inputs import build_inputs


def _write_participant(root, number: int, days: int = 2, libre: bool = True, variant: str = "full"):
    """A participant file shaped like the real ones, on a 1-minute grid.

    variant "full": has METs and Amount Consumed. variant "sparse": the real-world gaps seen in 11 of 45 files
    (no METs, an Intensity category instead, no Amount Consumed, odd meal labels).
    """
    n = days * 1440
    ts = pd.date_range("2025-03-01 07:00", periods=n, freq="min")
    rest_kcal, ex_kcal = 1.512, 6.804  # 1.0 and 4.5 METs for a 90.72 kg participant
    df = pd.DataFrame(
        {
            "Unnamed: 0": np.arange(n),
            "Timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "Libre GL": 110.0 + 20.0 * np.sin(np.arange(n) / 200.0) if libre else np.nan,
            "Dexcom GL": 112.0 + 20.0 * np.sin(np.arange(n) / 200.0),
            "HR": 70.0,
            "Calories (Activity)": rest_kcal,
            "METs": 10.0,
            "Intensity": 0,
            "Meal Type": None,
            "Calories": np.nan,
            "Carbs": np.nan,
            "Protein": np.nan,
            "Fat": np.nan,
            "Fiber": np.nan,
            "Amount Consumed": np.nan,
            "Image path": None,
        }
    )
    sparse = variant == "sparse"
    labels = ("Snacks", "snack 1") if sparse else ("Breakfast", "Lunch")
    df.loc[60, ["Meal Type", "Calories", "Carbs", "Protein", "Fat", "Fiber", "Amount Consumed"]] = [
        labels[0],
        400,
        60,
        20,
        10,
        5,
        50,
    ]
    df.loc[360, ["Meal Type", "Calories", "Carbs", "Protein", "Fat", "Fiber"]] = [
        labels[1],
        700,
        80,
        30,
        25,
        9,
    ]
    df.loc[400:430, "METs"] = 45.0
    df.loc[400:430, "Calories (Activity)"] = ex_kcal
    if variant == "fraction":
        # 8 of 45 real files write 1.0 for a whole meal; values above 1 count the items on the plate
        df.loc[60, "Amount Consumed"] = 0.5
        df.loc[360, "Amount Consumed"] = 1.0
        df.loc[700, ["Meal Type", "Calories", "Carbs", "Protein", "Fat", "Fiber", "Amount Consumed"]] = [
            "dinner",
            500,
            50,
            20,
            15,
            4,
            3.0,
        ]
    if variant == "counts":
        df.loc[60, "Amount Consumed"] = 100.0
        df.loc[360, "Amount Consumed"] = 400.0
    if sparse:
        df = df.drop(columns=["METs", "Amount Consumed"])
    else:
        df = df.drop(columns=["Intensity"])
    folder = root / f"CGMacros-{number:03d}"
    folder.mkdir(parents=True)
    df.to_csv(folder / f"CGMacros-{number:03d}.csv", index=False)


@pytest.fixture
def root(tmp_path):
    _write_participant(tmp_path, 1)
    _write_participant(tmp_path, 2, libre=False)
    _write_participant(tmp_path, 3, variant="sparse")
    _write_participant(tmp_path, 4, variant="fraction")
    _write_participant(tmp_path, 5, variant="counts")
    pd.DataFrame(
        {
            "subject": [1, 2, 3, 4, 5],
            "Age": [50, 61, 44, 39, 52],
            "Gender": ["F", "M", "F", "M", "F"],
            "BMI": [31.0, 27.0, 33.0, 29.0, 30.0],
            "Body weight ": [200.0, 180.0, 250.0, 200.0, 200.0],
            "Height ": [65, 70, 64, 68, 66],
            "A1c PDL (Lab)": [7.1, 5.4, 6.9, 6.0, 5.2],
            "Fasting GLU - PDL (Lab)": [140, 92, 131, 104, 90],
            "Insulin ": [18.0, 6.0, 15.0, 9.0, 5.0],
        }
    ).to_csv(tmp_path / "bio.csv", index=False)
    return tmp_path


def test_bio_headers_are_stripped_and_indexed_by_participant(root):
    bio = load_bio(root)
    assert "Body weight" in bio.columns and list(bio.index) == [1, 2, 3, 4, 5]


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


def test_file_with_mets_says_so(root):
    assert load_all(root)[0].static["activity_source"] == "mets"


def test_file_without_mets_derives_them_from_activity_calories(root):
    rec = load_all(root)[2]  # participant 3 has Intensity instead of METs
    assert rec.static["activity_source"] == "derived_from_activity_calories"
    assert rec.activity["met"].min() == pytest.approx(1.0, abs=0.01)
    assert rec.activity["met"].max() == pytest.approx(4.5, abs=0.01)


def test_missing_amount_consumed_means_the_whole_meal_was_eaten(root):
    assert load_all(root)[2].meals["carb_g"].tolist() == [60.0, 80.0]


def test_meal_labels_are_normalised_across_files(root):
    assert load_all(root)[0].meals["label"].tolist() == ["breakfast", "lunch"]
    assert load_all(root)[2].meals["label"].tolist() == ["snack", "snack"]


def test_unnamed_index_column_is_ignored(root):
    assert len(load_all(root)[2].cgm) == 2 * 96


def test_amount_consumed_on_a_fraction_scale_is_not_read_as_percent(root):
    # 0.5 is half the breakfast, 1.0 the whole lunch, and 3.0 counts three items on the dinner plate
    rec = load_all(root)[3]
    assert rec.meals["carb_g"].tolist() == [30.0, 80.0, 50.0]
    assert rec.static["amount_consumed_unit"] == "fraction"


def test_amount_consumed_above_a_whole_meal_is_an_item_count_not_a_multiplier(root):
    assert load_all(root)[4].meals["carb_g"].tolist() == [60.0, 80.0]


def _edit(root, number, change):
    path = root / f"CGMacros-{number:03d}" / f"CGMacros-{number:03d}.csv"
    change(pd.read_csv(path)).to_csv(path, index=False)


def test_sensor_tokens_such_as_lo_and_hi_are_treated_as_missing(root):
    def tokens(d):
        d["Libre GL"] = d["Libre GL"].astype(object)
        d.loc[100:130, "Libre GL"] = "LO"
        d.loc[900:930, "Libre GL"] = "HI"
        return d

    _edit(root, 1, tokens)
    rec = load_all(root)[0]
    assert rec.static["primary_sensor"] == "libre" and 185 <= len(rec.cgm) < 192


def test_sensor_column_that_is_not_numeric_is_an_error_not_a_silent_switch_of_sensor(root):
    _edit(
        root, 1, lambda d: d.assign(**{"Libre GL": d["Libre GL"].map(lambda v: f"{v:.1f}".replace(".", ","))})
    )
    with pytest.raises(ValueError, match="CGMacros-001.csv.*Libre GL.*not numeric"):
        load_all(root)


def test_file_without_a_timestamp_column_names_the_headers_it_found(root):
    _edit(root, 1, lambda d: d.rename(columns={"Timestamp": "Time"}))
    with pytest.raises(ValueError, match="CGMacros-001.csv.*no Timestamp column among .*Time"):
        load_all(root)


def test_empty_or_undated_participant_file_is_skipped(root):
    _edit(root, 1, lambda d: d.iloc[:0])
    _edit(root, 3, lambda d: d.assign(Timestamp="not a date"))
    assert [r.rec_id for r in load_all(root)] == ["cgmacros-002", "cgmacros-004", "cgmacros-005"]


def test_files_present_but_none_usable_is_reported_as_such(root):
    for number in range(1, 6):
        _edit(root, number, lambda d: d.iloc[:0])
    with pytest.raises(ValueError, match="none of the 5 participant files"):
        load_all(root)


def test_zero_body_weight_in_the_record_is_treated_as_missing(root):
    bio = pd.read_csv(root / "bio.csv")
    bio.loc[0, "Body weight "] = 0.0
    bio.to_csv(root / "bio.csv", index=False)
    assert np.isnan(load_all(root)[0].static["weight_kg"])


def test_activity_is_derived_without_needing_a_body_weight(root):
    # Stored METs equal activity calories divided by the participant's own resting rate, in every real file
    # that has both columns; body weight does not enter.
    bio = pd.read_csv(root / "bio.csv")
    bio.loc[2, "Body weight "] = np.nan
    bio.to_csv(root / "bio.csv", index=False)
    rec = load_all(root)[2]
    assert rec.static["activity_source"] == "derived_from_activity_calories"
    assert rec.activity["met"].min() == pytest.approx(1.0, abs=0.01)
    assert rec.activity["met"].max() == pytest.approx(4.5, abs=0.01)


def test_amount_consumed_of_zero_means_not_recorded_so_the_meal_counts_in_full(root):
    # In the real files, glucose rises after "0 % eaten" meals just as it does after whole meals.
    _edit(root, 1, lambda d: d.assign(**{"Amount Consumed": d["Amount Consumed"].where(d.index != 60, 0.0)}))
    assert load_all(root)[0].meals["carb_g"].tolist() == [60.0, 80.0]


def test_fraction_file_dominated_by_item_counts_is_still_read_as_fractions(root):
    _edit(root, 4, lambda d: d.assign(**{"Amount Consumed": d["Amount Consumed"].where(d.index != 360, 4.0)}))
    rec = load_all(root)[
        3
    ]  # amounts are now 0.5, 4 and 3: mostly item counts, yet still the fraction convention
    assert rec.static["amount_consumed_unit"] == "fraction"
    assert rec.meals["carb_g"].tolist() == [30.0, 80.0, 50.0]
