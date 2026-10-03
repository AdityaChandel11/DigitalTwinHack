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
