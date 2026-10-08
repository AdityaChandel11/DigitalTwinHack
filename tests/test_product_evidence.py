"""The Evidence screen: numbers from results/, words from the records, and the two must agree."""

import json

import pytest

from chhaya.config import REPO_ROOT
from chhaya.product.evidence import LIMITS, evidence

EV = evidence()


def _quotes(result: dict):
    fig = result["figure"]
    for item in [*fig["items"], *fig.get("counts", []), *([fig["ref"]] if "ref" in fig else [])]:
        yield from item.get("quote", [])


@pytest.mark.parametrize("result", EV["results"], ids=[r["id"] for r in EV["results"]])
def test_every_figure_value_is_found_in_the_words_of_its_claim(result):
    quotes = list(_quotes(result))
    assert quotes, "a figure with no number tied to its claim"
    for quote in quotes:
        assert quote in result["claim"], quote


def test_the_screen_is_strict_json_with_ten_results_and_the_tally():
    json.dumps(EV, allow_nan=False)
    assert len(EV["results"]) == 10 and EV["tally"] == {"bars": 9, "passed": 5, "missed": 4, "descriptive": 6}


def test_the_label_check_and_both_aurocs_are_the_committed_numbers():
    by = {r["id"]: r["figure"] for r in EV["results"]}
    low, high = by["label"]["items"]
    assert (low["n"], low["of"], high["n"], high["of"]) == (8, 64, 732, 809) and "0 of 9" in low["note"]
    score, plain = by["stale"]["items"]
    assert score["text"] == plain["text"] == "0.82" and (round(score["lo"], 2), round(plain["hi"], 2)) == (
        0.63,
        0.97,
    )


def test_a_missing_results_file_names_the_file_and_the_command_that_writes_it(tmp_path):
    with pytest.raises(FileNotFoundError, match=r"gate2.*chhaya\.eval\.gate2"):
        evidence(tmp_path)


def test_each_limit_is_the_design_specs_own_sentence():
    spec = " ".join(
        (REPO_ROOT / "docs/specs/2026-10-04-chhaya-m3-design.md")
        .read_text(encoding="utf-8")
        .split()
    )
    for line in LIMITS:
        assert line in spec, line
