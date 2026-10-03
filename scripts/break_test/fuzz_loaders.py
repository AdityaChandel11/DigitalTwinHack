"""Break test, loaders: malformed dataset files. Run from the repo root: uv run python fuzz_loaders.py"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "tests")

import numpy as np
import pandas as pd
from test_cgmacros import _write_participant

from chhaya.data import cgmacros, shanghai
from chhaya.twin.inputs import build_inputs

RESULTS = []
CLEAR = (ValueError, FileNotFoundError)  # the loaders' own, deliberate errors


def attack(name):
    def deco(fn):
        try:
            status, detail = fn()
        except CLEAR as e:
            status, detail = "OK", f"clear error: {type(e).__name__}: {str(e)[:150]}"
        except Exception as e:
            status, detail = "CRASH", f"{type(e).__name__}: {str(e)[:150]}"
        RESULTS.append((name, status, detail))
        print(f"[{status:5}] {name}: {detail}", flush=True)
        return fn

    return deco


def cg_tree(mutate=None, bio=True, n=1, variant="full"):
    """A temp CGMacros tree with one participant; `mutate(df) -> df` edits the participant file."""
    root = Path(tempfile.mkdtemp())
    for i in range(1, n + 1):
        _write_participant(root, i, variant=variant)
    path = root / "CGMacros-001" / "CGMacros-001.csv"
    if mutate is not None:
        df = mutate(pd.read_csv(path))
        df.to_csv(path, index=False)
    if bio:
        pd.DataFrame(
            {
                "subject": list(range(1, n + 1)),
                "Age": 50,
                "Gender": "F",
                "BMI": 30.0,
                "Body weight ": 200.0,
                "Height ": 65,
                "A1c PDL (Lab)": 7.0,
                "Fasting GLU - PDL (Lab)": 140,
                "Insulin ": 15.0,
            }
        ).to_csv(root / "bio.csv", index=False)
    return root


def describe(recs):
    r = recs[0]
    inp, obs_idx, _ = build_inputs(r)
    return f"{len(recs)} recording(s); {len(r.cgm)} CGM, {len(r.meals)} meals, carbs {r.meals['carb_g'].sum():.0f} g, max MET {float(inp.met.max()):.1f}"


@attack("cgmacros: participant file with a header and no rows")
def _():
    return "OK", describe(cgmacros.load_all(cg_tree(lambda d: d.iloc[:0])))


@attack("cgmacros: sensor column contains LO / HI tokens (as real Libre exports do)")
def _():
    def m(d):
        d["Libre GL"] = d["Libre GL"].astype(object)
        d.loc[100:130, "Libre GL"] = "LO"
        d.loc[900:930, "Libre GL"] = "HI"
        return d

    return "OK", describe(cgmacros.load_all(cg_tree(m)))


@attack("cgmacros: decimal commas in the sensor column")
def _():
    def m(d):
        d["Libre GL"] = d["Libre GL"].map(lambda v: f"{v:.1f}".replace(".", ","))
        return d

    recs = cgmacros.load_all(cg_tree(m))
    return (
        "WEAK" if recs[0].static["primary_sensor"] != "libre" else "OK"
    ), f"primary sensor silently became {recs[0].static['primary_sensor']}; " + describe(recs)


@attack("cgmacros: no Timestamp column")
def _():
    return "OK", describe(cgmacros.load_all(cg_tree(lambda d: d.rename(columns={"Timestamp": "Time"}))))


@attack("cgmacros: every timestamp unparseable")
def _():
    return "OK", describe(cgmacros.load_all(cg_tree(lambda d: d.assign(Timestamp="not a date"))))


@attack("cgmacros: both sensors empty for the only participant")
def _():
    return "OK", describe(
        cgmacros.load_all(cg_tree(lambda d: d.assign(**{"Libre GL": np.nan, "Dexcom GL": np.nan})))
    )


@attack("cgmacros: participant absent from bio.csv")
def _():
    root = cg_tree()
    pd.read_csv(root / "bio.csv").assign(subject=99).to_csv(root / "bio.csv", index=False)
    recs = cgmacros.load_all(root)
    inp, _, _ = build_inputs(recs[0])
    return (
        "OK",
        f"loaded with defaults: body mass {inp.body_mass} kg, fasting insulin {inp.ib}; group {recs[0].static['group']}",
    )


@attack("cgmacros: no METs column and no body weight")
def _():
    root = cg_tree(variant="sparse")
    pd.read_csv(root / "bio.csv").assign(**{"Body weight ": np.nan}).to_csv(root / "bio.csv", index=False)
    recs = cgmacros.load_all(root)
    return "OK", f"activity source {recs[0].static['activity_source']!r}; " + describe(recs)


@attack("cgmacros: bio.csv identifies participants as text (CGMacros-001)")
def _():
    root = cg_tree()
    pd.read_csv(root / "bio.csv").assign(subject="CGMacros-001").to_csv(root / "bio.csv", index=False)
    return "OK", describe(cgmacros.load_all(root))


@attack("cgmacros: body weight of 0 in bio.csv")
def _():
    root = cg_tree()
    pd.read_csv(root / "bio.csv").assign(**{"Body weight ": 0.0}).to_csv(root / "bio.csv", index=False)
    recs = cgmacros.load_all(root)
    inp, _, _ = build_inputs(recs[0])
    return ("BREAK" if inp.body_mass <= 0 else "OK"), f"body mass passed to the model: {inp.body_mass} kg"


@attack("cgmacros: clock set back an hour mid-recording (duplicated timestamps)")
def _():
    def m(d):
        t = pd.to_datetime(d["Timestamp"])
        t[1000:] = t[1000:] - pd.Timedelta(hours=1)
        return d.assign(Timestamp=t.dt.strftime("%Y-%m-%d %H:%M:%S"))

    recs = cgmacros.load_all(cg_tree(m))
    return (
        "WEAK",
        f"an hour of rows is dropped as duplicates without a warning; {describe(recs)}; n_min {recs[0].n_min}",
    )


@attack("cgmacros: a meal row whose carbohydrate is text")
def _():
    def m(d):
        d["Carbs"] = d["Carbs"].astype(object)
        d.loc[60, "Carbs"] = "about 60"
        return d

    return "OK", describe(cgmacros.load_all(cg_tree(m)))


def sh_tree(mutate=None, summary=True):
    root = Path(tempfile.mkdtemp())
    (root / "Shanghai_T2DM").mkdir()
    n = 3 * 96
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2021-07-01 08:00", periods=n, freq="15min"),
            "CGM (mg / dl)": 150.0 + 30.0 * np.sin(np.arange(n) / 10.0),
            "CBG (mg / dl)": np.nan,
            "Dietary intake": None,
            "Insulin dose - s.c.": None,
            "Non-insulin hypoglycemic agents": None,
        }
    )
    df.loc[[2, 50], "CBG (mg / dl)"] = [171.0, 142.2]
    df.loc[1, "Dietary intake"] = "rice 100 g"
    if mutate is not None:
        df = mutate(df)
    df.to_excel(root / "Shanghai_T2DM" / "2001_0_20210701.xlsx", index=False)
    if summary:
        pd.DataFrame(
            {
                "Patient Number": ["2001_0_20210701"],
                "Age (years)": [63],
                "Weight (kg)": [68.0],
                "Fasting Plasma Glucose (mg/dl)": [158.4],
                "Fasting Insulin (pmol/L)": [72.0],
                "HbA1c (mmol/mol)": [69],
            }
        ).to_excel(root / "Shanghai_T2DM_Summary.xlsx", index=False)
    return root


@attack("shanghai: CGM cells containing text (HI, blanks)")
def _():
    def m(d):
        d["CGM (mg / dl)"] = d["CGM (mg / dl)"].astype(object)
        d.loc[10:20, "CGM (mg / dl)"] = "HI"
        return d

    recs = shanghai.load_all(sh_tree(m))
    return "OK", f"{len(recs[0].cgm)} of 288 readings kept"


@attack("shanghai: workbook with headers and no rows")
def _():
    recs = shanghai.load_all(sh_tree(lambda d: d.iloc[:0]))
    return ("WEAK" if recs == [] else "OK"), f"load_all returned {len(recs)} recordings and no error"


@attack("shanghai: summary sheet missing")
def _():
    return "OK", str(len(shanghai.load_all(sh_tree(summary=False))))


@attack("shanghai: dates stored as text")
def _():
    recs = shanghai.load_all(sh_tree(lambda d: d.assign(Date=d["Date"].dt.strftime("%Y/%m/%d %H:%M"))))
    return "OK", f"{len(recs[0].cgm)} readings, start {recs[0].start}"


@attack("shanghai: fingersticks in mmol/L while the sensor is in mg/dL")
def _():
    def m(d):
        d.loc[[2, 50], "CBG (mg / dl)"] = [9.5, 7.9]
        return d

    fs = shanghai.load_all(sh_tree(m))[0].fingersticks["glucose_mgdl"].round(0).tolist()
    return ("OK" if min(fs) > 100 else "BREAK"), f"fingersticks stored as {fs} mg/dL"


@attack("shanghai: a single fingerstick of 5.6 (mmol/L) among mg/dL values")
def _():
    def m(d):
        d.loc[[2, 50, 80], "CBG (mg / dl)"] = [171.0, 5.6, 142.0]
        return d

    fs = shanghai.load_all(sh_tree(m))[0].fingersticks["glucose_mgdl"].round(1).tolist()
    return (
        "WEAK" if len(fs) == 2 else "OK"
    ), f"fingersticks kept: {fs} (the 5.6 is dropped as out of range, silently)"


print()
print("SUMMARY", {s: sum(1 for r in RESULTS if r[1] == s) for s in ("OK", "WEAK", "BREAK", "CRASH")})
for name, status, detail in RESULTS:
    if status != "OK":
        print(f"  {status}: {name} -> {detail}")
