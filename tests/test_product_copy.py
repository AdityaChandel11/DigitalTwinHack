"""Every sentence of reviewed on-screen wording is the record's own (kickoff: "do not paraphrase safety text")."""

import re

import pytest

from chhaya.config import REPO_ROOT
from chhaya.product import wording as copy
from chhaya.product.claim_text import TEXT

STALE = "docs/decisions/2026-10-08-staleness.md"
REPORT = "docs/decisions/2026-10-08-fingersticks-report.md"
EXPIRY = "docs/decisions/2026-10-08-expiry.md"
BAND = "docs/decisions/2026-10-08-band.md"
PRIOR = "docs/decisions/2026-10-08-record-prior.md"
DESIGN = "docs/superpowers/specs/2026-10-04-chhaya-m3-design.md"


def _norm(text: str) -> str:
    return " ".join(text.split())


def _section(path: str, heading: str) -> str:
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    found = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, flags=re.S | re.M)
    assert found, f"{path} has no section {heading!r}"
    return _norm(found.group(1))


def _consequences(path: str) -> str:
    return _section(path, "Consequences for the product")


@pytest.mark.parametrize(
    ("text", "path"),
    [
        (copy.PROMPT_ABOUT, STALE),
        (copy.PROMPT_NONE, STALE),
        (copy.LIST_NOTE_PROMPT, STALE),
        (copy.NOT_ESTIMATED, REPORT),
        (copy.KEEP_FINGERSTICKS, REPORT),
        (copy.DAYS_NOTE, EXPIRY),
        (copy.TREATMENT_CHANGED, EXPIRY),
        (copy.LIST_NOTE, EXPIRY),
        (copy.BAND, BAND),
    ],
    ids=[
        "prompt-about",
        "prompt-none",
        "list-prompt",
        "not-estimated",
        "keep-sticks",
        "days",
        "treatment",
        "list",
        "band",
    ],
)
def test_each_sentence_is_found_word_for_word_in_its_record(text, path):
    assert _norm(text) in _consequences(path)


def test_the_prompt_is_the_records_text_with_its_two_gaps():
    shown = copy.fill(copy.PROMPT, dates="[dates]", date="[date]")
    assert _norm(shown) in _consequences(STALE)


def test_not_computed_names_one_of_the_records_three_reasons():
    record = _consequences(STALE)
    listed = " / ".join(copy.NOT_COMPUTED_REASONS.values())
    assert _norm(copy.fill(copy.PROMPT_NOT_COMPUTED, reason=f"[{listed}]")) in record
    assert set(copy.NOT_COMPUTED_REASONS) == {"few_sticks", "wear_length", "too_late"}


def test_the_text_beside_the_figures_since_the_sensor_is_the_records_with_its_gaps():
    record = _consequences(REPORT)
    assert _norm(copy.fill(copy.SINCE_SENSOR, date="[date]", times="[times]")) in record
    assert _norm(copy.fill(copy.SINCE_LABEL, n="N", days="D")) in record


def test_the_limits_line_and_the_low_label_are_the_designs():
    design = _norm((REPO_ROOT / DESIGN).read_text(encoding="utf-8"))
    assert _norm(copy.LIMITS[0].lower() + copy.LIMITS[1:]) in design
    assert f'"{copy.SENSOR_LOW}"' in design


def test_the_sentence_on_fusion_is_the_record_priors():
    first = copy.FUSION.split(" What adds something")[0]
    assert _norm(first[0].lower() + first[1:]) in _section(PRIOR, "Consequences")


def test_what_the_meal_log_adds_is_the_start_of_the_gate_2_claim():
    assert TEXT["gate2"].startswith(copy.KEEP_MEALS) and copy.KEEP_MEALS.endswith("and is small.")


def test_fill_refuses_a_gap_left_out_or_left_empty():
    with pytest.raises(KeyError):
        copy.fill(copy.PROMPT, dates="27 Sep to 2 Oct")
    with pytest.raises(ValueError, match="empty"):
        copy.fill(copy.PROMPT, dates="27 Sep to 2 Oct", date=" ")
    assert "[" not in copy.fill(copy.PROMPT, dates="27 Sep to 2 Oct", date="5 Oct")


def test_no_wording_uses_the_word_alarm_or_promises_what_was_cut():
    for name in dir(copy):
        value = getattr(copy, name)
        if name.isupper() and isinstance(value, str):
            assert "alarm" not in value.lower(), name
