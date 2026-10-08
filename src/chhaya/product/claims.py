"""The results the Evidence screen shows, in its order: grade, bars, wording, command, record, figure.

Wording only. Each claim is its record's "claim to quote", whole (`claim_text.py`); each bar is the registered
one (docs/PREREGISTRATION.md). No number is computed here: `evidence.py` reads every figure value from
`results/`, by the `key` of each figure item.
"""

from __future__ import annotations

from typing import NamedTuple

from chhaya.product.claim_text import TEXT


class Claim(NamedTuple):
    id: str
    grade: str  # "pass", "miss" or "descriptive"
    bars: tuple[str, ...]  # the registered bars it was judged by; none for a descriptive result
    title: str
    sub: str
    claim: str
    bar_text: tuple[str, ...]  # the bar as written beforehand, then what a reader must be told with it
    cohort: str
    command: str
    record: str  # path inside the repository
    figure: dict  # what to draw; item values are filled from results/ by evidence.py


def _item(key: str, label: str, emph: bool = False) -> dict:
    return {"key": key, "label": label, "emph": emph}


CLAIMS: tuple[Claim, ...] = (
    Claim(
        id="gate2",
        grade="pass",
        bars=("P1", "P2", "P3"),
        title="The reveal",
        sub="Gate 2",
        claim=TEXT["gate2"],
        bar_text=(
            "Bar, written before the run. P1: the median over patients of (twin RMSE minus average-day RMSE) is "
            "below 0, and a one-sided Wilcoxon signed-rank test gives p < 0.05.",
            "P2 passes only because its bar cannot discriminate: time in range is not a strength, and no time in "
            "range is shown from any estimate.",
        ),
        cohort="CGMacros, free-living · 19 held-out participants",
        command="python -m chhaya.eval.gate2 --dataset cgmacros --k 3 5 7",
        record="docs/decisions/2026-10-04-gate2-corrected.md",
        figure={
            "type": "dots",
            "title": "Distance from the hidden sensor",
            "unit": "RMSE in mg/dL, lower is closer",
            "min": 20,
            "max": 25,
            "items": [
                _item("gate2.twin", "Chhaya", True),
                _item("gate2.day", "The patient's average day"),
            ],
        },
    ),
    Claim(
        id="label",
        grade="descriptive",
        bars=(),
        title="Which readings not to believe",
        sub="Label check",
        claim=TEXT["label"],
        bar_text=(
            "No bar. A check of the labels, run before any model was built on them. It is why there is no "
            'low-glucose estimate anywhere, and why a sensor low on screen reads "sensor low, unconfirmed".',
        ),
        cohort="ShanghaiT2DM, supervised care · all patients",
        command="python -m chhaya.data.audit",
        record="results/audit/label_validity.json",
        figure={
            "type": "counts",
            "title": "Sensor readings confirmed by a fingerstick",
            "unit": "taken within 10 minutes",
            "items": [
                _item("label.low", "sensor lows, below 70 mg/dL"),
                _item("label.high", "sensor highs, above 180 mg/dL"),
            ],
        },
    ),
    Claim(
        id="gate3",
        grade="miss",
        bars=("M1", "M2", "M3"),
        title="Post-meal excursions without the sensor",
        sub="Gate 3",
        claim=TEXT["gate3"],
        bar_text=(
            "Bars, written before the run. M1: fused (sensor off) minus each of record only, sensor history only "
            "and fingersticks only, the lower end of the interval for the AUPRC difference is above 0 for all "
            "three. M2: fused minus the personal rate, lower end of the interval above 0. M3: calibration slope "
            "between 0.8 and 1.2.",
            "All three missed. There is no meal alert, and no probability is shown.",
        ),
        cohort="ShanghaiT2DM, supervised care · 47 held-out patients",
        command="python -m chhaya.eval.gate3 --confirm",
        record="docs/decisions/2026-10-08-gate3.md",
        figure={
            "type": "dots",
            "title": "Predicting an excursion at meal time",
            "unit": "AUPRC, higher is better",
            "min": 0.2,
            "max": 0.8,
            "ref": {"key": "gate3.prevalence", "label": "event rate"},
            "items": [
                _item("gate3.record", "Record only"),
                _item("gate3.history", "Sensor week only"),
                _item("gate3.fingersticks", "Fingersticks only"),
                _item("gate3.fused", "Fused, sensor off", True),
                _item("gate3.personal", "The patient's own rate"),
                _item("gate3.sensor_on", "Sensor on"),
            ],
        },
    ),
    Claim(
        id="prior",
        grade="miss",
        bars=("P1",),
        title="The record as the twin's prior",
        sub="Fusion, second test",
        claim=TEXT["prior"],
        bar_text=(
            "Bar, written before the run. At k = 1, the estimate with the record prior has lower RMSE than with "
            "the population prior: median paired difference below 0, p < 0.05.",
            "Fusion is built and measured. It is not a gain.",
        ),
        cohort="CGMacros, free-living · 20 held-out participants",
        command="python -m chhaya.eval.fusion",
        record="docs/decisions/2026-10-08-record-prior.md",
        figure={
            "type": "stat",
            "title": "Change in the error of the estimate",
            "unit": "with one day of sensor data, median, mg/dL",
            "items": [_item("prior.diff", "median change"), _item("prior.p", "p")],
        },
    ),
    Claim(
        id="sticks",
        grade="pass",
        bars=("F1", "F2"),
        title="Fingersticks keep the report truer",
        sub="Experiment F",
        claim=TEXT["sticks"],
        bar_text=(
            "Bars, written before the run. F1: live estimate against the control, median paired RMSE difference "
            "below 0, p < 0.05. F2: the in-hindsight estimate against the control, the same test.",
            "To be told with it: the filter was chosen on development patients by a criterion other than the "
            "plan's written rule (dated note in the registration, before the test run), and the estimate is still "
            "about 22 % off the next fingerstick where a real sensor is about 12 %.",
        ),
        cohort="ShanghaiT2DM, supervised care · 29 held-out patients",
        command="python -m chhaya.eval.fingersticks --confirm",
        record="docs/decisions/2026-10-08-fingersticks.md",
        figure={
            "type": "dots",
            "title": "Closer to the hidden sensor than the daily shape alone",
            "unit": "mg/dL, with 95 % intervals",
            "min": 0,
            "max": 13,
            "items": [
                _item("sticks.live", "As fingersticks arrive", True),
                _item("sticks.hindsight", "In hindsight", True),
                _item("sticks.one_a_day", "One fingerstick a day"),
            ],
        },
    ),
    Claim(
        id="report",
        grade="descriptive",
        bars=(),
        title="Fingersticks at report level",
        sub="A plain baseline beats our estimator",
        claim=TEXT["report"],
        bar_text=(
            "No bar. Registered as descriptive before the run. The figures on the patient screen therefore come "
            "from the plain converted average, not from our estimator.",
        ),
        cohort="ShanghaiT2DM, supervised care · 29 held-out patients",
        command="python -m chhaya.eval.fingersticks_report --confirm",
        record="docs/decisions/2026-10-08-fingersticks-report.md",
        figure={
            "type": "dots",
            "title": "Miss in mean glucose over the following days",
            "unit": "median, mg/dL, lower is closer",
            "min": 0,
            "max": 20,
            "items": [
                _item("report.stale", "Three-day sensor report"),
                _item("report.hindsight", "Chhaya, rebuilt from fingersticks", True),
                _item("report.sticks", "Plain average, sensor's scale"),
                _item("report.sticks_raw", "Plain average, as read"),
            ],
        },
    ),
    Claim(
        id="expiry",
        grade="descriptive",
        bars=(),
        title="How long the report stays true",
        sub="Expiry",
        claim=TEXT["expiry"],
        bar_text=(
            "No bar. Registered as descriptive before the run. These data do not give a number of days.",
        ),
        cohort="Both cohorts · 47 and 19 held-out; a case series of 8",
        command="python -m chhaya.eval.expiry shanghai --confirm",
        record="docs/decisions/2026-10-08-expiry.md",
        figure={
            "type": "dots",
            "title": "Growth of the distance from the report",
            "unit": "mg/dL per day, with 95 % intervals",
            "min": -1,
            "max": 3,
            "ref": {"value": 0, "label": "no growth"},
            "items": [
                _item("expiry.shanghai", "Supervised care"),
                _item("expiry.cgmacros", "Free-living"),
            ],
        },
    ),
    Claim(
        id="band",
        grade="descriptive",
        bars=(),
        title="The band",
        sub="The recalibration did not transfer",
        claim=TEXT["band"],
        bar_text=(
            "Rule, written before the run. The recalibrated band is used only if, on held-out participants, mean "
            "coverage is no further from 80 % than before and no fewer participants fall within 70 to 90 %. It "
            "was further, so the band is drawn as Gate 2 scored it.",
        ),
        cohort="CGMacros, free-living · 19 held-out participants",
        command="python -m chhaya.eval.calibrate --confirm",
        record="docs/decisions/2026-10-08-band.md",
        figure={
            "type": "dots",
            "title": "Hidden readings inside the 80 % band",
            "unit": "per cent; the line spans individuals",
            "min": 50,
            "max": 100,
            "ref": {"value": 80, "label": "target 80"},
            "items": [
                _item("band.scored", "As scored, shown", True),
                _item("band.recalibrated", "Recalibrated, not used"),
            ],
        },
    ),
    Claim(
        id="stale",
        grade="descriptive",
        bars=(),
        title="The prompt to consider a new sensor wear",
        sub="A plain baseline does as well",
        claim=TEXT["stale"],
        bar_text=(
            "No bar. Registered as descriptive before the run. Not shown to do better than comparing the "
            "fingerstick average with the report. On a patient screen it appears only inside the tested range; "
            "everywhere else it lives here.",
        ),
        cohort="ShanghaiT2DM, supervised care · 32 held-out recordings",
        command="python -m chhaya.eval.staleness --confirm",
        record="docs/decisions/2026-10-08-staleness.md",
        figure={
            "type": "dots",
            "title": "Telling drifted from stable reports",
            "unit": "AUROC with 95 % intervals",
            "min": 0.5,
            "max": 1,
            "ref": {"value": 0.5, "label": "chance"},
            "items": [
                _item("stale.score", "Running sum of fingerstick surprises", True),
                _item("stale.plain", "Fingerstick average against the report"),
            ],
            "counts": [
                {"key": "stale.raised", "label": "Raised in"},
                {"key": "stale.false", "label": "False prompts"},
            ],
        },
    ),
)


def tally() -> dict[str, int]:
    """Bars written before the runs, how many passed and missed, and how many results have no bar."""
    passed = sum(len(c.bars) for c in CLAIMS if c.grade == "pass")
    missed = sum(len(c.bars) for c in CLAIMS if c.grade == "miss")
    return {
        "bars": passed + missed,
        "passed": passed,
        "missed": missed,
        "descriptive": sum(c.grade == "descriptive" for c in CLAIMS),
    }
