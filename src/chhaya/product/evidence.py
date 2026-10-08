"""The Evidence screen's data: every number read from `results/`, every word from `claims.py` (rule 8).

Each figure value carries the `quote` it must be found as in its claim. `tests/test_product_evidence.py`
checks that, so the figures and the wording cannot drift apart: a rerun that changes a number breaks the test
until the record, and with it the claim, says the new number.
"""

from __future__ import annotations

import json
from pathlib import Path

from chhaya.config import RESULTS_DIR
from chhaya.product import wording
from chhaya.product.claims import CLAIMS, tally

LIMITS = (
    "No Indian data.",
    "Shanghai is supervised care with treatment being adjusted.",
    "Hidden windows are at most eleven days, and these data do not give a number of days for how long a report "
    "stays true: about 1 mg/dL per day, downward, in supervised care; none detected over a week in free-living "
    "participants; eight patients re-recorded up to 168 days later (a case series, not a rule).",
    "The effect of the physiology is about 2 %.",
    "Against the next fingerstick the estimate is about 22 % off where a real sensor is about 12 %",
    "No exogenous insulin, no drug kinetics, no counter-regulation in the model.",
)
DATA = (
    {
        "name": "ShanghaiT2DM",
        "what": "100 patients with type 2 diabetes, 109 recordings of 3 to 14 days, supervised care. Sensor every "
        "15 minutes, fingersticks, diet text, drugs, laboratory values.",
        "licence": "CC BY 4.0",
    },
    {
        "name": "CGMacros",
        "what": "45 free-living participants. Two sensors, a wrist band, meal macronutrients. No medication data.",
        "licence": "CC BY-NC-SA 4.0, non-commercial",
    },
)
COMMANDS = {c.id: c.command for c in CLAIMS}


def _load(results_dir: Path, rel: str, claim_id: str) -> dict:
    path = results_dir / rel
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing; regenerate it with `{COMMANDS[claim_id]}`")
    return json.loads(path.read_text(encoding="utf-8"))


def _v(value: float, text: str, quote=(), lo: float | None = None, hi: float | None = None) -> dict:
    out = {"value": float(value), "text": text, "quote": [quote] if isinstance(quote, str) else list(quote)}
    if lo is not None:
        out.update({"lo": float(lo), "hi": float(hi)})
    return out


def _by(rows: list[dict], **want) -> dict:
    return next(r for r in rows if all(r[k] == v for k, v in want.items()))


def values(results_dir: Path = RESULTS_DIR) -> dict[str, dict]:
    """Every figure value by key, with the text shown and the words it is quoted as in its claim."""
    out: dict[str, dict] = {}
    g2 = _load(results_dir, "gate2/cgmacros-test/summary.json", "gate2")["primary"]
    closer = g2["day_rmse"] - g2["twin_rmse"]
    out["gate2.twin"] = _v(g2["twin_rmse"], f"{g2['twin_rmse']:.1f}", f"{closer:.1f} mg/dL")
    out["gate2.day"] = _v(g2["day_rmse"], f"{g2['day_rmse']:.1f}")

    la = _load(results_dir, "audit/label_validity.json", "label")
    low, high, night = la["thresholds"]["below_70"], la["thresholds"]["above_180"], la["sensor_below_70"]
    at_night = round(night["night_confirmed_share"] * night["night_n"])
    out["label.low"] = {
        "n": low["both"], "of": low["sensor_flags"], "note": f"At night, {at_night} of {night['night_n']}.",
        "quote": [f"{low['both']} ({100 * low['ppv']:.1f} %) were confirmed", f"{at_night} of {night['night_n']} at night"],
    }  # fmt: skip
    out["label.high"] = {
        "n": high["both"], "of": high["sensor_flags"], "note": "",
        "quote": [f"of {high['sensor_flags']} sensor readings above 180, {high['both']} ({100 * high['ppv']:.1f} %)"],
    }  # fmt: skip

    g3 = _load(results_dir, "gate3/shanghai/summary.json", "gate3")["primary"]
    quoted = {
        "fused": "AUPRC {}",
        "fingersticks": "fingersticks only: {}",
        "personal_rate": "({};",
        "sensor_on": "reaches {}",
    }
    for arm, key in (("record", "record"), ("history", "history"), ("fingersticks", "fingersticks"),
                     ("fused", "fused"), ("personal_rate", "personal"), ("sensor_on", "sensor_on")):  # fmt: skip
        a = g3["arms"][arm]["auprc"]
        out[f"gate3.{key}"] = _v(a, f"{a:.2f}", quoted[arm].format(f"{a:.2f}") if arm in quoted else ())
    out["gate3.prevalence"] = _v(
        g3["prevalence"], f"{g3['prevalence']:.2f}", f"{100 * g3['prevalence']:.0f} %"
    )

    k1 = _by(_load(results_dir, "fusion/summary.json", "prior")["by_k"], k_days=1)
    out["prior.diff"] = _v(
        abs(k1["twin_median_diff"]),
        f"{abs(k1['twin_median_diff']):.2f} mg/dL",
        f"{abs(k1['twin_median_diff']):.2f} mg/dL",
    )
    out["prior.p"] = _v(k1["twin_p"], f"p = {k1['twin_p']:.2f}", f"p = {k1['twin_p']:.2f}")

    rules = _load(results_dir, "fingersticks/shanghai/summary.json", "sticks")["by_k"][0]["rules"]
    for key, name in (("live", "live"), ("hindsight", "hindsight")):
        d, lo, hi = (
            -rules["all"][f"{name}_median_diff"],
            -rules["all"][f"{name}_diff_hi"],
            -rules["all"][f"{name}_diff_lo"],
        )
        out[f"sticks.{key}"] = _v(d, f"{d:.1f}", [f"{d:.1f} mg/dL closer", f"{lo:.1f} to {hi:.1f}"], lo, hi)
    one = -rules["1/day"]["live_median_diff"]
    out["sticks.one_a_day"] = _v(one, f"{one:.1f}", f"{one:.1f} mg/dL")

    err = _load(results_dir, "fingersticks/shanghai-report/summary.json", "report")["by_k"][0]["mean"][
        "errors"
    ]
    out["report.stale"] = _v(err["stale"], f"{err['stale']:.1f}", f"median of {err['stale']:.1f} mg/dL")
    out["report.hindsight"] = _v(
        err["hindsight"], f"{err['hindsight']:.1f}", f"missed it by {err['hindsight']:.1f}"
    )
    out["report.sticks"] = _v(err["sticks"], f"{err['sticks']:.1f}", f"({err['sticks']:.1f})")
    out["report.sticks_raw"] = _v(
        err["sticks_raw"], f"{err['sticks_raw']:.1f}", f"{err['sticks_raw']:.1f} mg/dL from the sensor's mean"
    )

    for name, words in (("shanghai", "{:.1f} mg/dL per day (95 % interval {:.1f} to {:.1f})"),
                        ("cgmacros", "{:.1f} mg/dL per day, interval {:.1f} to {:.1f}")):  # fmt: skip
        slopes = _load(results_dir, f"expiry/{name}/summary.json", "expiry")["by_k"][0]["slopes"]
        s = _by(slopes, column="abs_dmean")
        m, lo, hi = s["median_slope"], s["slope_lo"], s["slope_hi"]
        out[f"expiry.{name}"] = _v(m, f"{m:.1f}", words.format(m, lo, hi), lo, hi)

    cal = _load(results_dir, "calibrate/cgmacros/summary.json", "band")["by_k"][0]
    b, a = cal["before"], cal["after"]
    out["band.scored"] = _v(
        100 * b["mean_coverage"], f"{100 * b['mean_coverage']:.1f}",
        [f"{100 * b['mean_coverage']:.1f} %", f"between {100 * b['min']:.0f} % and {100 * b['max']:.1f} %"],
        100 * b["min"], 100 * b["max"],
    )  # fmt: skip
    out["band.recalibrated"] = _v(
        100 * a["mean_coverage"], f"{100 * a['mean_coverage']:.1f}", f"{100 * a['mean_coverage']:.1f} %"
    )

    st = _load(results_dir, "staleness/shanghai/summary.json", "stale")["by_k"][0]
    sc, pl = st["auroc"]["score"], st["auroc"]["plain"]
    out["stale.score"] = _v(
        sc["auroc"],
        f"{sc['auroc']:.2f}",
        f"AUROC {sc['auroc']:.2f} (95 % interval {sc['lo']:.2f} to {sc['hi']:.2f})",
        sc["lo"],
        sc["hi"],
    )
    out["stale.plain"] = _v(
        pl["auroc"],
        f"{pl['auroc']:.2f}",
        f"{pl['auroc']:.2f} ({pl['lo']:.2f} to {pl['hi']:.2f})",
        pl["lo"],
        pl["hi"],
    )
    hit = st["score"]
    out["stale.raised"] = {
        "text": f"{hit['drifted_alarmed']} of {hit['n_drifted']} drifted",
        "quote": [f"{hit['drifted_alarmed']} of {hit['n_drifted']} drifted recordings"],
    }
    out["stale.false"] = {
        "text": f"{hit['quiet_alarmed']} of {hit['n_quiet']} stable",
        "quote": [f"{hit['quiet_alarmed']} of {hit['n_quiet']} stable ones"],
    }

    bands = _load(results_dir, "stickband/shanghai/summary.json", "stickband")["by_k"][0]["bands"]
    for key, words in (("live", "{:.1f} % of hidden sensor readings"), ("hindsight", "{:.1f} % around")):
        s = bands[key]["patient"]
        out[f"stickband.{key}"] = _v(
            s["mean"], f"{s['mean']:.1f}", words.format(s["mean"]), s["min"], s["max"]
        )
    f = bands["live"]["filter"]
    out["stickband.filter"] = _v(f["mean"], f"{f['mean']:.1f}", (), f["min"], f["max"])
    return out


def _figure(spec: dict, found: dict[str, dict]) -> dict:
    fig = {k: v for k, v in spec.items() if k not in ("items", "counts", "ref")}
    fig["items"] = [{"label": i["label"], "emph": i["emph"], **found[i["key"]]} for i in spec["items"]]
    if "counts" in spec:
        fig["counts"] = [{"label": c["label"], **found[c["key"]]} for c in spec["counts"]]
    if "ref" in spec:
        ref = spec["ref"]
        fig["ref"] = {
            "label": ref["label"],
            "value": ref["value"] if "value" in ref else found[ref["key"]]["value"],
        }
        if "key" in ref:
            fig["ref"]["label"] = f"{ref['label']} {found[ref['key']]['text']}"
            fig["ref"]["quote"] = found[ref["key"]]["quote"]
    return fig


def evidence(results_dir: Path = RESULTS_DIR) -> dict:
    found = values(results_dir)
    return {
        "tally": tally(),
        "fusion": wording.FUSION,
        "results": [
            {
                **c._asdict(),
                "bars": list(c.bars),
                "bar_text": list(c.bar_text),
                "figure": _figure(c.figure, found),
            }
            for c in CLAIMS
        ],
        "limits": [f"{line}." if not line.endswith(".") else line for line in LIMITS],
        "data": list(DATA),
    }
