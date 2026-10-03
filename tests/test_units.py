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
