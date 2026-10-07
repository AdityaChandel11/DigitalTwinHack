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
    p = pd.DataFrame(
        {"cgm": [60.0, 65.0, 60.0, 200.0, 190.0, 100.0], "cbg": [65.0, 95.0, 100.0, 210.0, 170.0, 60.0]}
    )
    v = validity_table(p)
    assert v["below_70"] == {
        "sensor_flags": 3,
        "fingerstick_flags": 2,
        "both": 1,
        "ppv": 1 / 3,
        "sensitivity": 0.5,
    }
    assert v["above_180"]["sensor_flags"] == 2 and v["above_180"]["both"] == 1
    assert v["above_180"]["ppv"] == 0.5 and v["above_180"]["sensitivity"] == 1.0


def test_label_validity_reports_pairs_and_patients(rec):
    sticks = pd.DataFrame({"t_min": [30.0, 600.0], "glucose_mgdl": [100.0, 150.0]})
    out = label_validity([dataclasses.replace(rec, fingersticks=sticks)])
    assert out["n_pairs"] == 2 and out["n_patients"] == 1
    assert set(out["thresholds"]) == {"below_54", "below_70", "above_180", "above_250"}
    assert out["mard_percent"] > 0.0
