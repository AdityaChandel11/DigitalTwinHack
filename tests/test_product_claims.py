"""The nine results as the Evidence screen states them: wording is each record's own, whole (rule 8)."""

import importlib.util
import json
import re

import pytest

from chhaya.config import REPO_ROOT, RESULTS_DIR
from chhaya.product.claims import CLAIMS, tally

BY_ID = {c.id: c for c in CLAIMS}
WHOLE = ["gate3", "prior", "sticks", "report", "expiry", "band", "stale"]


def _norm(text: str) -> str:
    return " ".join(text.split())


def _section(path: str, heading: str = "The claim to quote") -> str:
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    found = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M)
    assert found, f"{path} has no section {heading!r}"
    return found.group(1)


def test_nine_results_in_the_order_of_the_evidence_screen():
    assert [c.id for c in CLAIMS] == [
        "gate2",
        "label",
        "gate3",
        "prior",
        "sticks",
        "report",
        "expiry",
        "band",
        "stale",
    ]


@pytest.mark.parametrize("cid", WHOLE)
def test_each_claim_is_its_records_claim_to_quote_whole(cid):
    claim = BY_ID[cid]
    assert _norm(claim.claim) == _norm(_section(claim.record))


def test_the_gate_2_claim_is_its_records_sentence_with_the_clause_the_expiry_record_corrected():
    claim = BY_ID["gate2"]
    sentence = _norm(_section(claim.record)).split(" This replaces the sentence")[0]
    corrected = _section("docs/decisions/2026-10-08-expiry.md", "What it means for the Gate 2 sentence")
    clause = _norm(" ".join(line[2:] for line in corrected.splitlines() if line.startswith("> ")))
    assert clause.startswith("The gain comes from the meal log and is small.")
    assert _norm(claim.claim) == f"{sentence} {clause}"
    assert "lasts about five days" not in claim.claim


def test_the_label_check_claim_states_the_counts_the_audit_wrote():
    found = json.loads((RESULTS_DIR / "audit" / "label_validity.json").read_text(encoding="utf-8"))
    low, high = found["thresholds"]["below_70"], found["thresholds"]["above_180"]
    claim = BY_ID["label"].claim
    assert f"Of {low['sensor_flags']} sensor readings below 70 mg/dL" in claim
    assert f"{low['both']} ({100 * low['ppv']:.1f} %) were confirmed" in claim
    assert (
        f"of {high['sensor_flags']} sensor readings above 180, {high['both']} ({100 * high['ppv']:.1f} %)"
        in claim
    )


def test_nothing_shown_uses_the_word_alarm():
    for claim in CLAIMS:
        shown = " ".join([claim.title, claim.sub, claim.claim, *claim.bar_text, claim.cohort])
        assert "alarm" not in shown.lower(), claim.id


def test_every_record_exists_and_every_command_names_a_module_that_imports():
    for claim in CLAIMS:
        assert (REPO_ROOT / claim.record).exists(), claim.record
        module = re.search(r"python -m (chhaya[\w.]+)", claim.command).group(1)
        assert importlib.util.find_spec(module) is not None, module


def test_a_result_with_no_bar_is_descriptive_and_one_with_bars_passed_or_missed():
    for claim in CLAIMS:
        assert claim.grade in ("pass", "miss", "descriptive")
        assert (claim.grade == "descriptive") == (not claim.bars), claim.id
        assert claim.bar_text, claim.id


def test_the_tally_is_five_bars_passed_four_missed_and_five_descriptive_results():
    assert tally() == {"bars": 9, "passed": 5, "missed": 4, "descriptive": 5}
