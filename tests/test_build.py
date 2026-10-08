"""The build command: its guards, and that the committed demo bundle is what the code writes."""

import json

import pytest

from chhaya import build


def test_real_patients_are_read_only_on_request_and_on_committed_code():
    with pytest.raises(SystemExit, match="--confirm"):
        build.check_real(False, "")
    with pytest.raises(SystemExit, match="uncommitted"):
        build.check_real(True, " M src/chhaya/build.py")
    build.check_real(True, "")


def test_the_prompts_thresholds_are_the_ones_the_staleness_pass_committed():
    th = build.thresholds()
    assert set(th) == {3.0, 5.0} and th[3.0] == pytest.approx(5.407, abs=0.001)


def test_the_page_gets_every_sentence_from_the_bundle_and_none_says_alarm():
    words = build.words()
    assert words["limits"].startswith("Research prototype") and set(words["not_computed_reasons"]) == {
        "few_sticks",
        "wear_length",
        "too_late",
    }
    assert "alarm" not in json.dumps(words).lower()


def test_the_committed_demo_bundle_holds_the_synthetic_patient_only_and_strict_json():
    index = json.loads((build.DEMO_DIR / "index.json").read_text(encoding="utf-8"))
    assert index["bundle"] == "demo" and [p["id"] for p in index["patients"]] == ["mrs-r"]
    assert index["patients"][0]["synthetic"] is True
    patient = json.loads((build.DEMO_DIR / "patients" / "mrs-r.json").read_text(encoding="utf-8"))
    assert patient["estimate"] == {"kind": "twin"} and patient["treatment"] == {"state": "changed", "day": 2}
    assert len(json.loads((build.DEMO_DIR / "evidence.json").read_text(encoding="utf-8"))["results"]) == 10


@pytest.mark.slow
def test_a_rebuild_gives_the_committed_demo_patient(tmp_path):
    fresh = build.demo_patient(build.thresholds())
    committed = json.loads((build.DEMO_DIR / "patients" / "mrs-r.json").read_text(encoding="utf-8"))
    assert {k: fresh[k] for k in ("prompt", "since", "treatment", "days_since")} == {
        k: committed[k] for k in ("prompt", "since", "treatment", "days_since")
    }
    a, b = fresh["days"][0], committed["days"][0]
    assert a["t"] == b["t"] and max(abs(x - y) for x, y in zip(a["est"], b["est"], strict=True)) < 0.5
